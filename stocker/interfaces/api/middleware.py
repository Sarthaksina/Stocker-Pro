"""Middleware for STOCKER Pro API.

This module provides middleware components for the FastAPI application.
"""

import time
from typing import Callable, Dict, Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from stocker.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request and response details.
    
    This middleware logs information about each request and response,
    including method, path, status code, and processing time.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log details.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The response from the next middleware or route handler
        """
        # Record start time
        start_time = time.time()
        
        # Get request details
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_host = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(
            f"Request: {method} {path}",
            extra={
                "request_method": method,
                "request_path": path,
                "request_query": query_params,
                "client_host": client_host,
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} - {process_time:.4f}s",
                extra={
                    "response_status": response.status_code,
                    "process_time": process_time,
                    "request_method": method,
                    "request_path": path,
                }
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        except Exception as e:
            # Log exception
            logger.error(
                f"Error processing request: {str(e)}",
                exc_info=True,
                extra={
                    "request_method": method,
                    "request_path": path,
                    "error": str(e),
                }
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests.
    
    This middleware implements a simple rate limiting mechanism
    to prevent abuse of the API.
    """
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        """Initialize the middleware.
        
        Args:
            app: The ASGI application
            requests_per_minute: Maximum number of requests per minute per client
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.clients: Dict[str, Dict[str, Any]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and apply rate limiting.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The response from the next middleware or route handler
        """
        # Get client IP
        client_host = request.client.host if request.client else "unknown"
        
        # Check if client exists in tracking dict
        if client_host not in self.clients:
            self.clients[client_host] = {
                "last_request_time": time.time(),
                "request_count": 1
            }
        else:
            # Get client data
            client_data = self.clients[client_host]
            current_time = time.time()
            
            # Reset count if more than a minute has passed
            if current_time - client_data["last_request_time"] > 60:
                client_data["request_count"] = 1
                client_data["last_request_time"] = current_time
            else:
                # Increment request count
                client_data["request_count"] += 1
            
            # Check if rate limit exceeded
            if client_data["request_count"] > self.requests_per_minute:
                # Log rate limit exceeded
                logger.warning(
                    f"Rate limit exceeded for client {client_host}",
                    extra={
                        "client_host": client_host,
                        "request_count": client_data["request_count"],
                        "rate_limit": self.requests_per_minute
                    }
                )
                
                # Return rate limit response
                return Response(
                    content='{"detail":"Rate limit exceeded. Please try again later."}',
                    status_code=429,
                    media_type="application/json"
                )
        
        # Process request normally
        return await call_next(request)
