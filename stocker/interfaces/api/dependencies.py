"""API dependencies for STOCKER Pro.

This module provides dependency injection for FastAPI routes.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger
from stocker.domain.user import User, UserRole
from stocker.interfaces.api.schemas.auth import TokenData
from stocker.interfaces.api.security import (
    oauth2_scheme, 
    decode_token, 
    is_token_expired,
    get_security_settings,
    create_access_token,
    create_refresh_token
)
from stocker.services.user_service import UserService
from stocker.services.stock_service import StockService
from stocker.services.portfolio_service import PortfolioService
from stocker.services.strategy_service import StrategyService
from stocker.infrastructure.database.session import get_db

# Initialize logger
logger = get_logger(__name__)

# Settings dependency
def get_api_settings():
    """Get API settings.
    
    Returns:
        API settings from the application configuration
    """
    return get_settings().api


# Service dependencies
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Get user service instance.
    
    Args:
        db: Database session
        
    Returns:
        UserService instance
    """
    return UserService(db)


def get_stock_service(db: Session = Depends(get_db)) -> StockService:
    """Get stock service instance.
    
    Args:
        db: Database session
        
    Returns:
        StockService instance
    """
    return StockService(db)


def get_portfolio_service(db: Session = Depends(get_db)) -> PortfolioService:
    """Get portfolio service instance.
    
    Args:
        db: Database session
        
    Returns:
        PortfolioService instance
    """
    return PortfolioService(db)


def get_strategy_service(db: Session = Depends(get_db)) -> StrategyService:
    """Get strategy service instance.
    
    Args:
        db: Database session
        
    Returns:
        StrategyService instance
    """
    return StrategyService(db)


# Authentication dependencies
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
    request: Request = None
) -> User:
    """Get current authenticated user from token.
    
    Args:
        token: JWT token
        user_service: User service instance
        request: FastAPI request object
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Check if token is expired
        if is_token_expired(token):
            logger.warning("Expired JWT token")
            raise credentials_exception
        
        # Decode JWT token
        payload = decode_token(token)
        
        # Check token type
        token_type = payload.get("token_type")
        if token_type != "access":
            logger.warning(f"Invalid token type: {token_type}")
            raise credentials_exception
        
        # Extract user ID from token
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing subject claim")
            raise credentials_exception
        
        # Create token data
        token_data = TokenData(
            sub=user_id,
            username=payload.get("username"),
            exp=payload.get("exp"),
            roles=payload.get("roles", [])
        )
        
        # Log request with user info if request object is available
        if request:
            logger.info(
                f"Authenticated request from user {user_id}",
                extra={
                    "user_id": user_id,
                    "username": payload.get("username"),
                    "path": request.url.path,
                    "method": request.method
                }
            )
    except JWTError as e:
        logger.error(f"JWT token validation failed: {str(e)}")
        raise credentials_exception
    
    # Get user from database
    user = user_service.get_user_by_id(user_id)
    if user is None:
        logger.error(f"User with ID {user_id} not found")
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user {current_user.id} attempted to access API")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current admin user.
    
    Args:
        current_user: Current active user
        
    Returns:
        Current admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if UserRole.ADMIN not in current_user.roles:
        logger.warning(f"Non-admin user {current_user.id} attempted to access admin API")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# Helper functions for token creation
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token.
    
    Args:
        data: Token data
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    # Get settings
    settings = get_settings()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.security.access_token_expire_minutes)
    
    # Add expiration time to token data
    to_encode.update({"exp": expire})
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.secret_key,
        algorithm=settings.security.algorithm
    )
    
    return encoded_jwt
