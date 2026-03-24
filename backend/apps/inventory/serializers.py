from django.utils import timezone
from rest_framework import serializers

from .models import StockAlert, StockLevel, StockMovement


class StockLevelSerializer(serializers.ModelSerializer):
    stock_status = serializers.CharField(read_only=True)
    display_label = serializers.CharField(read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)
    sku_code = serializers.CharField(source="sku.sku_code", read_only=True)

    class Meta:
        model = StockLevel
        fields = [
            "id",
            "sku_code",
            "quantity_on_hand",
            "low_stock_threshold",
            "is_unlimited",
            "backorder_enabled",
            "estimated_restock",
            "available_quantity",
            "stock_status",
            "display_label",
            "updated_at",
        ]
        read_only_fields = ["updated_at", "stock_status", "display_label", "available_quantity"]


class StockMovementSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source="sku.sku_code", read_only=True)
    performed_by_email = serializers.EmailField(
        source="performed_by.email",
        read_only=True,
        default=None,
    )

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "sku_code",
            "movement_type",
            "delta",
            "quantity_after",
            "order",
            "performed_by_email",
            "reason",
            "created_at",
        ]
        read_only_fields = fields


class StockAdjustmentRequestSerializer(serializers.Serializer):
    sku_id = serializers.IntegerField(min_value=1)
    delta = serializers.IntegerField()
    reason = serializers.CharField(max_length=500)

    def validate_delta(self, value):
        if value == 0:
            raise serializers.ValidationError("Delta must be non-zero.")
        return value


class StockAlertSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source="sku.sku_code", read_only=True)
    acknowledged_by_email = serializers.EmailField(
        source="acknowledged_by.email",
        read_only=True,
        default=None,
    )

    class Meta:
        model = StockAlert
        fields = [
            "id",
            "sku_code",
            "alert_type",
            "quantity_at_trigger",
            "is_active",
            "acknowledged_by_email",
            "acknowledged_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "sku_code",
            "alert_type",
            "quantity_at_trigger",
            "acknowledged_by_email",
            "acknowledged_at",
            "created_at",
            "updated_at",
        ]


class AcknowledgeAlertSerializer(serializers.Serializer):
    """Used for the PATCH acknowledge action."""

    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)
