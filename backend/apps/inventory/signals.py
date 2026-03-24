"""
Inventory signals.

Automatically creates a StockLevel record whenever a new SKU is saved
for the first time. Digital-product SKUs receive an unlimited stock level;
all others default to zero with standard thresholds.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender="catalog.SKU")
def create_stock_level_for_new_sku(sender, instance, created, **kwargs):
    """
    When a new SKU is created, provision its StockLevel automatically.

    - Digital product SKUs get is_unlimited=True.
    - Physical and bundle SKUs start at quantity_on_hand=0.
    """
    if not created:
        return

    # Avoid circular import — import here so the catalog app is ready
    from apps.inventory.models import StockLevel

    is_digital = instance.product.product_type == "digital"

    StockLevel.objects.get_or_create(
        sku=instance,
        defaults={
            "is_unlimited": is_digital,
            "quantity_on_hand": 0,
            "low_stock_threshold": 5,
            "backorder_enabled": False,
        },
    )
