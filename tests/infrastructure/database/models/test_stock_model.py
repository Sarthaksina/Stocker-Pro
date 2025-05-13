"""Tests for the stock database model.

This module contains tests for the StockModel and StockPriceModel classes.
"""

import pytest
from datetime import datetime, timedelta

from stocker.domain.stock import Stock, StockPrice, StockData, Exchange, Sector
from stocker.infrastructure.database.models.stock import StockModel, StockPriceModel


class TestStockModel:
    """Tests for the StockModel class."""
    
    def test_from_domain(self):
        """Test creating a model from a domain entity."""
        # Create a domain entity
        stock = Stock(
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
        
        # Convert to model
        model = StockModel.from_domain(stock)
        
        # Verify model attributes
        assert model.symbol == "AAPL"
        assert model.name == "Apple Inc."
        assert model.exchange == Exchange.NASDAQ.value
        assert model.sector == Sector.TECHNOLOGY.value
        assert model.industry == "Consumer Electronics"
        assert model.market_cap == 2500000000000.0
        assert model.pe_ratio == 30.5
        assert model.dividend_yield == 0.5
        assert model.beta == 1.2
        assert model.description == "Apple Inc. designs, manufactures, and markets smartphones."
    
    def test_to_domain(self):
        """Test converting a model to a domain entity."""
        # Create a model
        model = StockModel(
            symbol="AAPL",
            name="Apple Inc.",
            exchange=Exchange.NASDAQ.value,
            sector=Sector.TECHNOLOGY.value,
            industry="Consumer Electronics",
            market_cap=2500000000000.0,
            pe_ratio=30.5,
            dividend_yield=0.5,
            beta=1.2,
            description="Apple Inc. designs, manufactures, and markets smartphones."
        )
        
        # Convert to domain entity
        stock = model.to_domain()
        
        # Verify domain entity attributes
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
        assert stock.exchange == Exchange.NASDAQ
        assert stock.sector == Sector.TECHNOLOGY
        assert stock.industry == "Consumer Electronics"
        assert stock.market_cap == 2500000000000.0
        assert stock.pe_ratio == 30.5
        assert stock.dividend_yield == 0.5
        assert stock.beta == 1.2
        assert stock.description == "Apple Inc. designs, manufactures, and markets smartphones."
    
    def test_to_domain_with_prices(self, test_db_session):
        """Test converting a model to a domain entity with price data."""
        # Create a model with price data
        model = StockModel(
            symbol="AAPL",
            name="Apple Inc.",
            exchange=Exchange.NASDAQ.value,
            sector=Sector.TECHNOLOGY.value,
            industry="Consumer Electronics"
        )
        
        # Add price data
        today = datetime.now().date()
        price1 = StockPriceModel(
            symbol="AAPL",
            date=datetime.combine(today - timedelta(days=1), datetime.min.time()),
            open=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
            volume=1000000,
            adjusted_close=153.0
        )
        price2 = StockPriceModel(
            symbol="AAPL",
            date=datetime.combine(today, datetime.min.time()),
            open=153.0,
            high=160.0,
            low=152.0,
            close=158.0,
            volume=1200000,
            adjusted_close=158.0
        )
        
        model.prices = [price1, price2]
        
        # Save to database
        test_db_session.add(model)
        test_db_session.commit()
        
        # Convert to domain entity with prices
        stock = model.to_domain(include_prices=True)
        
        # Verify domain entity attributes
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
        assert stock.data is not None
        assert len(stock.data.prices) == 2
        assert stock.data.prices[0].close == 153.0
        assert stock.data.prices[1].close == 158.0
    
    def test_to_domain_with_missing_fields(self):
        """Test converting a model with missing fields to a domain entity."""
        # Create a model with missing fields
        model = StockModel(
            symbol="AAPL",
            name="Apple Inc."
        )
        
        # Convert to domain entity
        stock = model.to_domain()
        
        # Verify domain entity attributes
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
        assert stock.exchange == Exchange.OTHER
        assert stock.sector == Exchange.OTHER
        assert stock.industry == ""
        assert stock.description == ""


class TestStockPriceModel:
    """Tests for the StockPriceModel class."""
    
    def test_from_domain(self):
        """Test creating a model from a domain entity."""
        # Create a domain entity
        price = StockPrice(
            date=datetime(2023, 1, 1),
            open=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
            volume=1000000,
            adjusted_close=153.0
        )
        
        # Convert to model
        model = StockPriceModel.from_domain(price, "AAPL")
        
        # Verify model attributes
        assert model.symbol == "AAPL"
        assert model.date == datetime(2023, 1, 1)
        assert model.open == 150.0
        assert model.high == 155.0
        assert model.low == 149.0
        assert model.close == 153.0
        assert model.volume == 1000000
        assert model.adjusted_close == 153.0
    
    def test_to_domain(self):
        """Test converting a model to a domain entity."""
        # Create a model
        model = StockPriceModel(
            symbol="AAPL",
            date=datetime(2023, 1, 1),
            open=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
            volume=1000000,
            adjusted_close=153.0
        )
        
        # Convert to domain entity
        price = model.to_domain()
        
        # Verify domain entity attributes
        assert price.date == datetime(2023, 1, 1)
        assert price.open == 150.0
        assert price.high == 155.0
        assert price.low == 149.0
        assert price.close == 153.0
        assert price.volume == 1000000
        assert price.adjusted_close == 153.0
