from django.utils import timezone
from rest_framework import serializers


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------


class SingleEventSerializer(serializers.Serializer):
    """Validates a single event payload sent from the frontend."""

    event_name = serializers.CharField(max_length=100)
    session_id = serializers.CharField(max_length=64)
    properties = serializers.DictField(child=serializers.JSONField(), default=dict)
    occurred_at = serializers.DateTimeField(required=False, default=None)

    def validate_event_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("event_name must not be blank.")
        return value

    def validate_session_id(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("session_id must not be blank.")
        return value

    def validate_occurred_at(self, value):
        if value is None:
            return timezone.now()
        # Reject timestamps more than 24 hours in the future (clock skew guard).
        delta = value - timezone.now()
        if delta.total_seconds() > 86_400:
            raise serializers.ValidationError(
                "occurred_at cannot be more than 24 hours in the future."
            )
        return value


class EventIngestionSerializer(serializers.Serializer):
    """Top-level ingestion envelope: {events: [...]}"""

    events = SingleEventSerializer(many=True, allow_empty=False)

    def validate_events(self, value):
        if len(value) > 500:
            raise serializers.ValidationError(
                "A maximum of 500 events may be submitted per request."
            )
        return value


# ---------------------------------------------------------------------------
# Dashboard — operational
# ---------------------------------------------------------------------------


class OrderMetricsSerializer(serializers.Serializer):
    """Revenue + count stats for a single time bucket."""

    count = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


class OperationalDashboardSerializer(serializers.Serializer):
    """Output format for the operational metrics dashboard."""

    orders_today = OrderMetricsSerializer()
    orders_this_week = OrderMetricsSerializer()
    orders_this_month = OrderMetricsSerializer()
    pending_fulfillment = serializers.IntegerField(
        help_text="Orders in PROCESSING status awaiting shipment."
    )
    low_stock_items = serializers.IntegerField(
        help_text="Count of active StockAlert records."
    )
    payment_failures_last_7d = serializers.IntegerField(
        help_text="Payment records with status=failed in the past 7 days."
    )
    generated_at = serializers.DateTimeField()


# ---------------------------------------------------------------------------
# Dashboard — funnel
# ---------------------------------------------------------------------------


class FunnelStepSerializer(serializers.Serializer):
    """A single step in the conversion funnel."""

    step = serializers.CharField(help_text="Canonical funnel step name.")
    label = serializers.CharField(help_text="Human-readable label.")
    count = serializers.IntegerField(help_text="Unique sessions that reached this step.")
    drop_off_pct = serializers.FloatField(
        allow_null=True,
        help_text="Percentage of sessions lost relative to the previous step. Null for first step.",
    )
    conversion_pct = serializers.FloatField(
        allow_null=True,
        help_text="Percentage of first-step sessions that reached this step. Null for first step.",
    )


# ---------------------------------------------------------------------------
# Dashboard — revenue
# ---------------------------------------------------------------------------


class RevenueDataPointSerializer(serializers.Serializer):
    """A single data point in the revenue time-series."""

    date = serializers.DateField(help_text="Start of the time bucket (day/week/month).")
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    order_count = serializers.IntegerField()
    aov = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        allow_null=True,
        help_text="Average order value. Null when order_count is 0.",
    )


# ---------------------------------------------------------------------------
# Dashboard — abandonment
# ---------------------------------------------------------------------------


class AbandonmentWeekSerializer(serializers.Serializer):
    """Aggregated abandonment stats for a single week."""

    week_of = serializers.DateField()
    total_abandoned = serializers.IntegerField()
    guest_abandoned = serializers.IntegerField()
    registered_abandoned = serializers.IntegerField()
    checkout_started_pct = serializers.FloatField(
        help_text="% of abandoned carts that had started checkout."
    )
    avg_cart_value = serializers.DecimalField(
        max_digits=10, decimal_places=2, allow_null=True
    )
    # Value bucket breakdown
    bucket_under_25 = serializers.IntegerField()
    bucket_25_to_50 = serializers.IntegerField()
    bucket_50_to_100 = serializers.IntegerField()
    bucket_over_100 = serializers.IntegerField()


# ---------------------------------------------------------------------------
# Dashboard — top products
# ---------------------------------------------------------------------------


class TopProductSerializer(serializers.Serializer):
    """A single entry in the top-products list."""

    product_slug = serializers.CharField()
    product_title = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    units_sold = serializers.IntegerField()
    order_count = serializers.IntegerField()
