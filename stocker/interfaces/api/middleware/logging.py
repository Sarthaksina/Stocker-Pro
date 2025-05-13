"""Logging middleware for STOCKER Pro API.

This module provides request logging functionality for the API.
"""

import time
from typing import Callable, Dict, Any, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from stocker.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging API requests and responses.
    
    This middleware logs information about each request and response,
    including timing information, status codes, and other metadata.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        exclude_paths: Optional[list] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
        log_headers: bool = True,
        sensitive_headers: Optional[list] = None
    ):
        """Initialize request logging middleware.
        
        Args:
            app: ASGI application
            exclude_paths: List of paths to exclude from logging
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            log_headers: Whether to log headers
            sensitive_headers: List of headers to redact from logs
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or []
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.log_headers = log_headers
        self.sensitive_headers = [h.lower() for h in (sensitive_headers or [
            "Authorization", 
            "Cookie", 
            "Set-Cookie",
            "X-API-Key"
        ])]
    
    def _get_client_info(self, request: Request) -> Dict[str, Any]:
        """Extract client information from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Dict[str, Any]: Client information
        """
        # Get client IP, checking for proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Get user agent
        user_agent = request.headers.get("User-Agent", "unknown")
        
        return {
            "client_ip": client_ip,
            "user_agent": user_agent
        }
    
    def _get_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Process headers for logging, redacting sensitive information.
        
        Args:
            headers: Request or response headers
            
        Returns:
            Dict[str, str]: Processed headers
        """
        if not self.log_headers:
            return {}
        
        # Create a copy of headers with sensitive information redacted
        processed_headers = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                processed_headers[key] = "[REDACTED]"
            else:
                processed_headers[key] = value
        
        return processed_headers
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through the middleware.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response: FastAPI response object
        """
        # Skip logging for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Prepare request info
        request_info = {
            "method": request.method,
            "path": path,
            "query_params": dict(request.query_params),
            **self._get_client_info(request)
        }
        
        # Add headers if enabled
        if self.log_headers:
            request_info["headers"] = self._get_headers(dict(request.headers))
        
        # Add request body if enabled
        if self.log_request_body:
            try:
                # Clone the request body
                body = await request.body()
                request_info["body"] = body.decode("utf-8")
                
                # Reconstruct request body for downstream handlers
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
            except Exception as e:
                request_info["body_error"] = str(e)
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Log exception
            logger.exception(
                f"Error processing request: {str(e)}",
                extra={
                    "request": request_info,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Prepare response info
        response_info = {
            "status_code": status_code,
            "process_time_ms": round(process_time * 1000, 2)
        }
        
        # Add response headers if enabled
        if self.log_headers:
            response_info["headers"] = self._get_headers(dict(response.headers))
        
        # Add response body if enabled
        if self.log_response_body:
            try:
                # Get response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # Decode body
                response_info["body"] = body.decode("utf-8")
                
                # Reconstruct response for client
                response = Response(
                    content=body,
                    status_code=status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            except Exception as e:
                response_info["body_error"] = str(e)
        
        # Log request and response
        log_level = "warning" if status_code >= 400 else "info"
        getattr(logger, log_level)(
            f"{request.method} {path} {status_code} {response_info['process_time_ms']}ms",
            extra={
                "request": request_info,
                "response": response_info
            }
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(response_info["process_time_ms"])
        
        return response


def add_request_logging_middleware(app: FastAPI) -> None:
    """Add request logging middleware to FastAPI application.
    
    Args:
        app: FastAPI application
    """
    app.add_middleware(
        RequestLoggingMiddleware,
        exclude_paths=[
            "/health",
            "/metrics",
            "/favicon.ico"
        ],
        log_request_body=False,  # Set to True for debugging only
        log_response_body=False,  # Set to True for debugging only
        log_headers=True,
        sensitive_headers=[
            "Authorization", 
            "Cookie", 
            "Set-Cookie",
            "X-API-Key"
        ]
    )
    
    logger.info("Request logging middleware added")
