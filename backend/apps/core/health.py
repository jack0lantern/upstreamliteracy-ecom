import json
import logging

from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint.

    Returns 200 with status "ok" when both database and Redis are reachable.
    Returns 503 with status "degraded" if the database is unreachable
    (Redis failure alone is non-fatal but still reported).
    """
    db_status = "ok"
    redis_status = "ok"

    # --- Database check ---
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        logger.exception("Health check: database is unreachable")
        db_status = "error"

    # --- Redis check ---
    try:
        from django.core.cache import cache

        cache.set("__health_check__", "1", timeout=5)
        value = cache.get("__health_check__")
        if value != "1":
            raise RuntimeError("Redis get did not return the expected value")
    except Exception:
        logger.exception("Health check: Redis is unreachable")
        redis_status = "error"

    overall = "ok" if db_status == "ok" else "degraded"
    http_status = 200 if db_status == "ok" else 503

    payload = {
        "status": overall,
        "database": db_status,
        "redis": redis_status,
    }

    return JsonResponse(payload, status=http_status)
