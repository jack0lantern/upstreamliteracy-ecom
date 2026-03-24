from django.conf import settings
from django.db import models


class StockLevel(models.Model):
    sku = models.OneToOneField(
        "catalog.SKU",
        on_delete=models.CASCADE,
        related_name="stock_level",
    )
    quantity_on_hand = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    is_unlimited = models.BooleanField(default=False)
    backorder_enabled = models.BooleanField(default=False)
    estimated_restock = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class StockStatus(models.TextChoices):
        IN_STOCK = "in_stock", "In Stock"
        LOW_STOCK = "low_stock", "Low Stock"
        OUT_OF_STOCK = "out_of_stock", "Out of Stock"
        BACKORDER = "backorder", "Backorder"
        UNLIMITED = "unlimited", "Unlimited"

    @property
    def available_quantity(self):
        if self.is_unlimited:
            return 999999
        return self.quantity_on_hand

    @property
    def stock_status(self):
        if self.is_unlimited:
            return self.StockStatus.UNLIMITED
        if self.quantity_on_hand <= 0:
            if self.backorder_enabled:
                return self.StockStatus.BACKORDER
            return self.StockStatus.OUT_OF_STOCK
        if self.quantity_on_hand <= self.low_stock_threshold:
            return self.StockStatus.LOW_STOCK
        return self.StockStatus.IN_STOCK

    @property
    def display_label(self):
        status = self.stock_status
        if status == self.StockStatus.UNLIMITED:
            return "In Stock"
        if status == self.StockStatus.BACKORDER:
            if self.estimated_restock:
                return f"Available for Backorder — Ships by {self.estimated_restock.strftime('%b %d, %Y')}"
            return "Available for Backorder"
        if status == self.StockStatus.OUT_OF_STOCK:
            return "Out of Stock"
        if status == self.StockStatus.LOW_STOCK:
            return f"Only {self.quantity_on_hand} left"
        return "In Stock"

    def __str__(self):
        return f"{self.sku.sku_code}: {self.quantity_on_hand} ({self.stock_status})"


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        SALE = "sale", "Sale"
        RETURN = "return", "Return"
        ADJUSTMENT = "adjustment", "Adjustment"
        RESTOCK = "restock", "Restock"
        INITIAL = "initial", "Initial"
        RECONCILE = "reconcile", "Reconcile"

    sku = models.ForeignKey(
        "catalog.SKU",
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    delta = models.IntegerField()
    quantity_after = models.IntegerField()
    order = models.ForeignKey(
        "orders.Order",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["sku", "created_at"]),
        ]

    def __str__(self):
        return f"{self.sku.sku_code}: {self.movement_type} {self.delta:+d} → {self.quantity_after}"


class StockAlert(models.Model):
    class AlertType(models.TextChoices):
        LOW_STOCK = "low_stock", "Low Stock"
        OUT_OF_STOCK = "out_of_stock", "Out of Stock"
        BACKORDER_OVERDUE = "backorder_overdue", "Backorder Overdue"

    sku = models.ForeignKey(
        "catalog.SKU",
        on_delete=models.CASCADE,
        related_name="stock_alerts",
    )
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    quantity_at_trigger = models.IntegerField()
    is_active = models.BooleanField(default=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("sku", "alert_type", "is_active")]

    def __str__(self):
        return f"{self.sku.sku_code}: {self.alert_type} (active={self.is_active})"
