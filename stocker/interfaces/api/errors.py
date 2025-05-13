"""Error handling utilities for STOCKER Pro API.

This module provides error handling functionality for the API,
ensuring consistent error responses and proper logging.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type, Union, List
import traceback
import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from stocker.core.exceptions import StockerError, APIError, DatabaseError, AuthenticationError, AuthorizationError
from stocker.core.logging import get_logger
from stocker.core.config.settings import get_settings

# Initialize logger
logger = get_logger(__name__)


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for client reference")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    path: Optional[str] = Field(None, description="Request path")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Validation errors")


def get_error_code(exception: Exception) -> str:
    """Generate an error code for an exception.
    
    Args:
        exception: Exception instance
        
    Returns:
        str: Error code
    """
    # Use predefined error code if available
    if hasattr(exception, "error_code") and exception.error_code:
        return exception.error_code
    
    # Generate error code based on exception class
    error_type = type(exception).__name__
    return f"ERROR_{error_type.upper()}"


def get_error_status_code(exception: Exception) -> int:
    """Get HTTP status code for an exception.
    
    Args:
        exception: Exception instance
        
    Returns:
        int: HTTP status code
    """
    # Use predefined status code if available
    if hasattr(exception, "status_code") and exception.status_code:
        return exception.status_code
    
    # Map exception types to status codes
    if isinstance(exception, AuthenticationError):
        return status.HTTP_401_UNAUTHORIZED
    elif isinstance(exception, AuthorizationError):
        return status.HTTP_403_FORBIDDEN
    elif isinstance(exception, DatabaseError):
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exception, StockerError):
        return status.HTTP_400_BAD_REQUEST
    
    # Default to 500 for unknown exceptions
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def sanitize_error_detail(detail: Any, is_debug: bool = False) -> str:
    """Sanitize error detail for production environments.
    
    Args:
        detail: Error detail
        is_debug: Whether debug mode is enabled
        
    Returns:
        str: Sanitized error detail
    """
    # Convert to string
    if not isinstance(detail, str):
        detail = str(detail)
    
    # In non-debug mode, sanitize potentially sensitive information
    if not is_debug:
        # Check for common sensitive patterns
        if any(pattern in detail.lower() for pattern in [
            "password", "token", "secret", "key", "credential", "auth",
            "sql syntax", "database", "exception at", "stack trace", "traceback"
        ]):
            return "An internal server error occurred. Please contact support."
    
    return detail


async def stocker_exception_handler(request: Request, exc: StockerError) -> JSONResponse:
    """Handle StockerError exceptions.
    
    Args:
        request: FastAPI request
        exc: StockerError instance
        
    Returns:
        JSONResponse: Error response
    """
    settings = get_settings()
    is_debug = settings.environment.lower() in ["development", "test"]
    
    # Get error details
    status_code = get_error_status_code(exc)
    error_code = get_error_code(exc)
    detail = sanitize_error_detail(exc.detail if hasattr(exc, "detail") else str(exc), is_debug)
    
    # Get request ID from state or generate new one
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Log error
    log_level = "error" if status_code >= 500 else "warning"
    getattr(logger, log_level)(
        f"{error_code}: {detail}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": status_code,
            "error_code": error_code,
            "error_type": type(exc).__name__
        },
        exc_info=is_debug  # Include stack trace in debug mode
    )
    
    # Create error response
    error_response = ErrorResponse(
        detail=detail,
        error_code=error_code,
        request_id=request_id,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict(exclude_none=True)
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTPException.
    
    Args:
        request: FastAPI request
        exc: HTTPException instance
        
    Returns:
        JSONResponse: Error response
    """
    settings = get_settings()
    is_debug = settings.environment.lower() in ["development", "test"]
    
    # Get request ID from state or generate new one
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Log error
    log_level = "error" if exc.status_code >= 500 else "warning"
    getattr(logger, log_level)(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    # Create error response
    error_response = ErrorResponse(
        detail=sanitize_error_detail(exc.detail, is_debug),
        error_code=f"HTTP_{exc.status_code}",
        request_id=request_id,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict(exclude_none=True),
        headers=exc.headers
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle RequestValidationError.
    
    Args:
        request: FastAPI request
        exc: RequestValidationError instance
        
    Returns:
        JSONResponse: Error response
    """
    settings = get_settings()
    is_debug = settings.environment.lower() in ["development", "test"]
    
    # Get request ID from state or generate new one
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Extract validation errors
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })
    
    # Log error
    logger.warning(
        f"Validation error: {len(validation_errors)} errors",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "validation_errors": validation_errors
        }
    )
    
    # Create error response
    error_response = ErrorResponse(
        detail="Validation error",
        error_code="VALIDATION_ERROR",
        request_id=request_id,
        path=request.url.path,
        errors=validation_errors if is_debug else None
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.dict(exclude_none=True)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions.
    
    Args:
        request: FastAPI request
        exc: Exception instance
        
    Returns:
        JSONResponse: Error response
    """
    settings = get_settings()
    is_debug = settings.environment.lower() in ["development", "test"]
    
    # Get request ID from state or generate new one
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Get error details
    error_code = get_error_code(exc)
    status_code = get_error_status_code(exc)
    
    # In production, sanitize error messages
    detail = sanitize_error_detail(str(exc), is_debug)
    
    # Log error with stack trace
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error_code": error_code,
            "traceback": traceback.format_exc() if is_debug else None
        },
        exc_info=True  # Always include stack trace for unhandled exceptions
    )
    
    # Create error response
    error_response = ErrorResponse(
        detail=detail,
        error_code=error_code,
        request_id=request_id,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict(exclude_none=True)
    )


def setup_error_handlers(app: FastAPI) -> None:
    """Set up error handlers for the API.
    
    Args:
        app: FastAPI application
    """
    # Register exception handlers
    app.add_exception_handler(StockerError, stocker_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("API error handlers configured")
