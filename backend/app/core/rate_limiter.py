# backend/app/core/rate_limiter.py
"""
Advanced rate limiting system for API testing platform.
Supports multiple rate limiting strategies and service-specific limits.
"""

import time
import asyncio
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from .exceptions import RateLimitException

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_second: Optional[int] = None
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    burst_limit: Optional[int] = None
    concurrent_requests: Optional[int] = None
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW


@dataclass
class RequestRecord:
    """Record of a single request for rate limiting."""
    timestamp: datetime
    service: str
    endpoint: str
    success: bool = True


@dataclass
class RateLimitState:
    """Current state of rate limiting for a service."""
    service_name: str
    current_requests: int = 0
    active_requests: int = 0
    last_reset: datetime = field(default_factory=datetime.utcnow)
    request_history: List[RequestRecord] = field(default_factory=list)
    tokens: float = 0  # For token bucket strategy
    last_refill: datetime = field(default_factory=datetime.utcnow)


class RateLimiter:
    """
    Advanced rate limiter supporting multiple strategies and service-specific limits.
    """
    
    def __init__(self):
        self._service_states: Dict[str, RateLimitState] = {}
        self._service_configs: Dict[str, RateLimitConfig] = {}
        self._request_queue: Dict[str, asyncio.Queue] = {}
        self._processing_tasks: Dict[str, asyncio.Task] = {}
        
    def configure_service(self, service_name: str, config: RateLimitConfig):
        """Configure rate limits for a specific service."""
        self._service_configs[service_name] = config
        
        # Initialize state if not exists
        if service_name not in self._service_states:
            self._service_states[service_name] = RateLimitState(
                service_name=service_name,
                tokens=config.burst_limit or config.requests_per_minute or 10
            )
            
        # Initialize request queue for this service
        if service_name not in self._request_queue:
            self._request_queue[service_name] = asyncio.Queue()
            
        logger.info(f"Configured rate limits for service: {service_name}")
        
    async def check_rate_limit(
        self, 
        service_name: str, 
        endpoint: str = "default"
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed under current rate limits.
        
        Args:
            service_name: Name of the service
            endpoint: Specific endpoint (for endpoint-specific limits)
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        if service_name not in self._service_configs:
            # No rate limit configured - allow request
            return True, None
            
        config = self._service_configs[service_name]
        state = self._service_states[service_name]
        
        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._check_token_bucket(config, state, endpoint)
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._check_sliding_window(config, state, endpoint)
        elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._check_fixed_window(config, state, endpoint)
        else:
            return True, None
            
    async def _check_token_bucket(
        self, 
        config: RateLimitConfig, 
        state: RateLimitState, 
        endpoint: str
    ) -> Tuple[bool, Optional[int]]:
        """Token bucket rate limiting algorithm."""
        now = datetime.utcnow()
        
        # Refill tokens based on configured rate
        if config.requests_per_second:
            rate = config.requests_per_second
            time_passed = (now - state.last_refill).total_seconds()
            tokens_to_add = time_passed * rate
            state.tokens = min(
                config.burst_limit or rate * 2, 
                state.tokens + tokens_to_add
            )
            state.last_refill = now
            
        # Check if we have tokens available
        if state.tokens >= 1:
            state.tokens -= 1
            return True, None
        else:
            # Calculate retry after time
            retry_after = 1 / (config.requests_per_second or 1)
            return False, int(retry_after) + 1
            
    async def _check_sliding_window(
        self, 
        config: RateLimitConfig, 
        state: RateLimitState, 
        endpoint: str
    ) -> Tuple[bool, Optional[int]]:
        """Sliding window rate limiting algorithm."""
        now = datetime.utcnow()
        
        # Clean old requests from history
        self._cleanup_request_history(state, now)
        
        # Check each time window
        for window_size, limit in [
            (1, config.requests_per_second),
            (60, config.requests_per_minute),
            (3600, config.requests_per_hour),
            (86400, config.requests_per_day)
        ]:
            if limit is None:
                continue
                
            # Count requests in this window
            window_start = now - timedelta(seconds=window_size)
            requests_in_window = sum(
                1 for req in state.request_history 
                if req.timestamp >= window_start
            )
            
            if requests_in_window >= limit:
                # Calculate retry after time
                oldest_request = min(
                    req.timestamp for req in state.request_history 
                    if req.timestamp >= window_start
                )
                retry_after = int((oldest_request + timedelta(seconds=window_size) - now).total_seconds()) + 1
                return False, retry_after
                
        # Check concurrent requests limit
        if config.concurrent_requests and state.active_requests >= config.concurrent_requests:
            return False, 1
            
        return True, None
        
    async def _check_fixed_window(
        self, 
        config: RateLimitConfig, 
        state: RateLimitState, 
        endpoint: str
    ) -> Tuple[bool, Optional[int]]:
        """Fixed window rate limiting algorithm."""
        now = datetime.utcnow()
        
        # Determine window boundaries
        if config.requests_per_minute:
            window_start = now.replace(second=0, microsecond=0)
            window_size = 60
            limit = config.requests_per_minute
        elif config.requests_per_hour:
            window_start = now.replace(minute=0, second=0, microsecond=0)
            window_size = 3600
            limit = config.requests_per_hour
        elif config.requests_per_day:
            window_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            window_size = 86400
            limit = config.requests_per_day
        else:
            return True, None
            
        # Reset counter if we're in a new window
        if window_start > state.last_reset:
            state.current_requests = 0
            state.last_reset = window_start
            
        # Check if we're over the limit
        if state.current_requests >= limit:
            retry_after = int((window_start + timedelta(seconds=window_size) - now).total_seconds()) + 1
            return False, retry_after
            
        return True, None
        
    def _cleanup_request_history(self, state: RateLimitState, now: datetime):
        """Remove old requests from history to prevent memory bloat."""
        # Keep requests from the last 24 hours
        cutoff = now - timedelta(hours=24)
        state.request_history = [
            req for req in state.request_history 
            if req.timestamp >= cutoff
        ]
        
    async def record_request(
        self, 
        service_name: str, 
        endpoint: str, 
        success: bool = True
    ):
        """Record a completed request for rate limiting tracking."""
        if service_name not in self._service_states:
            return
            
        state = self._service_states[service_name]
        
        # Add to request history
        request_record = RequestRecord(
            timestamp=datetime.utcnow(),
            service=service_name,
            endpoint=endpoint,
            success=success
        )
        state.request_history.append(request_record)
        
        # Update counters
        if self._service_configs[service_name].strategy == RateLimitStrategy.FIXED_WINDOW:
            state.current_requests += 1
            
        logger.debug(f"Recorded request for {service_name}/{endpoint}: success={success}")
        
    async def start_request(self, service_name: str, endpoint: str):
        """Mark the start of a request (for concurrent request tracking)."""
        if service_name not in self._service_states:
            return
            
        state = self._service_states[service_name]
        state.active_requests += 1
        logger.debug(f"Started request for {service_name}/{endpoint} (active: {state.active_requests})")
        
    async def end_request(self, service_name: str, endpoint: str, success: bool = True):
        """Mark the end of a request."""
        if service_name not in self._service_states:
            return
            
        state = self._service_states[service_name]
        state.active_requests = max(0, state.active_requests - 1)
        
        # Record the request
        await self.record_request(service_name, endpoint, success)
        
        logger.debug(f"Ended request for {service_name}/{endpoint} (active: {state.active_requests})")
        
    async def wait_for_rate_limit(self, service_name: str, endpoint: str = "default"):
        """
        Wait for rate limit to allow request, with intelligent queuing.
        
        Args:
            service_name: Name of the service
            endpoint: Specific endpoint
            
        Raises:
            RateLimitException: If rate limit cannot be satisfied
        """
        max_wait_time = 300  # 5 minutes maximum wait
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            allowed, retry_after = await self.check_rate_limit(service_name, endpoint)
            
            if allowed:
                await self.start_request(service_name, endpoint)
                return
                
            if retry_after:
                if retry_after > max_wait_time:
                    raise RateLimitException(
                        f"Rate limit exceeded for {service_name}. Retry after {retry_after} seconds.",
                        retry_after=retry_after
                    )
                    
                logger.info(f"Rate limit hit for {service_name}, waiting {retry_after} seconds")
                await asyncio.sleep(retry_after)
            else:
                await asyncio.sleep(1)  # Default wait
                
        raise RateLimitException(
            f"Rate limit exceeded for {service_name}. Maximum wait time exceeded.",
            retry_after=60
        )
        
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get current rate limit status for a service."""
        if service_name not in self._service_configs:
            return {"error": "Service not configured"}
            
        config = self._service_configs[service_name]
        state = self._service_states.get(service_name)
        
        if not state:
            return {"error": "Service state not found"}
            
        now = datetime.utcnow()
        
        # Calculate current usage
        usage = {}
        for window_name, window_seconds in [
            ("last_second", 1),
            ("last_minute", 60),
            ("last_hour", 3600),
            ("last_day", 86400)
        ]:
            window_start = now - timedelta(seconds=window_seconds)
            requests_in_window = sum(
                1 for req in state.request_history 
                if req.timestamp >= window_start
            )
            usage[window_name] = requests_in_window
            
        return {
            "service_name": service_name,
            "strategy": config.strategy.value,
            "limits": {
                "requests_per_second": config.requests_per_second,
                "requests_per_minute": config.requests_per_minute,
                "requests_per_hour": config.requests_per_hour,
                "requests_per_day": config.requests_per_day,
                "burst_limit": config.burst_limit,
                "concurrent_requests": config.concurrent_requests
            },
            "current_usage": usage,
            "active_requests": state.active_requests,
            "available_tokens": state.tokens if config.strategy == RateLimitStrategy.TOKEN_BUCKET else None,
            "last_reset": state.last_reset.isoformat(),
            "total_requests": len(state.request_history)
        }
        
    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """Get rate limit status for all configured services."""
        return {
            service_name: self.get_service_status(service_name)
            for service_name in self._service_configs.keys()
        }
        
    async def reset_service_limits(self, service_name: str):
        """Reset rate limits for a specific service."""
        if service_name in self._service_states:
            state = self._service_states[service_name]
            state.current_requests = 0
            state.active_requests = 0
            state.request_history.clear()
            state.last_reset = datetime.utcnow()
            
            # Reset tokens for token bucket
            config = self._service_configs.get(service_name)
            if config and config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                state.tokens = config.burst_limit or config.requests_per_minute or 10
                state.last_refill = datetime.utcnow()
                
            logger.info(f"Reset rate limits for service: {service_name}")


# Global rate limiter instance
rate_limiter = RateLimiter()