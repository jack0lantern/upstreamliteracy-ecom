import uuid
import logging
from decimal import Decimal

from django.conf import settings

from .models import Payment, Transaction, Refund, WebhookEvent

logger = logging.getLogger(__name__)

_STRIPE_PLACEHOLDER_PREFIX = "sk_test_placeholder"


def _is_stripe_live():
    key = getattr(settings, "STRIPE_SECRET_KEY", "")
    return bool(key) and not key.startswith(_STRIPE_PLACEHOLDER_PREFIX)


class PaymentService:
    @staticmethod
    def create_payment_intent(checkout_session):
        """
        Create a Stripe PaymentIntent for the given checkout session.

        In dev/test mode (STRIPE_SECRET_KEY starts with 'sk_test_placeholder' or is absent),
        skips the real Stripe call and returns a mock client_secret.

        Returns a dict: { "client_secret": str, "payment_intent_id": str | None }
        """
        total = checkout_session.total or Decimal("0.00")
        amount_cents = int(total * 100)

        if not _is_stripe_live():
            mock_intent_id = f"pi_mock_{uuid.uuid4().hex[:16]}"
            mock_client_secret = f"{mock_intent_id}_secret_mock"
            logger.info(
                "Stripe mock mode: returning fake PaymentIntent %s", mock_intent_id
            )
            return {
                "client_secret": mock_client_secret,
                "payment_intent_id": mock_intent_id,
            }

        try:
            import stripe

            stripe.api_key = settings.STRIPE_SECRET_KEY

            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                metadata={
                    "checkout_session_id": str(checkout_session.id),
                    "session_token": checkout_session.session_token,
                    "user_id": str(checkout_session.user_id) if checkout_session.user_id else "",
                    "guest_email": checkout_session.guest_email or "",
                },
                idempotency_key=str(uuid.uuid4()),
            )
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
            }
        except Exception as exc:
            logger.exception("Stripe PaymentIntent creation failed")
            raise ValueError(f"Payment processing error: {exc}") from exc

    @staticmethod
    def process_webhook_event(payload, sig_header):
        """
        Verify the Stripe webhook signature and dispatch to the appropriate handler.

        Returns the WebhookEvent instance.
        Raises ValueError on signature verification failure.
        Raises RuntimeError if event was already processed.
        """
        import stripe

        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except stripe.error.SignatureVerificationError as exc:
            logger.warning("Stripe webhook signature verification failed: %s", exc)
            raise ValueError("Invalid Stripe webhook signature.") from exc
        except Exception as exc:
            logger.exception("Failed to parse Stripe webhook payload")
            raise ValueError("Malformed webhook payload.") from exc

        # Idempotency check
        existing = WebhookEvent.objects.filter(stripe_event_id=event["id"]).first()
        if existing and existing.processed:
            logger.info("Duplicate webhook event %s; skipping.", event["id"])
            return existing

        webhook_event = WebhookEvent.objects.get_or_create(
            stripe_event_id=event["id"],
            defaults={
                "event_type": event["type"],
                "payload": event,
                "processed": False,
            },
        )[0]

        try:
            handler_map = {
                "payment_intent.succeeded": PaymentService.handle_payment_succeeded,
                "payment_intent.payment_failed": PaymentService.handle_payment_failed,
            }
            handler = handler_map.get(event["type"])
            if handler:
                payment = handler(event)
                webhook_event.related_payment = payment
            else:
                logger.debug("Unhandled Stripe event type: %s", event["type"])

            webhook_event.processed = True
            webhook_event.save(update_fields=["processed", "related_payment"])
        except Exception as exc:
            logger.exception("Error processing webhook event %s", event["id"])
            webhook_event.processing_error = str(exc)
            webhook_event.save(update_fields=["processing_error"])

        return webhook_event

    @staticmethod
    def handle_payment_succeeded(event):
        """
        Handle payment_intent.succeeded webhook.
        Marks Payment succeeded, updates Order to PROCESSING, creates Transaction.
        Returns the Payment instance.
        """
        from apps.orders.services import update_order_status
        from apps.orders.models import Order

        intent = event["data"]["object"]
        intent_id = intent["id"]
        charge_id = intent.get("latest_charge", "")

        try:
            payment = Payment.objects.select_related("order").get(
                stripe_payment_intent_id=intent_id
            )
        except Payment.DoesNotExist:
            logger.warning(
                "No Payment found for PaymentIntent %s on succeeded event", intent_id
            )
            return None

        payment.status = Payment.Status.SUCCEEDED
        payment.stripe_charge_id = charge_id
        payment.save(update_fields=["status", "stripe_charge_id", "updated_at"])

        Transaction.objects.create(
            payment=payment,
            type=Transaction.Type.CHARGE,
            amount_cents=payment.amount_cents,
            stripe_object_id=charge_id or intent_id,
            idempotency_key=f"charge-{intent_id}",
            notes=f"Payment succeeded for order {payment.order.order_number}",
        )

        if payment.order.status == Order.Status.PENDING_PAYMENT:
            update_order_status(
                payment.order,
                Order.Status.PROCESSING,
                note="Payment confirmed via Stripe webhook.",
            )

        return payment

    @staticmethod
    def handle_payment_failed(event):
        """
        Handle payment_intent.payment_failed webhook.
        Marks Payment failed and records failure info.
        Returns the Payment instance.
        """
        intent = event["data"]["object"]
        intent_id = intent["id"]
        last_error = intent.get("last_payment_error") or {}
        failure_code = last_error.get("code", "unknown")
        failure_message = last_error.get("message", "Payment failed.")

        try:
            payment = Payment.objects.get(stripe_payment_intent_id=intent_id)
        except Payment.DoesNotExist:
            logger.warning(
                "No Payment found for PaymentIntent %s on failed event", intent_id
            )
            return None

        payment.status = Payment.Status.FAILED
        payment.failure_code = failure_code
        payment.failure_message = failure_message
        payment.save(
            update_fields=["status", "failure_code", "failure_message", "updated_at"]
        )
        return payment

    @staticmethod
    def create_refund(payment_id, amount_cents, reason, staff_user):
        """
        Issue a refund for a Payment.

        Validates the refund amount, calls stripe.Refund.create, creates Refund
        and Transaction records, and updates the Payment status.

        Returns the Refund instance.
        Raises ValueError on validation errors or Stripe failures.
        """
        try:
            payment = Payment.objects.get(pk=payment_id)
        except Payment.DoesNotExist:
            raise ValueError("Payment not found.")

        if payment.status not in (
            Payment.Status.SUCCEEDED,
            Payment.Status.PARTIALLY_REFUNDED,
        ):
            raise ValueError(
                f"Cannot refund a payment with status '{payment.status}'."
            )

        already_refunded = sum(
            r.amount_cents
            for r in payment.refunds.filter(status=Refund.Status.SUCCEEDED)
        )
        refundable = payment.amount_cents - already_refunded
        if amount_cents > refundable:
            raise ValueError(
                f"Refund amount ({amount_cents}¢) exceeds refundable amount ({refundable}¢)."
            )

        idempotency_key = f"refund-{payment_id}-{uuid.uuid4().hex[:8]}"

        stripe_refund_id = None
        if _is_stripe_live():
            try:
                import stripe

                stripe.api_key = settings.STRIPE_SECRET_KEY
                stripe_refund = stripe.Refund.create(
                    payment_intent=payment.stripe_payment_intent_id,
                    amount=amount_cents,
                    reason=reason if reason in ("duplicate", "fraudulent", "requested_by_customer") else "requested_by_customer",
                    idempotency_key=idempotency_key,
                )
                stripe_refund_id = stripe_refund.id
            except Exception as exc:
                logger.exception("Stripe refund creation failed for payment %s", payment_id)
                raise ValueError(f"Stripe refund error: {exc}") from exc
        else:
            stripe_refund_id = f"re_mock_{uuid.uuid4().hex[:16]}"
            logger.info("Stripe mock mode: fake refund %s", stripe_refund_id)

        refund = Refund.objects.create(
            payment=payment,
            initiated_by=staff_user,
            amount_cents=amount_cents,
            reason=reason,
            stripe_refund_id=stripe_refund_id,
            status=Refund.Status.SUCCEEDED,
        )

        Transaction.objects.create(
            payment=payment,
            type=Transaction.Type.REFUND,
            amount_cents=-amount_cents,
            stripe_object_id=stripe_refund_id,
            idempotency_key=idempotency_key,
            notes=f"Refund issued by {staff_user.email}: {reason}",
            created_by=staff_user,
        )

        # Update payment status
        total_refunded = already_refunded + amount_cents
        if total_refunded >= payment.amount_cents:
            payment.status = Payment.Status.REFUNDED
        else:
            payment.status = Payment.Status.PARTIALLY_REFUNDED
        payment.save(update_fields=["status", "updated_at"])

        return refund
