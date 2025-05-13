"""Security models for STOCKER Pro API.

This module defines security-related models for the API.
"""

from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field, EmailStr, validator


class Token(BaseModel):
    """Token response model."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    roles: List[str] = Field(default_factory=list, description="User roles")


class TokenData(BaseModel):
    """Token data model for decoded tokens."""
    
    sub: str = Field(..., description="Subject (user ID)")
    username: Optional[str] = Field(None, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    roles: List[str] = Field(default_factory=list, description="User roles")
    exp: Optional[int] = Field(None, description="Expiration timestamp")
    iat: Optional[int] = Field(None, description="Issued at timestamp")
    jti: Optional[str] = Field(None, description="JWT ID")


class UserLogin(BaseModel):
    """User login request model."""
    
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    
    @validator("username")
    def username_not_empty(cls, v):
        """Validate username is not empty."""
        if not v.strip():
            raise ValueError("Username cannot be empty")
        return v
    
    @validator("password")
    def password_not_empty(cls, v):
        """Validate password is not empty."""
        if not v.strip():
            raise ValueError("Password cannot be empty")
        return v


class PasswordChange(BaseModel):
    """Password change request model."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password")
    
    @validator("new_password")
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_-+={}[]|:;<>,.?/~`" for c in v):
            raise ValueError("Password must contain at least one special character")
        
        return v
    
    @validator("new_password")
    def new_password_different(cls, v, values):
        """Validate new password is different from current password."""
        if "current_password" in values and v == values["current_password"]:
            raise ValueError("New password must be different from current password")
        return v
