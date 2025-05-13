"""Strategy repository implementation for STOCKER Pro.

This module provides a repository implementation for strategy-related database operations,
following the repository pattern to abstract database access.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import select, and_, desc, func
from sqlalchemy.exc import SQLAlchemyError

from stocker.core.exceptions import DataError, DataNotFoundError
from stocker.core.logging import get_logger
from stocker.domain.strategy import Strategy, StrategyType, Signal, SignalType
from stocker.infrastructure.database.models.strategy import StrategyModel, SignalModel
from stocker.infrastructure.database.repositories.base import BaseRepository
from stocker.infrastructure.database.session import get_session

# Logger
logger = get_logger(__name__)


class StrategyRepository(BaseRepository[StrategyModel, Strategy]):
    """Repository for strategy-related database operations.
    
    This class implements the repository pattern for strategy-related database operations,
    providing methods for CRUD operations and strategy-specific queries.
    """
    def __init__(self):
        """Initialize the repository."""
        super().__init__(StrategyModel)
    
    def _to_model(self, entity: Strategy) -> StrategyModel:
        """Convert a domain entity to a database model.
        
        Args:
            entity: Strategy domain entity
            
        Returns:
            StrategyModel database model
        """
        return StrategyModel.from_domain(entity)
    
    def _to_entity(self, model: StrategyModel) -> Strategy:
        """Convert a database model to a domain entity.
        
        Args:
            model: StrategyModel database model
            
        Returns:
            Strategy domain entity
        """
        return model.to_domain()
    
    def get_by_owner(self, owner_id: str, limit: int = 10, offset: int = 0) -> List[Strategy]:
        """Get strategies by owner ID.
        
        Args:
            owner_id: Owner user ID
            limit: Maximum number of strategies to return
            offset: Number of strategies to skip
            
        Returns:
            List of Strategy domain entities owned by the specified user
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                query = select(StrategyModel).where(
                    StrategyModel.owner_id == owner_id
                ).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [self._to_entity(result) for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting strategies by owner {owner_id}: {str(e)}")
            raise DataError(f"Error getting strategies by owner: {str(e)}")
    
    def get_by_type(self, strategy_type: StrategyType, limit: int = 10, offset: int = 0) -> List[Strategy]:
        """Get strategies by type.
        
        Args:
            strategy_type: Strategy type to filter by
            limit: Maximum number of strategies to return
            offset: Number of strategies to skip
            
        Returns:
            List of Strategy domain entities of the specified type
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                query = select(StrategyModel).where(
                    StrategyModel.type == strategy_type.value
                ).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [self._to_entity(result) for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting strategies by type {strategy_type.value}: {str(e)}")
            raise DataError(f"Error getting strategies by type: {str(e)}")
    
    def get_active_strategies(self, limit: int = 10, offset: int = 0) -> List[Strategy]:
        """Get active strategies.
        
        Args:
            limit: Maximum number of strategies to return
            offset: Number of strategies to skip
            
        Returns:
            List of active Strategy domain entities
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                query = select(StrategyModel).where(
                    StrategyModel.is_active == True
                ).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [self._to_entity(result) for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting active strategies: {str(e)}")
            raise DataError(f"Error getting active strategies: {str(e)}")
    
    def add_signal(self, strategy_id: str, signal: Signal) -> Signal:
        """Add a signal for a strategy.
        
        Args:
            strategy_id: Strategy ID
            signal: Signal to add
            
        Returns:
            Added Signal domain entity
            
        Raises:
            DataNotFoundError: If the strategy is not found
            DataError: If an error occurs during the operation
        """
        try:
            with get_session() as session:
                # Check if strategy exists
                strategy_model = session.get(StrategyModel, strategy_id)
                if strategy_model is None:
                    raise DataNotFoundError(f"Strategy with ID {strategy_id} not found")
                
                # Create signal model
                signal_model = SignalModel.from_domain(signal)
                
                # Add signal to database
                session.add(signal_model)
                session.commit()
                session.refresh(signal_model)
                
                return signal_model.to_domain()
        except SQLAlchemyError as e:
            logger.error(f"Error adding signal to strategy {strategy_id}: {str(e)}")
            raise DataError(f"Error adding signal to strategy: {str(e)}")
    
    def get_signals(self, strategy_id: str, limit: int = 50, offset: int = 0) -> List[Signal]:
        """Get signals for a strategy.
        
        Args:
            strategy_id: Strategy ID
            limit: Maximum number of signals to return
            offset: Number of signals to skip
            
        Returns:
            List of Signal domain entities for the specified strategy
            
        Raises:
            DataNotFoundError: If the strategy is not found
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                # Check if strategy exists
                strategy_model = session.get(StrategyModel, strategy_id)
                if strategy_model is None:
                    raise DataNotFoundError(f"Strategy with ID {strategy_id} not found")
                
                # Get signals
                query = select(SignalModel).where(
                    SignalModel.strategy_id == strategy_id
                ).order_by(desc(SignalModel.date)).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [result.to_domain() for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting signals for strategy {strategy_id}: {str(e)}")
            raise DataError(f"Error getting signals for strategy: {str(e)}")
    
    def get_signals_by_symbol(self, symbol: str, limit: int = 50, offset: int = 0) -> List[Signal]:
        """Get signals for a specific symbol across all strategies.
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of signals to return
            offset: Number of signals to skip
            
        Returns:
            List of Signal domain entities for the specified symbol
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                # Get signals
                query = select(SignalModel).where(
                    SignalModel.symbol == symbol
                ).order_by(desc(SignalModel.date)).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [result.to_domain() for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting signals for symbol {symbol}: {str(e)}")
            raise DataError(f"Error getting signals for symbol: {str(e)}")
    
    def get_recent_signals(self, days: int = 7, limit: int = 50) -> List[Signal]:
        """Get recent signals across all strategies.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of signals to return
            
        Returns:
            List of recent Signal domain entities
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                # Calculate cutoff date
                cutoff_date = datetime.now() - datetime.timedelta(days=days)
                
                # Get signals
                query = select(SignalModel).where(
                    SignalModel.date >= cutoff_date
                ).order_by(desc(SignalModel.date)).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [result.to_domain() for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting recent signals: {str(e)}")
            raise DataError(f"Error getting recent signals: {str(e)}")
    
    def get_signals_by_type(self, signal_type: SignalType, limit: int = 50, offset: int = 0) -> List[Signal]:
        """Get signals by type across all strategies.
        
        Args:
            signal_type: Signal type to filter by
            limit: Maximum number of signals to return
            offset: Number of signals to skip
            
        Returns:
            List of Signal domain entities of the specified type
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                # Get signals
                query = select(SignalModel).where(
                    SignalModel.type == signal_type.value
                ).order_by(desc(SignalModel.date)).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [result.to_domain() for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting signals by type {signal_type.value}: {str(e)}")
            raise DataError(f"Error getting signals by type: {str(e)}")
    
    def update_strategy_performance(self, strategy_id: str, metrics: Dict[str, Any]) -> Strategy:
        """Update performance metrics for a strategy.
        
        Args:
            strategy_id: Strategy ID
            metrics: Performance metrics to update
            
        Returns:
            Updated Strategy domain entity
            
        Raises:
            DataNotFoundError: If the strategy is not found
            DataError: If an error occurs during the operation
        """
        try:
            with get_session() as session:
                # Check if strategy exists
                strategy_model = session.get(StrategyModel, strategy_id)
                if strategy_model is None:
                    raise DataNotFoundError(f"Strategy with ID {strategy_id} not found")
                
                # Update performance metrics
                strategy_model.performance_metrics = metrics
                strategy_model.updated_at = datetime.now()
                
                # Commit changes
                session.commit()
                session.refresh(strategy_model)
                
                return self._to_entity(strategy_model)
        except SQLAlchemyError as e:
            logger.error(f"Error updating performance metrics for strategy {strategy_id}: {str(e)}")
            raise DataError(f"Error updating performance metrics: {str(e)}")
