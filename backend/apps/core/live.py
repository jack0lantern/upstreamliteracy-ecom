from django.http import JsonResponse


def live(_request):
    """Process liveness probe (Railway/K8s). Does not check DB or Redis."""
    return JsonResponse({"status": "live"})
