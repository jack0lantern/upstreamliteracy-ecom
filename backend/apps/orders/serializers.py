from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_title",
            "product_slug",
            "sku_code",
            "product_image_url",
            "quantity",
            "unit_price",
            "line_total",
            "product_type",
        ]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.SerializerMethodField()

    class Meta:
        model = OrderStatusHistory
        fields = [
            "id",
            "from_status",
            "to_status",
            "changed_by",
            "changed_by_email",
            "note",
            "created_at",
        ]

    def get_changed_by_email(self, obj):
        if obj.changed_by:
            return obj.changed_by.email
        return None


class OrderSummarySerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "created_at",
            "item_count",
            "total",
        ]

    def get_item_count(self, obj):
        return sum(item.quantity for item in obj.items.all())


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "guest_email",
            "status",
            "shipping_address",
            "billing_address",
            "shipping_method",
            "subtotal",
            "shipping_cost",
            "tax_amount",
            "is_tax_exempt",
            "total",
            "tracking_number",
            "tracking_url",
            "notes",
            "created_at",
            "updated_at",
            "item_count",
            "items",
            "status_history",
        ]

    def get_item_count(self, obj):
        return sum(item.quantity for item in obj.items.all())
