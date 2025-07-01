# backend/app/services/base.py
"""
Base service class that all API service integrations inherit from.
Provides common functionality for authentication, rate limiting, request handling.
"""

import time
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
import httpx
import logging
from dataclasses import dataclass, field

from ..core.exceptions import (
    ServiceException, 
    AuthenticationException, 
    RateLimitException,
    ExternalAPIError,
    InvalidCredentialsError
)

logger = logging.getLogger(__name__)


@dataclass
class RequestInfo:
    """Information about an API request."""
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    body: Optional[Union[Dict, str, bytes]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration: Optional[float] = None
    status_code: Optional[int] = None
    response_size: Optional[int] = None
    error: Optional[str] = None


@dataclass
class RateLimitState:
    """Rate limiting state tracking."""
    requests_this_minute: int = 0
    requests_this_hour: int = 0
    requests_this_day: int = 0
    last_request_time: datetime = field(default_factory=datetime.utcnow)
    reset_times: Dict[str, datetime] = field(default_factory=dict)


class BaseService(ABC):
    """
    Abstract base class for all API service integrations.
    
    Provides:
    - Authentication handling
    - Rate limiting
    - Request/response logging
    - Error handling
    - Retry logic
    - Configuration management
    """
    
    _is_service_class = True  # Marker for service discovery
    
    def __init__(
        self, 
        config: Dict[str, Any], 
        credentials: Optional[Dict[str, Any]] = None
    ):
        self.config = config
        self.service_name = config.get('service_name', 'unknown')
        self.environment = config.get('environment', 'production')
        self.base_url = config.get('base_url', '')
        
        # Authentication
        self.credentials = credentials or {}
        self.auth_headers: Dict[str, str] = {}
        
        # Rate limiting
        self.rate_limits = config.get('rate_limits', {})
        self.rate_limit_state = RateLimitState()
        
        # HTTP client
        self.client_config = config.get('settings', {})
        self.timeout = self.client_config.get('timeout', 30)
        self.retries = self.client_config.get('retries', 3)
        self.verify_ssl = self.client_config.get('verify_ssl', True)
        
        # Request tracking
        self.request_history: List[RequestInfo] = []
        self.max_history_size = 1000
        
        # Initialize HTTP client
        self._http_client: Optional[httpx.AsyncClient] = None
        
        # Initialize authentication if credentials provided
        if self.credentials:
            self._setup_authentication()
            
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_http_client()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def _ensure_http_client(self):
        """Ensure HTTP client is initialized."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers=self._get_default_headers()
            )
            
    async def close(self):
        """Close HTTP client and cleanup resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
            
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        headers = {
            'User-Agent': f'API-Testing-Platform/{self.service_name}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Add authentication headers
        headers.update(self.auth_headers)
        
        return headers
        
    def _setup_authentication(self):
        """Setup authentication based on credentials and service config."""
        auth_methods = self.config.get('authentication', {})
        
        if not auth_methods:
            logger.warning(f"No authentication methods configured for {self.service_name}")
            return
            
        # Try to find and setup appropriate authentication method
        for method_name, method_config in auth_methods.items():
            if self._can_authenticate_with_method(method_config):
                self._setup_auth_method(method_config)
                logger.info(f"Using authentication method: {method_name}")
                return
                
        logger.warning(f"No suitable authentication method found for {self.service_name}")
        
    def _can_authenticate_with_method(self, method_config: Dict[str, Any]) -> bool:
        """Check if we have required credentials for this auth method."""
        required_fields = method_config.get('required_fields', [])
        return all(field in self.credentials for field in required_fields)
        
    def _setup_auth_method(self, method_config: Dict[str, Any]):
        """Setup authentication method based on configuration."""
        auth_type = method_config.get('type', '')
        
        if auth_type == 'api_key':
            self._setup_api_key_auth(method_config)
        elif auth_type == 'bearer':
            self._setup_bearer_auth(method_config)
        elif auth_type == 'basic':
            self._setup_basic_auth(method_config)
        elif auth_type == 'oauth2':
            self._setup_oauth2_auth(method_config)
        else:
            logger.warning(f"Unsupported authentication type: {auth_type}")
            
    def _setup_api_key_auth(self, method_config: Dict[str, Any]):
        """Setup API key authentication."""
        api_key = self.credentials.get('api_key')
        if not api_key:
            raise AuthenticationException("API key not provided")
            
        header_name = method_config.get('header', 'Authorization')
        
        if header_name.lower() == 'authorization':
            self.auth_headers[header_name] = f"Bearer {api_key}"
        else:
            self.auth_headers[header_name] = api_key
            
    def _setup_bearer_auth(self, method_config: Dict[str, Any]):
        """Setup Bearer token authentication."""
        token = self.credentials.get('access_token') or self.credentials.get('token')
        if not token:
            raise AuthenticationException("Bearer token not provided")
            
        self.auth_headers['Authorization'] = f"Bearer {token}"
        
    def _setup_basic_auth(self, method_config: Dict[str, Any]):
        """Setup Basic authentication."""
        username = self.credentials.get('username')
        password = self.credentials.get('password')
        
        if not username or not password:
            raise AuthenticationException("Username and password required for Basic auth")
            
        import base64
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.auth_headers['Authorization'] = f"Basic {credentials}"
        
    def _setup_oauth2_auth(self, method_config: Dict[str, Any]):
        """Setup OAuth2 authentication."""
        access_token = self.credentials.get('access_token')
        if not access_token:
            raise AuthenticationException("OAuth2 access token not provided")
            
        self.auth_headers['Authorization'] = f"Bearer {access_token}"
        
        # Check if token is expired and needs refresh
        if self._is_token_expired():
            self._refresh_oauth_token(method_config)
            
    def _is_token_expired(self) -> bool:
        """Check if OAuth token is expired."""
        expires_at = self.credentials.get('expires_at')
        if not expires_at:
            return False
            
        # Parse expiration time
        if isinstance(expires_at, str):
            from datetime import datetime
            try:
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            except ValueError:
                return False
                
        return datetime.utcnow() > expires_at
        
    def _refresh_oauth_token(self, method_config: Dict[str, Any]):
        """Refresh OAuth2 token."""
        # This is a placeholder - specific services should implement their own refresh logic
        logger.warning("OAuth token refresh not implemented for this service")
        
    async def _check_rate_limits(self):
        """Check and enforce rate limits."""
        if not self.rate_limits:
            return
            
        now = datetime.utcnow()
        
        # Reset counters if time windows have passed
        if 'requests_per_minute' in self.rate_limits:
            if now - self.rate_limit_state.last_request_time > timedelta(minutes=1):
                self.rate_limit_state.requests_this_minute = 0
                
        if 'requests_per_hour' in self.rate_limits:
            if now - self.rate_limit_state.last_request_time > timedelta(hours=1):
                self.rate_limit_state.requests_this_hour = 0
                
        if 'requests_per_day' in self.rate_limits:
            if now - self.rate_limit_state.last_request_time > timedelta(days=1):
                self.rate_limit_state.requests_this_day = 0
                
        # Check limits
        if (self.rate_limits.get('requests_per_minute') and 
            self.rate_limit_state.requests_this_minute >= self.rate_limits['requests_per_minute']):
            retry_after = 60 - (now - self.rate_limit_state.last_request_time).seconds
            raise RateLimitException(
                f"Rate limit exceeded: {self.rate_limits['requests_per_minute']} requests per minute",
                retry_after=max(retry_after, 1)
            )
            
        if (self.rate_limits.get('requests_per_hour') and 
            self.rate_limit_state.requests_this_hour >= self.rate_limits['requests_per_hour']):
            retry_after = 3600 - (now - self.rate_limit_state.last_request_time).seconds
            raise RateLimitException(
                f"Rate limit exceeded: {self.rate_limits['requests_per_hour']} requests per hour",
                retry_after=max(retry_after, 60)
            )
            
    def _update_rate_limit_counters(self):
        """Update rate limit counters after successful request."""
        self.rate_limit_state.requests_this_minute += 1
        self.rate_limit_state.requests_this_hour += 1
        self.rate_limit_state.requests_this_day += 1
        self.rate_limit_state.last_request_time = datetime.utcnow()
        
    async def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Union[Dict, str, bytes]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make an HTTP request with rate limiting, retries, and logging.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            headers: Additional headers
            body: Request body
            **kwargs: Additional httpx options
            
        Returns:
            HTTP response object
            
        Raises:
            RateLimitException: If rate limit exceeded
            ExternalAPIError: If API returns error
            ServiceException: For other service-related errors
        """
        await self._ensure_http_client()
        await self._check_rate_limits()
        
        # Construct full URL
        url = self._build_url(endpoint)
        
        # Prepare headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)
            
        # Create request info for logging
        request_info = RequestInfo(
            method=method.upper(),
            url=url,
            headers=request_headers.copy(),
            params=params or {},
            body=body
        )
        
        start_time = time.time()
        
        try:
            # Make request with retries
            response = await self._make_request_with_retries(
                method, url, params, request_headers, body, **kwargs
            )
            
            # Update request info
            request_info.duration = time.time() - start_time
            request_info.status_code = response.status_code
            request_info.response_size = len(response.content) if response.content else 0
            
            # Update rate limiting
            self._update_rate_limit_counters()
            
            # Log successful request
            self._log_request(request_info, response)
            
            # Check for API errors
            if response.status_code >= 400:
                await self._handle_api_error(response, request_info)
                
            return response
            
        except Exception as e:
            request_info.duration = time.time() - start_time
            request_info.error = str(e)
            self._log_request(request_info, None)
            raise
            
    async def _make_request_with_retries(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]],
        headers: Dict[str, str],
        body: Optional[Union[Dict, str, bytes]],
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        last_exception = None
        
        for attempt in range(self.retries + 1):
            try:
                response = await self._http_client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    json=body if isinstance(body, dict) else None,
                    data=body if isinstance(body, (str, bytes)) else None,
                    **kwargs
                )
                
                # Don't retry on successful responses or client errors
                if response.status_code < 500:
                    return response
                    
                # Server error - retry if we have attempts left
                if attempt < self.retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
                return response
                
            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise ServiceException(f"Request failed after {self.retries + 1} attempts: {str(e)}")
                    
        # This shouldn't be reached, but just in case
        if last_exception:
            raise last_exception
            
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from base URL and endpoint."""
        if endpoint.startswith('http'):
            return endpoint
            
        base = self.base_url.rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{base}/{endpoint}"
        
    async def _handle_api_error(self, response: httpx.Response, request_info: RequestInfo):
        """Handle API error responses."""
        try:
            error_data = response.json()
        except:
            error_data = response.text
            
        raise ExternalAPIError(
            service_name=self.service_name,
            status_code=response.status_code,
            response_body=str(error_data),
            request_id=request_info.timestamp.isoformat()
        )
        
    def _log_request(self, request_info: RequestInfo, response: Optional[httpx.Response]):
        """Log request details for debugging and analysis."""
        # Add to history
        self.request_history.append(request_info)
        
        # Limit history size
        if len(self.request_history) > self.max_history_size:
            self.request_history = self.request_history[-self.max_history_size:]
            
        # Log to system logger
        log_data = {
            'service': self.service_name,
            'environment': self.environment,
            'method': request_info.method,
            'url': request_info.url,
            'status_code': request_info.status_code,
            'duration': request_info.duration,
            'response_size': request_info.response_size,
            'error': request_info.error
        }
        
        if request_info.error:
            logger.error(f"API request failed: {log_data}")
        else:
            logger.info(f"API request completed: {log_data}")
            
    def update_credentials(self, credentials: Dict[str, Any]):
        """Update service credentials and re-setup authentication."""
        self.credentials = credentials
        self.auth_headers.clear()
        self._setup_authentication()
        
    def get_request_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get request history as serializable dictionaries."""
        history = self.request_history
        if limit:
            history = history[-limit:]
            
        return [
            {
                'method': req.method,
                'url': req.url,
                'timestamp': req.timestamp.isoformat(),
                'duration': req.duration,
                'status_code': req.status_code,
                'response_size': req.response_size,
                'error': req.error,
                'params': req.params,
                'headers': {k: v for k, v in req.headers.items() if k.lower() not in ['authorization']}
            }
            for req in history
        ]
        
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return {
            'service': self.service_name,
            'environment': self.environment,
            'limits': self.rate_limits,
            'current_usage': {
                'requests_this_minute': self.rate_limit_state.requests_this_minute,
                'requests_this_hour': self.rate_limit_state.requests_this_hour,
                'requests_this_day': self.rate_limit_state.requests_this_day
            },
            'last_request': self.rate_limit_state.last_request_time.isoformat(),
            'reset_times': {
                k: v.isoformat() for k, v in self.rate_limit_state.reset_times.items()
            }
        }
        
    # Abstract methods that services must implement
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection and authentication with the service.
        
        Returns:
            Dictionary with test results
        """
        pass
        
    @abstractmethod
    def get_supported_endpoints(self) -> List[str]:
        """
        Get list of supported API endpoints.
        
        Returns:
            List of endpoint names
        """
        pass
        
    # Optional methods that services can override
    
    async def validate_credentials(self) -> bool:
        """
        Validate current credentials.
        
        Returns:
            True if credentials are valid
        """
        try:
            result = await self.test_connection()
            return result.get('success', False)
        except Exception:
            return False
            
    def get_webhook_config(self) -> Optional[Dict[str, Any]]:
        """
        Get webhook configuration for this service.
        
        Returns:
            Webhook configuration or None if not supported
        """
        return self.config.get('webhooks')
        
    async def handle_webhook(self, headers: Dict[str, str], body: bytes) -> Dict[str, Any]:
        """
        Handle incoming webhook from the service.
        
        Args:
            headers: HTTP headers from webhook request
            body: Raw webhook body
            
        Returns:
            Processing results
        """
        return {
            'success': True,
            'message': 'Webhook received but not processed (default handler)'
        }