import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminUser
from apps.checkout.models import CheckoutSession
from .models import Payment
from .serializers import CreatePaymentIntentSerializer, CreateRefundSerializer
from .services import PaymentService

logger = logging.getLogger(__name__)


class CreatePaymentIntentView(APIView):
    """
    POST /payments/intent/
    Body: { "session_token": "<token>" }
    Creates a Stripe PaymentIntent for the given checkout session.
    Returns client_secret.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreatePaymentIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["session_token"]
        try:
            session = CheckoutSession.objects.get(session_token=token)
        except CheckoutSession.DoesNotExist:
            return Response(
                {"detail": "Checkout session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if session.is_expired():
            return Response(
                {"detail": "Checkout session has expired."},
                status=status.HTTP_410_GONE,
            )

        if session.status not in (
            CheckoutSession.Status.ACTIVE,
            CheckoutSession.Status.SUBMITTED,
        ):
            return Response(
                {"detail": f"Session is in status '{session.status}'."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            result = PaymentService.create_payment_intent(session)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(
            {
                "client_secret": result["client_secret"],
                "payment_intent_id": result.get("payment_intent_id"),
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    """
    POST /payments/webhooks/stripe/
    CSRF-exempt endpoint that verifies the Stripe signature and processes the event.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # Stripe doesn't send auth headers

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        if not sig_header:
            logger.warning("Stripe webhook received without signature header")
            return Response(
                {"detail": "Missing Stripe-Signature header."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            PaymentService.process_webhook_event(payload, sig_header)
        except ValueError as exc:
            logger.warning("Webhook processing error: %s", exc)
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Unexpected error processing Stripe webhook")
            return Response(
                {"detail": "Webhook processing failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"received": True})


class CreateRefundView(APIView):
    """
    POST /payments/<uuid:pk>/refunds/
    Admin only. Issues a refund for the given Payment.
    Body: { "amount_cents": int, "reason": str, "staff_notes": str }
    """

    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        serializer = CreateRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refund = PaymentService.create_refund(
                payment_id=pk,
                amount_cents=serializer.validated_data["amount_cents"],
                reason=serializer.validated_data["reason"],
                staff_user=request.user,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Unexpected error creating refund for payment %s", pk)
            return Response(
                {"detail": "Refund processing failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "refund_id": str(refund.id),
                "stripe_refund_id": refund.stripe_refund_id,
                "amount_cents": refund.amount_cents,
                "status": refund.status,
            },
            status=status.HTTP_201_CREATED,
        )
