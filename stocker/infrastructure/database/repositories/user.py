"""User repository implementation for STOCKER Pro.

This module provides a repository implementation for user-related database operations,
following the repository pattern to abstract database access.
"""

from typing import List, Optional, Dict, Any

from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError

from stocker.core.exceptions import DataError, DataNotFoundError
from stocker.core.logging import get_logger
from stocker.domain.user import User, UserRole
from stocker.infrastructure.database.models.user import UserModel, UserRoleModel
from stocker.infrastructure.database.repositories.base import BaseRepository
from stocker.infrastructure.database.session import get_session

# Logger
logger = get_logger(__name__)


class UserRepository(BaseRepository[UserModel, User]):
    """Repository for user-related database operations.
    
    This class implements the repository pattern for user-related database operations,
    providing methods for CRUD operations and user-specific queries.
    """
    def __init__(self):
        """Initialize the repository."""
        super().__init__(UserModel)
    
    def _to_model(self, entity: User) -> UserModel:
        """Convert a domain entity to a database model.
        
        Args:
            entity: User domain entity
            
        Returns:
            UserModel database model
        """
        return UserModel.from_domain(entity)
    
    def _to_entity(self, model: UserModel) -> User:
        """Convert a database model to a domain entity.
        
        Args:
            model: UserModel database model
            
        Returns:
            User domain entity
        """
        return model.to_domain()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User domain entity if found, None otherwise
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                query = select(UserModel).where(UserModel.username == username)
                result = session.execute(query).scalar_one_or_none()
                
                if result is None:
                    return None
                
                return self._to_entity(result)
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by username {username}: {str(e)}")
            raise DataError(f"Error getting user by username {username}: {str(e)}")
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email.
        
        Args:
            email: Email to search for
            
        Returns:
            User domain entity if found, None otherwise
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                query = select(UserModel).where(UserModel.email == email)
                result = session.execute(query).scalar_one_or_none()
                
                if result is None:
                    return None
                
                return self._to_entity(result)
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            raise DataError(f"Error getting user by email {email}: {str(e)}")
    
    def search_users(self, search_term: str, limit: int = 10, offset: int = 0) -> List[User]:
        """Search for users by username, email, or name.
        
        Args:
            search_term: Search term
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of matching User domain entities
            
        Raises:
            DataError: If an error occurs during search
        """
        try:
            with get_session() as session:
                # Create search pattern for LIKE queries
                pattern = f"%{search_term}%"
                
                # Build query with OR conditions for different fields
                query = select(UserModel).where(
                    or_(
                        UserModel.username.ilike(pattern),
                        UserModel.email.ilike(pattern),
                        UserModel.first_name.ilike(pattern),
                        UserModel.last_name.ilike(pattern)
                    )
                ).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [self._to_entity(result) for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error searching users with term '{search_term}': {str(e)}")
            raise DataError(f"Error searching users: {str(e)}")
    
    def get_users_by_role(self, role: UserRole, limit: int = 10, offset: int = 0) -> List[User]:
        """Get users by role.
        
        Args:
            role: User role to filter by
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of User domain entities with the specified role
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                # This query is more complex due to the many-to-many relationship
                # We need to join the user_roles table
                query = select(UserModel).join(
                    UserModel.roles
                ).where(
                    UserRoleModel.role == role.value
                ).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [self._to_entity(result) for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting users by role {role.value}: {str(e)}")
            raise DataError(f"Error getting users by role: {str(e)}")
    
    def add_role_to_user(self, user_id: str, role: UserRole) -> User:
        """Add a role to a user.
        
        Args:
            user_id: User ID
            role: Role to add
            
        Returns:
            Updated User domain entity
            
        Raises:
            DataNotFoundError: If the user is not found
            DataError: If an error occurs during the operation
        """
        try:
            with get_session() as session:
                # Get the user
                user_model = session.get(UserModel, user_id)
                if user_model is None:
                    raise DataNotFoundError(f"User with ID {user_id} not found")
                
                # Get or create the role
                role_model = session.execute(
                    select(UserRoleModel).where(UserRoleModel.role == role.value)
                ).scalar_one_or_none()
                
                if role_model is None:
                    role_model = UserRoleModel.from_enum(role)
                    session.add(role_model)
                
                # Add the role to the user if not already present
                if role_model not in user_model.roles:
                    user_model.roles.append(role_model)
                    session.commit()
                    session.refresh(user_model)
                
                return self._to_entity(user_model)
        except SQLAlchemyError as e:
            logger.error(f"Error adding role {role.value} to user {user_id}: {str(e)}")
            raise DataError(f"Error adding role to user: {str(e)}")
    
    def remove_role_from_user(self, user_id: str, role: UserRole) -> User:
        """Remove a role from a user.
        
        Args:
            user_id: User ID
            role: Role to remove
            
        Returns:
            Updated User domain entity
            
        Raises:
            DataNotFoundError: If the user is not found
            DataError: If an error occurs during the operation
        """
        try:
            with get_session() as session:
                # Get the user
                user_model = session.get(UserModel, user_id)
                if user_model is None:
                    raise DataNotFoundError(f"User with ID {user_id} not found")
                
                # Get the role
                role_model = session.execute(
                    select(UserRoleModel).where(UserRoleModel.role == role.value)
                ).scalar_one_or_none()
                
                if role_model is None:
                    # Role doesn't exist, so nothing to remove
                    return self._to_entity(user_model)
                
                # Remove the role from the user if present
                if role_model in user_model.roles and len(user_model.roles) > 1:
                    user_model.roles.remove(role_model)
                    session.commit()
                    session.refresh(user_model)
                
                return self._to_entity(user_model)
        except SQLAlchemyError as e:
            logger.error(f"Error removing role {role.value} from user {user_id}: {str(e)}")
            raise DataError(f"Error removing role from user: {str(e)}")
