from rest_framework import serializers
from apps.catalog.models import SKU
from .models import Cart, CartItem


class CartSKUSerializer(serializers.Serializer):
    """Lightweight SKU representation for cart items."""
    sku_code = serializers.CharField()
    variant_label = serializers.CharField()
    product_title = serializers.SerializerMethodField()
    primary_image_url = serializers.SerializerMethodField()

    def get_product_title(self, obj):
        return obj.product.title

    def get_primary_image_url(self, obj):
        image = obj.product.primary_image
        if image is None:
            return ""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(image.image.url)
        return image.image.url


class CartItemSerializer(serializers.ModelSerializer):
    sku = CartSKUSerializer(read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    max_quantity = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "sku", "quantity", "unit_price", "line_total", "max_quantity"]

    def get_max_quantity(self, obj):
        try:
            stock = obj.sku.stock_level
            if stock.is_unlimited:
                return 999
            return stock.available_quantity
        except Exception:
            return 0


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "token", "items", "subtotal", "item_count"]


class AddToCartSerializer(serializers.Serializer):
    sku_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        sku_id = attrs["sku_id"]
        quantity = attrs["quantity"]

        try:
            sku = SKU.objects.select_related("product", "stock_level").get(pk=sku_id)
        except SKU.DoesNotExist:
            raise serializers.ValidationError({"sku_id": "SKU not found."})

        if not sku.is_active:
            raise serializers.ValidationError({"sku_id": "This item is no longer available."})

        if not sku.product.is_active:
            raise serializers.ValidationError({"sku_id": "This product is no longer available."})

        try:
            stock = sku.stock_level
            if not stock.is_unlimited and stock.available_quantity < quantity:
                raise serializers.ValidationError(
                    {"quantity": f"Only {stock.available_quantity} units available."}
                )
        except Exception as exc:
            if "available_quantity" in str(exc) or "Only" in str(exc):
                raise
            # No stock record — treat as out of stock
            raise serializers.ValidationError({"sku_id": "Stock information unavailable."})

        attrs["sku"] = sku
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        # Context includes the cart item via self.context["cart_item"]
        cart_item = self.context.get("cart_item")
        if cart_item is None:
            return value
        try:
            stock = cart_item.sku.stock_level
            if not stock.is_unlimited and stock.available_quantity < value:
                raise serializers.ValidationError(
                    f"Only {stock.available_quantity} units available."
                )
        except Exception as exc:
            if "available_quantity" in str(exc) or "Only" in str(exc):
                raise
        return value
