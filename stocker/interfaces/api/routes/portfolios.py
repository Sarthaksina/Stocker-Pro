"""Portfolio routes for STOCKER Pro API.

This module provides route handlers for portfolio-related endpoints.
"""

from datetime import datetime, timedelta
from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path

from stocker.core.logging import get_logger
from stocker.domain.user import User
from stocker.interfaces.api.dependencies import (
    get_portfolio_service,
    get_stock_service,
    get_current_active_user
)
from stocker.interfaces.api.schemas.portfolios import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PositionCreate,
    PositionResponse,
    TransactionCreate,
    TransactionResponse,
    PortfolioPerformanceResponse
)
from stocker.services.portfolio_service import PortfolioService
from stocker.services.stock_service import StockService

# Initialize router
router = APIRouter()

# Initialize logger
logger = get_logger(__name__)


@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Create a new portfolio.
    
    Args:
        portfolio_data: Portfolio creation data
        portfolio_service: Portfolio service instance
        current_user: Current authenticated user
        
    Returns:
        Created portfolio
        
    Raises:
        HTTPException: If portfolio creation fails
    """
    # Set owner ID to current user if not provided
    if not portfolio_data.owner_id:
        portfolio_data.owner_id = current_user.id
    
    # Check if user is authorized to create portfolio for another user
    if portfolio_data.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create portfolio for another user"
        )
    
    # Create portfolio
    portfolio = portfolio_service.create_portfolio(
        name=portfolio_data.name,
        description=portfolio_data.description,
        type=portfolio_data.type.value,
        owner_id=portfolio_data.owner_id,
        cash_balance=portfolio_data.cash_balance,
        inception_date=portfolio_data.inception_date or datetime.now(),
        benchmark_symbol=portfolio_data.benchmark_symbol,
        id=portfolio_data.id
    )
    
    logger.info(f"Portfolio {portfolio.id} created by user {current_user.id}")
    return portfolio


@router.get("/", response_model=List[PortfolioResponse])
async def get_portfolios(
    skip: int = Query(0, ge=0, description="Skip N portfolios"),
    limit: int = Query(100, ge=1, le=1000, description="Limit to N portfolios"),
    owner_id: Optional[str] = Query(None, description="Filter by owner ID"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get all portfolios with optional filtering.
    
    Args:
        skip: Number of portfolios to skip
        limit: Maximum number of portfolios to return
        owner_id: Filter by owner ID
        portfolio_service: Portfolio service instance
        current_user: Current authenticated user
        
    Returns:
        List of portfolios
        
    Raises:
        HTTPException: If access denied
    """
    # Set owner ID to current user if not provided and not admin
    if not owner_id and not current_user.is_admin:
        owner_id = current_user.id
    
    # Check if user is authorized to view portfolios for another user
    if owner_id and owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view portfolios for another user"
        )
    
    # Get portfolios
    portfolios = portfolio_service.get_portfolios(
        skip=skip,
        limit=limit,
        owner_id=owner_id
    )
    
    return portfolios


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str = Path(..., description="Portfolio ID"),
    include_positions: bool = Query(True, description="Include positions"),
    include_transactions: bool = Query(False, description="Include transactions"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get a portfolio by ID.
    
    Args:
        portfolio_id: Portfolio ID
        include_positions: Whether to include positions
        include_transactions: Whether to include transactions
        portfolio_service: Portfolio service instance
        current_user: Current authenticated user
        
    Returns:
        Portfolio
        
    Raises:
        HTTPException: If portfolio not found or access denied
    """
    # Get portfolio
    portfolio = portfolio_service.get_portfolio(
        portfolio_id=portfolio_id,
        include_positions=include_positions,
        include_transactions=include_transactions
    )
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found"
        )
    
    # Check if user is authorized to view portfolio
    if portfolio.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this portfolio"
        )
    
    return portfolio


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_data: PortfolioUpdate,
    portfolio_id: str = Path(..., description="Portfolio ID"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Update a portfolio.
    
    Args:
        portfolio_data: Portfolio update data
        portfolio_id: Portfolio ID
        portfolio_service: Portfolio service instance
        current_user: Current authenticated user
        
    Returns:
        Updated portfolio
        
    Raises:
        HTTPException: If portfolio not found or access denied
    """
    # Get portfolio
    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found"
        )
    
    # Check if user is authorized to update portfolio
    if portfolio.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this portfolio"
        )
    
    # Update portfolio
    updated_portfolio = portfolio_service.update_portfolio(
        portfolio_id=portfolio_id,
        name=portfolio_data.name,
        description=portfolio_data.description,
        type=portfolio_data.type.value if portfolio_data.type else None,
        cash_balance=portfolio_data.cash_balance,
        benchmark_symbol=portfolio_data.benchmark_symbol
    )
    
    logger.info(f"Portfolio {portfolio_id} updated by user {current_user.id}")
    return updated_portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: str = Path(..., description="Portfolio ID"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Delete a portfolio.
    
    Args:
        portfolio_id: Portfolio ID
        portfolio_service: Portfolio service instance
        current_user: Current authenticated user
        
    Returns:
        No content
        
    Raises:
        HTTPException: If portfolio not found or access denied
    """
    # Get portfolio
    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found"
        )
    
    # Check if user is authorized to delete portfolio
    if portfolio.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this portfolio"
        )
    
    # Delete portfolio
    portfolio_service.delete_portfolio(portfolio_id)
    
    logger.info(f"Portfolio {portfolio_id} deleted by user {current_user.id}")
    return None


@router.post("/{portfolio_id}/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def add_position(
    position_data: PositionCreate,
    portfolio_id: str = Path(..., description="Portfolio ID"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Add a position to a portfolio.
    
    Args:
        position_data: Position creation data
        portfolio_id: Portfolio ID
        portfolio_service: Portfolio service instance
        stock_service: Stock service instance
        current_user: Current authenticated user
        
    Returns:
        Created position
        
    Raises:
        HTTPException: If portfolio not found, access denied, or stock not found
    """
    # Get portfolio
    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found"
        )
    
    # Check if user is authorized to update portfolio
    if portfolio.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this portfolio"
        )
    
    # Check if stock exists
    stock = stock_service.get_stock(position_data.symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol {position_data.symbol} not found"
        )
    
    # Add position
    position = portfolio_service.add_position(
        portfolio_id=portfolio_id,
        symbol=position_data.symbol,
        quantity=position_data.quantity,
        cost_basis=position_data.cost_basis,
        open_date=position_data.open_date or datetime.now()
    )
    
    logger.info(f"Position {position_data.symbol} added to portfolio {portfolio_id} by user {current_user.id}")
    return position


