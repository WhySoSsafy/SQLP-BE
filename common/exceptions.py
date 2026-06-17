import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from common import codes

logger = logging.getLogger(__name__)

def _flatten(detail, prefix="$"):
    out = []
    if isinstance(detail, dict):
        for key, val in detail.items():
            out += _flatten(val, f"{prefix}.{key}")
    elif isinstance(detail, list):
        for i, d in enumerate(detail):
            if isinstance(d, (dict, list)):
                out += _flatten(d, f"{prefix}[{i}]")
            else:
                out.append({"path": prefix, "message": str(d)})
    else:
        out.append({"path": prefix, "message": str(detail)})
    return out

def _code_for(exc):
    if isinstance(exc, exceptions.ValidationError):
        return codes.VALIDATION_ERROR
    if isinstance(exc, (exceptions.NotFound, Http404)):
        return codes.NOT_FOUND
    if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
        return codes.AUTHENTICATION_FAILED
    if isinstance(exc, (exceptions.PermissionDenied, DjangoPermissionDenied)):
        return codes.PERMISSION_DENIED
    return (getattr(exc, "default_code", None) or "ERROR").upper()

def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        # Not a DRF-recognized exception (e.g. ValueError, IntegrityError).
        # Normalize to the common envelope instead of leaking a bare 500,
        # but log the full traceback so the failure is not silently swallowed.
        logger.exception("Unhandled API exception", exc_info=exc)
        return Response(
            {"ok": False, "code": codes.INTERNAL_ERROR,
             "message": "서버 오류가 발생했습니다.", "errors": []},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    code = _code_for(exc)
    if isinstance(exc, exceptions.ValidationError):
        message = "입력값이 올바르지 않습니다."
        errors = _flatten(exc.detail)
    else:
        message = str(getattr(exc, "detail", "오류가 발생했습니다."))
        errors = []
    response.data = {"ok": False, "code": code, "message": message, "errors": errors}
    return response
