"""API documentation configuration for STOCKER Pro API.

This module provides enhanced documentation configuration for the API.
"""

from typing import Dict, List, Optional, Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def setup_api_docs(app: FastAPI) -> None:
    """Configure API documentation.
    
    This function enhances the OpenAPI documentation with additional information,
    security schemes, and custom documentation.
    
    Args:
        app: FastAPI application
    """
    settings = get_settings()
    
    # Skip if docs are disabled
    if not getattr(settings.api, "docs_enabled", True):
        logger.info("API documentation is disabled")
        return
    
    def custom_openapi():
        """Generate custom OpenAPI schema.
        
        Returns:
            Dict[str, Any]: OpenAPI schema
        """
        if app.openapi_schema:
            return app.openapi_schema
        
        # Generate base schema
        openapi_schema = get_openapi(
            title=settings.api.title,
            version=settings.version,
            description=settings.api.description,
            routes=app.routes
        )
        
        # Add API server URLs
        openapi_schema["servers"] = [
            {"url": settings.api.server_url or "/", "description": "Current environment"}
        ]
        
        # Add production server if available
        if getattr(settings.api, "production_url", None):
            openapi_schema["servers"].append({
                "url": settings.api.production_url,
                "description": "Production environment"
            })
        
        # Add security schemes
        openapi_schema["components"] = openapi_schema.get("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter JWT token in the format: `Bearer {token}`"
            },
            "apiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key authentication"
            }
        }
        
        # Add global security requirement
        openapi_schema["security"] = [
            {"bearerAuth": []},
            {"apiKeyAuth": []}
        ]
        
        # Add custom documentation sections
        openapi_schema["info"] = openapi_schema.get("info", {})
        
        # Add contact information
        openapi_schema["info"]["contact"] = {
            "name": "STOCKER Pro Support",
            "email": "support@stockerpro.example.com",
            "url": "https://stockerpro.example.com/support"
        }
        
        # Add license information
        openapi_schema["info"]["license"] = {
            "name": "Proprietary",
            "url": "https://stockerpro.example.com/license"
        }
        
        # Add terms of service
        openapi_schema["info"]["termsOfService"] = "https://stockerpro.example.com/terms"
        
        # Add extended description with markdown
        openapi_schema["info"]["description"] = f"""
        {settings.api.description}
        
        ## Authentication
        
        The API supports two authentication methods:
        
        1. **JWT Bearer Token**: Obtain a token via the `/auth/login` endpoint and include it in the Authorization header.
        2. **API Key**: Include your API key in the X-API-Key header.
        
        ## Rate Limiting
        
        The API implements rate limiting to prevent abuse. Current limits are {settings.api.rate_limit_per_minute} requests per minute per client.
        
        ## Versioning
        
        The API supports versioning through:
        
        1. URL path: `/v1/endpoint`
        2. Query parameter: `?version=1`
        3. Header: `X-API-Version: 1`
        
        Supported versions: {', '.join(getattr(settings.api, 'supported_versions', ['1']))}
        
        ## Error Handling
        
        The API returns consistent error responses with the following structure:
        
        ```json
        {{
            "detail": "Error message",
            "error_code": "ERROR_CODE",
            "timestamp": "2025-05-13T00:00:00Z"
        }}
        ```
        
        ## Environment
        
        Current environment: **{settings.environment}**
        """
        
        # Set the custom schema
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    # Set custom OpenAPI function
    app.openapi = custom_openapi
    
    # Configure Swagger UI and ReDoc
    app.docs_url = "/docs"
    app.redoc_url = "/redoc"
    
    logger.info("API documentation configured")
