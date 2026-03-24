from django.contrib import admin
from django.utils import timezone

from .models import StockAlert, StockLevel, StockMovement


class StockLevelInline(admin.StackedInline):
    model = StockLevel
    extra = 0
    max_num = 1
    can_delete = False
    fields = [
        "quantity_on_hand",
        "low_stock_threshold",
        "is_unlimited",
        "backorder_enabled",
        "estimated_restock",
        "updated_at",
    ]
    readonly_fields = ["updated_at"]


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = [
        "sku",
        "quantity_on_hand",
        "low_stock_threshold",
        "is_unlimited",
        "backorder_enabled",
        "stock_status_display",
        "updated_at",
    ]
    list_filter = ["is_unlimited", "backorder_enabled"]
    search_fields = ["sku__sku_code", "sku__product__title"]
    readonly_fields = ["stock_status_display", "display_label", "available_quantity", "updated_at"]
    ordering = ["sku__sku_code"]

    fieldsets = [
        (
            "Stock Details",
            {
                "fields": [
                    "sku",
                    "quantity_on_hand",
                    "low_stock_threshold",
                    "is_unlimited",
                    "backorder_enabled",
                    "estimated_restock",
                ],
            },
        ),
        (
            "Computed Status",
            {
                "fields": ["stock_status_display", "display_label", "available_quantity", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="Stock Status")
    def stock_status_display(self, obj):
        return obj.stock_status


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        "sku",
        "movement_type",
        "delta",
        "quantity_after",
        "order",
        "performed_by",
        "created_at",
    ]
    list_filter = ["movement_type", "created_at"]
    search_fields = ["sku__sku_code", "sku__product__title", "reason"]
    readonly_fields = [
        "sku",
        "movement_type",
        "delta",
        "quantity_after",
        "order",
        "performed_by",
        "reason",
        "created_at",
    ]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = [
        "sku",
        "alert_type",
        "quantity_at_trigger",
        "is_active",
        "acknowledged_by",
        "acknowledged_at",
        "created_at",
    ]
    list_filter = ["alert_type", "is_active", "created_at"]
    search_fields = ["sku__sku_code", "sku__product__title"]
    readonly_fields = [
        "sku",
        "alert_type",
        "quantity_at_trigger",
        "acknowledged_by",
        "acknowledged_at",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    actions = ["acknowledge_alerts"]

    @admin.action(description="Acknowledge selected alerts")
    def acknowledge_alerts(self, request, queryset):
        active_alerts = queryset.filter(is_active=True)
        count = active_alerts.count()
        active_alerts.update(
            is_active=False,
            acknowledged_by=request.user,
            acknowledged_at=timezone.now(),
        )
        self.message_user(
            request,
            f"{count} alert(s) acknowledged.",
        )
