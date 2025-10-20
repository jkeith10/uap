"""Custom exceptions for UAP"""

from typing import Any, Dict, Optional


class UAPException(Exception):
    """Base exception for all UAP-related errors"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ConfigurationError(UAPException):
    """Raised when there's a configuration issue"""
    pass


class ValidationError(UAPException):
    """Raised when data validation fails"""
    pass


class StorageError(UAPException):
    """Raised when storage operations fail"""
    pass


class RedisError(StorageError):
    """Raised when Redis operations fail"""
    pass


class PostgreSQLError(StorageError):
    """Raised when PostgreSQL operations fail"""
    pass


class ProtocolError(UAPException):
    """Raised when protocol operations fail"""
    pass


class MCPError(ProtocolError):
    """Raised when MCP protocol operations fail"""
    pass


class A2AError(ProtocolError):
    """Raised when A2A protocol operations fail"""
    pass


class ACPError(ProtocolError):
    """Raised when ACP protocol operations fail"""
    pass


class RoutingError(UAPException):
    """Raised when routing operations fail"""
    pass


class ReflectionError(UAPException):
    """Raised when reflection operations fail"""
    pass


class EventError(UAPException):
    """Raised when event operations fail"""
    pass


class VersioningError(UAPException):
    """Raised when versioning operations fail"""
    pass


class CircuitBreakerError(UAPException):
    """Raised when circuit breaker is open"""
    pass


class RateLimitError(UAPException):
    """Raised when rate limit is exceeded"""
    pass


class TimeoutError(UAPException):
    """Raised when operations timeout"""
    pass


class ConnectionError(UAPException):
    """Raised when connection operations fail"""
    pass


class AuthenticationError(UAPException):
    """Raised when authentication fails"""
    pass


class AuthorizationError(UAPException):
    """Raised when authorization fails"""
    pass


class ResourceNotFoundError(UAPException):
    """Raised when a resource is not found"""
    pass


class ResourceConflictError(UAPException):
    """Raised when there's a resource conflict"""
    pass


class ServiceUnavailableError(UAPException):
    """Raised when a service is unavailable"""
    pass


class InternalServerError(UAPException):
    """Raised when there's an internal server error"""
    pass
