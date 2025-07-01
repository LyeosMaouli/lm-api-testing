# backend/app/core/exceptions.py
"""
Custom exception classes for the API testing platform.
Provides structured error handling with detailed context.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class APITestingException(Exception):
    """Base exception for all API testing platform errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)


class ServiceException(APITestingException):
    """Base exception for service-related errors."""
    pass


class AuthenticationException(APITestingException):
    """Authentication-related errors."""
    pass


class ConfigurationException(APITestingException):
    """Configuration-related errors."""
    pass


class RateLimitException(APITestingException):
    """Rate limiting errors."""
    
    def __init__(
        self, 
        message: str, 
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.retry_after = retry_after
        super().__init__(message, details, "RATE_LIMIT_EXCEEDED")


class ServiceNotFoundError(ServiceException):
    """Service module not found."""
    
    def __init__(self, service_name: str):
        super().__init__(
            f"Service '{service_name}' not found or not configured",
            {"service_name": service_name},
            "SERVICE_NOT_FOUND"
        )


class ServiceConfigurationError(ServiceException):
    """Service configuration is invalid."""
    
    def __init__(self, service_name: str, config_error: str):
        super().__init__(
            f"Service '{service_name}' configuration error: {config_error}",
            {"service_name": service_name, "config_error": config_error},
            "SERVICE_CONFIG_ERROR"
        )


class AuthenticationMethodNotSupported(AuthenticationException):
    """Authentication method not supported by service."""
    
    def __init__(self, service_name: str, auth_method: str):
        super().__init__(
            f"Authentication method '{auth_method}' not supported by service '{service_name}'",
            {"service_name": service_name, "auth_method": auth_method},
            "AUTH_METHOD_NOT_SUPPORTED"
        )


class InvalidCredentialsError(AuthenticationException):
    """Invalid or expired credentials."""
    
    def __init__(self, service_name: str, reason: str = "Invalid credentials"):
        super().__init__(
            f"Authentication failed for service '{service_name}': {reason}",
            {"service_name": service_name, "reason": reason},
            "INVALID_CREDENTIALS"
        )


class TokenExpiredError(AuthenticationException):
    """OAuth token has expired."""
    
    def __init__(self, service_name: str):
        super().__init__(
            f"OAuth token expired for service '{service_name}'. Please re-authenticate.",
            {"service_name": service_name},
            "TOKEN_EXPIRED"
        )


class WebhookError(ServiceException):
    """Webhook-related errors."""
    
    def __init__(self, message: str, webhook_id: Optional[str] = None):
        super().__init__(
            message,
            {"webhook_id": webhook_id} if webhook_id else {},
            "WEBHOOK_ERROR"
        )


class RequestValidationError(APITestingException):
    """Request validation errors."""
    
    def __init__(self, validation_errors: Dict[str, Any]):
        super().__init__(
            "Request validation failed",
            {"validation_errors": validation_errors},
            "REQUEST_VALIDATION_ERROR"
        )


class ExternalAPIError(ServiceException):
    """External API returned an error."""
    
    def __init__(
        self, 
        service_name: str, 
        status_code: int, 
        response_body: str,
        request_id: Optional[str] = None
    ):
        super().__init__(
            f"External API error from {service_name}: HTTP {status_code}",
            {
                "service_name": service_name,
                "status_code": status_code,
                "response_body": response_body,
                "request_id": request_id
            },
            "EXTERNAL_API_ERROR"
        )


class EncryptionError(APITestingException):
    """Encryption/decryption errors."""
    
    def __init__(self, operation: str, reason: str):
        super().__init__(
            f"Encryption {operation} failed: {reason}",
            {"operation": operation, "reason": reason},
            "ENCRYPTION_ERROR"
        )


# HTTP Exception mapping for FastAPI
def map_exception_to_http(exc: APITestingException) -> HTTPException:
    """Map internal exceptions to HTTP exceptions for FastAPI."""
    
    error_mappings = {
        ServiceNotFoundError: status.HTTP_404_NOT_FOUND,
        ServiceConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        AuthenticationMethodNotSupported: status.HTTP_400_BAD_REQUEST,
        InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
        TokenExpiredError: status.HTTP_401_UNAUTHORIZED,
        RequestValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        RateLimitException: status.HTTP_429_TOO_MANY_REQUESTS,
        ExternalAPIError: status.HTTP_502_BAD_GATEWAY,
        EncryptionError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    status_code = error_mappings.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    headers = {}
    if isinstance(exc, RateLimitException) and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error": exc.error_code or "INTERNAL_ERROR",
            "message": exc.message,
            "details": exc.details
        },
        headers=headers if headers else None
    )