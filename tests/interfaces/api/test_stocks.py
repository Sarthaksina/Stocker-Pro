"""Tests for stock endpoints.

This module contains tests for the stock-related API endpoints.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from stocker.domain.user import User
from stocker.domain.stock import Stock, StockPrice
from stocker.services.stock_service import StockService


@pytest.fixture
def test_stock(db: Session, stock_service: StockService) -> Stock:
    """Create a test stock.
    
    Args:
        db: Database session
        stock_service: Stock service
        
    Returns:
        Stock: Test stock
    """
    return stock_service.create_stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="TECHNOLOGY"
    )


@pytest.fixture
def test_stock_with_prices(db: Session, stock_service: StockService, test_stock: Stock) -> Stock:
    """Create a test stock with price history.
    
    Args:
        db: Database session
        stock_service: Stock service
        test_stock: Test stock
        
    Returns:
        Stock: Test stock with prices
    """
    # Add prices for the last 5 days
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for i in range(5):
        date = today - timedelta(days=i)
        stock_service.add_stock_price(
            symbol=test_stock.symbol,
            date=date,
            open_price=150.0 + i,
            high=155.0 + i,
            low=145.0 + i,
            close=152.0 + i,
            volume=1000000 + i * 100000
        )
    
    return stock_service.get_stock(test_stock.symbol, include_prices=True)


def test_create_stock(client: TestClient, user_token_headers: dict):
    """Test creating a new stock.
    
    Args:
        client: Test client
        user_token_headers: User token headers
    """
    # Create stock
    response = client.post(
        "/api/stocks/",
        json={
            "symbol": "MSFT",
            "name": "Microsoft Corporation",
            "exchange": "NASDAQ",
            "sector": "TECHNOLOGY",
            "industry": "Software",
            "market_cap": 2000000000000,
            "pe_ratio": 30.5,
            "dividend_yield": 0.8,
            "beta": 1.2
        },
        headers=user_token_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == "MSFT"
    assert data["name"] == "Microsoft Corporation"
    assert data["exchange"] == "NASDAQ"
    assert data["sector"] == "TECHNOLOGY"
    assert data["industry"] == "Software"
    assert data["market_cap"] == 2000000000000
    assert data["pe_ratio"] == 30.5
    assert data["dividend_yield"] == 0.8
    assert data["beta"] == 1.2


def test_create_stock_duplicate(client: TestClient, user_token_headers: dict, test_stock: Stock):
    """Test creating a duplicate stock.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_stock: Existing test stock
    """
    response = client.post(
        "/api/stocks/",
        json={
            "symbol": test_stock.symbol,
            "name": "Duplicate Stock",
            "exchange": "NYSE",
            "sector": "TECHNOLOGY"
        },
        headers=user_token_headers
    )
    assert response.status_code == 400


def test_get_stocks(client: TestClient, user_token_headers: dict, test_stock: Stock):
    """Test getting all stocks.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_stock: Test stock
    """
    response = client.get("/api/stocks/", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check if test_stock is in the response
    stock_symbols = [stock["symbol"] for stock in data]
    assert test_stock.symbol in stock_symbols


def test_get_stocks_with_filters(client: TestClient, user_token_headers: dict, test_stock: Stock):
    """Test getting stocks with filters.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_stock: Test stock
    """
    # Filter by exchange
    response = client.get(
        f"/api/stocks/?exchange={test_stock.exchange}",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(stock["exchange"] == test_stock.exchange for stock in data)
    
    # Filter by sector
    response = client.get(
        f"/api/stocks/?sector={test_stock.sector}",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(stock["sector"] == test_stock.sector for stock in data)


def test_get_stock(client: TestClient, user_token_headers: dict, test_stock: Stock):
    """Test getting a stock by symbol.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_stock: Test stock
    """
    response = client.get(f"/api/stocks/{test_stock.symbol}", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == test_stock.symbol
    assert data["name"] == test_stock.name
    assert data["exchange"] == test_stock.exchange
    assert data["sector"] == test_stock.sector


def test_get_stock_with_prices(client: TestClient, user_token_headers: dict, test_stock_with_prices: Stock):
    """Test getting a stock with price history.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_stock_with_prices: Test stock with prices
    """
    response = client.get(
        f"/api/stocks/{test_stock_with_prices.symbol}?include_prices=true",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == test_stock_with_prices.symbol
    assert "data" in data
    assert data["data"] is not None
    assert "prices" in data["data"]
    assert len(data["data"]["prices"]) > 0


def test_get_stock_not_found(client: TestClient, user_token_headers: dict):
    """Test getting a non-existent stock.
    
    Args:
        client: Test client
        user_token_headers: User token headers
    """
    response = client.get("/api/stocks/NONEXISTENT", headers=user_token_headers)
    assert response.status_code == 404


def test_update_stock(client: TestClient, user_token_headers: dict, test_stock: Stock):
    """Test updating a stock.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_stock: Test stock
    """
    response = client.put(
        f"/api/stocks/{test_stock.symbol}",
        json={
            "name": "Updated Stock Name",
            "market_cap": 1500000000000,
            "pe_ratio": 25.0,
            "dividend_yield": 1.2,
            "description": "This is an updated description."
        },
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == test_stock.symbol
    assert data["name"] == "Updated Stock Name"
    assert data["market_cap"] == 1500000000000
    assert data["pe_ratio"] == 25.0
    assert data["dividend_yield"] == 1.2
    assert data["description"] == "This is an updated description."


def test_delete_stock(client: TestClient, admin_token_headers: dict, stock_service: StockService):
    """Test deleting a stock.
    
    Args:
        client: Test client
        admin_token_headers: Admin token headers
        stock_service: Stock service
    """
    # Create a stock to delete
    stock_to_delete = stock_service.create_stock(
        symbol="DELETE",
        name="Stock to Delete",
        exchange="NYSE",
        sector="ENERGY"
    )
    
    # Delete stock
    response = client.delete(f"/api/stocks/{stock_to_delete.symbol}", headers=admin_token_headers)
    assert response.status_code == 204
    
    # Verify stock is deleted
    deleted_stock = stock_service.get_stock(stock_to_delete.symbol)
    assert deleted_stock is None


def test_delete_stock_unauthorized(client: TestClient, user_token_headers: dict, test_stock: Stock):
    """Test deleting a stock without admin privileges.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_stock: Test stock
    """
    response = client.delete(f"/api/stocks/{test_stock.symbol}", headers=user_token_headers)
    assert response.status_code == 403


def test_add_stock_price(client: TestClient, user_token_headers: dict, test_stock: Stock):
    """Test adding a price entry for a stock.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_stock: Test stock
    """
    # Add price
    price_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    response = client.post(
        f"/api/stocks/{test_stock.symbol}/prices",
        json={
            "date": price_date.isoformat(),
            "open": 150.0,
            "high": 155.0,
            "low": 145.0,
            "close": 152.0,
            "volume": 1000000,
            "adjusted_close": 152.0
        },
        headers=user_token_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["date"].startswith(price_date.date().isoformat())
    assert data["open"] == 150.0
    assert data["high"] == 155.0
    assert data["low"] == 145.0
    assert data["close"] == 152.0
    assert data["volume"] == 1000000
    assert data["adjusted_close"] == 152.0


def test_add_duplicate_stock_price(client: TestClient, user_token_headers: dict, test_stock_with_prices: Stock):
    """Test adding a duplicate price entry for a stock.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_stock_with_prices: Test stock with prices
    """
    # Get an existing price date
    existing_price = test_stock_with_prices.prices[0]
    
    # Try to add a price for the same date
    response = client.post(
        f"/api/stocks/{test_stock_with_prices.symbol}/prices",
        json={
            "date": existing_price.date.isoformat(),
            "open": 160.0,
            "high": 165.0,
            "low": 155.0,
            "close": 162.0,
            "volume": 2000000
        },
        headers=user_token_headers
    )
    assert response.status_code == 400


def test_get_stock_prices(client: TestClient, user_token_headers: dict, test_stock_with_prices: Stock):
    """Test getting price history for a stock.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_stock_with_prices: Test stock with prices
    """
    response = client.get(
        f"/api/stocks/{test_stock_with_prices.symbol}/prices",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == test_stock_with_prices.symbol
    assert "prices" in data
    assert len(data["prices"]) > 0


def test_delete_stock_price(client: TestClient, admin_token_headers: dict, test_stock_with_prices: Stock):
    """Test deleting a price entry for a stock.
    
    Args:
        client: Test client
        admin_token_headers: Admin token headers
        test_stock_with_prices: Test stock with prices
    """
    # Get an existing price date
    existing_price = test_stock_with_prices.prices[0]
    
    # Delete price
    response = client.delete(
        f"/api/stocks/{test_stock_with_prices.symbol}/prices/{existing_price.date.isoformat()}",
        headers=admin_token_headers
    )
    assert response.status_code == 204


def test_delete_stock_price_unauthorized(client: TestClient, user_token_headers: dict, test_stock_with_prices: Stock):
    """Test deleting a price entry without admin privileges.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_stock_with_prices: Test stock with prices
    """
    # Get an existing price date
    existing_price = test_stock_with_prices.prices[0]
    
    # Try to delete price as non-admin
    response = client.delete(
        f"/api/stocks/{test_stock_with_prices.symbol}/prices/{existing_price.date.isoformat()}",
        headers=user_token_headers
    )
    assert response.status_code == 403
