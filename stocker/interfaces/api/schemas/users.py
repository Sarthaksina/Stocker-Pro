"""User schemas for STOCKER Pro API.

This module provides Pydantic models for user-related requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum


class UserRoleEnum(str, Enum):
    """User role enumeration.
    
    This enumeration represents the possible roles a user can have.
    """
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    USER = "user"
    GUEST = "guest"


class UserStatusEnum(str, Enum):
    """User status enumeration.
    
    This enumeration represents the possible statuses a user can have.
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserPreferencesBase(BaseModel):
    """User preferences base schema.
    
    This schema represents the base user preferences.
    """
    theme: Optional[str] = "light"
    language: Optional[str] = "en"
    timezone: Optional[str] = "UTC"
    notifications_enabled: Optional[bool] = True
    default_dashboard: Optional[str] = "overview"
    custom_settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UserPreferencesUpdate(UserPreferencesBase):
    """User preferences update schema.
    
    This schema represents a request to update user preferences.
    """
    pass


class UserBase(BaseModel):
    """User base schema.
    
    This schema represents the base user attributes.
    """
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, max_length=50, description="User first name")
    last_name: Optional[str] = Field(None, max_length=50, description="User last name")
    status: Optional[UserStatusEnum] = Field(UserStatusEnum.ACTIVE, description="User status")
    preferences: Optional[UserPreferencesBase] = Field(default_factory=UserPreferencesBase)


class UserCreate(UserBase):
    """User creation schema.
    
    This schema represents a request to create a new user.
    """
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    roles: Optional[List[UserRoleEnum]] = Field([UserRoleEnum.USER], description="User roles")
    
    # Validator to ensure username is not empty
    @validator("username")
    def username_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Username cannot be empty")
        return v
    
    # Validator to ensure password is strong enough
    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


class UserUpdate(BaseModel):
    """User update schema.
    
    This schema represents a request to update an existing user.
    """
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[UserStatusEnum] = None
    preferences: Optional[UserPreferencesBase] = None
    roles: Optional[List[UserRoleEnum]] = None


class UserResponse(UserBase):
    """User response schema.
    
    This schema represents a user in API responses.
    """
    id: str
    roles: List[UserRoleEnum]
    created_at: datetime
    last_login: Optional[datetime] = None
    portfolio_ids: List[str] = []
    
    class Config:
        orm_mode = True
