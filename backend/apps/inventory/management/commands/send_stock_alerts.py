"""
Management command: send_stock_alerts

Finds all active StockAlert records and sends notification emails to
staff/admin users. Intended to be run via cron (e.g. daily).

Usage:
    python manage.py send_stock_alerts
    python manage.py send_stock_alerts --dry-run
"""
import logging

from django.core.management.base import BaseCommand

from apps.core.email import send_transactional_email
from apps.inventory.models import StockAlert

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Email staff about active stock alerts (low-stock and out-of-stock)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print alerts without sending emails.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        alerts = (
            StockAlert.objects.filter(is_active=True)
            .select_related("sku__product")
            .order_by("alert_type", "sku__product__title")
        )

        if not alerts.exists():
            self.stdout.write(self.style.SUCCESS("No active stock alerts."))
            return

        lines = []
        for alert in alerts:
            product_title = alert.sku.product.title if alert.sku.product else alert.sku.sku_code
            lines.append(
                f"  [{alert.get_alert_type_display()}] {product_title} "
                f"(SKU: {alert.sku.sku_code}) — qty at trigger: {alert.quantity_at_trigger}"
            )

        summary = "\n".join(lines)
        self.stdout.write(f"Active alerts ({alerts.count()}):\n{summary}")

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No emails sent."))
            return

        try:
            send_transactional_email(
                subject=f"Stock Alert: {alerts.count()} item(s) need attention",
                message=(
                    "The following stock alerts are active:\n\n"
                    f"{summary}\n\n"
                    "Please review inventory levels in the admin dashboard."
                ),
                to_emails=["admin@upstream.dev"],
            )
            self.stdout.write(self.style.SUCCESS("Alert email sent."))
        except Exception:
            logger.exception("Failed to send stock alert email")
            self.stderr.write(self.style.ERROR("Failed to send alert email — see logs."))
