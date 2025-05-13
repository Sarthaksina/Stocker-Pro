"""Authentication schemas for STOCKER Pro API.

This module provides Pydantic models for authentication-related requests and responses.
"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator


class Token(BaseModel):
    """Token response schema.
    
    This schema represents an authentication token returned after successful login.
    """
    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    username: str


class TokenData(BaseModel):
    """Token data schema.
    
    This schema represents the data encoded in a JWT token.
    """
    sub: str  # Subject (user ID)
    username: Optional[str] = None
    exp: int  # Expiration time
    roles: list[str] = []  # User roles


class LoginRequest(BaseModel):
    """Login request schema.
    
    This schema represents a login request with username/email and password.
    """
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    
    # Validator to ensure username is not empty
    @validator("username")
    def username_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Username/email cannot be empty")
        return v


class PasswordChangeRequest(BaseModel):
    """Password change request schema.
    
    This schema represents a request to change a user's password.
    """
    current_password: str = Field(..., min_length=8, max_length=100, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")
    
    # Validator to ensure new password is different from current password
    @validator("new_password")
    def new_password_different(cls, v, values):
        if "current_password" in values and v == values["current_password"]:
            raise ValueError("New password must be different from current password")
        return v
