from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StockAlert, StockLevel, StockMovement
from .serializers import (
    AcknowledgeAlertSerializer,
    StockAdjustmentRequestSerializer,
    StockAlertSerializer,
    StockLevelSerializer,
    StockMovementSerializer,
)
from .services import InsufficientStockError, adjust_stock


class StockAdjustmentView(APIView):
    """
    POST /inventory/adjustments/

    Admin-only endpoint to manually adjust stock for a SKU.
    Accepts: { sku_id, delta, reason }
    Returns the updated StockLevel.
    """

    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = StockAdjustmentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data["sku_id"]
        delta = serializer.validated_data["delta"]
        reason = serializer.validated_data["reason"]

        try:
            stock = adjust_stock(
                sku_id=sku_id,
                delta=delta,
                reason=reason,
                admin_user=request.user,
            )
        except StockLevel.DoesNotExist:
            return Response(
                {"detail": f"No StockLevel found for SKU ID {sku_id}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            StockLevelSerializer(stock).data,
            status=status.HTTP_200_OK,
        )


class StockAlertViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET  /inventory/alerts/          — list active alerts (admin only)
    GET  /inventory/alerts/{id}/     — retrieve single alert
    PATCH /inventory/alerts/{id}/acknowledge/ — acknowledge an alert
    """

    permission_classes = [IsAdminUser]
    serializer_class = StockAlertSerializer

    def get_queryset(self):
        qs = StockAlert.objects.select_related("sku", "acknowledged_by").order_by(
            "-created_at"
        )
        active_only = self.request.query_params.get("active_only", "true").lower()
        if active_only == "true":
            qs = qs.filter(is_active=True)
        alert_type = self.request.query_params.get("alert_type")
        if alert_type:
            qs = qs.filter(alert_type=alert_type)
        return qs

    @action(detail=True, methods=["patch"], url_path="acknowledge")
    def acknowledge(self, request, pk=None):
        """Mark an alert as acknowledged by the current admin user."""
        alert = self.get_object()

        if not alert.is_active:
            return Response(
                {"detail": "This alert has already been acknowledged or is inactive."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AcknowledgeAlertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        alert.is_active = False
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save(update_fields=["is_active", "acknowledged_by", "acknowledged_at", "updated_at"])

        return Response(
            StockAlertSerializer(alert).data,
            status=status.HTTP_200_OK,
        )
