from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ["sku", "unit_price", "quantity", "line_total", "created_at", "updated_at"]
    fields = ["sku", "quantity", "unit_price", "line_total", "created_at"]

    def line_total(self, obj):
        return obj.line_total

    line_total.short_description = "Line Total"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]
    list_display = ["token_short", "user", "item_count", "subtotal", "expires_at", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["token", "user__email"]
    readonly_fields = ["id", "token", "user", "expires_at", "created_at", "updated_at", "subtotal", "item_count"]
    ordering = ["-created_at"]

    def token_short(self, obj):
        return obj.token[:12] + "..."

    token_short.short_description = "Token"

    def subtotal(self, obj):
        return f"${obj.subtotal:.2f}"

    subtotal.short_description = "Subtotal"

    def item_count(self, obj):
        return obj.item_count

    item_count.short_description = "Items"
