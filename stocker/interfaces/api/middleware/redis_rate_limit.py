"""Redis-based rate limiting middleware for STOCKER Pro API.

This module provides scalable rate limiting functionality using Redis
to support distributed deployments.
"""

import time
from typing import Callable, Dict, Optional, Tuple, List, Union

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import redis

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger
from stocker.infrastructure.cache import get_cache, RedisCache

# Initialize logger
logger = get_logger(__name__)


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based middleware for rate limiting API requests.
    
    This middleware uses Redis to track and limit the number of requests
    per client IP address, making it suitable for distributed deployments.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        redis_instance: Optional[redis.Redis] = None,
        requests_per_minute: int = 60,
        exclude_paths: Optional[List[str]] = None,
        whitelist_ips: Optional[List[str]] = None,
        key_func: Optional[Callable[[Request], str]] = None,
        key_prefix: str = "ratelimit:"
    ):
        """Initialize Redis rate limit middleware.
        
        Args:
            app: ASGI application
            redis_instance: Redis instance to use, or None to create a new one
            requests_per_minute: Maximum number of requests per minute
            exclude_paths: List of paths to exclude from rate limiting
            whitelist_ips: List of IP addresses to exclude from rate limiting
            key_func: Function to extract rate limit key from request
            key_prefix: Prefix for Redis keys
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.exclude_paths = exclude_paths or []
        self.whitelist_ips = whitelist_ips or []
        self.key_func = key_func or self._default_key_func
        self.key_prefix = key_prefix
        
        # Get or create Redis instance
        if redis_instance:
            self.redis = redis_instance
        else:
            # Try to get Redis from cache
            try:
                cache = get_cache("redis")
                if isinstance(cache, RedisCache):
                    self.redis = cache.redis
                else:
                    # Fall back to settings
                    settings = get_settings()
                    self.redis = redis.from_url(
                        settings.redis_url,
                        socket_timeout=5,
                        socket_connect_timeout=5,
                        retry_on_timeout=True,
                        decode_responses=False
                    )
            except Exception as e:
                logger.error(f"Failed to initialize Redis for rate limiting: {str(e)}")
                raise
        
        # Log configuration
        logger.info(
            f"Redis rate limit middleware initialized: {requests_per_minute} requests per minute",
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
    
    def _get_redis_key(self, key: str) -> str:
        """Get Redis key with prefix.
        
        Args:
            key: Base key
            
        Returns:
            str: Redis key with prefix
        """
        return f"{self.key_prefix}{key}"
    
    def _is_rate_limited(self, key: str) -> Tuple[bool, int, int]:
        """Check if a key has exceeded the rate limit.
        
        Uses Redis to implement a sliding window rate limit.
        
        Args:
            key: Rate limit key
            
        Returns:
            Tuple[bool, int, int]: (is_limited, current_count, ttl)
        """
        redis_key = self._get_redis_key(key)
        pipeline = self.redis.pipeline()
        
        # Get current time in seconds
        now = int(time.time())
        window_start = now - 60  # 1 minute ago
        
        try:
            # Remove old entries (older than 1 minute)
            pipeline.zremrangebyscore(redis_key, 0, window_start)
            
            # Add current request with timestamp as score
            pipeline.zadd(redis_key, {str(now): now})
            
            # Set key expiration to 2 minutes (cleanup)
            pipeline.expire(redis_key, 120)
            
            # Get count of requests in the last minute
            pipeline.zcard(redis_key)
            
            # Get TTL
            pipeline.ttl(redis_key)
            
            # Execute pipeline
            results = pipeline.execute()
            count = results[3]  # zcard result
            ttl = max(0, results[4])  # ttl result
            
            # Check if rate limit exceeded
            is_limited = count > self.requests_per_minute
            
            return is_limited, count, ttl
            
        except redis.RedisError as e:
            logger.error(f"Redis rate limit error: {str(e)}")
            # In case of Redis error, don't rate limit
            return False, 0, 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through the middleware.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response: FastAPI response object
        """
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
        is_limited, current_count, ttl = self._is_rate_limited(key)
        
        # Add rate limit headers to all responses
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.requests_per_minute - current_count))
        response.headers["X-RateLimit-Reset"] = str(ttl)
        
        # If rate limited, override response
        if is_limited:
            logger.warning(
                f"Rate limit exceeded for {key}",
                extra={
                    "client_ip": key,
                    "path": path,
                    "method": request.method,
                    "current_count": current_count
                }
            )
            
            # Return 429 Too Many Requests
            return Response(
                content='{"detail":"Too many requests"}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(ttl),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(ttl)
                }
            )
        
        return response


def add_redis_rate_limit_middleware(app: FastAPI) -> None:
    """Add Redis rate limit middleware to FastAPI application.
    
    Args:
        app: FastAPI application
    """
    settings = get_settings()
    
    # Skip if rate limiting is disabled
    if not settings.api.rate_limiting_enabled:
        logger.info("Rate limiting is disabled")
        return
    
    # Skip if Redis rate limiting is disabled
    if not getattr(settings.api, "use_redis_rate_limiting", False):
        logger.info("Redis rate limiting is disabled, using in-memory rate limiting")
        return
    
    # Add Redis rate limit middleware
    try:
        app.add_middleware(
            RedisRateLimitMiddleware,
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
        
        logger.info("Redis rate limit middleware added")
    except Exception as e:
        logger.error(f"Failed to add Redis rate limit middleware: {str(e)}")
        logger.info("Falling back to in-memory rate limiting")
        # Let the regular rate limit middleware handle it
