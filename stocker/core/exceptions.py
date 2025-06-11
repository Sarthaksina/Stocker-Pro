"""Exception hierarchy for STOCKER Pro.

This module defines a comprehensive exception hierarchy for the STOCKER Pro application.
All custom exceptions should inherit from StockerException to ensure consistent error handling.
"""

from typing import Any, Dict, List, Optional


class StockerException(Exception):
    """Base exception for all STOCKER Pro exceptions.
    
    All custom exceptions in the application should inherit from this class
    to ensure consistent error handling and logging.
    
    Args:
        message: Error message
        code: Error code for categorization
        details: Additional error details
    """
    def __init__(
        self, 
        message: str = "An error occurred", 
        code: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "message": self.message,
                "code": self.code,
                "details": self.details
            }
        }


# Configuration Exceptions
class ConfigurationError(StockerException):
    """Base exception for configuration errors."""
    def __init__(self, message: str = "Configuration error", **kwargs):
        super().__init__(message=message, code="CONFIG_ERROR", **kwargs)


class ConfigValidationError(ConfigurationError):
    """Exception raised when configuration validation fails."""
    def __init__(self, message: str = "Configuration validation failed", **kwargs):
        super().__init__(message=message, code="CONFIG_VALIDATION_ERROR", **kwargs)


# Data Exceptions
class DataError(StockerException):
    """Base exception for data-related errors."""
    def __init__(self, message: str = "Data error", **kwargs):
        super().__init__(message=message, code="DATA_ERROR", **kwargs)


class DataSourceError(DataError):
    """Exception raised when there's an issue with a data source."""
    def __init__(self, message: str = "Data source error", source: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {}) or {}
        if source:
            details["source"] = source
        super().__init__(message=message, code="DATA_SOURCE_ERROR", details=details, **kwargs)


class DataValidationError(DataError):
    """Exception raised when data validation fails."""
    def __init__(self, message: str = "Data validation failed", **kwargs):
        super().__init__(message=message, code="DATA_VALIDATION_ERROR", **kwargs)


class DataNotFoundError(DataError):
    """Exception raised when requested data is not found."""
    def __init__(self, message: str = "Data not found", **kwargs):
        super().__init__(message=message, code="DATA_NOT_FOUND", **kwargs)


# Model Exceptions
class ModelError(StockerException):
    """Base exception for model-related errors."""
    def __init__(self, message: str = "Model error", **kwargs):
        super().__init__(message=message, code="MODEL_ERROR", **kwargs)


class ModelNotFoundError(ModelError):
    """Exception raised when a model is not found."""
    def __init__(self, message: str = "Model not found", model_name: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {}) or {}
        if model_name:
            details["model_name"] = model_name
        super().__init__(message=message, code="MODEL_NOT_FOUND", details=details, **kwargs)


class ModelTrainingError(ModelError):
    """Exception raised when model training fails."""
    def __init__(self, message: str = "Model training failed", **kwargs):
        super().__init__(message=message, code="MODEL_TRAINING_ERROR", **kwargs)


class ModelPredictionError(ModelError):
    """Exception raised when model prediction fails."""
    def __init__(self, message: str = "Model prediction failed", **kwargs):
        super().__init__(message=message, code="MODEL_PREDICTION_ERROR", **kwargs)


# Portfolio Exceptions
class PortfolioError(StockerException):
    """Base exception for portfolio-related errors."""
    def __init__(self, message: str = "Portfolio error", **kwargs):
        super().__init__(message=message, code="PORTFOLIO_ERROR", **kwargs)


class PortfolioNotFoundError(PortfolioError):
    """Exception raised when a portfolio is not found."""
    def __init__(self, message: str = "Portfolio not found", portfolio_id: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {}) or {}
        if portfolio_id:
            details["portfolio_id"] = portfolio_id
        super().__init__(message=message, code="PORTFOLIO_NOT_FOUND", details=details, **kwargs)


class PortfolioValidationError(PortfolioError):
    """Exception raised when portfolio validation fails."""
    def __init__(self, message: str = "Portfolio validation failed", **kwargs):
        super().__init__(message=message, code="PORTFOLIO_VALIDATION_ERROR", **kwargs)


class PortfolioOptimizationError(PortfolioError):
    """Exception raised when portfolio optimization fails."""
    def __init__(self, message: str = "Portfolio optimization failed", **kwargs):
        super().__init__(message=message, code="PORTFOLIO_OPTIMIZATION_ERROR", **kwargs)


class PortfolioRebalanceError(PortfolioError):
    """Exception raised when portfolio rebalancing fails."""
    def __init__(self, message: str = "Portfolio rebalancing failed", **kwargs):
        super().__init__(message=message, code="PORTFOLIO_REBALANCE_ERROR", **kwargs)


# API Exceptions
class APIError(StockerException):
    """Base exception for API-related errors."""
    def __init__(self, message: str = "API error", status_code: int = 500, **kwargs):
        details = kwargs.pop("details", {}) or {}
        details["status_code"] = status_code
        super().__init__(message=message, code="API_ERROR", details=details, **kwargs)


class AuthenticationError(APIError):
    """Exception raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message=message, code="AUTHENTICATION_ERROR", status_code=401, **kwargs)


class AuthorizationError(APIError):
    """Exception raised when authorization fails."""
    def __init__(self, message: str = "Not authorized", **kwargs):
        super().__init__(message=message, code="AUTHORIZATION_ERROR", status_code=403, **kwargs)


class ResourceNotFoundError(APIError):
    """Exception raised when a resource is not found."""
    def __init__(self, message: str = "Resource not found", resource_type: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {}) or {}
        if resource_type:
            details["resource_type"] = resource_type
        super().__init__(message=message, code="RESOURCE_NOT_FOUND", status_code=404, details=details, **kwargs)


class ValidationError(APIError):
    """Exception raised when request validation fails."""
    def __init__(self, message: str = "Validation error", errors: Optional[List[Dict[str, Any]]] = None, **kwargs):
        details = kwargs.pop("details", {}) or {}
        if errors:
            details["errors"] = errors
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422, details=details, **kwargs)
