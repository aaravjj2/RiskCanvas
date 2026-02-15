"""
RiskCanvas Error Taxonomy - v1.0
Standardised error codes and helpers for the API layer.
"""

from typing import Optional


class ErrorCode:
    """Canonical error codes following the RiskCanvas error taxonomy."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    COMPUTATION_ERROR = "COMPUTATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    INTERNAL = "INTERNAL_ERROR"
    AUTH_ERROR = "AUTH_ERROR"
    RATE_LIMIT = "RATE_LIMIT"


class RiskCanvasError(Exception):
    """Base exception for all RiskCanvas API errors."""

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        request_id: Optional[str] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.request_id = request_id or ""
        super().__init__(message)


def error_response(
    error_code: str,
    message: str,
    request_id: Optional[str] = None,
) -> dict:
    """Build a JSON-serialisable error envelope."""
    return {
        "error_code": error_code,
        "message": message,
        "request_id": request_id or "",
    }
