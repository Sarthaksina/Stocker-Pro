"""API versioning utilities for STOCKER Pro API.

This module provides utilities for API versioning to ensure backward compatibility
as the API evolves.
"""

from enum import Enum
from typing import Callable, Dict, Optional, Type, Union

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel

from stocker.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class APIVersion(str, Enum):
    """API version enumeration.
    
    This enum defines the supported API versions.
    """
    V1 = "v1"
    V2 = "v2"
    
    @classmethod
    def default(cls) -> "APIVersion":
        """Get the default API version.
        
        Returns:
            APIVersion: Default API version
        """
        return cls.V1
    
    @classmethod
    def latest(cls) -> "APIVersion":
        """Get the latest API version.
        
        Returns:
            APIVersion: Latest API version
        """
        return cls.V2
    
    @classmethod
    def all(cls) -> list["APIVersion"]:
        """Get all API versions.
        
        Returns:
            list[APIVersion]: All API versions
        """
        return list(cls)


class VersionedAPIRouter(APIRouter):
    """Versioned API router.
    
    This router extends FastAPI's APIRouter to support versioning.
    """
    
    def __init__(
        self,
        version: APIVersion,
        prefix: str = "",
        *args,
        **kwargs
    ):
        """Initialize versioned API router.
        
        Args:
            version: API version
            prefix: Router prefix
            *args: Additional arguments for APIRouter
            **kwargs: Additional keyword arguments for APIRouter
        """
        self.version = version
        versioned_prefix = f"/api/{version}{prefix}"
        super().__init__(prefix=versioned_prefix, *args, **kwargs)


def get_api_version(x_api_version: Optional[str] = Header(None)) -> APIVersion:
    """Get API version from request header.
    
    Args:
        x_api_version: API version header
        
    Returns:
        APIVersion: API version
        
    Raises:
        HTTPException: If API version is invalid
    """
    if x_api_version is None:
        return APIVersion.default()
    
    try:
        return APIVersion(x_api_version.lower())
    except ValueError:
        valid_versions = ", ".join([v.value for v in APIVersion])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid API version: {x_api_version}. Valid versions: {valid_versions}"
        )


def version_dependency(version: APIVersion):
    """Create a dependency that checks if the requested API version is supported.
    
    Args:
        version: Required API version
        
    Returns:
        Callable: Dependency function
    """
    def _check_version(api_version: APIVersion = Depends(get_api_version)) -> None:
        if api_version.value < version.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This endpoint requires API version {version} or higher"
            )
    
    return _check_version


def setup_versioned_routes(app: FastAPI, routers: Dict[APIVersion, list[APIRouter]]) -> None:
    """Set up versioned routes in the FastAPI application.
    
    Args:
        app: FastAPI application
        routers: Dictionary mapping API versions to lists of routers
    """
    for version, router_list in routers.items():
        for router in router_list:
            app.include_router(router)
        
        logger.info(f"Registered API version {version} routes")
