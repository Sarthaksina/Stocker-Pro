"""Tests for the stock service.

This module contains tests for the StockService class.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from stocker.core.exceptions import ServiceError, DataNotFoundError
from stocker.domain.stock import Stock, StockPrice, StockData, Exchange, Sector
from stocker.infrastructure.database.repositories.stock import StockRepository
from stocker.services.stock import StockService


@pytest.fixture
def mock_stock_repository():
    """Create a mock stock repository for testing."""
    return Mock(spec=StockRepository)


@pytest.fixture
def sample_stock():
    """Create a sample stock for testing."""
    return Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange=Exchange.NASDAQ,
        sector=Sector.TECHNOLOGY,
        industry="Consumer Electronics",
        market_cap=2500000000000.0,
        pe_ratio=30.5,
        dividend_yield=0.5,
        beta=1.2,
        description="Apple Inc. designs, manufactures, and markets smartphones."
    )


@pytest.fixture
def sample_stock_prices():
    """Create sample stock prices for testing."""
    today = datetime.now().date()
    return [
        StockPrice(
            date=datetime.combine(today - timedelta(days=2), datetime.min.time()),
            open=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
            volume=1000000,
            adjusted_close=153.0
        ),
        StockPrice(
            date=datetime.combine(today - timedelta(days=1), datetime.min.time()),
            open=153.0,
            high=160.0,
            low=152.0,
            close=158.0,
            volume=1200000,
            adjusted_close=158.0
        ),
        StockPrice(
            date=datetime.combine(today, datetime.min.time()),
            open=158.0,
            high=165.0,
            low=157.0,
            close=163.0,
            volume=1500000,
            adjusted_close=163.0
        )
    ]


class TestStockService:
    """Tests for the StockService class."""
    
    def test_get_stock(self, mock_stock_repository, sample_stock):
        """Test getting a stock by symbol."""
        # Configure mock repository
        mock_stock_repository.get_by_symbol.return_value = sample_stock
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Get stock
        stock = service.get_stock("AAPL")
        
        # Verify repository was called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with("AAPL", False)
        
        # Verify stock was returned
        assert stock is not None
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
    
    def test_get_stock_with_prices(self, mock_stock_repository, sample_stock):
        """Test getting a stock by symbol with price data."""
        # Configure mock repository
        mock_stock_repository.get_by_symbol.return_value = sample_stock
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Get stock with prices
        stock = service.get_stock("AAPL", include_prices=True)
        
        # Verify repository was called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with("AAPL", True)
        
        # Verify stock was returned
        assert stock is not None
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
    
    def test_get_stock_not_found(self, mock_stock_repository):
        """Test getting a non-existent stock by symbol."""
        # Configure mock repository
        mock_stock_repository.get_by_symbol.return_value = None
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Get non-existent stock
        stock = service.get_stock("NONEXISTENT")
        
        # Verify repository was called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with("NONEXISTENT", False)
        
        # Verify stock was not found
        assert stock is None
    
    def test_get_stock_or_raise(self, mock_stock_repository, sample_stock):
        """Test getting a stock by symbol or raising an exception."""
        # Configure mock repository
        mock_stock_repository.get_by_symbol.return_value = sample_stock
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Get stock
        stock = service.get_stock_or_raise("AAPL")
        
        # Verify repository was called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with("AAPL", False)
        
        # Verify stock was returned
        assert stock is not None
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
    
    def test_get_stock_or_raise_not_found(self, mock_stock_repository):
        """Test getting a non-existent stock by symbol or raising an exception."""
        # Configure mock repository
        mock_stock_repository.get_by_symbol.return_value = None
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Get non-existent stock
        with pytest.raises(DataNotFoundError):
            service.get_stock_or_raise("NONEXISTENT")
        
        # Verify repository was called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with("NONEXISTENT", False)
    
    def test_create_stock(self, mock_stock_repository, sample_stock):
        """Test creating a stock."""
        # Configure mock repository
        mock_stock_repository.create.return_value = sample_stock
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Create stock
        created_stock = service.create_stock(sample_stock)
        
        # Verify repository was called correctly
        mock_stock_repository.create.assert_called_once_with(sample_stock)
        
        # Verify stock was created
        assert created_stock is not None
        assert created_stock.symbol == "AAPL"
        assert created_stock.name == "Apple Inc."
    
    def test_update_stock(self, mock_stock_repository, sample_stock):
        """Test updating a stock."""
        # Configure mock repository
        mock_stock_repository.get_by_symbol.return_value = sample_stock
        mock_stock_repository.update.return_value = sample_stock
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Update stock
        updated_stock = service.update_stock(sample_stock)
        
        # Verify repository was called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with("AAPL")
        mock_stock_repository.update.assert_called_once_with(sample_stock)
        
        # Verify stock was updated
        assert updated_stock is not None
        assert updated_stock.symbol == "AAPL"
        assert updated_stock.name == "Apple Inc."
    
    def test_update_stock_not_found(self, mock_stock_repository, sample_stock):
        """Test updating a non-existent stock."""
        # Configure mock repository
        mock_stock_repository.get_by_symbol.return_value = None
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Update non-existent stock
        with pytest.raises(DataNotFoundError):
            service.update_stock(sample_stock)
        
        # Verify repository was called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with("AAPL")
        mock_stock_repository.update.assert_not_called()
    
    def test_delete_stock(self, mock_stock_repository):
        """Test deleting a stock."""
        # Configure mock repository
        mock_stock_repository.delete.return_value = True
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Delete stock
        result = service.delete_stock("AAPL")
        
        # Verify repository was called correctly
        mock_stock_repository.delete.assert_called_once_with("AAPL")
        
        # Verify stock was deleted
        assert result is True
    
    def test_search_stocks(self, mock_stock_repository, sample_stock):
        """Test searching for stocks."""
        # Configure mock repository
        mock_stock_repository.search_stocks.return_value = [sample_stock]
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Search stocks
        stocks = service.search_stocks("Apple")
        
        # Verify repository was called correctly
        mock_stock_repository.search_stocks.assert_called_once_with("Apple", 10, 0)
        
        # Verify stocks were found
        assert len(stocks) == 1
        assert stocks[0].symbol == "AAPL"
        assert stocks[0].name == "Apple Inc."
    
    def test_get_stocks_by_exchange(self, mock_stock_repository, sample_stock):
        """Test getting stocks by exchange."""
        # Configure mock repository
        mock_stock_repository.get_stocks_by_exchange.return_value = [sample_stock]
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Get stocks by exchange
        stocks = service.get_stocks_by_exchange(Exchange.NASDAQ)
        
        # Verify repository was called correctly
        mock_stock_repository.get_stocks_by_exchange.assert_called_once_with(Exchange.NASDAQ, 100, 0)
        
        # Verify stocks were found
        assert len(stocks) == 1
        assert stocks[0].symbol == "AAPL"
        assert stocks[0].name == "Apple Inc."
    
    def test_get_stocks_by_sector(self, mock_stock_repository, sample_stock):
        """Test getting stocks by sector."""
        # Configure mock repository
        mock_stock_repository.get_stocks_by_sector.return_value = [sample_stock]
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Get stocks by sector
        stocks = service.get_stocks_by_sector(Sector.TECHNOLOGY)
        
        # Verify repository was called correctly
        mock_stock_repository.get_stocks_by_sector.assert_called_once_with(Sector.TECHNOLOGY, 100, 0)
        
        # Verify stocks were found
        assert len(stocks) == 1
        assert stocks[0].symbol == "AAPL"
        assert stocks[0].name == "Apple Inc."
    
    def test_add_price_data(self, mock_stock_repository, sample_stock_prices):
        """Test adding price data for a stock."""
        # Configure mock repository
        mock_stock_repository.add_price_data.return_value = True
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Add price data
        result = service.add_price_data("AAPL", sample_stock_prices)
        
        # Verify repository was called correctly
        mock_stock_repository.add_price_data.assert_called_once_with("AAPL", sample_stock_prices)
        
        # Verify price data was added
        assert result is True
    
    def test_get_price_data(self, mock_stock_repository, sample_stock_prices):
        """Test getting price data for a stock."""
        # Configure mock repository
        mock_stock_repository.get_price_data.return_value = sample_stock_prices
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Get price data
        prices = service.get_price_data("AAPL")
        
        # Verify repository was called correctly
        mock_stock_repository.get_price_data.assert_called_once_with("AAPL", None, None, 100)
        
        # Verify price data was retrieved
        assert len(prices) == 3
        assert prices[0].close == 153.0
        assert prices[1].close == 158.0
        assert prices[2].close == 163.0
    
    def test_get_latest_price(self, mock_stock_repository, sample_stock_prices):
        """Test getting the latest price for a stock."""
        # Configure mock repository
        mock_stock_repository.get_latest_price.return_value = sample_stock_prices[2]
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Get latest price
        price = service.get_latest_price("AAPL")
        
        # Verify repository was called correctly
        mock_stock_repository.get_latest_price.assert_called_once_with("AAPL")
        
        # Verify latest price was retrieved
        assert price is not None
        assert price.close == 163.0
    
    def test_get_stock_data(self, mock_stock_repository, sample_stock, sample_stock_prices):
        """Test getting stock data for analysis."""
        # Configure mock repository
        mock_stock_repository.get_by_symbol.return_value = sample_stock
        mock_stock_repository.get_price_data.return_value = sample_stock_prices
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Get stock data
        stock_data = service.get_stock_data("AAPL")
        
        # Verify repository was called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with("AAPL")
        mock_stock_repository.get_price_data.assert_called_once_with("AAPL", None, None, 100)
        
        # Verify stock data was retrieved
        assert stock_data is not None
        assert stock_data.symbol == "AAPL"
        assert stock_data.timeframe == "1d"
        assert len(stock_data.prices) == 3
        assert stock_data.prices[0].close == 153.0
        assert stock_data.prices[1].close == 158.0
        assert stock_data.prices[2].close == 163.0
    
    def test_get_stock_data_not_found(self, mock_stock_repository):
        """Test getting stock data for a non-existent stock."""
        # Configure mock repository
        mock_stock_repository.get_by_symbol.return_value = None
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Get stock data for non-existent stock
        with pytest.raises(DataNotFoundError):
            service.get_stock_data("NONEXISTENT")
        
        # Verify repository was called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with("NONEXISTENT")
        mock_stock_repository.get_price_data.assert_not_called()
    
    def test_error_handling(self, mock_stock_repository):
        """Test error handling in the service."""
        # Configure mock repository to raise an exception
        mock_stock_repository.get_by_symbol.side_effect = Exception("Test error")
        
        # Create service with mock repository
        service = StockService(mock_stock_repository)
        
        # Call method that should handle the error
        with pytest.raises(ServiceError) as excinfo:
            service.get_stock("AAPL")
        
        # Verify error was handled correctly
        assert "Service operation 'get_stock' failed" in str(excinfo.value)
        assert "Test error" in str(excinfo.value)
