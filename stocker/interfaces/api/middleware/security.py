"""Security middleware for STOCKER Pro API.

This module provides security-related middleware for the API.
"""

from typing import Callable, Dict, List, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses.
    
    This middleware adds security-related HTTP headers to all responses
    to improve the security posture of the API.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        headers: Optional[Dict[str, str]] = None,
        exclude_paths: Optional[List[str]] = None
    ):
        """Initialize security headers middleware.
        
        Args:
            app: ASGI application
            headers: Dictionary of security headers to add
            exclude_paths: List of paths to exclude from adding headers
        """
        super().__init__(app)
        self.headers = headers or {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        }
        self.exclude_paths = exclude_paths or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through the middleware.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response: FastAPI response object
        """
        # Process request normally
        response = await call_next(request)
        
        # Skip excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return response
        
        # Add security headers
        for header_name, header_value in self.headers.items():
            response.headers[header_name] = header_value
        
        return response


def add_security_headers_middleware(app: FastAPI) -> None:
    """Add security headers middleware to FastAPI application.
    
    Args:
        app: FastAPI application
    """
    settings = get_settings()
    
    # Default security headers
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()"
    }
    
    # Add HSTS header only if SSL is enabled
    if getattr(settings.security, "ssl_enabled", False):
        security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Add CSP header
    security_headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'"
    )
    
    # Add security headers middleware
    app.add_middleware(
        SecurityHeadersMiddleware,
        headers=security_headers,
        exclude_paths=[
            "/docs",  # Swagger UI needs to be framed
            "/redoc"  # ReDoc needs to be framed
        ]
    )
    
    logger.info("Security headers middleware added")
