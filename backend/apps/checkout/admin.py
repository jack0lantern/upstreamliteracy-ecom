from django.contrib import admin
from .models import CheckoutSession, ShippingRate, TaxCalculation


class TaxCalculationInline(admin.TabularInline):
    model = TaxCalculation
    extra = 0
    readonly_fields = [
        "destination_state",
        "destination_zip",
        "taxable_amount",
        "tax_rate",
        "tax_amount",
        "is_exempt",
        "provider",
        "calculated_at",
    ]
    fields = [
        "destination_state",
        "destination_zip",
        "taxable_amount",
        "tax_rate",
        "tax_amount",
        "is_exempt",
        "calculated_at",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CheckoutSession)
class CheckoutSessionAdmin(admin.ModelAdmin):
    inlines = [TaxCalculationInline]
    list_display = [
        "session_token_short",
        "status",
        "user",
        "guest_email",
        "subtotal",
        "total",
        "current_step",
        "expires_at",
        "created_at",
    ]
    list_filter = ["status", "current_step", "created_at"]
    search_fields = ["session_token", "guest_email", "user__email"]
    readonly_fields = [
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
        "shipping_cost",
        "tax_amount",
        "tax_rate",
        "tax_exempt",
        "stripe_payment_intent_id",
        "subtotal",
        "total",
        "status",
        "expires_at",
        "order",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    def session_token_short(self, obj):
        return obj.session_token[:12] + "..."

    session_token_short.short_description = "Session Token"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "flat_rate",
        "estimated_days_min",
        "estimated_days_max",
        "is_active",
        "sort_order",
    ]
    list_filter = ["is_active"]
    search_fields = ["name"]
    list_editable = ["flat_rate", "is_active", "sort_order"]
    ordering = ["sort_order", "flat_rate"]
    fields = [
        "name",
        "flat_rate",
        "estimated_days_min",
        "estimated_days_max",
        "description",
        "is_active",
        "sort_order",
    ]
