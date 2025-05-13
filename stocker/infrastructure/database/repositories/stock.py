"""Stock repository implementation for STOCKER Pro.

This module provides a repository implementation for stock-related database operations,
following the repository pattern to abstract database access.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import select, and_, desc, func
from sqlalchemy.exc import SQLAlchemyError

from stocker.core.exceptions import DataError, DataNotFoundError
from stocker.core.logging import get_logger
from stocker.domain.stock import Stock, StockPrice, StockData, Exchange, Sector
from stocker.infrastructure.database.models.stock import StockModel, StockPriceModel
from stocker.infrastructure.database.repositories.base import BaseRepository
from stocker.infrastructure.database.session import get_session

# Logger
logger = get_logger(__name__)


class StockRepository(BaseRepository[StockModel, Stock]):
    """Repository for stock-related database operations.
    
    This class implements the repository pattern for stock-related database operations,
    providing methods for CRUD operations and stock-specific queries.
    """
    def __init__(self):
        """Initialize the repository."""
        super().__init__(StockModel)
    
    def _to_model(self, entity: Stock) -> StockModel:
        """Convert a domain entity to a database model.
        
        Args:
            entity: Stock domain entity
            
        Returns:
            StockModel database model
        """
        return StockModel.from_domain(entity)
    
    def _to_entity(self, model: StockModel) -> Stock:
        """Convert a database model to a domain entity.
        
        Args:
            model: StockModel database model
            
        Returns:
            Stock domain entity
        """
        return model.to_domain()
    
    def get_by_symbol(self, symbol: str, include_prices: bool = False) -> Optional[Stock]:
        """Get a stock by symbol.
        
        Args:
            symbol: Stock symbol
            include_prices: Whether to include price data
            
        Returns:
            Stock domain entity if found, None otherwise
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                if include_prices:
                    # Load the stock with its prices
                    stock_model = session.get(StockModel, symbol)
                    if stock_model is None:
                        return None
                    return stock_model.to_domain(include_prices=True)
                else:
                    # Load just the stock without prices
                    stock_model = session.get(StockModel, symbol)
                    if stock_model is None:
                        return None
                    return self._to_entity(stock_model)
        except SQLAlchemyError as e:
            logger.error(f"Error getting stock by symbol {symbol}: {str(e)}")
            raise DataError(f"Error getting stock by symbol {symbol}: {str(e)}")
    
    def get_stocks_by_exchange(self, exchange: Exchange, limit: int = 100, offset: int = 0) -> List[Stock]:
        """Get stocks by exchange.
        
        Args:
            exchange: Exchange to filter by
            limit: Maximum number of stocks to return
            offset: Number of stocks to skip
            
        Returns:
            List of Stock domain entities in the specified exchange
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                query = select(StockModel).where(
                    StockModel.exchange == exchange.value
                ).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [self._to_entity(result) for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting stocks by exchange {exchange.value}: {str(e)}")
            raise DataError(f"Error getting stocks by exchange: {str(e)}")
    
    def get_stocks_by_sector(self, sector: Sector, limit: int = 100, offset: int = 0) -> List[Stock]:
        """Get stocks by sector.
        
        Args:
            sector: Sector to filter by
            limit: Maximum number of stocks to return
            offset: Number of stocks to skip
            
        Returns:
            List of Stock domain entities in the specified sector
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                query = select(StockModel).where(
                    StockModel.sector == sector.value
                ).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [self._to_entity(result) for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting stocks by sector {sector.value}: {str(e)}")
            raise DataError(f"Error getting stocks by sector: {str(e)}")
    
    def search_stocks(self, search_term: str, limit: int = 10, offset: int = 0) -> List[Stock]:
        """Search for stocks by symbol or name.
        
        Args:
            search_term: Search term
            limit: Maximum number of stocks to return
            offset: Number of stocks to skip
            
        Returns:
            List of matching Stock domain entities
            
        Raises:
            DataError: If an error occurs during search
        """
        try:
            with get_session() as session:
                # Create search pattern for LIKE queries
                pattern = f"%{search_term}%"
                
                # Build query with OR conditions for different fields
                query = select(StockModel).where(
                    StockModel.symbol.ilike(pattern) | 
                    StockModel.name.ilike(pattern)
                ).offset(offset).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                return [self._to_entity(result) for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error searching stocks with term '{search_term}': {str(e)}")
            raise DataError(f"Error searching stocks: {str(e)}")
    
    def add_price_data(self, symbol: str, prices: List[StockPrice]) -> bool:
        """Add price data for a stock.
        
        Args:
            symbol: Stock symbol
            prices: List of price data points
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            DataNotFoundError: If the stock is not found
            DataError: If an error occurs during the operation
        """
        try:
            with get_session() as session:
                # Check if stock exists
                stock_model = session.get(StockModel, symbol)
                if stock_model is None:
                    raise DataNotFoundError(f"Stock with symbol {symbol} not found")
                
                # Create price models
                price_models = [StockPriceModel.from_domain(price, symbol) for price in prices]
                
                # Add prices to database
                session.add_all(price_models)
                session.commit()
                
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error adding price data for stock {symbol}: {str(e)}")
            raise DataError(f"Error adding price data: {str(e)}")
    
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
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                # Check if stock exists
                stock_model = session.get(StockModel, symbol)
                if stock_model is None:
                    raise DataNotFoundError(f"Stock with symbol {symbol} not found")
                
                # Build query with date filters
                query = select(StockPriceModel).where(StockPriceModel.symbol == symbol)
                
                if start_date:
                    query = query.where(StockPriceModel.date >= start_date)
                
                if end_date:
                    query = query.where(StockPriceModel.date <= end_date)
                
                # Order by date descending and limit results
                query = query.order_by(desc(StockPriceModel.date)).limit(limit)
                
                results = session.execute(query).scalars().all()
                
                # Convert to domain entities
                return [result.to_domain() for result in results]
        except SQLAlchemyError as e:
            logger.error(f"Error getting price data for stock {symbol}: {str(e)}")
            raise DataError(f"Error getting price data: {str(e)}")
    
    def get_latest_price(self, symbol: str) -> Optional[StockPrice]:
        """Get the latest price for a stock.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest StockPrice domain entity if available, None otherwise
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                query = select(StockPriceModel).where(
                    StockPriceModel.symbol == symbol
                ).order_by(desc(StockPriceModel.date)).limit(1)
                
                result = session.execute(query).scalar_one_or_none()
                
                if result is None:
                    return None
                
                return result.to_domain()
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest price for stock {symbol}: {str(e)}")
            raise DataError(f"Error getting latest price: {str(e)}")
    
    def get_top_gainers(self, limit: int = 10) -> List[Tuple[Stock, float]]:
        """Get the top gaining stocks for the day.
        
        Args:
            limit: Maximum number of stocks to return
            
        Returns:
            List of tuples containing Stock domain entities and their percentage gain
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                # Get today's date and yesterday's date
                today = datetime.now().date()
                yesterday = today - timedelta(days=1)
                
                # This is a complex query that requires joining the stocks and prices tables
                # and calculating the percentage change between yesterday and today
                # For simplicity, we'll implement a basic version here
                
                # Get stocks with price data for today
                stocks_with_prices = session.execute(
                    select(StockModel, StockPriceModel.close, StockPriceModel.open)
                    .join(StockPriceModel, StockModel.symbol == StockPriceModel.symbol)
                    .where(func.date(StockPriceModel.date) == today)
                    .order_by(desc((StockPriceModel.close - StockPriceModel.open) / StockPriceModel.open))
                    .limit(limit)
                ).all()
                
                result = []
                for stock, close, open_price in stocks_with_prices:
                    # Calculate percentage gain
                    gain = (close - open_price) / open_price * 100 if open_price > 0 else 0
                    result.append((self._to_entity(stock), gain))
                
                return result
        except SQLAlchemyError as e:
            logger.error(f"Error getting top gainers: {str(e)}")
            raise DataError(f"Error getting top gainers: {str(e)}")
    
    def get_top_losers(self, limit: int = 10) -> List[Tuple[Stock, float]]:
        """Get the top losing stocks for the day.
        
        Args:
            limit: Maximum number of stocks to return
            
        Returns:
            List of tuples containing Stock domain entities and their percentage loss
            
        Raises:
            DataError: If an error occurs during retrieval
        """
        try:
            with get_session() as session:
                # Get today's date and yesterday's date
                today = datetime.now().date()
                yesterday = today - timedelta(days=1)
                
                # Similar to get_top_gainers but with reversed ordering
                stocks_with_prices = session.execute(
                    select(StockModel, StockPriceModel.close, StockPriceModel.open)
                    .join(StockPriceModel, StockModel.symbol == StockPriceModel.symbol)
                    .where(func.date(StockPriceModel.date) == today)
                    .order_by((StockPriceModel.close - StockPriceModel.open) / StockPriceModel.open)
                    .limit(limit)
                ).all()
                
                result = []
                for stock, close, open_price in stocks_with_prices:
                    # Calculate percentage loss
                    loss = (open_price - close) / open_price * 100 if open_price > 0 else 0
                    result.append((self._to_entity(stock), loss))
                
                return result
        except SQLAlchemyError as e:
            logger.error(f"Error getting top losers: {str(e)}")
            raise DataError(f"Error getting top losers: {str(e)}")
