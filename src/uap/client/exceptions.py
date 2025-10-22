"""Client-specific exceptions"""

from __future__ import annotations

from ..exceptions import UAPException


class UAPClientError(UAPException):
    """Base exception for UAP client errors"""
    pass


class ConnectionError(UAPClientError):
    """Raised when connection fails"""
    pass


class AuthenticationError(UAPClientError):
    """Raised when authentication fails"""
    pass


class NotFoundError(UAPClientError):
    """Raised when resource is not found"""
    pass


class ValidationError(UAPClientError):
    """Raised when validation fails"""
    pass


class TimeoutError(UAPClientError):
    """Raised when request times out"""
    pass


class RateLimitError(UAPClientError):
    """Raised when rate limit is exceeded"""
    pass
