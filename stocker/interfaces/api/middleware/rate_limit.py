"""Rate limiting middleware for STOCKER Pro API.

This module provides rate limiting functionality to protect the API from abuse.
"""

import time
from typing import Callable, Dict, Optional, Tuple

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests.
    
    This middleware limits the number of requests per client IP address
    to prevent abuse of the API.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        requests_per_minute: int = 60,
        exclude_paths: Optional[list] = None,
        whitelist_ips: Optional[list] = None,
        key_func: Optional[Callable[[Request], str]] = None
    ):
        """Initialize rate limit middleware.
        
        Args:
            app: ASGI application
            requests_per_minute: Maximum number of requests per minute
            exclude_paths: List of paths to exclude from rate limiting
            whitelist_ips: List of IP addresses to exclude from rate limiting
            key_func: Function to extract rate limit key from request
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.exclude_paths = exclude_paths or []
        self.whitelist_ips = whitelist_ips or []
        self.key_func = key_func or self._default_key_func
        
        # Request tracking
        self.requests: Dict[str, Tuple[int, float]] = {}
        
        # Log configuration
        logger.info(
            f"Rate limit middleware initialized: {requests_per_minute} requests per minute",
            extra={
                "requests_per_minute": requests_per_minute,
                "exclude_paths": exclude_paths,
                "whitelist_ips": whitelist_ips
            }
        )
    
    def _default_key_func(self, request: Request) -> str:
        """Default function to extract rate limit key from request.
        
        Uses client IP address as the key.
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: Rate limit key
        """
        # Try to get real IP from headers if behind proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the chain
            ip = forwarded_for.split(",")[0].strip()
        else:
            # Fall back to direct client IP
            ip = request.client.host if request.client else "unknown"
        
        return ip
    
    def _is_rate_limited(self, key: str) -> bool:
        """Check if a key has exceeded the rate limit.
        
        Args:
            key: Rate limit key
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        current_time = time.time()
        
        # If key not in requests dict, add it
        if key not in self.requests:
            self.requests[key] = (1, current_time)
            return False
        
        # Get current count and timestamp
        count, timestamp = self.requests[key]
        
        # If more than a minute has passed, reset counter
        if current_time - timestamp > 60:
            self.requests[key] = (1, current_time)
            return False
        
        # Check if rate limit exceeded
        if count >= self.requests_per_minute:
            return True
        
        # Increment counter
        self.requests[key] = (count + 1, timestamp)
        return False
    
    def _clean_old_entries(self):
        """Clean up old entries in the requests dictionary."""
        current_time = time.time()
        keys_to_remove = []
        
        # Find keys older than 5 minutes
        for key, (_, timestamp) in self.requests.items():
            if current_time - timestamp > 300:  # 5 minutes
                keys_to_remove.append(key)
        
        # Remove old keys
        for key in keys_to_remove:
            del self.requests[key]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through the middleware.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response: FastAPI response object
        """
        # Clean up old entries periodically
        if len(self.requests) > 1000:  # Arbitrary threshold
            self._clean_old_entries()
        
        # Skip rate limiting for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # Get rate limit key
        key = self.key_func(request)
        
        # Skip rate limiting for whitelisted IPs
        if key in self.whitelist_ips:
            return await call_next(request)
        
        # Check rate limit
        if self._is_rate_limited(key):
            logger.warning(
                f"Rate limit exceeded for {key}",
                extra={
                    "client_ip": key,
                    "path": path,
                    "method": request.method
                }
            )
            
            # Return 429 Too Many Requests
            return Response(
                content='{"detail":"Too many requests"}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Reset": "60"
                }
            )
        
        # Process request normally
        return await call_next(request)


def add_rate_limit_middleware(app: FastAPI) -> None:
    """Add rate limit middleware to FastAPI application.
    
    Args:
        app: FastAPI application
    """
    settings = get_settings()
    
    # Skip if rate limiting is disabled
    if not settings.api.rate_limiting_enabled:
        logger.info("Rate limiting is disabled")
        return
    
    # Add rate limit middleware
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.api.rate_limit_per_minute,
        exclude_paths=[
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics"
        ],
        whitelist_ips=["127.0.0.1", "localhost"]
    )
    
    logger.info("Rate limit middleware added")