@router.get("/{portfolio_id}/positions", response_model=Dict[str, PositionResponse])
async def get_positions(
    portfolio_id: str = Path(..., description="Portfolio ID"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get all positions in a portfolio.
    
    Args:
        portfolio_id: Portfolio ID
        portfolio_service: Portfolio service instance
        current_user: Current authenticated user
        
    Returns:
        Dictionary of positions
        
    Raises:
        HTTPException: If portfolio not found or access denied
    """
    # Get portfolio with positions
    portfolio = portfolio_service.get_portfolio(portfolio_id, include_positions=True)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found"
        )
    
    # Check if user is authorized to view portfolio
    if portfolio.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this portfolio"
        )
    
    return portfolio.positions


@router.delete("/{portfolio_id}/positions/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_position(
    portfolio_id: str = Path(..., description="Portfolio ID"),
    symbol: str = Path(..., description="Stock symbol"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Remove a position from a portfolio.
    
    Args:
        portfolio_id: Portfolio ID
        symbol: Stock symbol
        portfolio_service: Portfolio service instance
        current_user: Current authenticated user
        
    Returns:
        No content
        
    Raises:
        HTTPException: If portfolio not found, access denied, or position not found
    """
    # Get portfolio
    portfolio = portfolio_service.get_portfolio(portfolio_id, include_positions=True)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found"
        )
    
    # Check if user is authorized to update portfolio
    if portfolio.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this portfolio"
        )
    
    # Check if position exists
    if symbol.upper() not in portfolio.positions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position with symbol {symbol} not found in portfolio"
        )
    
    # Remove position
    portfolio_service.remove_position(portfolio_id, symbol)
    
    logger.info(f"Position {symbol} removed from portfolio {portfolio_id} by user {current_user.id}")
    return None


