"""Portfolio repository implementation for STOCKER Pro.

This module provides a repository implementation for portfolio-related database operations,
following the repository pattern to abstract database access.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import select, and_, desc, func
from sqlalchemy.exc import SQLAlchemyError

from stocker.core.exceptions import DataError, DataNotFoundError
from stocker.core.logging import get_logger
from stocker.domain.portfolio import Portfolio, Position, Transaction, PortfolioType, TransactionType
from stocker.infrastructure.database.models.portfolio import PortfolioModel, PositionModel, TransactionModel
from stocker.infrastructure.database.repositories.base import BaseRepository
from stocker.infrastructure.database.session import get_session

# Logger
logger = get_logger(__name__)


class PortfolioRepository(BaseRepository[PortfolioModel, Portfolio]):
    """Repository for portfolio-related database operations.
    
    This class implements the repository pattern for portfolio-related database operations,
    providing methods for CRUD operations and portfolio-specific queries.
    """
    def __init__(self):
        """Initialize the repository."""
        super().__init__(PortfolioModel)
    
    def _to_model(self, entity: Portfolio) -> PortfolioModel:
        """Convert a domain entity to a database model.
        
        Args:
            entity: Portfolio domain entity
            
        Returns:
            PortfolioModel database model
        """
        return PortfolioModel.from_domain(entity)
    
    def _to_entity(self, model: PortfolioModel) -> Portfolio:
        """Convert a database model to a domain entity.
        
        Args:
            model: PortfolioModel database model
            
        Returns:
            Portfolio domain entity
        """
        return model.to_domain()
    
    def get_by_owner(self, owner_id: str, limit: int = 10, offset: int = 0) -> List[Portfolio]:
        """Get portfolios by owner ID.
        
        Args:
            owner_id: Owner user ID
            limit: Maximum number of portfolios to return
            offset: Number of portfolios to skip
            
        Returns:
            List of Portfolio domain entities owned by the specified user
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                query = select(PortfolioModel).where(
                    PortfolioModel.owner_id == owner_id
                ).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [self._to_entity(result) for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting portfolios by owner {owner_id}: {str(e)}")
            raise DataError(f"Error getting portfolios by owner: {str(e)}")
    
    def get_by_type(self, portfolio_type: PortfolioType, limit: int = 10, offset: int = 0) -> List[Portfolio]:
        """Get portfolios by type.
        
        Args:
            portfolio_type: Portfolio type to filter by
            limit: Maximum number of portfolios to return
            offset: Number of portfolios to skip
            
        Returns:
            List of Portfolio domain entities of the specified type
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                query = select(PortfolioModel).where(
                    PortfolioModel.type == portfolio_type.value
                ).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [self._to_entity(result) for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting portfolios by type {portfolio_type.value}: {str(e)}")
            raise DataError(f"Error getting portfolios by type: {str(e)}")
    
    def add_position(self, portfolio_id: str, position: Position) -> Portfolio:
        """Add or update a position in a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            position: Position to add or update
            
        Returns:
            Updated Portfolio domain entity
            
        Raises:
            DataNotFoundError: If the portfolio is not found
            DataError: If an error occurs during the operation
        """
        try:
            with get_session() as session:
                # Check if portfolio exists
                portfolio_model = session.get(PortfolioModel, portfolio_id)
                if portfolio_model is None:
                    raise DataNotFoundError(f"Portfolio with ID {portfolio_id} not found")
                
                # Check if position already exists
                existing_position = session.execute(
                    select(PositionModel).where(
                        and_(
                            PositionModel.portfolio_id == portfolio_id,
                            PositionModel.symbol == position.symbol
                        )
                    )
                ).scalar_one_or_none()
                
                if existing_position:
                    # Update existing position
                    existing_position.quantity = position.quantity
                    existing_position.cost_basis = position.cost_basis
                    existing_position.last_updated = datetime.now()
                else:
                    # Create new position
                    position_model = PositionModel.from_domain(position, portfolio_id)
                    session.add(position_model)
                
                session.commit()
                session.refresh(portfolio_model)
                
                return self._to_entity(portfolio_model)
        except SQLAlchemyError as e:
            logger.error(f"Error adding position to portfolio {portfolio_id}: {str(e)}")
            raise DataError(f"Error adding position to portfolio: {str(e)}")
    
    def remove_position(self, portfolio_id: str, symbol: str) -> Portfolio:
        """Remove a position from a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol of the position to remove
            
        Returns:
            Updated Portfolio domain entity
            
        Raises:
            DataNotFoundError: If the portfolio or position is not found
            DataError: If an error occurs during the operation
        """
        try:
            with get_session() as session:
                # Check if portfolio exists
                portfolio_model = session.get(PortfolioModel, portfolio_id)
                if portfolio_model is None:
                    raise DataNotFoundError(f"Portfolio with ID {portfolio_id} not found")
                
                # Find the position
                position_model = session.execute(
                    select(PositionModel).where(
                        and_(
                            PositionModel.portfolio_id == portfolio_id,
                            PositionModel.symbol == symbol
                        )
                    )
                ).scalar_one_or_none()
                
                if position_model is None:
                    raise DataNotFoundError(f"Position with symbol {symbol} not found in portfolio {portfolio_id}")
                
                # Remove the position
                session.delete(position_model)
                session.commit()
                session.refresh(portfolio_model)
                
                return self._to_entity(portfolio_model)
        except SQLAlchemyError as e:
            logger.error(f"Error removing position from portfolio {portfolio_id}: {str(e)}")
            raise DataError(f"Error removing position from portfolio: {str(e)}")
    
    def add_transaction(self, portfolio_id: str, transaction: Transaction) -> Portfolio:
        """Add a transaction to a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            transaction: Transaction to add
            
        Returns:
            Updated Portfolio domain entity
            
        Raises:
            DataNotFoundError: If the portfolio is not found
            DataError: If an error occurs during the operation
        """
        try:
            with get_session() as session:
                # Check if portfolio exists
                portfolio_model = session.get(PortfolioModel, portfolio_id)
                if portfolio_model is None:
                    raise DataNotFoundError(f"Portfolio with ID {portfolio_id} not found")
                
                # Create transaction model
                transaction_model = TransactionModel.from_domain(transaction, portfolio_id)
                
                # Add transaction to database
                session.add(transaction_model)
                
                # Update portfolio cash balance
                if transaction.type == TransactionType.DEPOSIT:
                    portfolio_model.cash_balance += transaction.amount
                elif transaction.type == TransactionType.WITHDRAWAL:
                    portfolio_model.cash_balance -= transaction.amount
                elif transaction.type == TransactionType.BUY:
                    # For buy transactions, reduce cash balance by total cost
                    total_cost = transaction.amount + transaction.fees
                    portfolio_model.cash_balance -= total_cost
                    
                    # Update or create position
                    existing_position = session.execute(
                        select(PositionModel).where(
                            and_(
                                PositionModel.portfolio_id == portfolio_id,
                                PositionModel.symbol == transaction.symbol
                            )
                        )
                    ).scalar_one_or_none()
                    
                    if existing_position:
                        # Update existing position
                        new_quantity = existing_position.quantity + transaction.quantity
                        new_cost_basis = (
                            (existing_position.cost_basis * existing_position.quantity) +
                            (transaction.price * transaction.quantity)
                        ) / new_quantity if new_quantity > 0 else 0
                        
                        existing_position.quantity = new_quantity
                        existing_position.cost_basis = new_cost_basis
                        existing_position.last_updated = datetime.now()
                    else:
                        # Create new position
                        position = Position(
                            symbol=transaction.symbol,
                            quantity=transaction.quantity,
                            cost_basis=transaction.price,
                            open_date=transaction.date
                        )
                        position_model = PositionModel.from_domain(position, portfolio_id)
                        session.add(position_model)
                
                elif transaction.type == TransactionType.SELL:
                    # For sell transactions, increase cash balance by proceeds minus fees
                    proceeds = transaction.amount - transaction.fees
                    portfolio_model.cash_balance += proceeds
                    
                    # Update position
                    existing_position = session.execute(
                        select(PositionModel).where(
                            and_(
                                PositionModel.portfolio_id == portfolio_id,
                                PositionModel.symbol == transaction.symbol
                            )
                        )
                    ).scalar_one_or_none()
                    
                    if existing_position:
                        # Update existing position
                        new_quantity = existing_position.quantity - transaction.quantity
                        
                        if new_quantity <= 0:
                            # Remove position if quantity is zero or negative
                            session.delete(existing_position)
                        else:
                            # Update position with new quantity
                            existing_position.quantity = new_quantity
                            existing_position.last_updated = datetime.now()
                
                # Commit changes
                session.commit()
                session.refresh(portfolio_model)
                
                return self._to_entity(portfolio_model)
        except SQLAlchemyError as e:
            logger.error(f"Error adding transaction to portfolio {portfolio_id}: {str(e)}")
            raise DataError(f"Error adding transaction to portfolio: {str(e)}")
    
    def get_transactions(self, portfolio_id: str, limit: int = 50, offset: int = 0) -> List[Transaction]:
        """Get transactions for a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of Transaction domain entities for the specified portfolio
            
        Raises:
            DataNotFoundError: If the portfolio is not found
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                # Check if portfolio exists
                portfolio_model = session.get(PortfolioModel, portfolio_id)
                if portfolio_model is None:
                    raise DataNotFoundError(f"Portfolio with ID {portfolio_id} not found")
                
                # Get transactions
                query = select(TransactionModel).where(
                    TransactionModel.portfolio_id == portfolio_id
                ).order_by(desc(TransactionModel.date)).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [result.to_domain() for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting transactions for portfolio {portfolio_id}: {str(e)}")
            raise DataError(f"Error getting transactions for portfolio: {str(e)}")
    
    def get_positions(self, portfolio_id: str) -> Dict[str, Position]:
        """Get positions for a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Dictionary of positions keyed by symbol
            
        Raises:
            DataNotFoundError: If the portfolio is not found
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                # Check if portfolio exists
                portfolio_model = session.get(PortfolioModel, portfolio_id)
                if portfolio_model is None:
                    raise DataNotFoundError(f"Portfolio with ID {portfolio_id} not found")
                
                # Get positions
                query = select(PositionModel).where(PositionModel.portfolio_id == portfolio_id)
                results = session.execute(query).scalars().all()
                
                positions = {}
                for result in results:
                    position = result.to_domain()
                    positions[position.symbol] = position
                
                return positions
        except SQLAlchemyError as e:
            logger.error(f"Error getting positions for portfolio {portfolio_id}: {str(e)}")
            raise DataError(f"Error getting positions for portfolio: {str(e)}")
