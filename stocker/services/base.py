"""Base service implementation for STOCKER Pro.

This module provides a base service class that implements common functionality
and serves as a foundation for specific service implementations.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from stocker.core.exceptions import ServiceError
from stocker.core.logging import get_logger

# Logger
logger = get_logger(__name__)


class BaseService:
    """Base service class for business logic.
    
    This class provides common functionality for services and serves as a
    foundation for specific service implementations.
    """
    
    def __init__(self):
        """Initialize the service."""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    def _log_operation(self, operation: str, **kwargs) -> None:
        """Log an operation with structured data.
        
        Args:
            operation: Name of the operation
            **kwargs: Additional data to log
        """
        log_data = {"operation": operation}
        log_data.update(kwargs)
        self.logger.info(f"Service operation: {operation}", extra={"data": log_data})
    
    def _handle_error(self, operation: str, error: Exception, **kwargs) -> None:
        """Handle and log an error.
        
        Args:
            operation: Name of the operation that failed
            error: Exception that occurred
            **kwargs: Additional data to log
            
        Raises:
            ServiceError: Wrapped exception with operation context
        """
        log_data = {"operation": operation, "error": str(error)}
        log_data.update(kwargs)
        self.logger.error(
            f"Service operation failed: {operation} - {str(error)}", 
            extra={"data": log_data},
            exc_info=True
        )
        
        # Wrap the exception in a ServiceError to provide context
        raise ServiceError(
            f"Service operation '{operation}' failed: {str(error)}",
            original_error=error
        ) from error
