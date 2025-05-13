"""Stock service implementation for STOCKER Pro.

This module provides a service implementation for stock-related business logic,
coordinating between domain models and repositories.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from stocker.core.exceptions import ServiceError, DataNotFoundError
from stocker.domain.stock import Stock, StockPrice, StockData, Exchange, Sector
from stocker.infrastructure.database.repositories.stock import StockRepository
from stocker.services.base import BaseService


class StockService(BaseService):
    """Service for stock-related business logic.
    
    This service coordinates between domain models and repositories to provide
    stock-related functionality.
    """
    
    def __init__(self, stock_repository: Optional[StockRepository] = None):
        """Initialize the service.
        
        Args:
            stock_repository: Stock repository instance (if None, create new instance)
        """
        super().__init__()
        self.stock_repository = stock_repository or StockRepository()
    
    def get_stock(self, symbol: str, include_prices: bool = False) -> Optional[Stock]:
        """Get a stock by symbol.
        
        Args:
            symbol: Stock symbol
            include_prices: Whether to include price data
            
        Returns:
            Stock domain entity if found, None otherwise
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_stock", symbol=symbol, include_prices=include_prices)
            return self.stock_repository.get_by_symbol(symbol, include_prices)
        except Exception as e:
            self._handle_error("get_stock", e, symbol=symbol, include_prices=include_prices)
    
    def get_stock_or_raise(self, symbol: str, include_prices: bool = False) -> Stock:
        """Get a stock by symbol or raise an exception if not found.
        
        Args:
            symbol: Stock symbol
            include_prices: Whether to include price data
            
        Returns:
            Stock domain entity
            
        Raises:
            DataNotFoundError: If the stock is not found
            ServiceError: If an error occurs during retrieval
        """
        stock = self.get_stock(symbol, include_prices)
        if stock is None:
            raise DataNotFoundError(f"Stock with symbol {symbol} not found")
        return stock
    
    def create_stock(self, stock: Stock) -> Stock:
        """Create a new stock.
        
        Args:
            stock: Stock domain entity to create
            
        Returns:
            Created Stock domain entity
            
        Raises:
            ServiceError: If an error occurs during creation
        """
        try:
            self._log_operation("create_stock", symbol=stock.symbol, name=stock.name)
            return self.stock_repository.create(stock)
        except Exception as e:
            self._handle_error("create_stock", e, symbol=stock.symbol, name=stock.name)
    
    def update_stock(self, stock: Stock) -> Stock:
        """Update an existing stock.
        
        Args:
            stock: Stock domain entity to update
            
        Returns:
            Updated Stock domain entity
            
        Raises:
            DataNotFoundError: If the stock is not found
            ServiceError: If an error occurs during update
        """
        try:
            # Check if stock exists
            existing_stock = self.get_stock(stock.symbol)
            if existing_stock is None:
                raise DataNotFoundError(f"Stock with symbol {stock.symbol} not found")
            
            self._log_operation("update_stock", symbol=stock.symbol, name=stock.name)
            return self.stock_repository.update(stock)
        except Exception as e:
            self._handle_error("update_stock", e, symbol=stock.symbol, name=stock.name)
    
    def delete_stock(self, symbol: str) -> bool:
        """Delete a stock.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if the stock was deleted, False otherwise
            
        Raises:
            ServiceError: If an error occurs during deletion
        """
        try:
            self._log_operation("delete_stock", symbol=symbol)
            return self.stock_repository.delete(symbol)
        except Exception as e:
            self._handle_error("delete_stock", e, symbol=symbol)
    
    def search_stocks(self, query: str, limit: int = 10, offset: int = 0) -> List[Stock]:
        """Search for stocks by symbol or name.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of matching Stock domain entities
            
        Raises:
            ServiceError: If an error occurs during search
        """
        try:
            self._log_operation("search_stocks", query=query, limit=limit, offset=offset)
            return self.stock_repository.search_stocks(query, limit, offset)
        except Exception as e:
            self._handle_error("search_stocks", e, query=query, limit=limit, offset=offset)
    
    def get_stocks_by_exchange(self, exchange: Exchange, limit: int = 100, offset: int = 0) -> List[Stock]:
        """Get stocks by exchange.
        
        Args:
            exchange: Exchange to filter by
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of Stock domain entities in the specified exchange
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_stocks_by_exchange", exchange=exchange.value, limit=limit, offset=offset)
            return self.stock_repository.get_stocks_by_exchange(exchange, limit, offset)
        except Exception as e:
            self._handle_error("get_stocks_by_exchange", e, exchange=exchange.value, limit=limit, offset=offset)
    
    def get_stocks_by_sector(self, sector: Sector, limit: int = 100, offset: int = 0) -> List[Stock]:
        """Get stocks by sector.
        
        Args:
            sector: Sector to filter by
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of Stock domain entities in the specified sector
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_stocks_by_sector", sector=sector.value, limit=limit, offset=offset)
            return self.stock_repository.get_stocks_by_sector(sector, limit, offset)
        except Exception as e:
            self._handle_error("get_stocks_by_sector", e, sector=sector.value, limit=limit, offset=offset)
    
    def add_price_data(self, symbol: str, prices: List[StockPrice]) -> bool:
        """Add price data for a stock.
        
        Args:
            symbol: Stock symbol
            prices: List of price data points
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            DataNotFoundError: If the stock is not found
            ServiceError: If an error occurs during the operation
        """
        try:
            self._log_operation("add_price_data", symbol=symbol, price_count=len(prices))
            return self.stock_repository.add_price_data(symbol, prices)
        except Exception as e:
            self._handle_error("add_price_data", e, symbol=symbol, price_count=len(prices))
    
    def get_price_data(self, symbol: str, start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None, limit: int = 100) -> List[StockPrice]:
        """Get price data for a stock.
        
        Args:
            symbol: Stock symbol
            start_date: Start date for price data
            end_date: End date for price data
            limit: Maximum number of data points to return
            
        Returns:
            List of StockPrice domain entities
            
        Raises:
            DataNotFoundError: If the stock is not found
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation(
                "get_price_data", 
                symbol=symbol, 
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None,
                limit=limit
            )
            return self.stock_repository.get_price_data(symbol, start_date, end_date, limit)
        except Exception as e:
            self._handle_error(
                "get_price_data", 
                e, 
                symbol=symbol, 
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None,
                limit=limit
            )
    
    def get_latest_price(self, symbol: str) -> Optional[StockPrice]:
        """Get the latest price for a stock.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest StockPrice domain entity if available, None otherwise
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_latest_price", symbol=symbol)
            return self.stock_repository.get_latest_price(symbol)
        except Exception as e:
            self._handle_error("get_latest_price", e, symbol=symbol)
    
    def get_top_gainers(self, limit: int = 10) -> List[Tuple[Stock, float]]:
        """Get the top gaining stocks for the day.
        
        Args:
            limit: Maximum number of stocks to return
            
        Returns:
            List of tuples containing Stock domain entities and their percentage gain
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_top_gainers", limit=limit)
            return self.stock_repository.get_top_gainers(limit)
        except Exception as e:
            self._handle_error("get_top_gainers", e, limit=limit)
    
    def get_top_losers(self, limit: int = 10) -> List[Tuple[Stock, float]]:
        """Get the top losing stocks for the day.
        
        Args:
            limit: Maximum number of stocks to return
            
        Returns:
            List of tuples containing Stock domain entities and their percentage loss
            
        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            self._log_operation("get_top_losers", limit=limit)
            return self.stock_repository.get_top_losers(limit)
        except Exception as e:
            self._handle_error("get_top_losers", e, limit=limit)
    
    def get_stock_data(self, symbol: str, timeframe: str = "1d", 
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      limit: int = 100) -> StockData:
        """Get stock data for analysis.
        
        This method combines stock and price data into a StockData object
        suitable for analysis.
        
        Args:
            symbol: Stock symbol
            timeframe: Data timeframe (e.g., "1d", "1h")
            start_date: Start date for price data
            end_date: End date for price data
            limit: Maximum number of data points to return
            
        Returns:
            StockData domain entity
            
        Raises:
            DataNotFoundError: If the stock is not found
            ServiceError: If an error occurs during retrieval
        """
        try:
            # Get stock information
            stock = self.get_stock_or_raise(symbol)
            
            # Get price data
            prices = self.get_price_data(symbol, start_date, end_date, limit)
            
            # Create and return stock data
            self._log_operation(
                "get_stock_data", 
                symbol=symbol, 
                timeframe=timeframe,
                price_count=len(prices)
            )
            
            return StockData(
                symbol=symbol,
                prices=prices,
                timeframe=timeframe
            )
        except Exception as e:
            self._handle_error(
                "get_stock_data", 
                e, 
                symbol=symbol, 
                timeframe=timeframe,
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None,
                limit=limit
            )
