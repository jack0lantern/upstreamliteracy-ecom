import logging

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def _build_error_response(code: str, message: str, field_errors: dict | None = None, status_code: int = 400) -> Response:
    payload = {
        "error": {
            "code": code,
            "message": message,
            "field_errors": field_errors or {},
        }
    }
    return Response(payload, status=status_code)


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler that normalises all errors into:
    {
        "error": {
            "code": "<snake_case_code>",
            "message": "<human readable>",
            "field_errors": { "<field>": ["<error>", ...] }
        }
    }
    """
    # Convert Django's built-in exceptions to DRF equivalents
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()
    elif isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(detail=exc.messages)

    # Let DRF handle it first to get a Response object
    response = drf_exception_handler(exc, context)

    if response is None:
        # Unhandled exception — log and return a generic 500
        logger.exception("Unhandled exception in view", exc_info=exc)
        return _build_error_response(
            code="internal_error",
            message="An unexpected error occurred. Please try again later.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, exceptions.ValidationError):
        detail = exc.detail
        if isinstance(detail, dict):
            field_errors = {}
            for field, errors in detail.items():
                if isinstance(errors, list):
                    field_errors[field] = [str(e) for e in errors]
                else:
                    field_errors[field] = [str(errors)]
            message = "Validation failed."
        elif isinstance(detail, list):
            field_errors = {"non_field_errors": [str(e) for e in detail]}
            message = str(detail[0]) if detail else "Validation failed."
        else:
            field_errors = {}
            message = str(detail)
        return _build_error_response(
            code="validation_error",
            message=message,
            field_errors=field_errors,
            status_code=response.status_code,
        )

    if isinstance(exc, exceptions.AuthenticationFailed):
        return _build_error_response(
            code="authentication_failed",
            message=str(exc.detail) if hasattr(exc, "detail") else "Authentication failed.",
            status_code=response.status_code,
        )

    if isinstance(exc, exceptions.NotAuthenticated):
        return _build_error_response(
            code="not_authenticated",
            message="Authentication credentials were not provided.",
            status_code=response.status_code,
        )

    if isinstance(exc, exceptions.PermissionDenied):
        return _build_error_response(
            code="permission_denied",
            message=str(exc.detail) if hasattr(exc, "detail") else "You do not have permission to perform this action.",
            status_code=response.status_code,
        )

    if isinstance(exc, exceptions.NotFound):
        return _build_error_response(
            code="not_found",
            message=str(exc.detail) if hasattr(exc, "detail") else "The requested resource was not found.",
            status_code=response.status_code,
        )

    if isinstance(exc, exceptions.MethodNotAllowed):
        return _build_error_response(
            code="method_not_allowed",
            message=str(exc.detail) if hasattr(exc, "detail") else "Method not allowed.",
            status_code=response.status_code,
        )

    if isinstance(exc, exceptions.Throttled):
        wait = getattr(exc, "wait", None)
        msg = f"Request was throttled. Expected available in {wait:.0f} seconds." if wait else "Request was throttled."
        return _build_error_response(
            code="throttled",
            message=msg,
            status_code=response.status_code,
        )

    # Generic API exception fallback
    detail = getattr(exc, "detail", str(exc))
    return _build_error_response(
        code="api_error",
        message=str(detail),
        status_code=response.status_code,
    )
