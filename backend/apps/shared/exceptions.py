from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class DomainError(Exception):
    """Raised by service-layer code for business-rule violations."""
    def __init__(self, message, code="domain_error", http_status=status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.code = code
        self.http_status = http_status
        super().__init__(message)


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default exception handler so DomainError raised in services
    is converted into a consistent JSON error envelope.
    """
    if isinstance(exc, DomainError):
        return Response(
            {"error": {"code": exc.code, "message": exc.message}},
            status=exc.http_status,
        )
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {"error": {"code": "error", "message": response.data}}
    return response
