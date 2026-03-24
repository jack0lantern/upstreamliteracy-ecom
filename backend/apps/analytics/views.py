"""
Analytics views.

All dashboard endpoints are restricted to IsAdminUser (is_staff=True).
EventIngestionView is public (AllowAny) — it is the backend receiver for
frontend-side tracking events.
"""
import hashlib
import logging
from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Count, DecimalField, Q, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.models import StockAlert
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment

from .models import AnalyticsEvent, CartAbandonmentRecord
from .serializers import (
    AbandonmentWeekSerializer,
    EventIngestionSerializer,
    FunnelStepSerializer,
    OperationalDashboardSerializer,
    RevenueDataPointSerializer,
    TopProductSerializer,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Funnel definition
# ---------------------------------------------------------------------------

FUNNEL_STEPS = [
    ("product_viewed", "Product Viewed"),
    ("added_to_cart", "Added to Cart"),
    ("checkout_started", "Checkout Started"),
    ("checkout_completed", "Checkout Completed"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_date_range(request, default_days=30):
    """
    Parse ?start=YYYY-MM-DD&end=YYYY-MM-DD query params.
    Returns (start_dt, end_dt) as timezone-aware datetimes.
    Defaults to the last `default_days` days when params are absent.
    """
    from datetime import datetime

    now = timezone.now()
    raw_start = request.query_params.get("start")
    raw_end = request.query_params.get("end")

    try:
        if raw_start:
            start_dt = timezone.make_aware(datetime.strptime(raw_start, "%Y-%m-%d"))
        else:
            start_dt = now - timedelta(days=default_days)

        if raw_end:
            # End of the given day.
            end_dt = timezone.make_aware(
                datetime.strptime(raw_end, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59
                )
            )
        else:
            end_dt = now
    except ValueError:
        raise ValueError("Date parameters must be in YYYY-MM-DD format.")

    if start_dt > end_dt:
        raise ValueError("start must be before end.")

    return start_dt, end_dt


# ---------------------------------------------------------------------------
# Event ingestion
# ---------------------------------------------------------------------------


class EventIngestionView(APIView):
    """
    POST /analytics/events/

    Accepts a batch of frontend analytics events and bulk-inserts them.
    Uses ignore_conflicts so re-delivered events are silently dropped.

    Request body:
        {
            "events": [
                {
                    "event_name": "product_viewed",
                    "session_id": "abc123",
                    "properties": {"product_slug": "phonics-workbook"},
                    "occurred_at": "2026-01-01T12:00:00Z"  // optional
                },
                ...
            ]
        }
    """

    permission_classes = [AllowAny]
    # No authentication required — this is the public tracking pixel equivalent.

    def post(self, request):
        serializer = EventIngestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_events = serializer.validated_data["events"]

        # Resolve the authenticated user if a JWT was provided (best-effort).
        auth_user = request.user if request.user.is_authenticated else None

        to_create = []
        for ev in validated_events:
            occurred_at = ev["occurred_at"]
            session_id = ev["session_id"]
            event_name = ev["event_name"]
            properties = ev.get("properties", {})

            key_input = f"{session_id}:{event_name}:{occurred_at.isoformat()}"
            idempotency_key = hashlib.sha256(key_input.encode()).hexdigest()

            to_create.append(
                AnalyticsEvent(
                    event_name=event_name,
                    session_id=session_id,
                    user=auth_user,
                    anonymous_id=properties.get("anonymous_id", ""),
                    occurred_at=occurred_at,
                    properties=properties,
                    idempotency_key=idempotency_key,
                    source="frontend",
                )
            )

        created = AnalyticsEvent.objects.bulk_create(
            to_create, ignore_conflicts=True
        )

        logger.info(
            "analytics_events_ingested",
            extra={
                "submitted": len(to_create),
                "inserted": len(created),
                "user_id": auth_user.pk if auth_user else None,
            },
        )

        return Response(
            {"accepted": len(to_create), "inserted": len(created)},
            status=status.HTTP_202_ACCEPTED,
        )


# ---------------------------------------------------------------------------
# Identity stitching
# ---------------------------------------------------------------------------


class IdentifyView(APIView):
    """
    POST /analytics/identify/

    Links all AnalyticsEvent rows that carry a given anonymous_id to the
    authenticated user. Call this after a successful login / registration so
    that pre-login funnel steps are attributed correctly.

    Request body:
        {"anonymous_id": "<uuid-or-string>"}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        anonymous_id = request.data.get("anonymous_id", "").strip()
        if not anonymous_id:
            return Response(
                {"detail": "anonymous_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = AnalyticsEvent.objects.filter(
            anonymous_id=anonymous_id, user__isnull=True
        ).update(user=request.user)

        logger.info(
            "analytics_identity_stitched",
            extra={
                "user_id": request.user.pk,
                "anonymous_id": anonymous_id,
                "events_updated": updated,
            },
        )

        return Response({"stitched_events": updated}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Operational dashboard
# ---------------------------------------------------------------------------


class OperationalDashboardView(APIView):
    """
    GET /analytics/dashboard/operational/

    Returns a snapshot of key operational metrics. Result is cached for 60s.
    """

    permission_classes = [IsAdminUser]
    CACHE_KEY = "analytics:operational_dashboard"
    CACHE_TTL = 60  # seconds

    def get(self, request):
        cached = cache.get(self.CACHE_KEY)
        if cached is not None:
            return Response(cached)

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)

        def _order_metrics(qs):
            agg = qs.aggregate(
                count=Count("id"),
                revenue=Sum("total", output_field=DecimalField()),
            )
            return {
                "count": agg["count"] or 0,
                "revenue": agg["revenue"] or Decimal("0.00"),
            }

        completed_statuses = [
            Order.Status.PROCESSING,
            Order.Status.SHIPPED,
            Order.Status.DELIVERED,
        ]
        base_qs = Order.objects.filter(status__in=completed_statuses)

        data = {
            "orders_today": _order_metrics(base_qs.filter(created_at__gte=today_start)),
            "orders_this_week": _order_metrics(base_qs.filter(created_at__gte=week_start)),
            "orders_this_month": _order_metrics(
                base_qs.filter(created_at__gte=month_start)
            ),
            "pending_fulfillment": Order.objects.filter(
                status=Order.Status.PROCESSING
            ).count(),
            "low_stock_items": StockAlert.objects.filter(is_active=True).count(),
            "payment_failures_last_7d": Payment.objects.filter(
                status=Payment.Status.FAILED,
                created_at__gte=now - timedelta(days=7),
            ).count(),
            "generated_at": now,
        }

        serializer = OperationalDashboardSerializer(data)
        cache.set(self.CACHE_KEY, serializer.data, self.CACHE_TTL)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Funnel view
# ---------------------------------------------------------------------------


class FunnelView(APIView):
    """
    GET /analytics/dashboard/funnel/?start=YYYY-MM-DD&end=YYYY-MM-DD

    Returns session-level conversion counts and drop-off percentages for the
    standard funnel: product_viewed → added_to_cart → checkout_started →
    checkout_completed.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            start_dt, end_dt = _parse_date_range(request, default_days=30)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # Count unique sessions per funnel step within the date range.
        step_counts = {}
        for step_name, _ in FUNNEL_STEPS:
            count = (
                AnalyticsEvent.objects.filter(
                    event_name=step_name,
                    occurred_at__gte=start_dt,
                    occurred_at__lte=end_dt,
                )
                .values("session_id")
                .distinct()
                .count()
            )
            step_counts[step_name] = count

        first_step_count = step_counts.get(FUNNEL_STEPS[0][0], 0)

        results = []
        prev_count = None
        for i, (step_name, label) in enumerate(FUNNEL_STEPS):
            count = step_counts.get(step_name, 0)

            if i == 0:
                drop_off_pct = None
                conversion_pct = None
            else:
                if prev_count and prev_count > 0:
                    drop_off_pct = round((prev_count - count) / prev_count * 100, 2)
                else:
                    drop_off_pct = None

                if first_step_count and first_step_count > 0:
                    conversion_pct = round(count / first_step_count * 100, 2)
                else:
                    conversion_pct = None

            results.append(
                {
                    "step": step_name,
                    "label": label,
                    "count": count,
                    "drop_off_pct": drop_off_pct,
                    "conversion_pct": conversion_pct,
                }
            )
            prev_count = count

        serializer = FunnelStepSerializer(results, many=True)
        return Response(
            {
                "start": start_dt.date().isoformat(),
                "end": end_dt.date().isoformat(),
                "steps": serializer.data,
            }
        )


# ---------------------------------------------------------------------------
# Revenue view
# ---------------------------------------------------------------------------


class RevenueView(APIView):
    """
    GET /analytics/dashboard/revenue/
        ?granularity=day|week|month
        &start=YYYY-MM-DD
        &end=YYYY-MM-DD

    Aggregates Order totals by time bucket. Only includes orders in a
    revenue-positive status (processing, shipped, delivered).
    """

    permission_classes = [IsAdminUser]

    TRUNC_MAP = {
        "day": TruncDay,
        "week": TruncWeek,
        "month": TruncMonth,
    }

    def get(self, request):
        granularity = request.query_params.get("granularity", "day").lower()
        if granularity not in self.TRUNC_MAP:
            return Response(
                {"detail": "granularity must be one of: day, week, month."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_dt, end_dt = _parse_date_range(request, default_days=30)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        trunc_fn = self.TRUNC_MAP[granularity]

        revenue_statuses = [
            Order.Status.PROCESSING,
            Order.Status.SHIPPED,
            Order.Status.DELIVERED,
        ]

        rows = (
            Order.objects.filter(
                status__in=revenue_statuses,
                created_at__gte=start_dt,
                created_at__lte=end_dt,
            )
            .annotate(bucket=trunc_fn("created_at"))
            .values("bucket")
            .annotate(
                order_count=Count("id"),
                revenue=Sum("total", output_field=DecimalField()),
            )
            .order_by("bucket")
        )

        data_points = []
        for row in rows:
            order_count = row["order_count"] or 0
            revenue = row["revenue"] or Decimal("0.00")
            aov = (revenue / order_count).quantize(Decimal("0.01")) if order_count else None
            data_points.append(
                {
                    "date": row["bucket"].date(),
                    "revenue": revenue,
                    "order_count": order_count,
                    "aov": aov,
                }
            )

        serializer = RevenueDataPointSerializer(data_points, many=True)
        return Response(
            {
                "granularity": granularity,
                "start": start_dt.date().isoformat(),
                "end": end_dt.date().isoformat(),
                "data": serializer.data,
            }
        )


# ---------------------------------------------------------------------------
# Abandonment view
# ---------------------------------------------------------------------------


class AbandonmentView(APIView):
    """
    GET /analytics/dashboard/abandonment/
        ?start=YYYY-MM-DD
        &end=YYYY-MM-DD

    Reads from CartAbandonmentRecord (populated by detect_abandoned_carts
    management command) and aggregates by week.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            start_dt, end_dt = _parse_date_range(request, default_days=90)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        records = CartAbandonmentRecord.objects.filter(
            week_of__gte=start_dt.date(),
            week_of__lte=end_dt.date(),
        )

        # Aggregate per week in Python — CartAbandonmentRecord rows are
        # materialised summaries so the dataset is typically small.
        from collections import defaultdict

        weeks: dict = defaultdict(
            lambda: {
                "total": 0,
                "guest": 0,
                "registered": 0,
                "checkout_started": 0,
                "cart_value_sum": Decimal("0.00"),
                "bucket_under_25": 0,
                "bucket_25_to_50": 0,
                "bucket_50_to_100": 0,
                "bucket_over_100": 0,
            }
        )

        for rec in records:
            w = rec.week_of
            weeks[w]["total"] += 1
            if rec.is_guest:
                weeks[w]["guest"] += 1
            else:
                weeks[w]["registered"] += 1
            if rec.checkout_started:
                weeks[w]["checkout_started"] += 1
            weeks[w]["cart_value_sum"] += rec.cart_value
            v = rec.cart_value
            if v < 25:
                weeks[w]["bucket_under_25"] += 1
            elif v < 50:
                weeks[w]["bucket_25_to_50"] += 1
            elif v < 100:
                weeks[w]["bucket_50_to_100"] += 1
            else:
                weeks[w]["bucket_over_100"] += 1

        result = []
        for week_of, agg in sorted(weeks.items()):
            total = agg["total"]
            avg_cv = (agg["cart_value_sum"] / total).quantize(Decimal("0.01")) if total else None
            checkout_pct = round(agg["checkout_started"] / total * 100, 2) if total else 0.0
            result.append(
                {
                    "week_of": week_of,
                    "total_abandoned": total,
                    "guest_abandoned": agg["guest"],
                    "registered_abandoned": agg["registered"],
                    "checkout_started_pct": checkout_pct,
                    "avg_cart_value": avg_cv,
                    "bucket_under_25": agg["bucket_under_25"],
                    "bucket_25_to_50": agg["bucket_25_to_50"],
                    "bucket_50_to_100": agg["bucket_50_to_100"],
                    "bucket_over_100": agg["bucket_over_100"],
                }
            )

        serializer = AbandonmentWeekSerializer(result, many=True)
        return Response(
            {
                "start": start_dt.date().isoformat(),
                "end": end_dt.date().isoformat(),
                "weeks": serializer.data,
            }
        )


# ---------------------------------------------------------------------------
# Top products view
# ---------------------------------------------------------------------------


class TopProductsView(APIView):
    """
    GET /analytics/dashboard/top-products/
        ?start=YYYY-MM-DD
        &end=YYYY-MM-DD
        &n=10           (default 10, max 50)
        &sort=revenue   (revenue | units)

    Aggregates OrderItem by product_slug across revenue-positive orders.
    """

    permission_classes = [IsAdminUser]
    DEFAULT_N = 10
    MAX_N = 50

    def get(self, request):
        try:
            start_dt, end_dt = _parse_date_range(request, default_days=30)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            n = min(int(request.query_params.get("n", self.DEFAULT_N)), self.MAX_N)
        except (TypeError, ValueError):
            n = self.DEFAULT_N

        sort_by = request.query_params.get("sort", "revenue").lower()
        if sort_by not in ("revenue", "units"):
            return Response(
                {"detail": "sort must be 'revenue' or 'units'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        revenue_statuses = [
            Order.Status.PROCESSING,
            Order.Status.SHIPPED,
            Order.Status.DELIVERED,
        ]

        qs = (
            OrderItem.objects.filter(
                order__status__in=revenue_statuses,
                order__created_at__gte=start_dt,
                order__created_at__lte=end_dt,
            )
            .values("product_slug", "product_title")
            .annotate(
                total_revenue=Sum("line_total", output_field=DecimalField()),
                units_sold=Sum("quantity"),
                order_count=Count("order_id", distinct=True),
            )
        )

        if sort_by == "units":
            qs = qs.order_by("-units_sold")
        else:
            qs = qs.order_by("-total_revenue")

        qs = qs[:n]

        serializer = TopProductSerializer(list(qs), many=True)
        return Response(
            {
                "start": start_dt.date().isoformat(),
                "end": end_dt.date().isoformat(),
                "sort": sort_by,
                "n": n,
                "products": serializer.data,
            }
        )