@router.post("/{portfolio_id}/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def add_transaction(
    transaction_data: TransactionCreate,
    portfolio_id: str = Path(..., description="Portfolio ID"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Add a transaction to a portfolio.
    
    Args:
        transaction_data: Transaction creation data
        portfolio_id: Portfolio ID
        portfolio_service: Portfolio service instance
        stock_service: Stock service instance
        current_user: Current authenticated user
        
    Returns:
        Created transaction
        
    Raises:
        HTTPException: If portfolio not found, access denied, or stock not found
    """
    # Get portfolio
    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found"
        )
    
    # Check if user is authorized to update portfolio
    if portfolio.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this portfolio"
        )
    
    # Check if stock exists for buy/sell transactions
    if transaction_data.symbol and transaction_data.type.value in ["buy", "sell"]:
        stock = stock_service.get_stock(transaction_data.symbol)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock with symbol {transaction_data.symbol} not found"
            )
    
    # Add transaction
    transaction = portfolio_service.add_transaction(
        portfolio_id=portfolio_id,
        transaction_type=transaction_data.type.value,
        symbol=transaction_data.symbol,
        date=transaction_data.date,
        quantity=transaction_data.quantity,
        price=transaction_data.price,
        amount=transaction_data.amount,
        fees=transaction_data.fees,
        notes=transaction_data.notes,
        transaction_id=transaction_data.id
    )
    
    logger.info(f"Transaction {transaction.id} added to portfolio {portfolio_id} by user {current_user.id}")
    return transaction


@router.get("/{portfolio_id}/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    portfolio_id: str = Path(..., description="Portfolio ID"),
    skip: int = Query(0, ge=0, description="Skip N transactions"),
    limit: int = Query(100, ge=1, le=1000, description="Limit to N transactions"),
    start_date: Optional[datetime] = Query(None, description="Start date for transactions"),
    end_date: Optional[datetime] = Query(None, description="End date for transactions"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get all transactions in a portfolio.
    
    Args:
        portfolio_id: Portfolio ID
        skip: Number of transactions to skip
        limit: Maximum number of transactions to return
        start_date: Start date for transactions
        end_date: End date for transactions
        portfolio_service: Portfolio service instance
        current_user: Current authenticated user
        
    Returns:
        List of transactions
        
    Raises:
        HTTPException: If portfolio not found or access denied
    """
    # Get portfolio
    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found"
        )
    
    # Check if user is authorized to view portfolio
    if portfolio.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this portfolio"
        )
    
    # Get transactions
    transactions = portfolio_service.get_transactions(
        portfolio_id=portfolio_id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    
    return transactions


@router.delete("/{portfolio_id}/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    portfolio_id: str = Path(..., description="Portfolio ID"),
    transaction_id: str = Path(..., description="Transaction ID"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Delete a transaction from a portfolio.
    
    Args:
        portfolio_id: Portfolio ID
        transaction_id: Transaction ID
        portfolio_service: Portfolio service instance
        current_user: Current authenticated user
        
    Returns:
        No content
        
    Raises:
        HTTPException: If portfolio not found, access denied, or transaction not found
    """
    # Get portfolio
    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found"
        )
    
    # Check if user is authorized to update portfolio
    if portfolio.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this portfolio"
        )
    
    # Check if transaction exists
    transaction = portfolio_service.get_transaction(portfolio_id, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found in portfolio"
        )
    
    # Delete transaction
    portfolio_service.delete_transaction(portfolio_id, transaction_id)
    
    logger.info(f"Transaction {transaction_id} deleted from portfolio {portfolio_id} by user {current_user.id}")
    return None


@router.get("/{portfolio_id}/performance", response_model=PortfolioPerformanceResponse)
async def get_portfolio_performance(
    portfolio_id: str = Path(..., description="Portfolio ID"),
    period_days: int = Query(30, ge=1, le=3650, description="Performance period in days"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get portfolio performance metrics.
    
    Args:
        portfolio_id: Portfolio ID
        period_days: Performance period in days
        portfolio_service: Portfolio service instance
        current_user: Current authenticated user
        
    Returns:
        Portfolio performance metrics
        
    Raises:
        HTTPException: If portfolio not found or access denied
    """
    # Get portfolio
    portfolio = portfolio_service.get_portfolio(portfolio_id, include_positions=True)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found"
        )
    
    # Check if user is authorized to view portfolio
    if portfolio.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this portfolio"
        )
    
    # Get performance metrics
    performance = portfolio_service.get_portfolio_performance(portfolio_id, period_days=period_days)
    
    return performance
