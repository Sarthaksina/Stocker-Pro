"""Tests for the portfolio service.

This module contains tests for the PortfolioService class.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import uuid

from stocker.core.exceptions import ServiceError, DataNotFoundError
from stocker.domain.portfolio import Portfolio, Position, Transaction, PortfolioType, TransactionType
from stocker.domain.stock import Stock, StockPrice
from stocker.infrastructure.database.repositories.portfolio import PortfolioRepository
from stocker.infrastructure.database.repositories.stock import StockRepository
from stocker.services.portfolio import PortfolioService


@pytest.fixture
def mock_portfolio_repository():
    """Create a mock portfolio repository for testing."""
    return Mock(spec=PortfolioRepository)


@pytest.fixture
def mock_stock_repository():
    """Create a mock stock repository for testing."""
    return Mock(spec=StockRepository)


@pytest.fixture
def sample_portfolio():
    """Create a sample portfolio for testing."""
    return Portfolio(
        id=str(uuid.uuid4()),
        name="Test Portfolio",
        description="A test portfolio",
        type=PortfolioType.PERSONAL,
        owner_id=str(uuid.uuid4()),
        cash_balance=10000.0,
        inception_date=datetime.now() - timedelta(days=30),
        benchmark_symbol="SPY"
    )


@pytest.fixture
def sample_position():
    """Create a sample position for testing."""
    return Position(
        symbol="AAPL",
        quantity=10.0,
        cost_basis=150.0,
        open_date=datetime.now() - timedelta(days=10)
    )


@pytest.fixture
def sample_transaction():
    """Create a sample transaction for testing."""
    return Transaction(
        id=str(uuid.uuid4()),
        type=TransactionType.BUY,
        symbol="AAPL",
        date=datetime.now() - timedelta(days=10),
        quantity=10.0,
        price=150.0,
        amount=1500.0,
        fees=9.99,
        notes="Test transaction"
    )


class TestPortfolioService:
    """Tests for the PortfolioService class."""
    
    def test_get_portfolio(self, mock_portfolio_repository, mock_stock_repository, sample_portfolio):
        """Test getting a portfolio by ID."""
        # Configure mock repository
        mock_portfolio_repository.get_by_id.return_value = sample_portfolio
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Get portfolio
        portfolio = service.get_portfolio(sample_portfolio.id)
        
        # Verify repository was called correctly
        mock_portfolio_repository.get_by_id.assert_called_once_with(sample_portfolio.id)
        
        # Verify portfolio was returned
        assert portfolio is not None
        assert portfolio.id == sample_portfolio.id
        assert portfolio.name == "Test Portfolio"
    
    def test_get_portfolio_not_found(self, mock_portfolio_repository, mock_stock_repository):
        """Test getting a non-existent portfolio by ID."""
        # Configure mock repository
        mock_portfolio_repository.get_by_id.return_value = None
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Get non-existent portfolio
        portfolio = service.get_portfolio("nonexistent-id")
        
        # Verify repository was called correctly
        mock_portfolio_repository.get_by_id.assert_called_once_with("nonexistent-id")
        
        # Verify portfolio was not found
        assert portfolio is None
    
    def test_get_portfolio_or_raise(self, mock_portfolio_repository, mock_stock_repository, sample_portfolio):
        """Test getting a portfolio by ID or raising an exception."""
        # Configure mock repository
        mock_portfolio_repository.get_by_id.return_value = sample_portfolio
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Get portfolio
        portfolio = service.get_portfolio_or_raise(sample_portfolio.id)
        
        # Verify repository was called correctly
        mock_portfolio_repository.get_by_id.assert_called_once_with(sample_portfolio.id)
        
        # Verify portfolio was returned
        assert portfolio is not None
        assert portfolio.id == sample_portfolio.id
        assert portfolio.name == "Test Portfolio"
    
    def test_get_portfolio_or_raise_not_found(self, mock_portfolio_repository, mock_stock_repository):
        """Test getting a non-existent portfolio by ID or raising an exception."""
        # Configure mock repository
        mock_portfolio_repository.get_by_id.return_value = None
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Get non-existent portfolio
        with pytest.raises(DataNotFoundError):
            service.get_portfolio_or_raise("nonexistent-id")
        
        # Verify repository was called correctly
        mock_portfolio_repository.get_by_id.assert_called_once_with("nonexistent-id")
    
    def test_get_portfolios_by_owner(self, mock_portfolio_repository, mock_stock_repository, sample_portfolio):
        """Test getting portfolios by owner ID."""
        # Configure mock repository
        mock_portfolio_repository.get_by_owner.return_value = [sample_portfolio]
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Get portfolios by owner
        portfolios = service.get_portfolios_by_owner(sample_portfolio.owner_id)
        
        # Verify repository was called correctly
        mock_portfolio_repository.get_by_owner.assert_called_once_with(sample_portfolio.owner_id, 10, 0)
        
        # Verify portfolios were returned
        assert len(portfolios) == 1
        assert portfolios[0].id == sample_portfolio.id
        assert portfolios[0].name == "Test Portfolio"
    
    def test_create_portfolio(self, mock_portfolio_repository, mock_stock_repository, sample_portfolio):
        """Test creating a portfolio."""
        # Configure mock repository
        mock_portfolio_repository.create.return_value = sample_portfolio
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Create portfolio
        created_portfolio = service.create_portfolio(sample_portfolio)
        
        # Verify repository was called correctly
        mock_portfolio_repository.create.assert_called_once()
        
        # Verify portfolio was created
        assert created_portfolio is not None
        assert created_portfolio.id == sample_portfolio.id
        assert created_portfolio.name == "Test Portfolio"
    
    def test_update_portfolio(self, mock_portfolio_repository, mock_stock_repository, sample_portfolio):
        """Test updating a portfolio."""
        # Configure mock repository
        mock_portfolio_repository.get_by_id.return_value = sample_portfolio
        mock_portfolio_repository.update.return_value = sample_portfolio
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Update portfolio
        updated_portfolio = service.update_portfolio(sample_portfolio)
        
        # Verify repository was called correctly
        mock_portfolio_repository.get_by_id.assert_called_once_with(sample_portfolio.id)
        mock_portfolio_repository.update.assert_called_once_with(sample_portfolio)
        
        # Verify portfolio was updated
        assert updated_portfolio is not None
        assert updated_portfolio.id == sample_portfolio.id
        assert updated_portfolio.name == "Test Portfolio"
    
    def test_update_portfolio_not_found(self, mock_portfolio_repository, mock_stock_repository, sample_portfolio):
        """Test updating a non-existent portfolio."""
        # Configure mock repository
        mock_portfolio_repository.get_by_id.return_value = None
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Update non-existent portfolio
        with pytest.raises(DataNotFoundError):
            service.update_portfolio(sample_portfolio)
        
        # Verify repository was called correctly
        mock_portfolio_repository.get_by_id.assert_called_once_with(sample_portfolio.id)
        mock_portfolio_repository.update.assert_not_called()
    
    def test_delete_portfolio(self, mock_portfolio_repository, mock_stock_repository):
        """Test deleting a portfolio."""
        # Configure mock repository
        mock_portfolio_repository.delete.return_value = True
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Delete portfolio
        result = service.delete_portfolio("portfolio-id")
        
        # Verify repository was called correctly
        mock_portfolio_repository.delete.assert_called_once_with("portfolio-id")
        
        # Verify portfolio was deleted
        assert result is True
    
    def test_add_position(self, mock_portfolio_repository, mock_stock_repository, sample_portfolio, sample_position):
        """Test adding a position to a portfolio."""
        # Configure mock repositories
        mock_stock_repository.get_by_symbol.return_value = Mock()
        mock_portfolio_repository.add_position.return_value = sample_portfolio
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Add position
        updated_portfolio = service.add_position(sample_portfolio.id, sample_position)
        
        # Verify repositories were called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with(sample_position.symbol)
        mock_portfolio_repository.add_position.assert_called_once_with(sample_portfolio.id, sample_position)
        
        # Verify portfolio was updated
        assert updated_portfolio is not None
        assert updated_portfolio.id == sample_portfolio.id
    
    def test_add_position_stock_not_found(self, mock_portfolio_repository, mock_stock_repository, sample_portfolio, sample_position):
        """Test adding a position with a non-existent stock."""
        # Configure mock repositories
        mock_stock_repository.get_by_symbol.return_value = None
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Add position with non-existent stock
        with pytest.raises(DataNotFoundError):
            service.add_position(sample_portfolio.id, sample_position)
        
        # Verify repositories were called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with(sample_position.symbol)
        mock_portfolio_repository.add_position.assert_not_called()
    
    def test_remove_position(self, mock_portfolio_repository, mock_stock_repository, sample_portfolio):
        """Test removing a position from a portfolio."""
        # Configure mock repository
        mock_portfolio_repository.remove_position.return_value = sample_portfolio
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Remove position
        updated_portfolio = service.remove_position(sample_portfolio.id, "AAPL")
        
        # Verify repository was called correctly
        mock_portfolio_repository.remove_position.assert_called_once_with(sample_portfolio.id, "AAPL")
        
        # Verify portfolio was updated
        assert updated_portfolio is not None
        assert updated_portfolio.id == sample_portfolio.id
    
    def test_add_transaction(self, mock_portfolio_repository, mock_stock_repository, sample_portfolio, sample_transaction):
        """Test adding a transaction to a portfolio."""
        # Configure mock repositories
        mock_stock_repository.get_by_symbol.return_value = Mock()
        mock_portfolio_repository.add_transaction.return_value = sample_portfolio
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Add transaction
        updated_portfolio = service.add_transaction(sample_portfolio.id, sample_transaction)
        
        # Verify repositories were called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with(sample_transaction.symbol)
        mock_portfolio_repository.add_transaction.assert_called_once_with(sample_portfolio.id, sample_transaction)
        
        # Verify portfolio was updated
        assert updated_portfolio is not None
        assert updated_portfolio.id == sample_portfolio.id
    
    def test_add_transaction_stock_not_found(self, mock_portfolio_repository, mock_stock_repository, sample_portfolio, sample_transaction):
        """Test adding a transaction with a non-existent stock."""
        # Configure mock repositories
        mock_stock_repository.get_by_symbol.return_value = None
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Add transaction with non-existent stock
        with pytest.raises(DataNotFoundError):
            service.add_transaction(sample_portfolio.id, sample_transaction)
        
        # Verify repositories were called correctly
        mock_stock_repository.get_by_symbol.assert_called_once_with(sample_transaction.symbol)
        mock_portfolio_repository.add_transaction.assert_not_called()
    
    def test_get_transactions(self, mock_portfolio_repository, mock_stock_repository, sample_transaction):
        """Test getting transactions for a portfolio."""
        # Configure mock repository
        mock_portfolio_repository.get_transactions.return_value = [sample_transaction]
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Get transactions
        transactions = service.get_transactions("portfolio-id")
        
        # Verify repository was called correctly
        mock_portfolio_repository.get_transactions.assert_called_once_with("portfolio-id", 50, 0)
        
        # Verify transactions were returned
        assert len(transactions) == 1
        assert transactions[0].id == sample_transaction.id
        assert transactions[0].symbol == "AAPL"
    
    def test_get_positions(self, mock_portfolio_repository, mock_stock_repository, sample_position):
        """Test getting positions for a portfolio."""
        # Configure mock repository
        mock_portfolio_repository.get_positions.return_value = {"AAPL": sample_position}
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Get positions
        positions = service.get_positions("portfolio-id")
        
        # Verify repository was called correctly
        mock_portfolio_repository.get_positions.assert_called_once_with("portfolio-id")
        
        # Verify positions were returned
        assert len(positions) == 1
        assert "AAPL" in positions
        assert positions["AAPL"].symbol == "AAPL"
        assert positions["AAPL"].quantity == 10.0
    
    def test_calculate_portfolio_value(self, mock_portfolio_repository, mock_stock_repository, sample_portfolio, sample_position):
        """Test calculating the value of a portfolio."""
        # Configure mock repositories
        mock_portfolio_repository.get_by_id.return_value = sample_portfolio
        mock_portfolio_repository.get_positions.return_value = {"AAPL": sample_position}
        
        # Create a mock latest price
        latest_price = StockPrice(
            date=datetime.now(),
            open=160.0,
            high=165.0,
            low=159.0,
            close=163.0,
            volume=1000000
        )
        mock_stock_repository.get_latest_price.return_value = latest_price
        
        # Create service with mock repositories
        service = PortfolioService(mock_portfolio_repository, mock_stock_repository)
        
        # Calculate portfolio value
        value = service.calculate_portfolio_value(sample_portfolio.id)
        
        # Verify repositories were called correctly
        mock_portfolio_repository.get_by_id.assert_called_once_with(sample_portfolio.id)
        mock_portfolio_repository.get_positions.assert_called_once_with(sample_portfolio.id)
        mock_stock_repository.get_latest_price.assert_called_once_with("AAPL")
        
        # Verify value was calculated correctly
        # Cash balance (10000.0) + Position value (10 shares * $163.0 = 1630.0)
        expected_value = 10000.0 + (10.0 * 163.0)
        assert value == expected_value
