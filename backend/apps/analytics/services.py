import hashlib
import logging

from django.utils import timezone

from .models import AnalyticsEvent

logger = logging.getLogger(__name__)


def track_event(
    event_name,
    user=None,
    session_id="",
    properties=None,
    source="backend",
    occurred_at=None,
):
    """
    Record an analytics event. Idempotent via idempotency_key.

    The idempotency key is derived from session_id + event_name + occurred_at so
    that re-delivery of the same frontend event (e.g. on page reload) does not
    produce duplicate rows.

    Returns (event, created) tuple.
    """
    if occurred_at is None:
        occurred_at = timezone.now()
    if properties is None:
        properties = {}

    key_input = f"{session_id}:{event_name}:{occurred_at.isoformat()}"
    idempotency_key = hashlib.sha256(key_input.encode()).hexdigest()

    event, created = AnalyticsEvent.objects.get_or_create(
        idempotency_key=idempotency_key,
        defaults={
            "event_name": event_name,
            "session_id": session_id,
            "user": user,
            "anonymous_id": properties.get("anonymous_id", ""),
            "occurred_at": occurred_at,
            "properties": properties,
            "source": source,
        },
    )

    if created:
        logger.debug(
            "analytics_event_created",
            extra={"event_name": event_name, "session_id": session_id, "source": source},
        )

    return event, created
