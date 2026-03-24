"""
Management command: reconcile_inventory

Verifies that StockLevel.quantity_on_hand matches the sum of all
StockMovement deltas for each SKU. Reports and optionally fixes
discrepancies.

Usage:
    python manage.py reconcile_inventory
    python manage.py reconcile_inventory --fix
"""
import logging

from django.core.management.base import BaseCommand
from django.db.models import Sum

from apps.inventory.models import StockLevel, StockMovement

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Reconcile StockLevel.quantity_on_hand against StockMovement history."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Correct discrepancies by updating quantity_on_hand to match movement history.",
        )

    def handle(self, *args, **options):
        fix = options["fix"]
        discrepancies = 0
        checked = 0

        stock_levels = StockLevel.objects.select_related("sku__product").all()

        for stock in stock_levels:
            if stock.is_unlimited:
                continue

            checked += 1

            movement_total = (
                StockMovement.objects.filter(sku=stock.sku)
                .aggregate(total=Sum("delta"))["total"]
            ) or 0

            if stock.quantity_on_hand != movement_total:
                discrepancies += 1
                product_title = (
                    stock.sku.product.title if stock.sku.product else stock.sku.sku_code
                )
                self.stdout.write(
                    self.style.WARNING(
                        f"  MISMATCH: {product_title} (SKU: {stock.sku.sku_code}) — "
                        f"on_hand={stock.quantity_on_hand}, movements_sum={movement_total}"
                    )
                )

                if fix:
                    old_qty = stock.quantity_on_hand
                    stock.quantity_on_hand = movement_total
                    stock.save(update_fields=["quantity_on_hand", "updated_at"])

                    StockMovement.objects.create(
                        sku=stock.sku,
                        movement_type=StockMovement.MovementType.ADJUSTMENT,
                        delta=movement_total - old_qty,
                        quantity_after=movement_total,
                        reason=f"Reconciliation fix: was {old_qty}, corrected to {movement_total}",
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"    FIXED: {old_qty} → {movement_total}")
                    )

        if discrepancies == 0:
            self.stdout.write(
                self.style.SUCCESS(f"All {checked} SKUs reconciled — no discrepancies.")
            )
        else:
            mode = "Fixed" if fix else "Found"
            self.stdout.write(
                self.style.WARNING(
                    f"{mode} {discrepancies} discrepancy(ies) out of {checked} SKUs checked."
                )
            )
