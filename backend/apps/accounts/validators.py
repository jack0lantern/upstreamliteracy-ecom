import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class NumericCharacterValidator:
    """
    Validate that the password contains at least one numeric character.
    """

    def validate(self, password, user=None):
        if not re.search(r"\d", password):
            raise ValidationError(
                _("The password must contain at least one numeric character (0–9)."),
                code="password_no_number",
            )

    def get_help_text(self):
        return _("Your password must contain at least one numeric character (0–9).")


class SpecialCharacterValidator:
    """
    Validate that the password contains at least one special character.
    """

    SPECIAL_CHARS = r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]"

    def validate(self, password, user=None):
        if not re.search(self.SPECIAL_CHARS, password):
            raise ValidationError(
                _("The password must contain at least one special character (e.g., !@#$%^&*)."),
                code="password_no_special",
            )

    def get_help_text(self):
        return _("Your password must contain at least one special character (e.g., !@#$%^&*).")
