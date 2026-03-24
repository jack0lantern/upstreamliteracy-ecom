import logging

logger = logging.getLogger(__name__)


class AuditLogMiddleware:
    """
    After a request completes, if the authenticated user is a staff member,
    record the request details to the AuditLog model.

    Non-staff users are not logged here — higher-level business logic
    (e.g., order placement) should create AuditLog entries directly.

    Uses try/except throughout so that any failure in audit logging
    never breaks the request/response cycle.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            self._maybe_log(request, response)
        except Exception:
            logger.exception("AuditLogMiddleware failed to write audit log entry")

        return response

    def _maybe_log(self, request, response):
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated or not user.is_staff:
            return

        # Import here to avoid circular imports at module load time
        from apps.accounts.models import AuditLog

        ip_address = self._get_client_ip(request)
        method = request.method
        path = request.get_full_path()
        status_code = response.status_code

        AuditLog.objects.create(
            actor=user,
            actor_email=user.email,
            action=f"{method} {path}",
            target_type="http_request",
            target_id="",
            ip_address=ip_address,
            metadata={
                "method": method,
                "path": path,
                "status_code": status_code,
            },
        )

    @staticmethod
    def _get_client_ip(request) -> str | None:
        """Extract the real client IP, respecting common proxy headers."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
