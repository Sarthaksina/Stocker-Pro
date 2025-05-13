"""User service implementation for STOCKER Pro.

This module provides a service implementation for user-related business logic,
coordinating between domain models and repositories.
"""

from datetime import datetime
from typing import Dict, List, Optional, Set, Any
import uuid

from stocker.core.exceptions import ServiceError, DataNotFoundError, AuthenticationError
from stocker.domain.user import User, UserRole, UserStatus, UserPreferences
from stocker.infrastructure.database.repositories.user import UserRepository
from stocker.services.base import BaseService


class UserService(BaseService):
    """Service for user-related business logic.
    
    This service coordinates between domain models and repositories to provide
    user-related functionality.
    """
    
    def __init__(self, user_repository: Optional[UserRepository] = None):
        """Initialize the service.
        
        Args:
            user_repository: User repository instance (if None, create new instance)
        """
        super().__init__()
        self.user_repository = user_repository or UserRepository()
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User domain entity if found, None otherwise
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_user", user_id=user_id)
            return self.user_repository.get_by_id(user_id)
        except Exception as e:
            self._handle_error("get_user", e, user_id=user_id)
    
    def get_user_or_raise(self, user_id: str) -> User:
        """Get a user by ID or raise an exception if not found.
        
        Args:
            user_id: User ID
            
        Returns:
            User domain entity
            
        Raises:
            DataNotFoundError: If the user is not found
            ServiceError: If an error occurs during retrieval
        """
        user = self.get_user(user_id)
        if user is None:
            raise DataNotFoundError(f"User with ID {user_id} not found")
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username.
        
        Args:
            username: Username
            
        Returns:
            User domain entity if found, None otherwise
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_user_by_username", username=username)
            return self.user_repository.get_by_username(username)
        except Exception as e:
            self._handle_error("get_user_by_username", e, username=username)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email.
        
        Args:
            email: Email address
            
        Returns:
            User domain entity if found, None otherwise
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_user_by_email", email=email)
            return self.user_repository.get_by_email(email)
        except Exception as e:
            self._handle_error("get_user_by_email", e, email=email)
    
    def create_user(self, user: User, password: str) -> User:
        """Create a new user.
        
        Args:
            user: User domain entity to create
            password: User password (will be hashed)
            
        Returns:
            Created User domain entity
            
        Raises:
            ServiceError: If an error occurs during creation
        """
        try:
            # Check if username or email already exists
            existing_username = self.user_repository.get_by_username(user.username)
            if existing_username:
                raise ServiceError(f"Username '{user.username}' is already taken")
            
            existing_email = self.user_repository.get_by_email(user.email)
            if existing_email:
                raise ServiceError(f"Email '{user.email}' is already registered")
            
            # Ensure user has an ID
            if not user.id:
                user.id = str(uuid.uuid4())
            
            # Ensure user has at least one role
            if not user.roles:
                user.roles = {UserRole.USER}
            
            # Set created_at if not set
            if not user.created_at:
                user.created_at = datetime.now()
            
            # Create user model
            from stocker.infrastructure.database.models.user import UserModel
            user_model = UserModel.from_domain(user)
            
            # Set password hash
            from werkzeug.security import generate_password_hash
            user_model.password_hash = generate_password_hash(password)
            
            # Save to database using direct session access
            # This is a special case because we need to handle the password hash
            from stocker.infrastructure.database.session import get_session
            with get_session() as session:
                session.add(user_model)
                session.commit()
                session.refresh(user_model)
            
            self._log_operation("create_user", user_id=user.id, username=user.username)
            return user_model.to_domain()
        except Exception as e:
            self._handle_error("create_user", e, username=user.username, email=user.email)
    
    def update_user(self, user: User) -> User:
        """Update an existing user.
        
        Args:
            user: User domain entity to update
            
        Returns:
            Updated User domain entity
            
        Raises:
            DataNotFoundError: If the user is not found
            ServiceError: If an error occurs during update
        """
        try:
            # Check if user exists
            existing_user = self.get_user(user.id)
            if existing_user is None:
                raise DataNotFoundError(f"User with ID {user.id} not found")
            
            # Check if username is being changed and if it's already taken
            if user.username != existing_user.username:
                username_check = self.user_repository.get_by_username(user.username)
                if username_check and username_check.id != user.id:
                    raise ServiceError(f"Username '{user.username}' is already taken")
            
            # Check if email is being changed and if it's already registered
            if user.email != existing_user.email:
                email_check = self.user_repository.get_by_email(user.email)
                if email_check and email_check.id != user.id:
                    raise ServiceError(f"Email '{user.email}' is already registered")
            
            self._log_operation("update_user", user_id=user.id, username=user.username)
            return self.user_repository.update(user)
        except Exception as e:
            self._handle_error("update_user", e, user_id=user.id, username=user.username)
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if the user was deleted, False otherwise
            
        Raises:
            ServiceError: If an error occurs during deletion
        """
        try:
            self._log_operation("delete_user", user_id=user_id)
            return self.user_repository.delete(user_id)
        except Exception as e:
            self._handle_error("delete_user", e, user_id=user_id)
    
    def search_users(self, search_term: str, limit: int = 10, offset: int = 0) -> List[User]:
        """Search for users by username, email, or name.
        
        Args:
            search_term: Search term
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of matching User domain entities
            
        Raises:
            ServiceError: If an error occurs during search
        """
        try:
            self._log_operation("search_users", search_term=search_term, limit=limit, offset=offset)
            return self.user_repository.search_users(search_term, limit, offset)
        except Exception as e:
            self._handle_error("search_users", e, search_term=search_term, limit=limit, offset=offset)
    
    def get_users_by_role(self, role: UserRole, limit: int = 10, offset: int = 0) -> List[User]:
        """Get users by role.
        
        Args:
            role: User role to filter by
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of User domain entities with the specified role
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_users_by_role", role=role.value, limit=limit, offset=offset)
            return self.user_repository.get_users_by_role(role, limit, offset)
        except Exception as e:
            self._handle_error("get_users_by_role", e, role=role.value, limit=limit, offset=offset)
    
    def add_role_to_user(self, user_id: str, role: UserRole) -> User:
        """Add a role to a user.
        
        Args:
            user_id: User ID
            role: Role to add
            
        Returns:
            Updated User domain entity
            
        Raises:
            DataNotFoundError: If the user is not found
            ServiceError: If an error occurs during the operation
        """
        try:
            self._log_operation("add_role_to_user", user_id=user_id, role=role.value)
            return self.user_repository.add_role_to_user(user_id, role)
        except Exception as e:
            self._handle_error("add_role_to_user", e, user_id=user_id, role=role.value)
    
    def remove_role_from_user(self, user_id: str, role: UserRole) -> User:
        """Remove a role from a user.
        
        Args:
            user_id: User ID
            role: Role to remove
            
        Returns:
            Updated User domain entity
            
        Raises:
            DataNotFoundError: If the user is not found
            ServiceError: If an error occurs during the operation
        """
        try:
            self._log_operation("remove_role_from_user", user_id=user_id, role=role.value)
            return self.user_repository.remove_role_from_user(user_id, role)
        except Exception as e:
            self._handle_error("remove_role_from_user", e, user_id=user_id, role=role.value)
    
    def authenticate_user(self, username_or_email: str, password: str) -> User:
        """Authenticate a user by username/email and password.
        
        Args:
            username_or_email: Username or email address
            password: User password
            
        Returns:
            Authenticated User domain entity
            
        Raises:
            AuthenticationError: If authentication fails
            ServiceError: If an error occurs during authentication
        """
        try:
            # Check if input is an email
            is_email = "@" in username_or_email
            
            # Get user by username or email
            user = None
            if is_email:
                user = self.user_repository.get_by_email(username_or_email)
            else:
                user = self.user_repository.get_by_username(username_or_email)
            
            # Check if user exists
            if user is None:
                raise AuthenticationError("Invalid username/email or password")
            
            # Check if user is active
            if user.status != UserStatus.ACTIVE:
                raise AuthenticationError(f"User account is {user.status.value}")
            
            # Get user model to check password
            from stocker.infrastructure.database.models.user import UserModel
            from stocker.infrastructure.database.session import get_session
            with get_session() as session:
                user_model = session.query(UserModel).filter_by(id=user.id).first()
                
                # Check password
                from werkzeug.security import check_password_hash
                if not check_password_hash(user_model.password_hash, password):
                    raise AuthenticationError("Invalid username/email or password")
                
                # Update last login time
                user_model.last_login = datetime.now()
                session.commit()
                session.refresh(user_model)
                
                # Return updated user
                return user_model.to_domain()
        except AuthenticationError:
            # Don't log sensitive details for authentication errors
            self._log_operation("authenticate_user", success=False)
            raise
        except Exception as e:
            self._handle_error("authenticate_user", e)
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change a user's password.
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            True if the password was changed successfully
            
        Raises:
            DataNotFoundError: If the user is not found
            AuthenticationError: If the current password is incorrect
            ServiceError: If an error occurs during the operation
        """
        try:
            # Get user model
            from stocker.infrastructure.database.models.user import UserModel
            from stocker.infrastructure.database.session import get_session
            with get_session() as session:
                user_model = session.query(UserModel).filter_by(id=user_id).first()
                
                # Check if user exists
                if user_model is None:
                    raise DataNotFoundError(f"User with ID {user_id} not found")
                
                # Check current password
                from werkzeug.security import check_password_hash, generate_password_hash
                if not check_password_hash(user_model.password_hash, current_password):
                    raise AuthenticationError("Current password is incorrect")
                
                # Update password
                user_model.password_hash = generate_password_hash(new_password)
                session.commit()
            
            self._log_operation("change_password", user_id=user_id, success=True)
            return True
        except (DataNotFoundError, AuthenticationError):
            # Don't log sensitive details for these errors
            self._log_operation("change_password", user_id=user_id, success=False)
            raise
        except Exception as e:
            self._handle_error("change_password", e, user_id=user_id)
    
    def update_user_preferences(self, user_id: str, preferences: UserPreferences) -> User:
        """Update a user's preferences.
        
        Args:
            user_id: User ID
            preferences: User preferences
            
        Returns:
            Updated User domain entity
            
        Raises:
            DataNotFoundError: If the user is not found
            ServiceError: If an error occurs during the operation
        """
        try:
            # Get user
            user = self.get_user_or_raise(user_id)
            
            # Update preferences
            user.preferences = preferences
            
            # Save user
            self._log_operation("update_user_preferences", user_id=user_id)
            return self.user_repository.update(user)
        except Exception as e:
            self._handle_error("update_user_preferences", e, user_id=user_id)
