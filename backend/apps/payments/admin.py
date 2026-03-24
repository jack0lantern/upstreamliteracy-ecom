from django.contrib import admin
from .models import Payment, Transaction, Refund, WebhookEvent


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = [
        "id",
        "type",
        "amount_cents",
        "source",
        "stripe_object_id",
        "idempotency_key",
        "notes",
        "created_by",
        "created_at",
    ]
    fields = [
        "type",
        "amount_cents",
        "source",
        "stripe_object_id",
        "notes",
        "created_by",
        "created_at",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0
    readonly_fields = [
        "id",
        "initiated_by",
        "amount_cents",
        "reason",
        "stripe_refund_id",
        "status",
        "created_at",
    ]
    fields = [
        "initiated_by",
        "amount_cents",
        "reason",
        "stripe_refund_id",
        "status",
        "staff_notes",
        "created_at",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    inlines = [TransactionInline, RefundInline]
    list_display = [
        "id",
        "order",
        "status",
        "method",
        "amount_cents",
        "currency",
        "stripe_payment_intent_id",
        "created_at",
    ]
    list_filter = ["status", "method", "currency", "created_at"]
    search_fields = [
        "order__order_number",
        "stripe_payment_intent_id",
        "stripe_charge_id",
    ]
    readonly_fields = [
        "id",
        "order",
        "stripe_payment_intent_id",
        "stripe_charge_id",
        "idempotency_key",
        "amount_cents",
        "currency",
        "method",
        "status",
        "failure_code",
        "failure_message",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "payment",
        "type",
        "amount_cents",
        "source",
        "stripe_object_id",
        "created_at",
    ]
    list_filter = ["type", "source", "created_at"]
    search_fields = ["payment__order__order_number", "stripe_object_id", "idempotency_key"]
    readonly_fields = [
        "id",
        "payment",
        "type",
        "amount_cents",
        "source",
        "stripe_object_id",
        "idempotency_key",
        "notes",
        "created_by",
        "created_at",
    ]
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "payment",
        "initiated_by",
        "amount_cents",
        "reason",
        "status",
        "created_at",
    ]
    list_filter = ["status", "reason", "created_at"]
    search_fields = [
        "payment__order__order_number",
        "stripe_refund_id",
        "initiated_by__email",
    ]
    readonly_fields = [
        "id",
        "payment",
        "initiated_by",
        "amount_cents",
        "reason",
        "stripe_refund_id",
        "status",
        "created_at",
    ]
    fields = [
        "id",
        "payment",
        "initiated_by",
        "amount_cents",
        "reason",
        "stripe_refund_id",
        "status",
        "staff_notes",
        "created_at",
    ]
    ordering = ["-created_at"]


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = [
        "stripe_event_id",
        "event_type",
        "processed",
        "related_payment",
        "created_at",
    ]
    list_filter = ["event_type", "processed", "created_at"]
    search_fields = ["stripe_event_id", "event_type"]
    readonly_fields = [
        "stripe_event_id",
        "event_type",
        "payload",
        "processed",
        "processing_error",
        "related_payment",
        "created_at",
    ]
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
