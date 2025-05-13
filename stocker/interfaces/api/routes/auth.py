"""Authentication routes for STOCKER Pro API.

This module provides route handlers for authentication-related endpoints.
"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger
from stocker.domain.user import User
from stocker.interfaces.api.dependencies import (
    get_user_service,
    get_current_active_user,
    create_access_token
)
from stocker.interfaces.api.schemas.auth import Token, LoginRequest, PasswordChangeRequest
from stocker.services.user_service import UserService

# Initialize router
router = APIRouter()

# Initialize logger
logger = get_logger(__name__)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
) -> Any:
    """Login and get access token.
    
    Args:
        form_data: OAuth2 password request form
        user_service: User service instance
        
    Returns:
        Access token
        
    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate user
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user {form_data.username} attempted to login")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Get settings
    settings = get_settings()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.security.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "roles": [role.value for role in user.roles]
        },
        expires_delta=access_token_expires
    )
    
    # Update last login time
    user_service.update_last_login(user.id)
    
    # Return token
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.security.access_token_expire_minutes * 60,
        "user_id": user.id,
        "username": user.username
    }


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    user_service: UserService = Depends(get_user_service)
) -> Any:
    """Login with username/email and password.
    
    Args:
        login_data: Login request data
        user_service: User service instance
        
    Returns:
        Access token
        
    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate user
    user = user_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user {login_data.username} attempted to login")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Get settings
    settings = get_settings()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.security.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "roles": [role.value for role in user.roles]
        },
        expires_delta=access_token_expires
    )
    
    # Update last login time
    user_service.update_last_login(user.id)
    
    # Return token
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.security.access_token_expire_minutes * 60,
        "user_id": user.id,
        "username": user.username
    }


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
) -> Any:
    """Change user password.
    
    Args:
        password_data: Password change request data
        current_user: Current authenticated user
        user_service: User service instance
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If password change fails
    """
    # Verify current password
    if not user_service.verify_password(password_data.current_password, current_user.password_hash):
        logger.warning(f"Failed password change attempt for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Change password
    user_service.change_password(current_user.id, password_data.new_password)
    
    # Return success message
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Logout current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # Note: JWT tokens cannot be invalidated without a token blacklist
    # This endpoint is provided for client-side logout functionality
    logger.info(f"User {current_user.id} logged out")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "roles": [role.value for role in current_user.roles],
        "is_active": current_user.is_active,
        "preferences": current_user.preferences
    }
