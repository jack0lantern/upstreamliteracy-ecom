"""
Admin registrations for the analytics app.

Both models are intentionally read-only in the admin — these are append-only
audit / materialized records that should never be manually edited via the UI.
"""
from django.contrib import admin

from .models import AnalyticsEvent, CartAbandonmentRecord


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------


class ReadOnlyAdminMixin:
    """Disable all write operations in the Django admin for a model."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# AnalyticsEvent
# ---------------------------------------------------------------------------


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "event_name",
        "source",
        "session_id_short",
        "user",
        "anonymous_id_short",
        "occurred_at",
        "received_at",
    )
    list_filter = (
        "event_name",
        "source",
    )
    search_fields = (
        "session_id",
        "anonymous_id",
        "idempotency_key",
        "user__email",
    )
    date_hierarchy = "occurred_at"
    ordering = ("-occurred_at",)
    readonly_fields = (
        "event_name",
        "session_id",
        "user",
        "anonymous_id",
        "occurred_at",
        "received_at",
        "properties",
        "idempotency_key",
        "source",
    )

    # Limit the detail view to the most important fields to keep load times fast.
    fields = readonly_fields

    # Disable the default "Save" buttons so it's clear this is read-only.
    save_on_top = False

    def session_id_short(self, obj):
        return obj.session_id[:12] + "…" if len(obj.session_id) > 12 else obj.session_id

    session_id_short.short_description = "Session"

    def anonymous_id_short(self, obj):
        if not obj.anonymous_id:
            return "—"
        return obj.anonymous_id[:12] + "…" if len(obj.anonymous_id) > 12 else obj.anonymous_id

    anonymous_id_short.short_description = "Anon ID"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user")
        )


# ---------------------------------------------------------------------------
# CartAbandonmentRecord
# ---------------------------------------------------------------------------


@admin.register(CartAbandonmentRecord)
class CartAbandonmentRecordAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "cart",
        "user",
        "is_guest",
        "cart_value",
        "item_count",
        "checkout_started",
        "week_of",
        "abandoned_at",
    )
    list_filter = (
        "is_guest",
        "checkout_started",
        "week_of",
    )
    search_fields = (
        "cart__token",
        "user__email",
    )
    date_hierarchy = "abandoned_at"
    ordering = ("-abandoned_at",)
    readonly_fields = (
        "cart",
        "user",
        "is_guest",
        "cart_value",
        "item_count",
        "checkout_started",
        "last_event_at",
        "abandoned_at",
        "week_of",
    )
    fields = readonly_fields

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "cart")
        )
