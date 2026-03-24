from django.db import transaction

from .models import StockAlert, StockLevel, StockMovement


class InsufficientStockError(Exception):
    def __init__(self, sku_id, available):
        self.sku_id = sku_id
        self.available = available
        super().__init__(f"Insufficient stock for SKU {sku_id}: {available} available")


def reserve_stock(sku_id, quantity, order=None):
    """
    Atomic stock decrement for a confirmed sale.

    Must be called inside an existing atomic transaction block.
    Raises InsufficientStockError if the SKU has insufficient quantity and
    backorders are not enabled.

    Returns the created StockMovement.
    """
    stock = StockLevel.objects.select_for_update(nowait=True).get(sku_id=sku_id)

    if stock.is_unlimited:
        movement = StockMovement.objects.create(
            sku_id=sku_id,
            movement_type=StockMovement.MovementType.SALE,
            delta=0,
            quantity_after=stock.quantity_on_hand,
            order=order,
        )
        return movement

    if stock.available_quantity < quantity and not stock.backorder_enabled:
        raise InsufficientStockError(sku_id, stock.available_quantity)

    stock.quantity_on_hand -= quantity
    stock.save(update_fields=["quantity_on_hand", "updated_at"])

    movement = StockMovement.objects.create(
        sku_id=sku_id,
        movement_type=StockMovement.MovementType.SALE,
        delta=-quantity,
        quantity_after=stock.quantity_on_hand,
        order=order,
    )

    _check_alerts(stock)
    return movement


def release_stock(sku_id, quantity, order=None):
    """
    Reverse a stock reservation due to order cancellation or payment failure.

    Increments quantity_on_hand and deactivates low/out-of-stock alerts
    if stock has recovered. Safe to call outside a transaction; acquires its own lock.
    """
    with transaction.atomic():
        stock = StockLevel.objects.select_for_update().get(sku_id=sku_id)

        if stock.is_unlimited:
            return

        stock.quantity_on_hand += quantity
        stock.save(update_fields=["quantity_on_hand", "updated_at"])

        StockMovement.objects.create(
            sku_id=sku_id,
            movement_type=StockMovement.MovementType.RETURN,
            delta=quantity,
            quantity_after=stock.quantity_on_hand,
            order=order,
        )

        # Deactivate alerts if stock recovered above zero
        if stock.quantity_on_hand > 0:
            StockAlert.objects.filter(
                sku_id=sku_id,
                is_active=True,
                alert_type__in=[
                    StockAlert.AlertType.LOW_STOCK,
                    StockAlert.AlertType.OUT_OF_STOCK,
                ],
            ).update(is_active=False)


def adjust_stock(sku_id, delta, reason, admin_user=None):
    """
    Manual stock adjustment performed by an admin.

    Positive delta = restock; negative delta = write-down.
    Acquires a row-level lock and records a StockMovement.
    Returns the updated StockLevel instance.
    """
    with transaction.atomic():
        stock = StockLevel.objects.select_for_update().get(sku_id=sku_id)
        stock.quantity_on_hand += delta
        stock.save(update_fields=["quantity_on_hand", "updated_at"])

        movement_type = (
            StockMovement.MovementType.RESTOCK
            if delta > 0
            else StockMovement.MovementType.ADJUSTMENT
        )
        StockMovement.objects.create(
            sku_id=sku_id,
            movement_type=movement_type,
            delta=delta,
            quantity_after=stock.quantity_on_hand,
            performed_by=admin_user,
            reason=reason,
        )

        _check_alerts(stock)
        return stock


def get_stock_status(sku_id):
    """
    Read-only stock status dictionary for a given SKU ID.

    Returns a dict with keys: available_quantity, is_unlimited,
    backorder_enabled, estimated_restock, status, display_label.
    Falls back to out-of-stock defaults if no StockLevel exists.
    """
    try:
        stock = StockLevel.objects.get(sku_id=sku_id)
        return {
            "available_quantity": stock.available_quantity,
            "is_unlimited": stock.is_unlimited,
            "backorder_enabled": stock.backorder_enabled,
            "estimated_restock": stock.estimated_restock,
            "status": stock.stock_status,
            "display_label": stock.display_label,
        }
    except StockLevel.DoesNotExist:
        return {
            "available_quantity": 0,
            "is_unlimited": False,
            "backorder_enabled": False,
            "estimated_restock": None,
            "status": "out_of_stock",
            "display_label": "Out of Stock",
        }


def _check_alerts(stock):
    """
    Create or deactivate StockAlert records based on the current stock level.

    Called internally after any write operation. Not intended for direct use.
    """
    if stock.is_unlimited:
        return

    if stock.quantity_on_hand <= 0 and not stock.backorder_enabled:
        StockAlert.objects.get_or_create(
            sku_id=stock.sku_id,
            alert_type=StockAlert.AlertType.OUT_OF_STOCK,
            is_active=True,
            defaults={"quantity_at_trigger": stock.quantity_on_hand},
        )
        # Supersede any lingering low-stock alert
        StockAlert.objects.filter(
            sku_id=stock.sku_id,
            alert_type=StockAlert.AlertType.LOW_STOCK,
            is_active=True,
        ).update(is_active=False)

    elif 0 < stock.quantity_on_hand <= stock.low_stock_threshold:
        StockAlert.objects.get_or_create(
            sku_id=stock.sku_id,
            alert_type=StockAlert.AlertType.LOW_STOCK,
            is_active=True,
            defaults={"quantity_at_trigger": stock.quantity_on_hand},
        )
        # Deactivate out-of-stock alert if stock recovered above zero
        StockAlert.objects.filter(
            sku_id=stock.sku_id,
            alert_type=StockAlert.AlertType.OUT_OF_STOCK,
            is_active=True,
        ).update(is_active=False)

    else:
        # Stock is healthy — deactivate all active alerts
        StockAlert.objects.filter(
            sku_id=stock.sku_id,
            is_active=True,
        ).update(is_active=False)
