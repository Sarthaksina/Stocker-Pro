"""Strategy service implementation for STOCKER Pro.

This module provides a service implementation for strategy-related business logic,
coordinating between domain models and repositories.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import uuid

from stocker.core.exceptions import ServiceError, DataNotFoundError
from stocker.domain.strategy import Strategy, StrategyType, StrategyParameters, Signal, SignalType
from stocker.domain.stock import Stock, StockPrice, StockData
from stocker.infrastructure.database.repositories.strategy import StrategyRepository
from stocker.infrastructure.database.repositories.stock import StockRepository
from stocker.services.base import BaseService


class StrategyService(BaseService):
    """Service for strategy-related business logic.
    
    This service coordinates between domain models and repositories to provide
    strategy-related functionality.
    """
    
    def __init__(self, strategy_repository: Optional[StrategyRepository] = None,
                 stock_repository: Optional[StockRepository] = None):
        """Initialize the service.
        
        Args:
            strategy_repository: Strategy repository instance (if None, create new instance)
            stock_repository: Stock repository instance (if None, create new instance)
        """
        super().__init__()
        self.strategy_repository = strategy_repository or StrategyRepository()
        self.stock_repository = stock_repository or StockRepository()
    
    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """Get a strategy by ID.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Strategy domain entity if found, None otherwise
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_strategy", strategy_id=strategy_id)
            return self.strategy_repository.get_by_id(strategy_id)
        except Exception as e:
            self._handle_error("get_strategy", e, strategy_id=strategy_id)
    
    def get_strategy_or_raise(self, strategy_id: str) -> Strategy:
        """Get a strategy by ID or raise an exception if not found.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Strategy domain entity
            
        Raises:
            DataNotFoundError: If the strategy is not found
            ServiceError: If an error occurs during retrieval
        """
        strategy = self.get_strategy(strategy_id)
        if strategy is None:
            raise DataNotFoundError(f"Strategy with ID {strategy_id} not found")
        return strategy
    
    def get_strategies_by_owner(self, owner_id: str, limit: int = 10, offset: int = 0) -> List[Strategy]:
        """Get strategies by owner ID.
        
        Args:
            owner_id: Owner user ID
            limit: Maximum number of strategies to return
            offset: Number of strategies to skip
            
        Returns:
            List of Strategy domain entities owned by the specified user
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_strategies_by_owner", owner_id=owner_id, limit=limit, offset=offset)
            return self.strategy_repository.get_by_owner(owner_id, limit, offset)
        except Exception as e:
            self._handle_error("get_strategies_by_owner", e, owner_id=owner_id, limit=limit, offset=offset)
    
    def get_strategies_by_type(self, strategy_type: StrategyType, limit: int = 10, offset: int = 0) -> List[Strategy]:
        """Get strategies by type.
        
        Args:
            strategy_type: Strategy type to filter by
            limit: Maximum number of strategies to return
            offset: Number of strategies to skip
            
        Returns:
            List of Strategy domain entities of the specified type
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_strategies_by_type", strategy_type=strategy_type.value, limit=limit, offset=offset)
            return self.strategy_repository.get_by_type(strategy_type, limit, offset)
        except Exception as e:
            self._handle_error("get_strategies_by_type", e, strategy_type=strategy_type.value, limit=limit, offset=offset)
    
    def get_active_strategies(self, limit: int = 10, offset: int = 0) -> List[Strategy]:
        """Get active strategies.
        
        Args:
            limit: Maximum number of strategies to return
            offset: Number of strategies to skip
            
        Returns:
            List of active Strategy domain entities
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_active_strategies", limit=limit, offset=offset)
            return self.strategy_repository.get_active_strategies(limit, offset)
        except Exception as e:
            self._handle_error("get_active_strategies", e, limit=limit, offset=offset)
    
    def create_strategy(self, strategy: Strategy) -> Strategy:
        """Create a new strategy.
        
        Args:
            strategy: Strategy domain entity to create
            
        Returns:
            Created Strategy domain entity
            
        Raises:
            ServiceError: If an error occurs during creation
        """
        try:
            # Ensure strategy has an ID
            if not strategy.id:
                strategy.id = str(uuid.uuid4())
            
            # Set created_at and updated_at if not set
            if not strategy.created_at:
                strategy.created_at = datetime.now()
            if not strategy.updated_at:
                strategy.updated_at = datetime.now()
            
            self._log_operation("create_strategy", strategy_id=strategy.id, name=strategy.name, type=strategy.type.value)
            return self.strategy_repository.create(strategy)
        except Exception as e:
            self._handle_error("create_strategy", e, strategy_id=strategy.id, name=strategy.name, type=strategy.type.value)
    
    def update_strategy(self, strategy: Strategy) -> Strategy:
        """Update an existing strategy.
        
        Args:
            strategy: Strategy domain entity to update
            
        Returns:
            Updated Strategy domain entity
            
        Raises:
            DataNotFoundError: If the strategy is not found
            ServiceError: If an error occurs during update
        """
        try:
            # Check if strategy exists
            existing_strategy = self.get_strategy(strategy.id)
            if existing_strategy is None:
                raise DataNotFoundError(f"Strategy with ID {strategy.id} not found")
            
            # Update updated_at timestamp
            strategy.updated_at = datetime.now()
            
            self._log_operation("update_strategy", strategy_id=strategy.id, name=strategy.name, type=strategy.type.value)
            return self.strategy_repository.update(strategy)
        except Exception as e:
            self._handle_error("update_strategy", e, strategy_id=strategy.id, name=strategy.name, type=strategy.type.value)
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """Delete a strategy.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            True if the strategy was deleted, False otherwise
            
        Raises:
            ServiceError: If an error occurs during deletion
        """
        try:
            self._log_operation("delete_strategy", strategy_id=strategy_id)
            return self.strategy_repository.delete(strategy_id)
        except Exception as e:
            self._handle_error("delete_strategy", e, strategy_id=strategy_id)
    
    def add_signal(self, strategy_id: str, signal: Signal) -> Signal:
        """Add a signal for a strategy.
        
        Args:
            strategy_id: Strategy ID
            signal: Signal to add
            
        Returns:
            Added Signal domain entity
            
        Raises:
            DataNotFoundError: If the strategy or stock is not found
            ServiceError: If an error occurs during the operation
        """
        try:
            # Check if strategy exists
            strategy = self.get_strategy_or_raise(strategy_id)
            
            # Check if stock exists
            stock = self.stock_repository.get_by_symbol(signal.symbol)
            if stock is None:
                raise DataNotFoundError(f"Stock with symbol {signal.symbol} not found")
            
            # Ensure signal has an ID and strategy_id
            if not signal.id:
                signal.id = str(uuid.uuid4())
            signal.strategy_id = strategy_id
            
            # Set date if not set
            if not signal.date:
                signal.date = datetime.now()
            
            self._log_operation(
                "add_signal", 
                strategy_id=strategy_id, 
                signal_id=signal.id,
                symbol=signal.symbol,
                type=signal.type.value
            )
            return self.strategy_repository.add_signal(strategy_id, signal)
        except Exception as e:
            self._handle_error(
                "add_signal", 
                e, 
                strategy_id=strategy_id, 
                signal_id=signal.id if signal.id else None,
                symbol=signal.symbol,
                type=signal.type.value
            )
    
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
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_signals", strategy_id=strategy_id, limit=limit, offset=offset)
            return self.strategy_repository.get_signals(strategy_id, limit, offset)
        except Exception as e:
            self._handle_error("get_signals", e, strategy_id=strategy_id, limit=limit, offset=offset)
    
    def get_signals_by_symbol(self, symbol: str, limit: int = 50, offset: int = 0) -> List[Signal]:
        """Get signals for a specific symbol across all strategies.
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of signals to return
            offset: Number of signals to skip
            
        Returns:
            List of Signal domain entities for the specified symbol
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_signals_by_symbol", symbol=symbol, limit=limit, offset=offset)
            return self.strategy_repository.get_signals_by_symbol(symbol, limit, offset)
        except Exception as e:
            self._handle_error("get_signals_by_symbol", e, symbol=symbol, limit=limit, offset=offset)
    
    def get_recent_signals(self, days: int = 7, limit: int = 50) -> List[Signal]:
        """Get recent signals across all strategies.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of signals to return
            
        Returns:
            List of recent Signal domain entities
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_recent_signals", days=days, limit=limit)
            return self.strategy_repository.get_recent_signals(days, limit)
        except Exception as e:
            self._handle_error("get_recent_signals", e, days=days, limit=limit)
    
    def get_signals_by_type(self, signal_type: SignalType, limit: int = 50, offset: int = 0) -> List[Signal]:
        """Get signals by type across all strategies.
        
        Args:
            signal_type: Signal type to filter by
            limit: Maximum number of signals to return
            offset: Number of signals to skip
            
        Returns:
            List of Signal domain entities of the specified type
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_signals_by_type", signal_type=signal_type.value, limit=limit, offset=offset)
            return self.strategy_repository.get_signals_by_type(signal_type, limit, offset)
        except Exception as e:
            self._handle_error("get_signals_by_type", e, signal_type=signal_type.value, limit=limit, offset=offset)
    
    def run_strategy(self, strategy_id: str, symbols: Optional[List[str]] = None, 
                    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Signal]:
        """Run a strategy to generate signals.
        
        Args:
            strategy_id: Strategy ID
            symbols: List of stock symbols to run the strategy on (if None, use strategy parameters)
            start_date: Start date for historical data (if None, use recent data)
            end_date: End date for historical data (if None, use current date)
            
        Returns:
            List of generated Signal domain entities
            
        Raises:
            DataNotFoundError: If the strategy or any stock is not found
            ServiceError: If an error occurs during execution
        """
        try:
            # Get strategy
            strategy = self.get_strategy_or_raise(strategy_id)
            
            # Set default dates if not provided
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                # Use lookback period from strategy parameters or default to 30 days
                lookback_days = 30
                if hasattr(strategy.parameters, "lookback_period"):
                    lookback_days = strategy.parameters.lookback_period
                start_date = end_date - timedelta(days=lookback_days)
            
            # Use symbols from parameters if not provided
            if symbols is None and hasattr(strategy.parameters, "symbols"):
                symbols = strategy.parameters.symbols
            
            # Ensure we have symbols to work with
            if not symbols:
                raise ServiceError("No symbols provided for strategy execution")
            
            # Get stock data for each symbol
            stock_data_dict = {}
            for symbol in symbols:
                # Check if stock exists
                stock = self.stock_repository.get_by_symbol(symbol)
                if stock is None:
                    raise DataNotFoundError(f"Stock with symbol {symbol} not found")
                
                # Get price data
                prices = self.stock_repository.get_price_data(symbol, start_date, end_date)
                
                # Create stock data
                stock_data = StockData(
                    symbol=symbol,
                    prices=prices,
                    timeframe="1d"  # Default timeframe
                )
                
                stock_data_dict[symbol] = stock_data
            
            # Execute strategy based on type
            signals = []
            
            # Import specific strategy execution functions based on type
            if strategy.type == StrategyType.MOMENTUM:
                from stocker.domain.strategy.momentum import execute_momentum_strategy
                signals = execute_momentum_strategy(strategy, stock_data_dict)
            elif strategy.type == StrategyType.MEAN_REVERSION:
                from stocker.domain.strategy.mean_reversion import execute_mean_reversion_strategy
                signals = execute_mean_reversion_strategy(strategy, stock_data_dict)
            else:
                # For custom strategies, execute the strategy's run method
                if hasattr(strategy, "run") and callable(getattr(strategy, "run")):
                    signals = strategy.run(stock_data_dict)
                else:
                    raise ServiceError(f"Strategy type {strategy.type.value} is not supported for execution")
            
            # Save signals to database
            saved_signals = []
            for signal in signals:
                # Set strategy ID and ensure signal has an ID
                signal.strategy_id = strategy_id
                if not signal.id:
                    signal.id = str(uuid.uuid4())
                
                # Save signal
                saved_signal = self.strategy_repository.add_signal(strategy_id, signal)
                saved_signals.append(saved_signal)
            
            # Update strategy performance metrics
            self.update_strategy_performance(strategy_id)
            
            self._log_operation(
                "run_strategy", 
                strategy_id=strategy_id, 
                symbol_count=len(symbols),
                signal_count=len(saved_signals)
            )
            return saved_signals
        except Exception as e:
            self._handle_error(
                "run_strategy", 
                e, 
                strategy_id=strategy_id, 
                symbol_count=len(symbols) if symbols else 0
            )
    
    def update_strategy_performance(self, strategy_id: str) -> Strategy:
        """Update performance metrics for a strategy.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Updated Strategy domain entity
            
        Raises:
            DataNotFoundError: If the strategy is not found
            ServiceError: If an error occurs during the operation
        """
        try:
            # Get strategy
            strategy = self.get_strategy_or_raise(strategy_id)
            
            # Get signals
            signals = self.strategy_repository.get_signals(strategy_id)
            
            # Calculate performance metrics
            metrics = self._calculate_strategy_performance(strategy, signals)
            
            self._log_operation("update_strategy_performance", strategy_id=strategy_id)
            return self.strategy_repository.update_strategy_performance(strategy_id, metrics)
        except Exception as e:
            self._handle_error("update_strategy_performance", e, strategy_id=strategy_id)
    
    def _calculate_strategy_performance(self, strategy: Strategy, signals: List[Signal]) -> Dict[str, Any]:
        """Calculate performance metrics for a strategy.
        
        Args:
            strategy: Strategy domain entity
            signals: List of signals for the strategy
            
        Returns:
            Dictionary containing performance metrics
        """
        # This is a simplified implementation
        # In a real application, you would need to calculate more sophisticated metrics
        
        # Initialize metrics
        metrics = {
            "signal_count": len(signals),
            "last_run": datetime.now().isoformat(),
            "symbols": set(),
            "buy_signals": 0,
            "sell_signals": 0,
            "neutral_signals": 0
        }
        
        # Calculate metrics
        for signal in signals:
            metrics["symbols"].add(signal.symbol)
            
            if signal.type == SignalType.BUY:
                metrics["buy_signals"] += 1
            elif signal.type == SignalType.SELL:
                metrics["sell_signals"] += 1
            else:
                metrics["neutral_signals"] += 1
        
        # Convert set to list for JSON serialization
        metrics["symbols"] = list(metrics["symbols"])
        metrics["symbol_count"] = len(metrics["symbols"])
        
        return metrics
