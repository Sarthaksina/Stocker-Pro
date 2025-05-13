"""User domain model for STOCKER Pro.

This module defines the core domain entities related to users, roles,
and user preferences.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from uuid import uuid4


class UserRole(str, Enum):
    """User role enumeration.
    
    Defines the possible roles a user can have in the system, which
    determine their permissions and access levels.
    """
    ADMIN = "admin"          # Administrator with full access
    MANAGER = "manager"      # Manager with elevated access
    ANALYST = "analyst"      # Analyst with data access
    USER = "user"            # Regular user
    GUEST = "guest"          # Guest user with limited access


class UserStatus(str, Enum):
    """User status enumeration.
    
    Defines the possible statuses a user account can have.
    """
    ACTIVE = "active"            # Active user
    INACTIVE = "inactive"        # Inactive user
    SUSPENDED = "suspended"      # Suspended user
    PENDING = "pending"          # Pending activation
    LOCKED = "locked"            # Locked account


@dataclass
class UserPreferences:
    """User preferences.
    
    This class represents a user's preferences for the application,
    such as UI theme, default views, and notification settings.
    
    Attributes:
        theme: UI theme preference
        default_portfolio_id: Default portfolio to show
        default_timeframe: Default timeframe for charts
        default_chart_type: Default chart type
        email_notifications: Whether to send email notifications
        watchlist: List of stock symbols in the user's watchlist
        custom_settings: Dictionary of additional custom settings
    """
    theme: str = "dark"
    default_portfolio_id: Optional[str] = None
    default_timeframe: str = "1d"
    default_chart_type: str = "candlestick"
    email_notifications: bool = True
    watchlist: List[str] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the preferences to a dictionary representation."""
        return {
            "theme": self.theme,
            "default_portfolio_id": self.default_portfolio_id,
            "default_timeframe": self.default_timeframe,
            "default_chart_type": self.default_chart_type,
            "email_notifications": self.email_notifications,
            "watchlist": self.watchlist,
            "custom_settings": self.custom_settings
        }


@dataclass
class User:
    """User domain entity.
    
    This class represents a user as a business entity, including
    their account information, roles, and preferences.
    
    Attributes:
        id: Unique user ID
        username: Username for login
        email: Email address
        first_name: First name
        last_name: Last name
        roles: Set of user roles
        status: Account status
        preferences: User preferences
        created_at: Account creation date
        last_login: Last login date
        portfolio_ids: List of portfolio IDs owned by the user
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    username: str
    email: str
    first_name: str = ""
    last_name: str = ""
    roles: Set[UserRole] = field(default_factory=lambda: {UserRole.USER})
    status: UserStatus = UserStatus.ACTIVE
    preferences: UserPreferences = field(default_factory=UserPreferences)
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    portfolio_ids: List[str] = field(default_factory=list)
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    @property
    def is_admin(self) -> bool:
        """Check if the user has admin role."""
        return UserRole.ADMIN in self.roles
    
    @property
    def is_active(self) -> bool:
        """Check if the user account is active."""
        return self.status == UserStatus.ACTIVE
    
    def has_role(self, role: UserRole) -> bool:
        """Check if the user has a specific role.
        
        Args:
            role: Role to check
            
        Returns:
            True if the user has the role, False otherwise
        """
        return role in self.roles
    
    def add_role(self, role: UserRole) -> None:
        """Add a role to the user.
        
        Args:
            role: Role to add
        """
        self.roles.add(role)
    
    def remove_role(self, role: UserRole) -> None:
        """Remove a role from the user.
        
        Args:
            role: Role to remove
        """
        if role in self.roles and len(self.roles) > 1:
            self.roles.remove(role)
    
    def add_portfolio(self, portfolio_id: str) -> None:
        """Add a portfolio to the user's portfolios.
        
        Args:
            portfolio_id: Portfolio ID to add
        """
        if portfolio_id not in self.portfolio_ids:
            self.portfolio_ids.append(portfolio_id)
    
    def remove_portfolio(self, portfolio_id: str) -> None:
        """Remove a portfolio from the user's portfolios.
        
        Args:
            portfolio_id: Portfolio ID to remove
        """
        if portfolio_id in self.portfolio_ids:
            self.portfolio_ids.remove(portfolio_id)
    
    def add_to_watchlist(self, symbol: str) -> None:
        """Add a stock symbol to the user's watchlist.
        
        Args:
            symbol: Stock symbol to add
        """
        if symbol not in self.preferences.watchlist:
            self.preferences.watchlist.append(symbol)
    
    def remove_from_watchlist(self, symbol: str) -> None:
        """Remove a stock symbol from the user's watchlist.
        
        Args:
            symbol: Stock symbol to remove
        """
        if symbol in self.preferences.watchlist:
            self.preferences.watchlist.remove(symbol)
    
    def update_last_login(self) -> None:
        """Update the user's last login time to now."""
        self.last_login = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the user to a dictionary representation."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "roles": [role.value for role in self.roles],
            "status": self.status.value,
            "preferences": self.preferences.to_dict(),
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "portfolio_ids": self.portfolio_ids,
            "is_admin": self.is_admin,
            "is_active": self.is_active
        }
