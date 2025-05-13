"""Base repository implementation for STOCKER Pro.

This module provides a base repository class that implements common CRUD operations
and serves as a foundation for specific repository implementations.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from stocker.core.exceptions import DataError
from stocker.core.logging import get_logger
from stocker.infrastructure.database.session import get_session

# Type variable for the model class
ModelT = TypeVar('ModelT')

# Type variable for the domain entity class
EntityT = TypeVar('EntityT')

# Logger
logger = get_logger(__name__)


class BaseRepository(Generic[ModelT, EntityT]):
    """Base repository class for database operations.
    
    This class implements common CRUD operations and serves as a foundation
    for specific repository implementations.
    
    Attributes:
        model_class: SQLAlchemy model class
    """
    def __init__(self, model_class: Type[ModelT]):
        """Initialize the repository.
        
        Args:
            model_class: SQLAlchemy model class
        """
        self.model_class = model_class
    
    def create(self, entity: EntityT) -> EntityT:
        """Create a new entity in the database.
        
        Args:
            entity: Domain entity to create
            
        Returns:
            Created domain entity
            
        Raises:
            DataError: If an error occurs during creation
        """
        try:
            # Convert domain entity to database model
            model = self._to_model(entity)
            
            # Save to database
            with get_session() as session:
                session.add(model)
                session.commit()
                session.refresh(model)
            
            # Convert back to domain entity
            return self._to_entity(model)
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model_class.__name__}: {str(e)}")
            raise DataError(f"Error creating {self.model_class.__name__}: {str(e)}")
    
    def get_by_id(self, id: Any) -> Optional[EntityT]:
        """Get an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Domain entity if found, None otherwise
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                result = session.get(self.model_class, id)
                
                if result is None:
                    return None
                
                return self._to_entity(result)
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model_class.__name__} by ID {id}: {str(e)}")
            raise DataError(f"Error getting {self.model_class.__name__} by ID {id}: {str(e)}")
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[EntityT]:
        """Get all entities.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of domain entities
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                query = select(self.model_class)
                
                if offset is not None:
                    query = query.offset(offset)
                
                if limit is not None:
                    query = query.limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [self._to_entity(result) for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model_class.__name__}: {str(e)}")
            raise DataError(f"Error getting all {self.model_class.__name__}: {str(e)}")
    
    def update(self, entity: EntityT) -> EntityT:
        """Update an entity in the database.
        
        Args:
            entity: Domain entity to update
            
        Returns:
            Updated domain entity
            
        Raises:
            DataError: If an error occurs during update
        """
        try:
            # Convert domain entity to database model
            model = self._to_model(entity)
            
            # Update in database
            with get_session() as session:
                session.merge(model)
                session.commit()
                session.refresh(model)
            
            # Convert back to domain entity
            return self._to_entity(model)
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model_class.__name__}: {str(e)}")
            raise DataError(f"Error updating {self.model_class.__name__}: {str(e)}")
    
    def delete(self, id: Any) -> bool:
        """Delete an entity from the database.
        
        Args:
            id: Entity ID
            
        Returns:
            True if the entity was deleted, False otherwise
            
        Raises:
            DataError: If an error occurs during deletion
        """
        try:
            with get_session() as session:
                entity = session.get(self.model_class, id)
                
                if entity is None:
                    return False
                
                session.delete(entity)
                session.commit()
                
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model_class.__name__} with ID {id}: {str(e)}")
            raise DataError(f"Error deleting {self.model_class.__name__} with ID {id}: {str(e)}")
    
    def _to_model(self, entity: EntityT) -> ModelT:
        """Convert a domain entity to a database model.
        
        This method should be implemented by subclasses.
        
        Args:
            entity: Domain entity
            
        Returns:
            Database model
        """
        raise NotImplementedError("Subclasses must implement _to_model")
    
    def _to_entity(self, model: ModelT) -> EntityT:
        """Convert a database model to a domain entity.
        
        This method should be implemented by subclasses.
        
        Args:
            model: Database model
            
        Returns:
            Domain entity
        """
        raise NotImplementedError("Subclasses must implement _to_entity")
