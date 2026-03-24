import uuid
import secrets
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class ShippingRate(models.Model):
    name = models.CharField(max_length=100)
    flat_rate = models.DecimalField(max_digits=8, decimal_places=2)
    estimated_days_min = models.PositiveSmallIntegerField(default=3)
    estimated_days_max = models.PositiveSmallIntegerField(default=7)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "flat_rate"]

    def __str__(self):
        return f"{self.name} (${self.flat_rate})"


class CheckoutSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUBMITTED = "submitted", "Submitted"
        CONFIRMED = "confirmed", "Confirmed"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        default=secrets.token_urlsafe,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    guest_email = models.EmailField(null=True, blank=True)
    current_step = models.CharField(max_length=32, default="contact")
    cart_snapshot = models.JSONField(default=dict)
    shipping_address = models.JSONField(null=True, blank=True)
    billing_address = models.JSONField(null=True, blank=True)
    billing_same_as_shipping = models.BooleanField(default=True)
    shipping_rate = models.ForeignKey(
        ShippingRate,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    tax_exempt = models.BooleanField(default=False)
    stripe_payment_intent_id = models.CharField(max_length=64, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    expires_at = models.DateTimeField()
    order = models.OneToOneField(
        "orders.Order",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=2)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def extend_expiry(self, minutes=30):
        self.expires_at = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save(update_fields=["expires_at"])

    def compute_total(self):
        shipping = self.shipping_cost or Decimal("0.00")
        tax = self.tax_amount or Decimal("0.00")
        self.total = self.subtotal + shipping + tax
        self.save(update_fields=["total"])

    def __str__(self):
        return f"Session {self.session_token[:8]}... ({self.status})"


class TaxCalculation(models.Model):
    checkout_session = models.ForeignKey(
        CheckoutSession,
        on_delete=models.CASCADE,
        related_name="tax_calculations",
    )
    destination_state = models.CharField(max_length=2)
    destination_zip = models.CharField(max_length=10)
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_exempt = models.BooleanField(default=False)
    provider = models.CharField(max_length=20, default="state_table")
    calculated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.destination_state} — ${self.tax_amount}"
