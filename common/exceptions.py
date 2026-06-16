from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc, context):
    """Stub exception handler — full implementation is Task 2.1."""
    return drf_exception_handler(exc, context)
