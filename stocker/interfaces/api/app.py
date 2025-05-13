"""FastAPI application for STOCKER Pro.

This module provides a function to create a FastAPI application with all routes
and middleware configured.
"""

import logging
import datetime
import time
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi

from stocker.core.config.settings import get_settings
from stocker.core.exceptions import StockerException
from stocker.core.logging import get_logger
from stocker.interfaces.api.middleware import (
    RequestLoggingMiddleware, 
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    VersionHeaderMiddleware
)
from stocker.interfaces.api.middleware.logging import add_request_logging_middleware
from stocker.interfaces.api.middleware.rate_limit import add_rate_limit_middleware
from stocker.interfaces.api.middleware.security import add_security_headers_middleware
from stocker.interfaces.api.middleware.version import add_version_header_middleware
from stocker.interfaces.api.routes import (
    stock_router,
    portfolio_router,
    user_router,
    strategy_router,
    auth_router
)

# Initialize logger
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure a FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    # Get settings
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="STOCKER Pro API",
        description="API for STOCKER Pro stock analysis and portfolio management",
        version=settings.version,
        docs_url=None,  # We'll set up custom docs below
        redoc_url=None,  # We'll set up custom redoc below
        openapi_url="/api/openapi.json",
        root_path=settings.api.root_path,
        swagger_ui_parameters={"persistAuthorization": True}
    )
    
    # Configure custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
            
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Add security schemes
        openapi_schema["components"] = {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Enter JWT token"
                }
            }
        }
        
        # Apply global security
        openapi_schema["security"] = [{"BearerAuth": []}]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With", "X-CSRF-Token"],
        expose_headers=["X-Process-Time", "X-API-Version", "X-Request-ID"],
        max_age=600,  # 10 minutes cache for preflight requests
    )
    
    # Add production-grade middleware
    add_request_logging_middleware(app)
    add_rate_limit_middleware(app)
    add_security_headers_middleware(app)
    add_version_header_middleware(app)
    
    # Add exception handlers
    @app.exception_handler(StockerException)
    async def stocker_exception_handler(request: Request, exc: StockerException):
        # Get appropriate status code based on exception type or default to 500
        status_code = getattr(exc, "status_code", 500)
        
        # Log exception with request details
        logger.error(
            f"StockerException: {str(exc)}",
            extra={
                "exception_type": exc.__class__.__name__,
                "status_code": status_code,
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("User-Agent", "unknown")
            }
        )
        
        # Create response with error details
        return JSONResponse(
            status_code=status_code,
            content={
                "error": exc.__class__.__name__,
                "message": str(exc),
                "details": exc.to_dict() if hasattr(exc, "to_dict") else None,
                "timestamp": datetime.datetime.now().isoformat(),
                "path": request.url.path
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Log exception with full traceback and request details
        logger.error(
            f"Unhandled exception: {str(exc)}",
            exc_info=True,
            extra={
                "exception_type": exc.__class__.__name__,
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("User-Agent", "unknown")
            }
        )
        
        # In production, don't expose internal error details
        settings = get_settings()
        is_production = settings.environment == "production"
        
        # Create response with appropriate level of detail
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred" if is_production else str(exc),
                "timestamp": datetime.datetime.now().isoformat(),
                "path": request.url.path,
                # Only include exception type in non-production environments
                **({}if is_production else {"exception_type": exc.__class__.__name__})
            }
        )
    
    # Include routers
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(user_router, prefix="/api/users", tags=["Users"])
    app.include_router(stock_router, prefix="/api/stocks", tags=["Stocks"])
    app.include_router(portfolio_router, prefix="/api/portfolios", tags=["Portfolios"])
    app.include_router(strategy_router, prefix="/api/strategies", tags=["Strategies"])
    
    # Set up static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Custom documentation endpoints
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - ReDoc",
            swagger_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.css",
        )
    
    # Enhanced health check endpoint
    @app.get("/health", tags=["Health"], summary="API Health Check", description="Get the health status of the API and related services")
    async def health_check():
        # Get settings
        settings = get_settings()
        
        # Start time for measuring response time
        start_time = time.time()
        
        # Check database connection
        db_status = {
            "status": "ok",
            "message": "Database connection successful"
        }
        
        try:
            # This would be replaced with an actual DB check in a real implementation
            # For example: db = get_db(); result = db.execute("SELECT 1")
            pass
        except Exception as e:
            db_status = {
                "status": "error",
                "message": f"Database connection failed: {str(e)}"
            }
            logger.error(f"Health check database error: {str(e)}", exc_info=True)
        
        # Check external services (like Alpha Vantage)
        services_status = {}
        
        # Alpha Vantage status - this would be a real check in production
        if settings.alpha_vantage_api_key:
            services_status["alpha_vantage"] = {
                "status": "ok",
                "message": "API key configured"
            }
        else:
            services_status["alpha_vantage"] = {
                "status": "warning",
                "message": "API key not configured"
            }
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Determine overall status
        overall_status = "ok"
        if db_status["status"] != "ok":
            overall_status = "error"
        elif any(s["status"] == "error" for s in services_status.values()):
            overall_status = "error"
        elif any(s["status"] == "warning" for s in services_status.values()):
            overall_status = "warning"
        
        # Get memory info
        import psutil
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        }
        
        # Return comprehensive health status
        return {
            "status": overall_status,
            "version": settings.version,
            "api_version": app.version,
            "environment": settings.environment,
            "timestamp": datetime.datetime.now().isoformat(),
            "uptime": time.time() - psutil.boot_time(),
            "response_time": response_time,
            "database": db_status,
            "services": services_status,
            "system": {
                "memory": memory_info,
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=0.1)
            }
        }
    
    # Add version header to all responses
    @app.middleware("http")
    async def add_version_header(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-API-Version"] = app.version
        return response
    
    return app
