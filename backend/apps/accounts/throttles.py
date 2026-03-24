from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Throttle login attempts to 5 per minute per IP address.
    """

    scope = "login"
    THROTTLE_RATES = {"login": "5/min"}


class ResetRateThrottle(AnonRateThrottle):
    """
    Throttle password reset requests to 3 per hour per IP address.
    """

    scope = "password_reset"
    THROTTLE_RATES = {"password_reset": "3/hour"}
