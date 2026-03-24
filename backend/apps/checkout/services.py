import json
import logging
from decimal import Decimal
from pathlib import Path

from .models import ShippingRate, TaxCalculation

logger = logging.getLogger(__name__)

# Load state tax rates from fixture
STATE_TAX_RATES = {}
_fixture_path = Path(__file__).parent / "tax_rates.json"
if _fixture_path.exists():
    STATE_TAX_RATES = json.loads(_fixture_path.read_text())


class TaxService:
    @staticmethod
    def calculate(session, state_code, zip_code):
        """
        Calculate sales tax for the given session based on the destination state.
        Updates session.tax_amount and session.tax_rate.
        Returns the TaxCalculation record.
        """
        if session.tax_exempt:
            calc = TaxCalculation.objects.create(
                checkout_session=session,
                destination_state=state_code,
                destination_zip=zip_code,
                taxable_amount=session.subtotal,
                tax_rate=Decimal("0"),
                tax_amount=Decimal("0"),
                is_exempt=True,
            )
            session.tax_amount = Decimal("0")
            session.tax_rate = Decimal("0")
            session.save(update_fields=["tax_amount", "tax_rate"])
            return calc

        rate = Decimal(str(STATE_TAX_RATES.get(state_code.upper(), 0)))
        amount = (session.subtotal * rate).quantize(Decimal("0.01"))

        calc = TaxCalculation.objects.create(
            checkout_session=session,
            destination_state=state_code,
            destination_zip=zip_code,
            taxable_amount=session.subtotal,
            tax_rate=rate,
            tax_amount=amount,
        )
        session.tax_amount = amount
        session.tax_rate = rate
        session.save(update_fields=["tax_amount", "tax_rate"])
        return calc


class ShippingService:
    @staticmethod
    def get_rates():
        """Return all active shipping rates."""
        return ShippingRate.objects.filter(is_active=True)

    @staticmethod
    def apply_rate(session, rate_id):
        """
        Apply a shipping rate to the session.
        Updates session.shipping_rate and session.shipping_cost.
        Returns the ShippingRate instance.
        """
        rate = ShippingRate.objects.get(id=rate_id, is_active=True)
        session.shipping_rate = rate
        session.shipping_cost = rate.flat_rate
        session.save(update_fields=["shipping_rate", "shipping_cost"])
        return rate
