"""
Management command: detect_abandoned_carts

Identifies shopping carts that were abandoned (no associated Order and no
checkout_completed analytics event) and materialises a CartAbandonmentRecord
for each one.

Abandonment criteria
--------------------
A cart is considered abandoned when ALL of the following are true:

1. The cart has at least one item.
2. The cart was last updated more than 24 hours ago (configurable via
   --inactivity-hours).
3. No Order exists that was created within 24 hours of the cart's last
   activity and belongs to the same user / guest session.
4. No AnalyticsEvent with event_name='checkout_completed' exists for the
   cart's session(s) within 24 hours of the cart's last activity.

The command is idempotent — re-running it will not create duplicate records
because CartAbandonmentRecord has a OneToOne relationship with Cart.

Usage
-----
    python manage.py detect_abandoned_carts
    python manage.py detect_abandoned_carts --inactivity-hours 48
    python manage.py detect_abandoned_carts --dry-run
"""
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.analytics.models import AnalyticsEvent, CartAbandonmentRecord
from apps.cart.models import Cart
from apps.orders.models import Order

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Detect abandoned carts and materialise CartAbandonmentRecord rows."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--inactivity-hours",
            type=int,
            default=24,
            help=(
                "Minimum hours of inactivity before a cart is considered abandoned "
                "(default: 24)."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Analyse and report without writing any records to the database.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Number of carts to process per database batch (default: 500).",
        )

    def handle(self, *args, **options):
        inactivity_hours = options["inactivity_hours"]
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]

        if inactivity_hours < 1:
            raise CommandError("--inactivity-hours must be >= 1.")

        now = timezone.now()
        cutoff = now - timedelta(hours=inactivity_hours)

        self.stdout.write(
            self.style.NOTICE(
                f"Scanning for carts inactive since {cutoff.isoformat()} "
                f"(>= {inactivity_hours}h ago)…"
                + (" [DRY RUN]" if dry_run else "")
            )
        )

        # ------------------------------------------------------------------
        # 1. Candidate carts: have items, were last touched before the cutoff,
        #    and do not already have a CartAbandonmentRecord.
        # ------------------------------------------------------------------
        candidate_carts = (
            Cart.objects.filter(
                updated_at__lte=cutoff,
                items__isnull=False,  # has at least one item
            )
            .exclude(abandonment_record__isnull=False)  # not already recorded
            .distinct()
            .prefetch_related("items")
            .select_related("user")
        )

        total_candidates = candidate_carts.count()
        self.stdout.write(f"Candidate carts found: {total_candidates}")

        if total_candidates == 0:
            self.stdout.write(self.style.SUCCESS("No new abandonments detected."))
            return

        # ------------------------------------------------------------------
        # 2. Pre-fetch sets of session_ids and user_ids that completed
        #    checkout within the look-back window, so we can exclude them
        #    in Python without N+1 queries.
        # ------------------------------------------------------------------
        # Window: only look at checkout events from inactivity_hours * 2 ago
        # up to now, to keep the fetch bounded.
        event_window_start = now - timedelta(hours=inactivity_hours * 2)

        completed_sessions = set(
            AnalyticsEvent.objects.filter(
                event_name="checkout_completed",
                occurred_at__gte=event_window_start,
            ).values_list("session_id", flat=True)
        )

        # Users who placed an order after the cutoff reference point.
        ordered_user_ids = set(
            Order.objects.filter(
                created_at__gte=event_window_start,
                user__isnull=False,
            ).values_list("user_id", flat=True)
        )

        # ------------------------------------------------------------------
        # 3. Iterate candidates in batches and build records.
        # ------------------------------------------------------------------
        newly_created = 0
        skipped_completed = 0
        errors = 0

        # We'll collect records to bulk_create in chunks.
        buffer = []

        def _flush_buffer():
            nonlocal newly_created
            if buffer and not dry_run:
                with transaction.atomic():
                    CartAbandonmentRecord.objects.bulk_create(
                        buffer, ignore_conflicts=True
                    )
                newly_created += len(buffer)
            elif buffer and dry_run:
                newly_created += len(buffer)
            buffer.clear()

        # Paginate the queryset manually to avoid loading all into memory.
        offset = 0
        while True:
            batch = list(candidate_carts[offset: offset + batch_size])
            if not batch:
                break
            offset += batch_size

            for cart in batch:
                try:
                    # -------------------------------------------------------
                    # Filter: skip carts whose owner completed checkout.
                    # -------------------------------------------------------
                    # Check by user if authenticated.
                    if cart.user_id and cart.user_id in ordered_user_ids:
                        skipped_completed += 1
                        continue

                    # Check by session_id stored in analytics events for this
                    # cart.  We look up the most recent session associated
                    # with the cart token or user.
                    cart_sessions = set(
                        AnalyticsEvent.objects.filter(
                            occurred_at__gte=event_window_start,
                        )
                        .filter(
                            Q_for_cart(cart)
                        )
                        .values_list("session_id", flat=True)
                        .distinct()
                    )
                    if cart_sessions & completed_sessions:
                        skipped_completed += 1
                        continue

                    # -------------------------------------------------------
                    # Build the record.
                    # -------------------------------------------------------
                    # Compute cart value from items (the Cart.subtotal property
                    # issues additional queries, so we compute here with the
                    # prefetched items).
                    items = list(cart.items.all())
                    if not items:
                        continue  # race condition — item was removed

                    cart_value = sum(item.line_total for item in items)
                    item_count = sum(item.quantity for item in items)

                    # Did this cart start checkout? Check for checkout_started
                    # event in any of its sessions.
                    checkout_started = bool(
                        cart_sessions
                        and AnalyticsEvent.objects.filter(
                            event_name="checkout_started",
                            session_id__in=cart_sessions,
                            occurred_at__gte=event_window_start,
                        ).exists()
                    )

                    # last_event_at: most recent analytics event OR cart update
                    last_event_at = cart.updated_at
                    if cart_sessions:
                        latest_event = (
                            AnalyticsEvent.objects.filter(
                                session_id__in=cart_sessions,
                            )
                            .order_by("-occurred_at")
                            .values_list("occurred_at", flat=True)
                            .first()
                        )
                        if latest_event and latest_event > last_event_at:
                            last_event_at = latest_event

                    # ISO week start (Monday).
                    week_of = _iso_week_start(last_event_at.date())

                    buffer.append(
                        CartAbandonmentRecord(
                            cart=cart,
                            user=cart.user,
                            is_guest=(cart.user is None),
                            cart_value=cart_value,
                            item_count=item_count,
                            checkout_started=checkout_started,
                            last_event_at=last_event_at,
                            week_of=week_of,
                        )
                    )

                    if len(buffer) >= batch_size:
                        _flush_buffer()

                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    logger.exception(
                        "detect_abandoned_carts_error",
                        extra={"cart_id": str(cart.pk), "error": str(exc)},
                    )

        # Flush any remaining items.
        _flush_buffer()

        # ------------------------------------------------------------------
        # 4. Summary output.
        # ------------------------------------------------------------------
        mode = "DRY RUN — " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{mode}Detection complete.\n"
                f"  New abandonment records : {newly_created}\n"
                f"  Skipped (completed)     : {skipped_completed}\n"
                f"  Errors                  : {errors}\n"
                f"  Total candidates        : {total_candidates}\n"
            )
        )

        if errors:
            self.stderr.write(
                self.style.WARNING(
                    f"{errors} cart(s) raised exceptions — check logs for details."
                )
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def Q_for_cart(cart):
    """
    Build a Q object that matches AnalyticsEvent rows belonging to this cart.
    Matches by user_id (if authenticated) OR by anonymous_id derived from the
    cart token.
    """
    from django.db.models import Q

    conditions = Q(anonymous_id=cart.token)
    if cart.user_id:
        conditions |= Q(user_id=cart.user_id)
    return conditions


def _iso_week_start(d):
    """Return the Monday of the ISO week containing date `d`."""
    from datetime import date, timedelta

    return d - timedelta(days=d.weekday())
