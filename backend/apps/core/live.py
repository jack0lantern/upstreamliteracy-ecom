from django.http import JsonResponse


def live(_request):
    """Liveness probe for Railway/K8s (no DB/Redis checks)."""
    return JsonResponse({"status": "live"})
