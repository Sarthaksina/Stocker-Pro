"""Health check endpoints for STOCKER Pro API.

This module provides health check endpoints for monitoring the API's status.
"""

import os
import time
import platform
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, status, Request
from pydantic import BaseModel, Field

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger
from stocker.infrastructure.database.session import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text

# Initialize logger
logger = get_logger(__name__)

# Create router
router = APIRouter(tags=["Health"])


class ServiceStatus(BaseModel):
    """Status of a service dependency."""
    
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status (up, down, degraded)")
    latency_ms: Optional[float] = Field(None, description="Latency in milliseconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Overall API status (up, down, degraded)")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current server time")
    uptime_seconds: float = Field(..., description="API uptime in seconds")
    environment: str = Field(..., description="Deployment environment")
    services: List[ServiceStatus] = Field([], description="Status of service dependencies")
    host_info: Dict[str, Any] = Field({}, description="Host information")


# Track API start time
API_START_TIME = time.time()


def check_database_health(db: Session) -> ServiceStatus:
    """Check database health.
    
    Args:
        db: Database session
        
    Returns:
        ServiceStatus: Database service status
    """
    start_time = time.time()
    status_obj = ServiceStatus(
        name="database",
        status="down",
        details={}
    )
    
    try:
        # Execute simple query to check connection
        result = db.execute(text("SELECT 1")).scalar()
        
        if result == 1:
            status_obj.status = "up"
            
            # Get database version
            try:
                version_query = db.execute(text("SELECT version()")).scalar()
                status_obj.details["version"] = version_query
            except Exception as e:
                logger.warning(f"Failed to get database version: {str(e)}")
                
            # Get connection info
            try:
                connection_info = db.execute(text("SELECT current_database(), current_user")).first()
                if connection_info:
                    status_obj.details["database"] = connection_info[0]
                    status_obj.details["user"] = connection_info[1]
            except Exception as e:
                logger.warning(f"Failed to get connection info: {str(e)}")
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        status_obj.status = "down"
        status_obj.details["error"] = str(e)
    
    # Calculate latency
    status_obj.latency_ms = round((time.time() - start_time) * 1000, 2)
    
    return status_obj


def check_redis_health() -> ServiceStatus:
    """Check Redis health.
    
    Returns:
        ServiceStatus: Redis service status
    """
    from stocker.infrastructure.cache import get_cache
    from stocker.infrastructure.cache.redis_cache import RedisCache
    
    start_time = time.time()
    status_obj = ServiceStatus(
        name="redis",
        status="down",
        details={}
    )
    
    try:
        # Get Redis cache
        cache = get_cache("redis")
        
        # Check if it's a Redis cache
        if not isinstance(cache, RedisCache):
            status_obj.status = "not_configured"
            return status_obj
        
        # Ping Redis
        if cache.redis.ping():
            status_obj.status = "up"
            
            # Get Redis info
            info = cache.redis.info()
            status_obj.details["version"] = info.get("redis_version")
            status_obj.details["used_memory"] = info.get("used_memory_human")
            status_obj.details["clients"] = info.get("connected_clients")
            status_obj.details["uptime"] = info.get("uptime_in_seconds")
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        status_obj.status = "down"
        status_obj.details["error"] = str(e)
    
    # Calculate latency
    status_obj.latency_ms = round((time.time() - start_time) * 1000, 2)
    
    return status_obj


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Get the health status of the API and its dependencies"
)
async def health_check(request: Request, db: Session = Depends(get_db)) -> HealthResponse:
    """Health check endpoint.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        HealthResponse: Health check response
    """
    settings = get_settings()
    
    # Check database health
    services = [check_database_health(db)]
    
    # Check Redis health if configured
    if getattr(settings, "redis_url", None):
        try:
            services.append(check_redis_health())
        except Exception as e:
            logger.error(f"Redis health check error: {str(e)}")
            services.append(ServiceStatus(
                name="redis",
                status="error",
                details={"error": str(e)}
            ))
    
    # Determine overall status
    if all(service.status == "up" for service in services):
        overall_status = "up"
    elif any(service.status == "down" for service in services):
        overall_status = "down"
    else:
        overall_status = "degraded"
    
    # Get host information
    host_info = {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "process_id": os.getpid()
    }
    
    # Create response
    response = HealthResponse(
        status=overall_status,
        version=settings.version,
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=round(time.time() - API_START_TIME, 2),
        environment=settings.environment,
        services=services,
        host_info=host_info
    )
    
    # Log health check result
    log_level = "info" if overall_status == "up" else "warning"
    getattr(logger, log_level)(
        f"Health check: {overall_status}",
        extra={
            "health_status": overall_status,
            "services": {s.name: s.status for s in services}
        }
    )
    
    # Set appropriate status code
    if overall_status == "down":
        request.state.response_status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif overall_status == "degraded":
        request.state.response_status_code = status.HTTP_207_MULTI_STATUS
    
    return response


@router.get(
    "/ping",
    response_model=Dict[str, str],
    summary="Simple Ping",
    description="Simple ping endpoint for basic availability checks"
)
async def ping() -> Dict[str, str]:
    """Simple ping endpoint.
    
    Returns:
        Dict[str, str]: Simple response
    """
    return {"status": "ok", "message": "pong"}
