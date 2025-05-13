"""Tests for portfolio endpoints.

This module contains tests for the portfolio-related API endpoints.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from stocker.domain.user import User
from stocker.domain.portfolio import Portfolio, Position, Transaction
from stocker.domain.stock import Stock
from stocker.services.portfolio_service import PortfolioService
from stocker.services.stock_service import StockService


@pytest.fixture
def test_portfolio(db: Session, portfolio_service: PortfolioService, test_user: User) -> Portfolio:
    """Create a test portfolio.
    
    Args:
        db: Database session
        portfolio_service: Portfolio service
        test_user: Test user
        
    Returns:
        Portfolio: Test portfolio
    """
    return portfolio_service.create_portfolio(
        name="Test Portfolio",
        description="A test portfolio",
        type="personal",
        owner_id=test_user.id,
        cash_balance=10000.0
    )


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
def test_portfolio_with_positions(
    db: Session,
    portfolio_service: PortfolioService,
    test_portfolio: Portfolio,
    test_stock: Stock
) -> Portfolio:
    """Create a test portfolio with positions.
    
    Args:
        db: Database session
        portfolio_service: Portfolio service
        test_portfolio: Test portfolio
        test_stock: Test stock
        
    Returns:
        Portfolio: Test portfolio with positions
    """
    # Add position
    portfolio_service.add_position(
        portfolio_id=test_portfolio.id,
        symbol=test_stock.symbol,
        quantity=10.0,
        cost_basis=150.0
    )
    
    # Add another position
    stock_service = StockService(db)
    stock_service.create_stock(
        symbol="MSFT",
        name="Microsoft Corporation",
        exchange="NASDAQ",
        sector="TECHNOLOGY"
    )
    
    portfolio_service.add_position(
        portfolio_id=test_portfolio.id,
        symbol="MSFT",
        quantity=5.0,
        cost_basis=250.0
    )
    
    return portfolio_service.get_portfolio(test_portfolio.id, include_positions=True)


@pytest.fixture
def test_portfolio_with_transactions(
    db: Session,
    portfolio_service: PortfolioService,
    test_portfolio: Portfolio,
    test_stock: Stock
) -> Portfolio:
    """Create a test portfolio with transactions.
    
    Args:
        db: Database session
        portfolio_service: Portfolio service
        test_portfolio: Test portfolio
        test_stock: Test stock
        
    Returns:
        Portfolio: Test portfolio with transactions
    """
    # Add buy transaction
    portfolio_service.add_transaction(
        portfolio_id=test_portfolio.id,
        transaction_type="buy",
        symbol=test_stock.symbol,
        date=datetime.now(),
        quantity=10.0,
        price=150.0,
        amount=1500.0
    )
    
    # Add deposit transaction
    portfolio_service.add_transaction(
        portfolio_id=test_portfolio.id,
        transaction_type="deposit",
        date=datetime.now() - timedelta(days=1),
        amount=5000.0,
        notes="Initial deposit"
    )
    
    return portfolio_service.get_portfolio(test_portfolio.id, include_transactions=True)


def test_create_portfolio(client: TestClient, user_token_headers: dict, test_user: User):
    """Test creating a new portfolio.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_user: Test user
    """
    # Create portfolio
    response = client.post(
        "/api/portfolios/",
        json={
            "name": "New Portfolio",
            "description": "A new test portfolio",
            "type": "personal",
            "cash_balance": 5000.0,
            "benchmark_symbol": "SPY"
        },
        headers=user_token_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Portfolio"
    assert data["description"] == "A new test portfolio"
    assert data["type"] == "personal"
    assert data["cash_balance"] == 5000.0
    assert data["benchmark_symbol"] == "SPY"
    assert data["owner_id"] == test_user.id


def test_create_portfolio_for_another_user(client: TestClient, admin_token_headers: dict, test_user: User):
    """Test creating a portfolio for another user as admin.
    
    Args:
        client: Test client
        admin_token_headers: Admin token headers
        test_user: Test user
    """
    # Create portfolio for another user
    response = client.post(
        "/api/portfolios/",
        json={
            "name": "Admin Created Portfolio",
            "description": "Portfolio created by admin for another user",
            "type": "model",
            "owner_id": test_user.id,
            "cash_balance": 10000.0
        },
        headers=admin_token_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Admin Created Portfolio"
    assert data["owner_id"] == test_user.id


def test_create_portfolio_for_another_user_unauthorized(client: TestClient, user_token_headers: dict, test_admin: User):
    """Test creating a portfolio for another user without admin privileges.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_admin: Test admin user
    """
    response = client.post(
        "/api/portfolios/",
        json={
            "name": "Unauthorized Portfolio",
            "description": "Portfolio created for another user",
            "type": "personal",
            "owner_id": test_admin.id,
            "cash_balance": 5000.0
        },
        headers=user_token_headers
    )
    assert response.status_code == 403


def test_get_portfolios(client: TestClient, user_token_headers: dict, test_portfolio: Portfolio, test_user: User):
    """Test getting all portfolios for a user.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_portfolio: Test portfolio
        test_user: Test user
    """
    response = client.get("/api/portfolios/", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check if test_portfolio is in the response
    portfolio_ids = [portfolio["id"] for portfolio in data]
    assert test_portfolio.id in portfolio_ids
    
    # Check if all portfolios belong to the user
    for portfolio in data:
        assert portfolio["owner_id"] == test_user.id


def test_get_all_portfolios_as_admin(client: TestClient, admin_token_headers: dict, test_portfolio: Portfolio):
    """Test getting all portfolios as admin.
    
    Args:
        client: Test client
        admin_token_headers: Admin token headers
        test_portfolio: Test portfolio
    """
    response = client.get("/api/portfolios/", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check if test_portfolio is in the response
    portfolio_ids = [portfolio["id"] for portfolio in data]
    assert test_portfolio.id in portfolio_ids


def test_get_portfolios_by_owner(client: TestClient, admin_token_headers: dict, test_portfolio: Portfolio, test_user: User):
    """Test getting portfolios by owner as admin.
    
    Args:
        client: Test client
        admin_token_headers: Admin token headers
        test_portfolio: Test portfolio
        test_user: Test user
    """
    response = client.get(f"/api/portfolios/?owner_id={test_user.id}", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check if all portfolios belong to the specified user
    for portfolio in data:
        assert portfolio["owner_id"] == test_user.id


def test_get_portfolios_by_owner_unauthorized(client: TestClient, user_token_headers: dict, test_admin: User):
    """Test getting portfolios by owner without admin privileges.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_admin: Test admin user
    """
    response = client.get(f"/api/portfolios/?owner_id={test_admin.id}", headers=user_token_headers)
    assert response.status_code == 403


def test_get_portfolio(client: TestClient, user_token_headers: dict, test_portfolio: Portfolio):
    """Test getting a portfolio by ID.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_portfolio: Test portfolio
    """
    response = client.get(f"/api/portfolios/{test_portfolio.id}", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_portfolio.id
    assert data["name"] == test_portfolio.name
    assert data["description"] == test_portfolio.description
    assert data["type"] == test_portfolio.type
    assert data["cash_balance"] == test_portfolio.cash_balance


def test_get_portfolio_with_positions(client: TestClient, user_token_headers: dict, test_portfolio_with_positions: Portfolio):
    """Test getting a portfolio with positions.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_portfolio_with_positions: Test portfolio with positions
    """
    response = client.get(
        f"/api/portfolios/{test_portfolio_with_positions.id}?include_positions=true",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_portfolio_with_positions.id
    assert "positions" in data
    assert len(data["positions"]) == 2
    assert "AAPL" in data["positions"]
    assert "MSFT" in data["positions"]
    assert data["positions"]["AAPL"]["quantity"] == 10.0
    assert data["positions"]["MSFT"]["quantity"] == 5.0


def test_get_portfolio_with_transactions(client: TestClient, user_token_headers: dict, test_portfolio_with_transactions: Portfolio):
    """Test getting a portfolio with transactions.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_portfolio_with_transactions: Test portfolio with transactions
    """
    response = client.get(
        f"/api/portfolios/{test_portfolio_with_transactions.id}?include_transactions=true",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_portfolio_with_transactions.id
    assert "transactions" in data
    assert len(data["transactions"]) == 2
    
    # Check transaction types
    transaction_types = [tx["type"] for tx in data["transactions"]]
    assert "buy" in transaction_types
    assert "deposit" in transaction_types


def test_get_portfolio_unauthorized(client: TestClient, user_token_headers: dict, portfolio_service: PortfolioService, test_admin: User):
    """Test getting another user's portfolio without admin privileges.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        portfolio_service: Portfolio service
        test_admin: Test admin user
    """
    # Create a portfolio for the admin user
    admin_portfolio = portfolio_service.create_portfolio(
        name="Admin Portfolio",
        owner_id=test_admin.id,
        cash_balance=10000.0
    )
    
    # Try to access admin's portfolio as regular user
    response = client.get(f"/api/portfolios/{admin_portfolio.id}", headers=user_token_headers)
    assert response.status_code == 403


def test_update_portfolio(client: TestClient, user_token_headers: dict, test_portfolio: Portfolio):
    """Test updating a portfolio.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_portfolio: Test portfolio
    """
    response = client.put(
        f"/api/portfolios/{test_portfolio.id}",
        json={
            "name": "Updated Portfolio",
            "description": "Updated description",
            "cash_balance": 15000.0,
            "benchmark_symbol": "QQQ"
        },
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_portfolio.id
    assert data["name"] == "Updated Portfolio"
    assert data["description"] == "Updated description"
    assert data["cash_balance"] == 15000.0
    assert data["benchmark_symbol"] == "QQQ"


def test_update_portfolio_unauthorized(client: TestClient, user_token_headers: dict, portfolio_service: PortfolioService, test_admin: User):
    """Test updating another user's portfolio without admin privileges.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        portfolio_service: Portfolio service
        test_admin: Test admin user
    """
    # Create a portfolio for the admin user
    admin_portfolio = portfolio_service.create_portfolio(
        name="Admin Portfolio",
        owner_id=test_admin.id,
        cash_balance=10000.0
    )
    
    # Try to update admin's portfolio as regular user
    response = client.put(
        f"/api/portfolios/{admin_portfolio.id}",
        json={"name": "Unauthorized Update"},
        headers=user_token_headers
    )
    assert response.status_code == 403


def test_delete_portfolio(client: TestClient, user_token_headers: dict, portfolio_service: PortfolioService, test_user: User):
    """Test deleting a portfolio.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        portfolio_service: Portfolio service
        test_user: Test user
    """
    # Create a portfolio to delete
    portfolio_to_delete = portfolio_service.create_portfolio(
        name="Portfolio to Delete",
        owner_id=test_user.id,
        cash_balance=5000.0
    )
    
    # Delete portfolio
    response = client.delete(f"/api/portfolios/{portfolio_to_delete.id}", headers=user_token_headers)
    assert response.status_code == 204
    
    # Verify portfolio is deleted
    deleted_portfolio = portfolio_service.get_portfolio(portfolio_to_delete.id)
    assert deleted_portfolio is None


def test_delete_portfolio_unauthorized(client: TestClient, user_token_headers: dict, portfolio_service: PortfolioService, test_admin: User):
    """Test deleting another user's portfolio without admin privileges.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        portfolio_service: Portfolio service
        test_admin: Test admin user
    """
    # Create a portfolio for the admin user
    admin_portfolio = portfolio_service.create_portfolio(
        name="Admin Portfolio",
        owner_id=test_admin.id,
        cash_balance=10000.0
    )
    
    # Try to delete admin's portfolio as regular user
    response = client.delete(f"/api/portfolios/{admin_portfolio.id}", headers=user_token_headers)
    assert response.status_code == 403


def test_add_position(client: TestClient, user_token_headers: dict, test_portfolio: Portfolio, test_stock: Stock):
    """Test adding a position to a portfolio.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_portfolio: Test portfolio
        test_stock: Test stock
    """
    response = client.post(
        f"/api/portfolios/{test_portfolio.id}/positions",
        json={
            "symbol": test_stock.symbol,
            "quantity": 15.0,
            "cost_basis": 160.0
        },
        headers=user_token_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == test_stock.symbol
    assert data["quantity"] == 15.0
    assert data["cost_basis"] == 160.0


def test_get_positions(client: TestClient, user_token_headers: dict, test_portfolio_with_positions: Portfolio):
    """Test getting all positions in a portfolio.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_portfolio_with_positions: Test portfolio with positions
    """
    response = client.get(
        f"/api/portfolios/{test_portfolio_with_positions.id}/positions",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 2
    assert "AAPL" in data
    assert "MSFT" in data
    assert data["AAPL"]["quantity"] == 10.0
    assert data["MSFT"]["quantity"] == 5.0


def test_remove_position(client: TestClient, user_token_headers: dict, test_portfolio_with_positions: Portfolio):
    """Test removing a position from a portfolio.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_portfolio_with_positions: Test portfolio with positions
    """
    response = client.delete(
        f"/api/portfolios/{test_portfolio_with_positions.id}/positions/AAPL",
        headers=user_token_headers
    )
    assert response.status_code == 204
    
    # Verify position is removed
    response = client.get(
        f"/api/portfolios/{test_portfolio_with_positions.id}/positions",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "AAPL" not in data
    assert "MSFT" in data


def test_add_transaction(client: TestClient, user_token_headers: dict, test_portfolio: Portfolio, test_stock: Stock):
    """Test adding a transaction to a portfolio.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_portfolio: Test portfolio
        test_stock: Test stock
    """
    # Add buy transaction
    transaction_date = datetime.now()
    response = client.post(
        f"/api/portfolios/{test_portfolio.id}/transactions",
        json={
            "type": "buy",
            "symbol": test_stock.symbol,
            "date": transaction_date.isoformat(),
            "quantity": 10.0,
            "price": 150.0,
            "amount": 1500.0,
            "fees": 5.0,
            "notes": "Test buy transaction"
        },
        headers=user_token_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "buy"
    assert data["symbol"] == test_stock.symbol
    assert data["quantity"] == 10.0
    assert data["price"] == 150.0
    assert data["amount"] == 1500.0
    assert data["fees"] == 5.0
    assert data["notes"] == "Test buy transaction"
    
    # Add deposit transaction
    response = client.post(
        f"/api/portfolios/{test_portfolio.id}/transactions",
        json={
            "type": "deposit",
            "date": transaction_date.isoformat(),
            "amount": 5000.0,
            "notes": "Test deposit"
        },
        headers=user_token_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "deposit"
    assert data["amount"] == 5000.0
    assert data["notes"] == "Test deposit"


def test_get_transactions(client: TestClient, user_token_headers: dict, test_portfolio_with_transactions: Portfolio):
    """Test getting all transactions in a portfolio.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_portfolio_with_transactions: Test portfolio with transactions
    """
    response = client.get(
        f"/api/portfolios/{test_portfolio_with_transactions.id}/transactions",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    
    # Check transaction types
    transaction_types = [tx["type"] for tx in data]
    assert "buy" in transaction_types
    assert "deposit" in transaction_types


def test_delete_transaction(client: TestClient, user_token_headers: dict, test_portfolio_with_transactions: Portfolio):
    """Test deleting a transaction from a portfolio.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_portfolio_with_transactions: Test portfolio with transactions
    """
    # Get a transaction ID
    response = client.get(
        f"/api/portfolios/{test_portfolio_with_transactions.id}/transactions",
        headers=user_token_headers
    )
    assert response.status_code == 200
    transactions = response.json()
    transaction_id = transactions[0]["id"]
    
    # Delete transaction
    response = client.delete(
        f"/api/portfolios/{test_portfolio_with_transactions.id}/transactions/{transaction_id}",
        headers=user_token_headers
    )
    assert response.status_code == 204
    
    # Verify transaction is deleted
    response = client.get(
        f"/api/portfolios/{test_portfolio_with_transactions.id}/transactions",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    transaction_ids = [tx["id"] for tx in data]
    assert transaction_id not in transaction_ids


def test_get_portfolio_performance(client: TestClient, user_token_headers: dict, test_portfolio_with_positions: Portfolio):
    """Test getting portfolio performance metrics.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_portfolio_with_positions: Test portfolio with positions
    """
    response = client.get(
        f"/api/portfolios/{test_portfolio_with_positions.id}/performance",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "current_value" in data
    assert "cash_balance" in data
    assert "position_value" in data
    assert "position_count" in data
    assert data["position_count"] == 2
