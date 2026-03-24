from django.contrib import admin, messages
from .models import Order, OrderItem, OrderStatusHistory
from .services import update_order_status


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = [
        "product_title",
        "product_slug",
        "sku_code",
        "product_image_url",
        "quantity",
        "unit_price",
        "line_total",
        "product_type",
    ]
    fields = [
        "product_title",
        "sku_code",
        "quantity",
        "unit_price",
        "line_total",
        "product_type",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["from_status", "to_status", "changed_by", "note", "created_at"]
    fields = ["from_status", "to_status", "changed_by", "note", "created_at"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.action(description="Mark selected orders as Processing")
def mark_processing(modeladmin, request, queryset):
    updated = 0
    for order in queryset:
        if order.status != Order.Status.PROCESSING:
            update_order_status(
                order,
                Order.Status.PROCESSING,
                changed_by=request.user,
                note="Marked processing via admin action.",
            )
            updated += 1
    modeladmin.message_user(
        request,
        f"{updated} order(s) updated to Processing.",
        messages.SUCCESS,
    )


@admin.action(description="Mark selected orders as Shipped")
def mark_shipped(modeladmin, request, queryset):
    updated = 0
    for order in queryset:
        if order.status != Order.Status.SHIPPED:
            update_order_status(
                order,
                Order.Status.SHIPPED,
                changed_by=request.user,
                note="Marked shipped via admin action.",
            )
            updated += 1
    modeladmin.message_user(
        request,
        f"{updated} order(s) updated to Shipped.",
        messages.SUCCESS,
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    actions = [mark_processing, mark_shipped]
    list_display = [
        "order_number",
        "status",
        "user_or_guest",
        "total",
        "shipping_method",
        "created_at",
    ]
    list_filter = ["status", "created_at", "is_tax_exempt"]
    search_fields = ["order_number", "user__email", "guest_email", "guest_tracking_token"]
    readonly_fields = [
        "id",
        "order_number",
        "user",
        "guest_email",
        "guest_tracking_token",
        "subtotal",
        "shipping_cost",
        "tax_amount",
        "is_tax_exempt",
        "total",
        "shipping_address",
        "billing_address",
        "shipping_method",
        "created_at",
        "updated_at",
    ]
    fields = [
        "id",
        "order_number",
        "status",
        "user",
        "guest_email",
        "guest_tracking_token",
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
    ]
    ordering = ["-created_at"]

    def user_or_guest(self, obj):
        if obj.user:
            return obj.user.email
        return obj.guest_email or "—"

    user_or_guest.short_description = "Customer"
