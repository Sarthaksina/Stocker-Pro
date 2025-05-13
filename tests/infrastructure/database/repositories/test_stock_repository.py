"""Tests for the stock repository.

This module contains tests for the StockRepository class.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from stocker.core.exceptions import DataError, DataNotFoundError
from stocker.domain.stock import Stock, StockPrice, StockData, Exchange, Sector
from stocker.infrastructure.database.models.stock import StockModel, StockPriceModel
from stocker.infrastructure.database.repositories.stock import StockRepository


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


class TestStockRepository:
    """Tests for the StockRepository class."""
    
    def test_create(self, mock_get_session, test_db_session, sample_stock):
        """Test creating a stock."""
        # Create repository
        repo = StockRepository()
        
        # Create stock
        created_stock = repo.create(sample_stock)
        
        # Verify stock was created
        assert created_stock.symbol == "AAPL"
        assert created_stock.name == "Apple Inc."
        
        # Verify stock exists in database
        db_stock = test_db_session.get(StockModel, "AAPL")
        assert db_stock is not None
        assert db_stock.symbol == "AAPL"
        assert db_stock.name == "Apple Inc."
    
    def test_get_by_id(self, mock_get_session, test_db_session, sample_stock):
        """Test getting a stock by ID (symbol)."""
        # Create repository
        repo = StockRepository()
        
        # Add stock to database
        model = StockModel.from_domain(sample_stock)
        test_db_session.add(model)
        test_db_session.commit()
        
        # Get stock by ID
        stock = repo.get_by_id("AAPL")
        
        # Verify stock was retrieved
        assert stock is not None
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
    
    def test_get_by_symbol(self, mock_get_session, test_db_session, sample_stock):
        """Test getting a stock by symbol."""
        # Create repository
        repo = StockRepository()
        
        # Add stock to database
        model = StockModel.from_domain(sample_stock)
        test_db_session.add(model)
        test_db_session.commit()
        
        # Get stock by symbol
        stock = repo.get_by_symbol("AAPL")
        
        # Verify stock was retrieved
        assert stock is not None
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
    
    def test_get_by_symbol_with_prices(self, mock_get_session, test_db_session, sample_stock, sample_stock_prices):
        """Test getting a stock by symbol with price data."""
        # Create repository
        repo = StockRepository()
        
        # Add stock to database
        model = StockModel.from_domain(sample_stock)
        test_db_session.add(model)
        
        # Add price data
        for price in sample_stock_prices:
            price_model = StockPriceModel.from_domain(price, "AAPL")
            test_db_session.add(price_model)
        
        test_db_session.commit()
        
        # Get stock by symbol with prices
        stock = repo.get_by_symbol("AAPL", include_prices=True)
        
        # Verify stock was retrieved with prices
        assert stock is not None
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
        assert stock.data is not None
        assert len(stock.data.prices) == 3
    
    def test_get_by_symbol_not_found(self, mock_get_session):
        """Test getting a non-existent stock by symbol."""
        # Create repository
        repo = StockRepository()
        
        # Get non-existent stock
        stock = repo.get_by_symbol("NONEXISTENT")
        
        # Verify stock was not found
        assert stock is None
    
    def test_update(self, mock_get_session, test_db_session, sample_stock):
        """Test updating a stock."""
        # Create repository
        repo = StockRepository()
        
        # Add stock to database
        model = StockModel.from_domain(sample_stock)
        test_db_session.add(model)
        test_db_session.commit()
        
        # Update stock
        sample_stock.name = "Apple Inc. Updated"
        sample_stock.market_cap = 3000000000000.0
        
        updated_stock = repo.update(sample_stock)
        
        # Verify stock was updated
        assert updated_stock.name == "Apple Inc. Updated"
        assert updated_stock.market_cap == 3000000000000.0
        
        # Verify stock was updated in database
        db_stock = test_db_session.get(StockModel, "AAPL")
        assert db_stock.name == "Apple Inc. Updated"
        assert db_stock.market_cap == 3000000000000.0
    
    def test_delete(self, mock_get_session, test_db_session, sample_stock):
        """Test deleting a stock."""
        # Create repository
        repo = StockRepository()
        
        # Add stock to database
        model = StockModel.from_domain(sample_stock)
        test_db_session.add(model)
        test_db_session.commit()
        
        # Delete stock
        result = repo.delete("AAPL")
        
        # Verify stock was deleted
        assert result is True
        
        # Verify stock was deleted from database
        db_stock = test_db_session.get(StockModel, "AAPL")
        assert db_stock is None
    
    def test_delete_not_found(self, mock_get_session):
        """Test deleting a non-existent stock."""
        # Create repository
        repo = StockRepository()
        
        # Delete non-existent stock
        result = repo.delete("NONEXISTENT")
        
        # Verify deletion failed
        assert result is False
    
    def test_get_stocks_by_exchange(self, mock_get_session, test_db_session):
        """Test getting stocks by exchange."""
        # Create repository
        repo = StockRepository()
        
        # Add stocks to database
        nasdaq_stock1 = StockModel(
            symbol="AAPL",
            name="Apple Inc.",
            exchange=Exchange.NASDAQ.value
        )
        nasdaq_stock2 = StockModel(
            symbol="MSFT",
            name="Microsoft Corporation",
            exchange=Exchange.NASDAQ.value
        )
        nyse_stock = StockModel(
            symbol="IBM",
            name="International Business Machines",
            exchange=Exchange.NYSE.value
        )
        
        test_db_session.add_all([nasdaq_stock1, nasdaq_stock2, nyse_stock])
        test_db_session.commit()
        
        # Get stocks by exchange
        nasdaq_stocks = repo.get_stocks_by_exchange(Exchange.NASDAQ)
        nyse_stocks = repo.get_stocks_by_exchange(Exchange.NYSE)
        
        # Verify stocks were retrieved
        assert len(nasdaq_stocks) == 2
        assert nasdaq_stocks[0].symbol in ["AAPL", "MSFT"]
        assert nasdaq_stocks[1].symbol in ["AAPL", "MSFT"]
        
        assert len(nyse_stocks) == 1
        assert nyse_stocks[0].symbol == "IBM"
    
    def test_get_stocks_by_sector(self, mock_get_session, test_db_session):
        """Test getting stocks by sector."""
        # Create repository
        repo = StockRepository()
        
        # Add stocks to database
        tech_stock1 = StockModel(
            symbol="AAPL",
            name="Apple Inc.",
            sector=Sector.TECHNOLOGY.value
        )
        tech_stock2 = StockModel(
            symbol="MSFT",
            name="Microsoft Corporation",
            sector=Sector.TECHNOLOGY.value
        )
        finance_stock = StockModel(
            symbol="JPM",
            name="JPMorgan Chase & Co.",
            sector=Sector.FINANCIAL.value
        )
        
        test_db_session.add_all([tech_stock1, tech_stock2, finance_stock])
        test_db_session.commit()
        
        # Get stocks by sector
        tech_stocks = repo.get_stocks_by_sector(Sector.TECHNOLOGY)
        finance_stocks = repo.get_stocks_by_sector(Sector.FINANCIAL)
        
        # Verify stocks were retrieved
        assert len(tech_stocks) == 2
        assert tech_stocks[0].symbol in ["AAPL", "MSFT"]
        assert tech_stocks[1].symbol in ["AAPL", "MSFT"]
        
        assert len(finance_stocks) == 1
        assert finance_stocks[0].symbol == "JPM"
    
    def test_search_stocks(self, mock_get_session, test_db_session):
        """Test searching for stocks."""
        # Create repository
        repo = StockRepository()
        
        # Add stocks to database
        stock1 = StockModel(
            symbol="AAPL",
            name="Apple Inc."
        )
        stock2 = StockModel(
            symbol="MSFT",
            name="Microsoft Corporation"
        )
        stock3 = StockModel(
            symbol="GOOGL",
            name="Alphabet Inc."
        )
        
        test_db_session.add_all([stock1, stock2, stock3])
        test_db_session.commit()
        
        # Search for stocks
        apple_stocks = repo.search_stocks("Apple")
        microsoft_stocks = repo.search_stocks("Microsoft")
        a_stocks = repo.search_stocks("A")
        
        # Verify stocks were found
        assert len(apple_stocks) == 1
        assert apple_stocks[0].symbol == "AAPL"
        
        assert len(microsoft_stocks) == 1
        assert microsoft_stocks[0].symbol == "MSFT"
        
        # Should find both Apple and Alphabet
        assert len(a_stocks) >= 2
    
    def test_add_price_data(self, mock_get_session, test_db_session, sample_stock, sample_stock_prices):
        """Test adding price data for a stock."""
        # Create repository
        repo = StockRepository()
        
        # Add stock to database
        model = StockModel.from_domain(sample_stock)
        test_db_session.add(model)
        test_db_session.commit()
        
        # Add price data
        result = repo.add_price_data("AAPL", sample_stock_prices)
        
        # Verify price data was added
        assert result is True
        
        # Verify price data exists in database
        price_models = test_db_session.query(StockPriceModel).filter_by(symbol="AAPL").all()
        assert len(price_models) == 3
    
    def test_add_price_data_stock_not_found(self, mock_get_session, sample_stock_prices):
        """Test adding price data for a non-existent stock."""
        # Create repository
        repo = StockRepository()
        
        # Add price data for non-existent stock
        with pytest.raises(DataNotFoundError):
            repo.add_price_data("NONEXISTENT", sample_stock_prices)
    
    def test_get_price_data(self, mock_get_session, test_db_session, sample_stock, sample_stock_prices):
        """Test getting price data for a stock."""
        # Create repository
        repo = StockRepository()
        
        # Add stock to database
        model = StockModel.from_domain(sample_stock)
        test_db_session.add(model)
        
        # Add price data
        for price in sample_stock_prices:
            price_model = StockPriceModel.from_domain(price, "AAPL")
            test_db_session.add(price_model)
        
        test_db_session.commit()
        
        # Get price data
        prices = repo.get_price_data("AAPL")
        
        # Verify price data was retrieved
        assert len(prices) == 3
        
        # Get price data with date range
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        prices = repo.get_price_data(
            "AAPL",
            start_date=datetime.combine(yesterday, datetime.min.time())
        )
        
        # Verify filtered price data was retrieved
        assert len(prices) == 2
    
    def test_get_price_data_stock_not_found(self, mock_get_session):
        """Test getting price data for a non-existent stock."""
        # Create repository
        repo = StockRepository()
        
        # Get price data for non-existent stock
        with pytest.raises(DataNotFoundError):
            repo.get_price_data("NONEXISTENT")
    
    def test_get_latest_price(self, mock_get_session, test_db_session, sample_stock, sample_stock_prices):
        """Test getting the latest price for a stock."""
        # Create repository
        repo = StockRepository()
        
        # Add stock to database
        model = StockModel.from_domain(sample_stock)
        test_db_session.add(model)
        
        # Add price data
        for price in sample_stock_prices:
            price_model = StockPriceModel.from_domain(price, "AAPL")
            test_db_session.add(price_model)
        
        test_db_session.commit()
        
        # Get latest price
        price = repo.get_latest_price("AAPL")
        
        # Verify latest price was retrieved
        assert price is not None
        assert price.close == 163.0  # Latest price in sample data
