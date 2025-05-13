"""User routes for STOCKER Pro API.

This module provides route handlers for user-related endpoints.
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path

from stocker.core.logging import get_logger
from stocker.domain.user import User, UserRole
from stocker.interfaces.api.dependencies import (
    get_user_service,
    get_current_active_user,
    get_current_admin_user
)
from stocker.interfaces.api.schemas.users import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserPreferencesUpdate
)
from stocker.services.user_service import UserService

# Initialize router
router = APIRouter()

# Initialize logger
logger = get_logger(__name__)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Create a new user.
    
    Args:
        user_data: User creation data
        user_service: User service instance
        current_user: Current admin user
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If user creation fails
    """
    # Check if username or email already exists
    if user_service.get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    if user_service.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = user_service.create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        roles=[role for role in user_data.roles],
        preferences=user_data.preferences.dict() if user_data.preferences else None
    )
    
    logger.info(f"User {user.id} created by admin {current_user.id}")
    return user


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="Skip N users"),
    limit: int = Query(100, ge=1, le=1000, description="Limit to N users"),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Get all users.
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        user_service: User service instance
        current_user: Current admin user
        
    Returns:
        List of users
    """
    users = user_service.get_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str = Path(..., description="User ID"),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get a user by ID.
    
    Args:
        user_id: User ID
        user_service: User service instance
        current_user: Current authenticated user
        
    Returns:
        User
        
    Raises:
        HTTPException: If user not found or access denied
    """
    # Check if current user is admin or requesting their own data
    if user_id != current_user.id and UserRole.ADMIN not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get user
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_data: UserUpdate,
    user_id: str = Path(..., description="User ID"),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Update a user.
    
    Args:
        user_data: User update data
        user_id: User ID
        user_service: User service instance
        current_user: Current authenticated user
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If user not found or access denied
    """
    # Check if current user is admin or updating their own data
    is_admin = UserRole.ADMIN in current_user.roles
    if user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get user
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if roles are being updated (admin only)
    if user_data.roles is not None and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update user roles"
        )
    
    # Update user
    updated_user = user_service.update_user(
        user_id=user_id,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        status=user_data.status.value if user_data.status else None,
        roles=[role for role in user_data.roles] if user_data.roles else None,
        preferences=user_data.preferences.dict() if user_data.preferences else None
    )
    
    logger.info(f"User {user_id} updated by {current_user.id}")
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str = Path(..., description="User ID"),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Delete a user.
    
    Args:
        user_id: User ID
        user_service: User service instance
        current_user: Current admin user
        
    Returns:
        No content
        
    Raises:
        HTTPException: If user not found or is the current user
    """
    # Check if user exists
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own user account"
        )
    
    # Delete user
    user_service.delete_user(user_id)
    
    logger.info(f"User {user_id} deleted by admin {current_user.id}")
    return None


@router.put("/{user_id}/preferences", response_model=UserResponse)
async def update_user_preferences(
    preferences_data: UserPreferencesUpdate,
    user_id: str = Path(..., description="User ID"),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Update user preferences.
    
    Args:
        preferences_data: User preferences update data
        user_id: User ID
        user_service: User service instance
        current_user: Current authenticated user
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If user not found or access denied
    """
    # Check if current user is admin or updating their own data
    if user_id != current_user.id and UserRole.ADMIN not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get user
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update preferences
    updated_user = user_service.update_user_preferences(
        user_id=user_id,
        preferences=preferences_data.dict()
    )
    
    logger.info(f"User {user_id} preferences updated")
    return updated_user
