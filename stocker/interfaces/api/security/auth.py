"""Authentication utilities for STOCKER Pro API.

This module provides authentication-related functionality for the API.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import uuid

from fastapi import Depends, HTTPException, status, Security, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger
from stocker.core.exceptions import AuthenticationError, AuthorizationError
from stocker.domain.user import User
from stocker.infrastructure.database.session import get_db
from stocker.interfaces.api.security.models import TokenData
from stocker.services.user_service import UserService

# Initialize logger
logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for JWT authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False
)

# API key scheme for API key authentication
api_key_scheme = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token.
    
    Args:
        data: Token data
        expires_delta: Token expiration time delta
        
    Returns:
        str: JWT token
    """
    settings = get_settings()
    
    # Create a copy of the data
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.security.access_token_expire_minutes)
    
    # Add claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    })
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.secret_key,
        algorithm=settings.security.algorithm
    )
    
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        TokenData: Decoded token data
        
    Raises:
        AuthenticationError: If token is invalid
    """
    settings = get_settings()
    
    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm]
        )
        
        # Extract data
        token_data = TokenData(
            sub=payload.get("sub"),
            username=payload.get("username"),
            email=payload.get("email"),
            roles=payload.get("roles", []),
            exp=payload.get("exp"),
            iat=payload.get("iat"),
            jti=payload.get("jti")
        )
        
        return token_data
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise AuthenticationError("Invalid authentication credentials")


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user.
    
    This function supports both JWT and API key authentication.
    
    Args:
        request: FastAPI request
        token: JWT token
        api_key: API key
        db: Database session
        
    Returns:
        User: Authenticated user
        
    Raises:
        AuthenticationError: If authentication fails
    """
    # Check if we have a token or API key
    if not token and not api_key:
        logger.warning("Authentication failed: No credentials provided")
        raise AuthenticationError("Not authenticated")
    
    # Create user service
    user_service = UserService(db)
    
    # Try JWT authentication first
    if token:
        try:
            # Decode token
            token_data = decode_token(token)
            
            # Get user by ID
            user = user_service.get_user_by_id(token_data.sub)
            if not user:
                logger.warning(f"User not found: {token_data.sub}")
                raise AuthenticationError("User not found")
            
            # Store token data in request state
            request.state.token_data = token_data
            
            return user
        except AuthenticationError:
            # If API key is provided, try that instead
            if not api_key:
                raise
    
    # Try API key authentication
    if api_key:
        try:
            # Get user by API key
            user = user_service.get_user_by_api_key(api_key)
            if not user:
                logger.warning("Invalid API key")
                raise AuthenticationError("Invalid API key")
            
            return user
        except Exception as e:
            logger.error(f"API key authentication error: {str(e)}")
            raise AuthenticationError("Authentication failed")
    
    # This should never happen
    raise AuthenticationError("Authentication failed")


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        User: Active user
        
    Raises:
        AuthorizationError: If user is inactive
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user: {current_user.id}")
        raise AuthorizationError("Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get the current admin user.
    
    Args:
        current_user: Authenticated active user
        
    Returns:
        User: Admin user
        
    Raises:
        AuthorizationError: If user is not an admin
    """
    if not current_user.is_superuser and "admin" not in current_user.roles:
        logger.warning(f"Non-admin user attempted admin action: {current_user.id}")
        raise AuthorizationError("Not authorized")
    return current_user


def require_roles(roles: List[str]):
    """Dependency for requiring specific roles.
    
    Args:
        roles: List of required roles
        
    Returns:
        callable: Dependency function
    """
    async def _require_roles(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """Check if user has required roles.
        
        Args:
            current_user: Authenticated active user
            
        Returns:
            User: User with required roles
            
        Raises:
            AuthorizationError: If user doesn't have required roles
        """
        # Superusers have all roles
        if current_user.is_superuser:
            return current_user
        
        # Check if user has any of the required roles
        user_roles = set(current_user.roles)
        required_roles = set(roles)
        
        if not user_roles.intersection(required_roles):
            logger.warning(
                f"User {current_user.id} lacks required roles: {roles}",
                extra={
                    "user_id": current_user.id,
                    "user_roles": list(user_roles),
                    "required_roles": roles
                }
            )
            raise AuthorizationError("Not authorized")
        
        return current_user
    
    return _require_roles
