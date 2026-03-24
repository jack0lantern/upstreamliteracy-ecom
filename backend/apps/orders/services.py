import secrets
import logging
from django.db import transaction
from django.utils import timezone

from .models import Order, OrderItem, OrderStatusHistory

logger = logging.getLogger(__name__)


def generate_order_number():
    year = timezone.now().year
    rand = secrets.token_hex(3).upper()
    return f"UL-{year}-{rand}"


@transaction.atomic
def create_order(checkout_session):
    """
    Create an Order (and its OrderItems) from a confirmed CheckoutSession.

    Decrements stock for physical items via inventory.services.reserve_stock.
    This function must be called inside a transaction.atomic() context — or it
    creates its own via the decorator.

    Returns the created Order instance.
    """
    from apps.catalog.models import SKU
    from apps.inventory.services import reserve_stock, InsufficientStockError

    order = Order.objects.create(
        order_number=generate_order_number(),
        user=checkout_session.user,
        guest_email=checkout_session.guest_email,
        guest_tracking_token=(
            secrets.token_urlsafe(32) if not checkout_session.user else None
        ),
        status=Order.Status.PENDING_PAYMENT,
        shipping_address=checkout_session.shipping_address or {},
        billing_address=(
            checkout_session.billing_address
            or checkout_session.shipping_address
            or {}
        ),
        shipping_method=(
            checkout_session.shipping_rate.name
            if checkout_session.shipping_rate
            else ""
        ),
        subtotal=checkout_session.subtotal,
        shipping_cost=checkout_session.shipping_cost or 0,
        tax_amount=checkout_session.tax_amount or 0,
        is_tax_exempt=checkout_session.tax_exempt,
        total=checkout_session.total,
    )

    for item in checkout_session.cart_snapshot.get("items", []):
        OrderItem.objects.create(
            order=order,
            product_title=item["product_title"],
            product_slug=item["product_slug"],
            sku_code=item["sku_code"],
            product_image_url=item.get("product_image_url", ""),
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            line_total=item["line_total"],
            product_type=item.get("product_type", "physical"),
        )

        if item.get("product_type", "physical") != "digital":
            try:
                sku = SKU.objects.get(sku_code=item["sku_code"])
                reserve_stock(sku.id, item["quantity"], order=order)
            except InsufficientStockError as exc:
                logger.error(
                    "Insufficient stock during order creation: %s", exc
                )
                raise ValueError(str(exc)) from exc
            except SKU.DoesNotExist:
                logger.warning(
                    "SKU %s not found during stock reservation", item["sku_code"]
                )

    OrderStatusHistory.objects.create(
        order=order,
        from_status="",
        to_status=Order.Status.PENDING_PAYMENT,
    )

    return order


def update_order_status(order, new_status, changed_by=None, note=""):
    """
    Transition an order to a new status and record history.
    """
    old_status = order.status
    order.status = new_status
    order.save(update_fields=["status", "updated_at"])
    OrderStatusHistory.objects.create(
        order=order,
        from_status=old_status,
        to_status=new_status,
        changed_by=changed_by,
        note=note,
    )
    return order
