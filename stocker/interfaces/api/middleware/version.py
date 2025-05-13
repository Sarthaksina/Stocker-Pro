"""Version header middleware for STOCKER Pro API.

This module provides middleware to add API version information to responses.
"""

from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class VersionHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware for adding version headers to responses.
    
    This middleware adds API version information to all responses
    to help clients track which version of the API they are using.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        version: Optional[str] = None
    ):
        """Initialize version header middleware.
        
        Args:
            app: ASGI application
            version: API version string
        """
        super().__init__(app)
        self.version = version or get_settings().version
    
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
        
        # Add version header
        response.headers["X-API-Version"] = self.version
        
        return response


def add_version_header_middleware(app: FastAPI) -> None:
    """Add version header middleware to FastAPI application.
    
    Args:
        app: FastAPI application
    """
    settings = get_settings()
    
    # Add version header middleware
    app.add_middleware(
        VersionHeaderMiddleware,
        version=settings.version
    )
    
    logger.info(f"Version header middleware added: {settings.version}")
