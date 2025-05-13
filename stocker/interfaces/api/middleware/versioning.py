"""API versioning middleware for STOCKER Pro API.

This module provides API versioning functionality to ensure backward compatibility.
"""

from typing import Callable, Dict, List, Optional, Union, Any
import re

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger
from stocker.core.exceptions import APIVersionError

# Initialize logger
logger = get_logger(__name__)


class VersioningMiddleware(BaseHTTPMiddleware):
    """Middleware for API versioning.
    
    This middleware handles API versioning through URL paths or headers,
    ensuring backward compatibility for clients.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        default_version: str = "1",
        supported_versions: Optional[List[str]] = None,
        version_param: str = "version",
        version_header: str = "X-API-Version",
        version_path_pattern: str = r"^/v(\d+)/",
        exclude_paths: Optional[List[str]] = None
    ):
        """Initialize versioning middleware.
        
        Args:
            app: ASGI application
            default_version: Default API version
            supported_versions: List of supported API versions
            version_param: Query parameter name for version
            version_header: Header name for version
            version_path_pattern: Regex pattern for extracting version from path
            exclude_paths: List of paths to exclude from versioning
        """
        super().__init__(app)
        self.default_version = default_version
        self.supported_versions = supported_versions or [default_version]
        self.version_param = version_param
        self.version_header = version_header
        self.version_path_pattern = re.compile(version_path_pattern)
        self.exclude_paths = exclude_paths or [
            "/docs", 
            "/redoc", 
            "/openapi.json",
            "/health",
            "/metrics"
        ]
        
        # Log configuration
        logger.info(
            f"API versioning middleware initialized: default={default_version}, supported={supported_versions}",
            extra={
                "default_version": default_version,
                "supported_versions": supported_versions
            }
        )
    
    def _extract_version_from_path(self, path: str) -> Optional[str]:
        """Extract version from URL path.
        
        Args:
            path: URL path
            
        Returns:
            Optional[str]: Extracted version or None
        """
        match = self.version_path_pattern.match(path)
        if match:
            return match.group(1)
        return None
    
    def _get_version(self, request: Request) -> str:
        """Get API version from request.
        
        Priority order:
        1. URL path (/v1/...)
        2. Query parameter (?version=1)
        3. Header (X-API-Version: 1)
        4. Default version
        
        Args:
            request: FastAPI request
            
        Returns:
            str: API version
            
        Raises:
            APIVersionError: If version is not supported
        """
        version = None
        
        # Check path first
        path_version = self._extract_version_from_path(request.url.path)
        if path_version:
            version = path_version
        
        # Check query parameter
        if not version and self.version_param in request.query_params:
            version = request.query_params[self.version_param]
        
        # Check header
        if not version and self.version_header in request.headers:
            version = request.headers[self.version_header]
        
        # Fall back to default
        if not version:
            version = self.default_version
        
        # Validate version
        if version not in self.supported_versions:
            raise APIVersionError(
                f"Unsupported API version: {version}. Supported versions: {', '.join(self.supported_versions)}"
            )
        
        return version
    
    def _rewrite_path(self, path: str, version: str) -> str:
        """Rewrite path to remove version prefix.
        
        Args:
            path: Original URL path
            version: API version
            
        Returns:
            str: Rewritten path
        """
        # If path starts with /vX/, remove it
        match = self.version_path_pattern.match(path)
        if match:
            return path[match.end() - 1:]  # Keep the trailing slash
        return path
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through the middleware.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response: FastAPI response object
        """
        # Skip versioning for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        try:
            # Get API version
            version = self._get_version(request)
            
            # Store version in request state
            request.state.api_version = version
            
            # Rewrite path if needed
            original_path = path
            rewritten_path = self._rewrite_path(path, version)
            
            if rewritten_path != original_path:
                # Update request scope with rewritten path
                request.scope["path"] = rewritten_path
            
            # Add version header to response
            response = await call_next(request)
            response.headers[self.version_header] = version
            
            return response
            
        except APIVersionError as e:
            # Return error response for unsupported version
            logger.warning(
                f"API version error: {str(e)}",
                extra={
                    "path": path,
                    "error": str(e)
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": str(e),
                    "supported_versions": self.supported_versions
                }
            )
        except Exception as e:
            # Log unexpected errors
            logger.exception(
                f"Error in versioning middleware: {str(e)}",
                extra={
                    "path": path,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise


def add_versioning_middleware(app: FastAPI) -> None:
    """Add versioning middleware to FastAPI application.
    
    Args:
        app: FastAPI application
    """
    settings = get_settings()
    
    # Skip if versioning is disabled
    if not getattr(settings.api, "versioning_enabled", True):
        logger.info("API versioning is disabled")
        return
    
    # Get versioning settings
    default_version = getattr(settings.api, "default_version", "1")
    supported_versions = getattr(settings.api, "supported_versions", [default_version])
    
    # Add versioning middleware
    app.add_middleware(
        VersioningMiddleware,
        default_version=default_version,
        supported_versions=supported_versions,
        exclude_paths=[
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
            "/favicon.ico"
        ]
    )
    
    logger.info("API versioning middleware added")
