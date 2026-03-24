import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.models import Cart
from apps.core.email import send_transactional_email
from .models import CheckoutSession, ShippingRate
from .serializers import (
    CheckoutSessionSerializer,
    CreateSessionSerializer,
    UpdateContactSerializer,
    UpdateAddressSerializer,
    UpdateShippingSerializer,
    UpdatePaymentSerializer,
    ShippingRateSerializer,
    TaxEstimateSerializer,
)
from .services import TaxService, ShippingService, STATE_TAX_RATES

logger = logging.getLogger(__name__)


def _get_session_or_404(token):
    try:
        return CheckoutSession.objects.select_related("shipping_rate", "order").get(
            session_token=token
        )
    except CheckoutSession.DoesNotExist:
        return None


def _snapshot_cart(cart):
    """
    Build a serialisable cart snapshot dict from a Cart instance.
    """
    items = []
    for item in cart.items.select_related("sku__product").all():
        product = item.sku.product
        primary_image = product.primary_image
        image_url = ""
        if primary_image:
            try:
                image_url = primary_image.image.url
            except Exception:
                pass
        items.append(
            {
                "sku_code": item.sku.sku_code,
                "variant_label": item.sku.variant_label,
                "product_title": product.title,
                "product_slug": product.slug,
                "product_image_url": image_url,
                "product_type": product.product_type,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "line_total": str(item.line_total),
            }
        )
    return {
        "items": items,
        "subtotal": str(cart.subtotal),
        "item_count": cart.item_count,
    }


