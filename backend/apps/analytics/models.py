import uuid
from django.db import models
from django.conf import settings


class AnalyticsEvent(models.Model):
    """Backend-side event log. Fallback for ad-blocked PostHog + powers funnel queries."""

    event_name = models.CharField(max_length=100, db_index=True)
    session_id = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_index=True,
        related_name="analytics_events",
    )
    anonymous_id = models.CharField(max_length=64, blank=True, db_index=True)
    occurred_at = models.DateTimeField(db_index=True)
    received_at = models.DateTimeField(auto_now_add=True)
    properties = models.JSONField(default=dict)
    idempotency_key = models.CharField(max_length=128, unique=True)
    source = models.CharField(
        max_length=20,
        choices=[("frontend", "Frontend"), ("backend", "Backend")],
        default="backend",
    )

    class Meta:
        indexes = [
            models.Index(fields=["event_name", "occurred_at"]),
            models.Index(fields=["session_id", "occurred_at"]),
        ]

    def __str__(self):
        return f"{self.event_name} @ {self.occurred_at}"


class CartAbandonmentRecord(models.Model):
    """Materialized summary of abandoned carts, populated by management command."""

    cart = models.OneToOneField(
        "cart.Cart",
        on_delete=models.CASCADE,
        related_name="abandonment_record",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cart_abandonment_records",
    )
    is_guest = models.BooleanField(default=False)
    cart_value = models.DecimalField(max_digits=10, decimal_places=2)
    item_count = models.IntegerField()
    checkout_started = models.BooleanField(default=False)
    last_event_at = models.DateTimeField()
    abandoned_at = models.DateTimeField(auto_now_add=True)
    week_of = models.DateField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_guest", "week_of"]),
        ]

    def __str__(self):
        label = f"user={self.user_id}" if self.user_id else "guest"
        return f"CartAbandonment cart={self.cart_id} ({label}) week={self.week_of}"
