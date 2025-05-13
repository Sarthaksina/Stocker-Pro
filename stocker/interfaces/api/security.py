"""Security utilities for STOCKER Pro API.

This module provides security-related utilities for the API, including
JWT token handling, password hashing, and authentication.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Union, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class SecuritySettings(BaseModel):
    """Security settings for STOCKER Pro API.
    
    This class contains security-related settings for the API.
    """
    secret_key: str = Field(..., description="Secret key for JWT token generation")
    algorithm: str = Field("HS256", description="Algorithm for JWT token generation")
    access_token_expire_minutes: int = Field(30, description="Access token expiration time in minutes")
    refresh_token_expire_days: int = Field(7, description="Refresh token expiration time in days")
    password_min_length: int = Field(8, description="Minimum password length")
    password_require_uppercase: bool = Field(True, description="Require uppercase letters in passwords")
    password_require_lowercase: bool = Field(True, description="Require lowercase letters in passwords")
    password_require_digit: bool = Field(True, description="Require digits in passwords")
    password_require_special: bool = Field(False, description="Require special characters in passwords")
    bcrypt_rounds: int = Field(12, description="Number of rounds for bcrypt hashing")


def get_security_settings() -> SecuritySettings:
    """Get security settings from application settings.
    
    Returns:
        SecuritySettings: Security settings
    """
    settings = get_settings()
    
    # Check if security settings exist in application settings
    if hasattr(settings, "security"):
        return settings.security
    
    # Create default security settings
    return SecuritySettings(
        secret_key=getattr(settings, "secret_key", "stocker_secret_key"),
        algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        password_min_length=8,
        password_require_uppercase=True,
        password_require_lowercase=True,
        password_require_digit=True,
        password_require_special=False,
        bcrypt_rounds=12
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


def validate_password_strength(password: str) -> Dict[str, Union[bool, str]]:
    """Validate password strength against security settings.
    
    Args:
        password: Plain text password
        
    Returns:
        Dict[str, Union[bool, str]]: Validation result with success flag and message
    """
    # Get security settings
    security_settings = get_security_settings()
    
    # Check password length
    if len(password) < security_settings.password_min_length:
        return {
            "success": False,
            "message": f"Password must be at least {security_settings.password_min_length} characters long"
        }
    
    # Check for uppercase letters
    if security_settings.password_require_uppercase and not any(c.isupper() for c in password):
        return {
            "success": False,
            "message": "Password must contain at least one uppercase letter"
        }
    
    # Check for lowercase letters
    if security_settings.password_require_lowercase and not any(c.islower() for c in password):
        return {
            "success": False,
            "message": "Password must contain at least one lowercase letter"
        }
    
    # Check for digits
    if security_settings.password_require_digit and not any(c.isdigit() for c in password):
        return {
            "success": False,
            "message": "Password must contain at least one digit"
        }
    
    # Check for special characters
    if security_settings.password_require_special and not any(not c.isalnum() for c in password):
        return {
            "success": False,
            "message": "Password must contain at least one special character"
        }
    
    return {
        "success": True,
        "message": "Password meets strength requirements"
    }


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.
    
    Args:
        data: Token data
        expires_delta: Token expiration time
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    # Get security settings
    security_settings = get_security_settings()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=security_settings.access_token_expire_minutes)
    
    # Add expiration time to token data
    to_encode.update({"exp": expire})
    
    # Add token type and issued at time
    to_encode.update({
        "token_type": "access",
        "iat": datetime.utcnow(),
        "nbf": datetime.utcnow()
    })
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        security_settings.secret_key,
        algorithm=security_settings.algorithm
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token.
    
    Args:
        data: Token data
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    # Get security settings
    security_settings = get_security_settings()
    
    # Set expiration time (longer than access token)
    expire = datetime.utcnow() + timedelta(days=security_settings.refresh_token_expire_days)
    
    # Add expiration time to token data
    to_encode.update({"exp": expire})
    
    # Add token type and issued at time
    to_encode.update({
        "token_type": "refresh",
        "iat": datetime.utcnow(),
        "nbf": datetime.utcnow()
    })
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        security_settings.secret_key,
        algorithm=security_settings.algorithm
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Dict[str, Any]: Decoded token data
        
    Raises:
        JWTError: If token is invalid
    """
    # Get security settings
    security_settings = get_security_settings()
    
    # Decode token
    return jwt.decode(
        token,
        security_settings.secret_key,
        algorithms=[security_settings.algorithm]
    )


def is_token_expired(token: str) -> bool:
    """Check if a JWT token is expired.
    
    Args:
        token: JWT token
        
    Returns:
        bool: True if token is expired, False otherwise
    """
    try:
        # Decode token
        payload = decode_token(token)
        
        # Check expiration time
        exp = payload.get("exp")
        if exp is None:
            return True
        
        # Check if token is expired
        return datetime.utcfromtimestamp(exp) < datetime.utcnow()
    except JWTError:
        return True


def get_token_expiration(token: str) -> Optional[datetime]:
    """Get the expiration time of a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Optional[datetime]: Token expiration time, or None if token is invalid
    """
    try:
        # Decode token
        payload = decode_token(token)
        
        # Get expiration time
        exp = payload.get("exp")
        if exp is None:
            return None
        
        # Return expiration time as datetime
        return datetime.utcfromtimestamp(exp)
    except JWTError:
        return None
