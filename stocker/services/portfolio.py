"""Portfolio service implementation for STOCKER Pro.

This module provides a service implementation for portfolio-related business logic,
coordinating between domain models and repositories.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
import uuid

from stocker.core.exceptions import ServiceError, DataNotFoundError
from stocker.domain.portfolio import Portfolio, Position, Transaction, PortfolioType, TransactionType
from stocker.domain.stock import Stock
from stocker.infrastructure.database.repositories.portfolio import PortfolioRepository
from stocker.infrastructure.database.repositories.stock import StockRepository
from stocker.services.base import BaseService


class PortfolioService(BaseService):
    """Service for portfolio-related business logic.
    
    This service coordinates between domain models and repositories to provide
    portfolio-related functionality.
    """
    
    def __init__(self, portfolio_repository: Optional[PortfolioRepository] = None,
                 stock_repository: Optional[StockRepository] = None):
        """Initialize the service.
        
        Args:
            portfolio_repository: Portfolio repository instance (if None, create new instance)
            stock_repository: Stock repository instance (if None, create new instance)
        """
        super().__init__()
        self.portfolio_repository = portfolio_repository or PortfolioRepository()
        self.stock_repository = stock_repository or StockRepository()
    
    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """Get a portfolio by ID.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Portfolio domain entity if found, None otherwise
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_portfolio", portfolio_id=portfolio_id)
            return self.portfolio_repository.get_by_id(portfolio_id)
        except Exception as e:
            self._handle_error("get_portfolio", e, portfolio_id=portfolio_id)
    
    def get_portfolio_or_raise(self, portfolio_id: str) -> Portfolio:
        """Get a portfolio by ID or raise an exception if not found.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Portfolio domain entity
            
        Raises:
            DataNotFoundError: If the portfolio is not found
            ServiceError: If an error occurs during retrieval
        """
        portfolio = self.get_portfolio(portfolio_id)
        if portfolio is None:
            raise DataNotFoundError(f"Portfolio with ID {portfolio_id} not found")
        return portfolio
    
    def get_portfolios_by_owner(self, owner_id: str, limit: int = 10, offset: int = 0) -> List[Portfolio]:
        """Get portfolios by owner ID.
        
        Args:
            owner_id: Owner user ID
            limit: Maximum number of portfolios to return
            offset: Number of portfolios to skip
            
        Returns:
            List of Portfolio domain entities owned by the specified user
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_portfolios_by_owner", owner_id=owner_id, limit=limit, offset=offset)
            return self.portfolio_repository.get_by_owner(owner_id, limit, offset)
        except Exception as e:
            self._handle_error("get_portfolios_by_owner", e, owner_id=owner_id, limit=limit, offset=offset)
    
    def create_portfolio(self, portfolio: Portfolio) -> Portfolio:
        """Create a new portfolio.
        
        Args:
            portfolio: Portfolio domain entity to create
            
        Returns:
            Created Portfolio domain entity
            
        Raises:
            ServiceError: If an error occurs during creation
        """
        try:
            # Ensure portfolio has an ID
            if not portfolio.id:
                portfolio.id = str(uuid.uuid4())
            
            self._log_operation("create_portfolio", portfolio_id=portfolio.id, name=portfolio.name)
            return self.portfolio_repository.create(portfolio)
        except Exception as e:
            self._handle_error("create_portfolio", e, portfolio_id=portfolio.id, name=portfolio.name)
    
    def update_portfolio(self, portfolio: Portfolio) -> Portfolio:
        """Update an existing portfolio.
        
        Args:
            portfolio: Portfolio domain entity to update
            
        Returns:
            Updated Portfolio domain entity
            
        Raises:
            DataNotFoundError: If the portfolio is not found
            ServiceError: If an error occurs during update
        """
        try:
            # Check if portfolio exists
            existing_portfolio = self.get_portfolio(portfolio.id)
            if existing_portfolio is None:
                raise DataNotFoundError(f"Portfolio with ID {portfolio.id} not found")
            
            self._log_operation("update_portfolio", portfolio_id=portfolio.id, name=portfolio.name)
            return self.portfolio_repository.update(portfolio)
        except Exception as e:
            self._handle_error("update_portfolio", e, portfolio_id=portfolio.id, name=portfolio.name)
    
    def delete_portfolio(self, portfolio_id: str) -> bool:
        """Delete a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            True if the portfolio was deleted, False otherwise
            
        Raises:
            ServiceError: If an error occurs during deletion
        """
        try:
            self._log_operation("delete_portfolio", portfolio_id=portfolio_id)
            return self.portfolio_repository.delete(portfolio_id)
        except Exception as e:
            self._handle_error("delete_portfolio", e, portfolio_id=portfolio_id)
    
    def add_position(self, portfolio_id: str, position: Position) -> Portfolio:
        """Add or update a position in a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            position: Position to add or update
            
        Returns:
            Updated Portfolio domain entity
            
        Raises:
            DataNotFoundError: If the portfolio or stock is not found
            ServiceError: If an error occurs during the operation
        """
        try:
            # Check if stock exists
            stock = self.stock_repository.get_by_symbol(position.symbol)
            if stock is None:
                raise DataNotFoundError(f"Stock with symbol {position.symbol} not found")
            
            self._log_operation(
                "add_position", 
                portfolio_id=portfolio_id, 
                symbol=position.symbol,
                quantity=position.quantity
            )
            return self.portfolio_repository.add_position(portfolio_id, position)
        except Exception as e:
            self._handle_error(
                "add_position", 
                e, 
                portfolio_id=portfolio_id, 
                symbol=position.symbol,
                quantity=position.quantity
            )
    
    def remove_position(self, portfolio_id: str, symbol: str) -> Portfolio:
        """Remove a position from a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol of the position to remove
            
        Returns:
            Updated Portfolio domain entity
            
        Raises:
            DataNotFoundError: If the portfolio or position is not found
            ServiceError: If an error occurs during the operation
        """
        try:
            self._log_operation("remove_position", portfolio_id=portfolio_id, symbol=symbol)
            return self.portfolio_repository.remove_position(portfolio_id, symbol)
        except Exception as e:
            self._handle_error("remove_position", e, portfolio_id=portfolio_id, symbol=symbol)
    
    def add_transaction(self, portfolio_id: str, transaction: Transaction) -> Portfolio:
        """Add a transaction to a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            transaction: Transaction to add
            
        Returns:
            Updated Portfolio domain entity
            
        Raises:
            DataNotFoundError: If the portfolio is not found
            ServiceError: If an error occurs during the operation
        """
        try:
            # Ensure transaction has an ID
            if not transaction.id:
                transaction.id = str(uuid.uuid4())
            
            # For buy/sell transactions, check if stock exists
            if transaction.type in [TransactionType.BUY, TransactionType.SELL] and transaction.symbol:
                stock = self.stock_repository.get_by_symbol(transaction.symbol)
                if stock is None:
                    raise DataNotFoundError(f"Stock with symbol {transaction.symbol} not found")
            
            self._log_operation(
                "add_transaction", 
                portfolio_id=portfolio_id, 
                transaction_id=transaction.id,
                transaction_type=transaction.type.value,
                symbol=transaction.symbol,
                amount=transaction.amount
            )
            return self.portfolio_repository.add_transaction(portfolio_id, transaction)
        except Exception as e:
            self._handle_error(
                "add_transaction", 
                e, 
                portfolio_id=portfolio_id, 
                transaction_id=transaction.id if transaction.id else None,
                transaction_type=transaction.type.value,
                symbol=transaction.symbol,
                amount=transaction.amount
            )
    
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
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_transactions", portfolio_id=portfolio_id, limit=limit, offset=offset)
            return self.portfolio_repository.get_transactions(portfolio_id, limit, offset)
        except Exception as e:
            self._handle_error("get_transactions", e, portfolio_id=portfolio_id, limit=limit, offset=offset)
    
    def get_positions(self, portfolio_id: str) -> Dict[str, Position]:
        """Get positions for a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Dictionary of positions keyed by symbol
            
        Raises:
            DataNotFoundError: If the portfolio is not found
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_positions", portfolio_id=portfolio_id)
            return self.portfolio_repository.get_positions(portfolio_id)
        except Exception as e:
            self._handle_error("get_positions", e, portfolio_id=portfolio_id)
    
    def calculate_portfolio_value(self, portfolio_id: str) -> float:
        """Calculate the current value of a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Current value of the portfolio (cash + positions)
            
        Raises:
            DataNotFoundError: If the portfolio is not found
            ServiceError: If an error occurs during calculation
        """
        try:
            # Get portfolio
            portfolio = self.get_portfolio_or_raise(portfolio_id)
            
            # Get positions
            positions = self.get_positions(portfolio_id)
            
            # Start with cash balance
            total_value = portfolio.cash_balance
            
            # Add value of each position
            for symbol, position in positions.items():
                # Get latest price
                latest_price = self.stock_repository.get_latest_price(symbol)
                if latest_price:
                    position_value = position.quantity * latest_price.close
                    total_value += position_value
            
            self._log_operation("calculate_portfolio_value", portfolio_id=portfolio_id, value=total_value)
            return total_value
        except Exception as e:
            self._handle_error("calculate_portfolio_value", e, portfolio_id=portfolio_id)
    
    def calculate_portfolio_performance(self, portfolio_id: str, days: int = 30) -> Dict[str, Any]:
        """Calculate the performance of a portfolio over a period.
        
        Args:
            portfolio_id: Portfolio ID
            days: Number of days to calculate performance for
            
        Returns:
            Dictionary containing performance metrics
            
        Raises:
            DataNotFoundError: If the portfolio is not found
            ServiceError: If an error occurs during calculation
        """
        try:
            # Get portfolio
            portfolio = self.get_portfolio_or_raise(portfolio_id)
            
            # Get positions
            positions = self.get_positions(portfolio_id)
            
            # Calculate current value
            current_value = self.calculate_portfolio_value(portfolio_id)
            
            # Get transactions within the period
            end_date = datetime.now()
            start_date = end_date - datetime.timedelta(days=days)
            
            # Get all transactions
            transactions = self.get_transactions(portfolio_id)
            
            # Filter transactions by date
            period_transactions = [tx for tx in transactions if tx.date >= start_date]
            
            # Calculate deposits and withdrawals during the period
            deposits = sum(tx.amount for tx in period_transactions if tx.type == TransactionType.DEPOSIT)
            withdrawals = sum(tx.amount for tx in period_transactions if tx.type == TransactionType.WITHDRAWAL)
            
            # Calculate net flow
            net_flow = deposits - withdrawals
            
            # Calculate performance
            # This is a simplified calculation and would need to be enhanced for a real application
            # to account for the timing of cash flows
            performance = {}
            
            # If we have transactions older than the period, we can calculate performance
            if any(tx.date < start_date for tx in transactions):
                # Calculate value at the start of the period
                # This is a placeholder for a more sophisticated calculation
                # In a real application, you would need historical prices and positions
                start_value = current_value - net_flow
                
                # Calculate return
                if start_value > 0:
                    period_return = (current_value - start_value - net_flow) / start_value * 100
                    performance["period_return_pct"] = period_return
            
            # Add other metrics
            performance["current_value"] = current_value
            performance["cash_balance"] = portfolio.cash_balance
            performance["position_value"] = current_value - portfolio.cash_balance
            performance["position_count"] = len(positions)
            performance["period_days"] = days
            performance["period_deposits"] = deposits
            performance["period_withdrawals"] = withdrawals
            
            self._log_operation("calculate_portfolio_performance", portfolio_id=portfolio_id, days=days)
            return performance
        except Exception as e:
            self._handle_error("calculate_portfolio_performance", e, portfolio_id=portfolio_id, days=days)