class CreateSessionView(APIView):
    """POST /checkout/sessions/ — create a CheckoutSession from a cart."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreateSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart_token = serializer.validated_data.get("cart_token", "")
        cart = None

        if request.user and request.user.is_authenticated:
            cart = (
                Cart.objects.filter(user=request.user)
                .prefetch_related("items__sku__product__images")
                .order_by("-created_at")
                .first()
            )
        elif cart_token:
            try:
                cart = Cart.objects.prefetch_related("items__sku__product__images").get(
                    token=cart_token
                )
            except Cart.DoesNotExist:
                pass

        if cart is None or cart.item_count == 0:
            return Response(
                {"detail": "Cart is empty or not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        snapshot = _snapshot_cart(cart)
        subtotal = Decimal(snapshot["subtotal"])

        session = CheckoutSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            cart_snapshot=snapshot,
            subtotal=subtotal,
            expires_at=timezone.now() + timezone.timedelta(hours=2),
        )

        out = CheckoutSessionSerializer(session)
        return Response(out.data, status=status.HTTP_201_CREATED)


class GetSessionView(APIView):
    """GET /checkout/sessions/<token>/ — return full session state."""

    permission_classes = [AllowAny]

    def get(self, request, token):
        session = _get_session_or_404(token)
        if session is None:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        if session.is_expired() and session.status == CheckoutSession.Status.ACTIVE:
            session.status = CheckoutSession.Status.EXPIRED
            session.save(update_fields=["status"])

        out = CheckoutSessionSerializer(session)
        return Response(out.data)


class UpdateContactView(APIView):
    """PATCH /checkout/sessions/<token>/contact/ — set email."""

    permission_classes = [AllowAny]

    def patch(self, request, token):
        session = _get_session_or_404(token)
        if session is None:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        if session.is_expired():
            return Response({"detail": "Session has expired."}, status=status.HTTP_410_GONE)

        serializer = UpdateContactSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        session.guest_email = serializer.validated_data.get("guest_email", session.guest_email)
        session.current_step = "address"
        session.save(update_fields=["guest_email", "current_step", "updated_at"])
        session.extend_expiry(minutes=60)

        out = CheckoutSessionSerializer(session)
        return Response(out.data)


class UpdateAddressView(APIView):
    """PATCH /checkout/sessions/<token>/address/ — set shipping/billing address, compute tax."""

    permission_classes = [AllowAny]

    def patch(self, request, token):
        session = _get_session_or_404(token)
        if session is None:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        if session.is_expired():
            return Response({"detail": "Session has expired."}, status=status.HTTP_410_GONE)

        serializer = UpdateAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shipping_addr = serializer.validated_data["shipping_address"]
        billing_same = serializer.validated_data["billing_same_as_shipping"]
        billing_addr = (
            shipping_addr
            if billing_same
            else serializer.validated_data.get("billing_address", shipping_addr)
        )

        session.shipping_address = shipping_addr
        session.billing_address = billing_addr
        session.billing_same_as_shipping = billing_same
        session.current_step = "shipping"
        session.save(
            update_fields=[
                "shipping_address",
                "billing_address",
                "billing_same_as_shipping",
                "current_step",
                "updated_at",
            ]
        )

        # Automatically calculate tax based on shipping state
        state = shipping_addr.get("state", "")
        zip_code = shipping_addr.get("zip_code", "")
        if state:
            TaxService.calculate(session, state, zip_code)
            session.refresh_from_db()

        session.compute_total()
        session.extend_expiry(minutes=60)
        session.refresh_from_db()

        out = CheckoutSessionSerializer(session)
        return Response(out.data)


class UpdateShippingView(APIView):
    """PATCH /checkout/sessions/<token>/shipping/ — select shipping rate."""

    permission_classes = [AllowAny]

    def patch(self, request, token):
        session = _get_session_or_404(token)
        if session is None:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        if session.is_expired():
            return Response({"detail": "Session has expired."}, status=status.HTTP_410_GONE)

        serializer = UpdateShippingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rate_id = serializer.validated_data["shipping_rate_id"]
        ShippingService.apply_rate(session, rate_id)
        session.current_step = "payment"
        session.save(update_fields=["current_step", "updated_at"])
        session.compute_total()
        session.extend_expiry(minutes=60)
        session.refresh_from_db()

        out = CheckoutSessionSerializer(session)
        return Response(out.data)


class UpdatePaymentView(APIView):
    """PATCH /checkout/sessions/<token>/payment/ — store stripe payment method."""

    permission_classes = [AllowAny]

    def patch(self, request, token):
        session = _get_session_or_404(token)
        if session is None:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        if session.is_expired():
            return Response({"detail": "Session has expired."}, status=status.HTTP_410_GONE)

        serializer = UpdatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Store the Stripe payment method ID for use during submission.
        # The full PaymentIntent is created at submit time.
        session.current_step = "review"
        session.save(update_fields=["current_step", "updated_at"])
        session.extend_expiry(minutes=60)

        # Attach the payment method id to session metadata (cart_snapshot extension)
        snapshot = session.cart_snapshot or {}
        snapshot["stripe_payment_method_id"] = serializer.validated_data[
            "stripe_payment_method_id"
        ]
        session.cart_snapshot = snapshot
        session.save(update_fields=["cart_snapshot"])
        session.refresh_from_db()

        out = CheckoutSessionSerializer(session)
        return Response(out.data)


class SubmitCheckoutView(APIView):
    """
    POST /checkout/sessions/<token>/submit/

    The main atomic checkout completion:
      1. Validate session readiness
      2. Create Stripe PaymentIntent (mocked when STRIPE_SECRET_KEY is a placeholder)
      3. Create Order + OrderItems
      4. Decrement stock
      5. Mark session as submitted
      6. Send confirmation email
    """

    permission_classes = [AllowAny]

    def post(self, request, token):
        from apps.payments.services import PaymentService
        from apps.orders.services import create_order

        session = _get_session_or_404(token)
        if session is None:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        if session.is_expired():
            return Response({"detail": "Session has expired."}, status=status.HTTP_410_GONE)

        if session.status != CheckoutSession.Status.ACTIVE:
            return Response(
                {"detail": f"Session is already {session.status}."},
                status=status.HTTP_409_CONFLICT,
            )

        # Validate required fields
        errors = {}
        if not session.guest_email and not session.user:
            errors["contact"] = "Email is required."
        if not session.shipping_address:
            errors["shipping_address"] = "Shipping address is required."
        if not session.shipping_rate_id:
            errors["shipping"] = "Shipping rate is required."
        if session.total is None or session.total <= 0:
            errors["total"] = "Order total is invalid."
        if errors:
            return Response(
                {"detail": "Checkout is incomplete.", "errors": errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                # Create PaymentIntent via payments service
                payment_result = PaymentService.create_payment_intent(session)
                client_secret = payment_result["client_secret"]
                intent_id = payment_result.get("payment_intent_id")

                if intent_id:
                    session.stripe_payment_intent_id = intent_id
                    session.save(update_fields=["stripe_payment_intent_id"])

                # Create order
                order = create_order(session)

                # Link order to session
                session.order = order
                session.status = CheckoutSession.Status.SUBMITTED
                session.save(update_fields=["order", "status", "updated_at"])

        except ValueError as exc:
            logger.error("Checkout submission failed: %s", exc)
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except Exception as exc:
            logger.exception("Unexpected error during checkout submission")
            return Response(
                {"detail": "An error occurred processing your order. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Send confirmation email (outside the atomic block so DB is committed)
        recipient = session.guest_email or (session.user.email if session.user else None)
        if recipient:
            try:
                send_transactional_email(
                    subject=f"Order Confirmed — {order.order_number}",
                    message=(
                        f"Thank you for your order!\n\n"
                        f"Order Number: {order.order_number}\n"
                        f"Total: ${order.total}\n\n"
                        f"We'll send a shipping confirmation once your order is on its way."
                    ),
                    to_emails=[recipient],
                )
            except Exception:
                logger.exception("Failed to send order confirmation email for %s", order.order_number)

        return Response(
            {
                "order_number": order.order_number,
                "order_id": str(order.id),
                "client_secret": client_secret,
                "guest_tracking_token": order.guest_tracking_token,
            },
            status=status.HTTP_201_CREATED,
        )


class ShippingRatesView(APIView):
    """GET /checkout/shipping-rates/ — return available shipping rates."""

    permission_classes = [AllowAny]

    def get(self, request):
        rates = ShippingService.get_rates()
        serializer = ShippingRateSerializer(rates, many=True)
        return Response(serializer.data)


class TaxEstimateView(APIView):
    """GET /checkout/tax-estimate/?state=TX&zip=78701 — return tax rate and amount."""

    permission_classes = [AllowAny]

    def get(self, request):
        serializer = TaxEstimateSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        state = serializer.validated_data["state"]
        zip_code = serializer.validated_data["zip"]
        session_token = serializer.validated_data.get("session_token", "")

        from decimal import Decimal as D
        rate = D(str(STATE_TAX_RATES.get(state.upper(), 0)))

        tax_amount = None
        is_exempt = False

        if session_token:
            session = _get_session_or_404(session_token)
            if session:
                is_exempt = session.tax_exempt
                if is_exempt:
                    rate = D("0")
                taxable = session.subtotal
                tax_amount = (taxable * rate).quantize(D("0.01"))

        return Response(
            {
                "state": state,
                "zip": zip_code,
                "tax_rate": str(rate),
                "tax_amount": str(tax_amount) if tax_amount is not None else None,
                "is_exempt": is_exempt,
            }
        )
