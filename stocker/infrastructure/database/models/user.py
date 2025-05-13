"""User database model for STOCKER Pro.

This module defines the SQLAlchemy model for users, including their
roles, preferences, and relationships to other entities.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Set, Any

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, Text, JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from stocker.infrastructure.database.session import Base
from stocker.domain.user import User, UserRole, UserStatus, UserPreferences


# Association table for user-role many-to-many relationship
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id")),
    Column("role", String(20))
)


class UserModel(Base):
    """SQLAlchemy model for users.
    
    This model maps to the 'users' table in the database and provides
    persistence for User domain entities.
    """
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    status = Column(String(20), default="active")
    preferences = Column(MutableDict.as_mutable(JSON), default=dict)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    roles = relationship(
        "UserRoleModel",
        secondary=user_roles,
        backref="users"
    )
    portfolios = relationship(
        "PortfolioModel",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    strategies = relationship(
        "StrategyModel",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    
    @classmethod
    def from_domain(cls, user: User) -> "UserModel":
        """Create a database model from a domain entity.
        
        Args:
            user: User domain entity
            
        Returns:
            UserModel database model
        """
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            status=user.status.value,
            preferences=user.preferences.to_dict(),
            created_at=user.created_at,
            last_login=user.last_login,
            # Note: password_hash must be set separately
        )
    
    def to_domain(self) -> User:
        """Convert to a domain entity.
        
        Returns:
            User domain entity
        """
        # Convert roles from database representation to domain enum
        roles = set()
        for role_name in [role.role for role in self.roles]:
            try:
                roles.add(UserRole(role_name))
            except ValueError:
                # Skip invalid roles
                pass
        
        # Create user preferences
        preferences = UserPreferences()
        if self.preferences:
            preferences_dict = self.preferences
            for key, value in preferences_dict.items():
                if hasattr(preferences, key):
                    setattr(preferences, key, value)
                else:
                    # Add to custom settings
                    preferences.custom_settings[key] = value
        
        # Create user domain entity
        return User(
            id=self.id,
            username=self.username,
            email=self.email,
            first_name=self.first_name or "",
            last_name=self.last_name or "",
            roles=roles or {UserRole.USER},
            status=UserStatus(self.status) if self.status else UserStatus.ACTIVE,
            preferences=preferences,
            created_at=self.created_at,
            last_login=self.last_login,
            portfolio_ids=[p.id for p in self.portfolios] if self.portfolios else []
        )


class UserRoleModel(Base):
    """SQLAlchemy model for user roles.
    
    This model maps to the 'user_role_types' table in the database and provides
    a list of valid role types.
    """
    __tablename__ = "user_role_types"
    
    role = Column(String(20), primary_key=True)
    description = Column(String(255))
    
    @classmethod
    def from_enum(cls, role: UserRole) -> "UserRoleModel":
        """Create a database model from a role enum.
        
        Args:
            role: UserRole enum value
            
        Returns:
            UserRoleModel database model
        """
        descriptions = {
            UserRole.ADMIN: "Administrator with full access",
            UserRole.MANAGER: "Manager with elevated access",
            UserRole.ANALYST: "Analyst with data access",
            UserRole.USER: "Regular user",
            UserRole.GUEST: "Guest user with limited access"
        }
        
        return cls(
            role=role.value,
            description=descriptions.get(role, "")
        )
