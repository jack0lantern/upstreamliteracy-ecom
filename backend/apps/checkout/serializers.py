from decimal import Decimal
from rest_framework import serializers
from .models import CheckoutSession, ShippingRate, TaxCalculation
from .services import STATE_TAX_RATES


class ShippingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingRate
        fields = [
            "id",
            "name",
            "flat_rate",
            "estimated_days_min",
            "estimated_days_max",
            "description",
        ]


class AddressSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    company = serializers.CharField(max_length=200, required=False, allow_blank=True)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=2, min_length=2)
    zip_code = serializers.CharField(max_length=10)
    country = serializers.CharField(max_length=2, default="US")
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def validate_state(self, value):
        return value.upper()

    def validate_country(self, value):
        return value.upper()


class CheckoutSessionSerializer(serializers.ModelSerializer):
    shipping_rate_detail = ShippingRateSerializer(source="shipping_rate", read_only=True)
    computed_total = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = CheckoutSession
        fields = [
            "id",
            "session_token",
            "user",
            "guest_email",
            "current_step",
            "cart_snapshot",
            "shipping_address",
            "billing_address",
            "billing_same_as_shipping",
            "shipping_rate",
            "shipping_rate_detail",
            "shipping_cost",
            "tax_amount",
            "tax_rate",
            "tax_exempt",
            "stripe_payment_intent_id",
            "subtotal",
            "total",
            "computed_total",
            "status",
            "expires_at",
            "is_expired",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "session_token",
            "user",
            "cart_snapshot",
            "subtotal",
            "total",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_computed_total(self, obj):
        shipping = obj.shipping_cost or Decimal("0.00")
        tax = obj.tax_amount or Decimal("0.00")
        return obj.subtotal + shipping + tax

    def get_is_expired(self, obj):
        return obj.is_expired()


class CreateSessionSerializer(serializers.Serializer):
    cart_token = serializers.CharField(required=False, allow_blank=True, default="")


class UpdateContactSerializer(serializers.Serializer):
    guest_email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            # For authenticated users, email comes from the user account
            attrs["guest_email"] = request.user.email
        else:
            if not attrs.get("guest_email"):
                raise serializers.ValidationError(
                    {"guest_email": "Email is required for guest checkout."}
                )
        return attrs


class UpdateAddressSerializer(serializers.Serializer):
    shipping_address = AddressSerializer()
    billing_same_as_shipping = serializers.BooleanField(default=True)
    billing_address = AddressSerializer(required=False)

    def validate(self, attrs):
        if not attrs.get("billing_same_as_shipping") and not attrs.get("billing_address"):
            raise serializers.ValidationError(
                {"billing_address": "Billing address is required when not same as shipping."}
            )
        return attrs


class UpdateShippingSerializer(serializers.Serializer):
    shipping_rate_id = serializers.IntegerField()

    def validate_shipping_rate_id(self, value):
        from .models import ShippingRate
        if not ShippingRate.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Shipping rate not found or inactive.")
        return value


class UpdatePaymentSerializer(serializers.Serializer):
    stripe_payment_method_id = serializers.CharField(max_length=255)


class TaxEstimateSerializer(serializers.Serializer):
    state = serializers.CharField(max_length=2, min_length=2)
    zip = serializers.CharField(max_length=10)
    session_token = serializers.CharField(required=False, allow_blank=True)

    def validate_state(self, value):
        return value.upper()
