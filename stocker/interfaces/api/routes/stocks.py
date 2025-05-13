"""Stock routes for STOCKER Pro API.

This module provides route handlers for stock-related endpoints.
"""

from datetime import datetime, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path

from stocker.core.logging import get_logger
from stocker.domain.user import User
from stocker.interfaces.api.dependencies import (
    get_stock_service,
    get_current_active_user,
    get_current_admin_user
)
from stocker.interfaces.api.schemas.stocks import (
    StockCreate,
    StockUpdate,
    StockResponse,
    StockPriceCreate,
    StockPriceResponse,
    StockDataResponse
)
from stocker.services.stock_service import StockService

# Initialize router
router = APIRouter()

# Initialize logger
logger = get_logger(__name__)


@router.post("/", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
async def create_stock(
    stock_data: StockCreate,
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Create a new stock.
    
    Args:
        stock_data: Stock creation data
        stock_service: Stock service instance
        current_user: Current authenticated user
        
    Returns:
        Created stock
        
    Raises:
        HTTPException: If stock creation fails
    """
    # Check if stock already exists
    existing_stock = stock_service.get_stock(stock_data.symbol)
    if existing_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock with symbol {stock_data.symbol} already exists"
        )
    
    # Create stock
    stock = stock_service.create_stock(
        symbol=stock_data.symbol,
        name=stock_data.name,
        exchange=stock_data.exchange.value,
        sector=stock_data.sector.value,
        industry=stock_data.industry,
        market_cap=stock_data.market_cap,
        pe_ratio=stock_data.pe_ratio,
        dividend_yield=stock_data.dividend_yield,
        beta=stock_data.beta,
        description=stock_data.description
    )
    
    logger.info(f"Stock {stock.symbol} created by user {current_user.id}")
    return stock


@router.get("/", response_model=List[StockResponse])
async def get_stocks(
    skip: int = Query(0, ge=0, description="Skip N stocks"),
    limit: int = Query(100, ge=1, le=1000, description="Limit to N stocks"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get all stocks with optional filtering.
    
    Args:
        skip: Number of stocks to skip
        limit: Maximum number of stocks to return
        exchange: Filter by exchange
        sector: Filter by sector
        stock_service: Stock service instance
        current_user: Current authenticated user
        
    Returns:
        List of stocks
    """
    stocks = stock_service.get_stocks(
        skip=skip,
        limit=limit,
        exchange=exchange,
        sector=sector
    )
    return stocks


@router.get("/{symbol}", response_model=StockResponse)
async def get_stock(
    symbol: str = Path(..., description="Stock symbol"),
    include_prices: bool = Query(False, description="Include price history"),
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get a stock by symbol.
    
    Args:
        symbol: Stock symbol
        include_prices: Whether to include price history
        stock_service: Stock service instance
        current_user: Current authenticated user
        
    Returns:
        Stock
        
    Raises:
        HTTPException: If stock not found
    """
    stock = stock_service.get_stock(symbol, include_prices=include_prices)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol {symbol} not found"
        )
    
    return stock


@router.put("/{symbol}", response_model=StockResponse)
async def update_stock(
    stock_data: StockUpdate,
    symbol: str = Path(..., description="Stock symbol"),
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Update a stock.
    
    Args:
        stock_data: Stock update data
        symbol: Stock symbol
        stock_service: Stock service instance
        current_user: Current authenticated user
        
    Returns:
        Updated stock
        
    Raises:
        HTTPException: If stock not found
    """
    # Check if stock exists
    existing_stock = stock_service.get_stock(symbol)
    if not existing_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol {symbol} not found"
        )
    
    # Update stock
    updated_stock = stock_service.update_stock(
        symbol=symbol,
        name=stock_data.name,
        exchange=stock_data.exchange.value if stock_data.exchange else None,
        sector=stock_data.sector.value if stock_data.sector else None,
        industry=stock_data.industry,
        market_cap=stock_data.market_cap,
        pe_ratio=stock_data.pe_ratio,
        dividend_yield=stock_data.dividend_yield,
        beta=stock_data.beta,
        description=stock_data.description
    )
    
    logger.info(f"Stock {symbol} updated by user {current_user.id}")
    return updated_stock


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock(
    symbol: str = Path(..., description="Stock symbol"),
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Delete a stock.
    
    Args:
        symbol: Stock symbol
        stock_service: Stock service instance
        current_user: Current admin user
        
    Returns:
        No content
        
    Raises:
        HTTPException: If stock not found
    """
    # Check if stock exists
    existing_stock = stock_service.get_stock(symbol)
    if not existing_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol {symbol} not found"
        )
    
    # Delete stock
    stock_service.delete_stock(symbol)
    
    logger.info(f"Stock {symbol} deleted by admin {current_user.id}")
    return None


@router.post("/{symbol}/prices", response_model=StockPriceResponse, status_code=status.HTTP_201_CREATED)
async def add_stock_price(
    price_data: StockPriceCreate,
    symbol: str = Path(..., description="Stock symbol"),
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Add a price entry for a stock.
    
    Args:
        price_data: Stock price creation data
        symbol: Stock symbol
        stock_service: Stock service instance
        current_user: Current authenticated user
        
    Returns:
        Created stock price
        
    Raises:
        HTTPException: If stock not found or price already exists
    """
    # Check if stock exists
    existing_stock = stock_service.get_stock(symbol)
    if not existing_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol {symbol} not found"
        )
    
    # Check if price already exists for this date
    existing_price = stock_service.get_stock_price(symbol, price_data.date)
    if existing_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Price already exists for {symbol} on {price_data.date}"
        )
    
    # Add price
    price = stock_service.add_stock_price(
        symbol=symbol,
        date=price_data.date,
        open_price=price_data.open,
        high=price_data.high,
        low=price_data.low,
        close=price_data.close,
        volume=price_data.volume,
        adjusted_close=price_data.adjusted_close
    )
    
    logger.info(f"Price added for stock {symbol} by user {current_user.id}")
    return price


@router.get("/{symbol}/prices", response_model=StockDataResponse)
async def get_stock_prices(
    symbol: str = Path(..., description="Stock symbol"),
    start_date: Optional[datetime] = Query(None, description="Start date for price history"),
    end_date: Optional[datetime] = Query(None, description="End date for price history"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of prices to return"),
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get price history for a stock.
    
    Args:
        symbol: Stock symbol
        start_date: Start date for price history
        end_date: End date for price history
        limit: Maximum number of prices to return
        stock_service: Stock service instance
        current_user: Current authenticated user
        
    Returns:
        Stock data with price history
        
    Raises:
        HTTPException: If stock not found
    """
    # Set default dates if not provided
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    
    # Get stock with prices
    stock = stock_service.get_stock(symbol, include_prices=True)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol {symbol} not found"
        )
    
    # Filter prices by date range
    filtered_prices = [
        price for price in stock.prices
        if start_date <= price.date <= end_date
    ]
    
    # Limit number of prices
    limited_prices = filtered_prices[:limit]
    
    # Return stock data
    return {
        "symbol": symbol,
        "prices": limited_prices,
        "timeframe": "1d"
    }


@router.delete("/{symbol}/prices/{date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_price(
    symbol: str = Path(..., description="Stock symbol"),
    date: datetime = Path(..., description="Price date"),
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Delete a price entry for a stock.
    
    Args:
        symbol: Stock symbol
        date: Price date
        stock_service: Stock service instance
        current_user: Current admin user
        
    Returns:
        No content
        
    Raises:
        HTTPException: If stock or price not found
    """
    # Check if stock exists
    existing_stock = stock_service.get_stock(symbol)
    if not existing_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol {symbol} not found"
        )
    
    # Check if price exists
    existing_price = stock_service.get_stock_price(symbol, date)
    if not existing_price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Price not found for {symbol} on {date}"
        )
    
    # Delete price
    stock_service.delete_stock_price(symbol, date)
    
    logger.info(f"Price for stock {symbol} on {date} deleted by admin {current_user.id}")
    return None


@router.post("/{symbol}/refresh", response_model=StockResponse)
async def refresh_stock_data(
    symbol: str = Path(..., description="Stock symbol"),
    days: int = Query(30, ge=1, le=365, description="Number of days of price history to fetch"),
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Refresh stock data from external sources.
    
    Args:
        symbol: Stock symbol
        days: Number of days of price history to fetch
        stock_service: Stock service instance
        current_user: Current authenticated user
        
    Returns:
        Updated stock
        
    Raises:
        HTTPException: If stock not found or refresh fails
    """
    # Check if stock exists
    existing_stock = stock_service.get_stock(symbol)
    if not existing_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol {symbol} not found"
        )
    
    try:
        # Refresh stock data
        updated_stock = stock_service.refresh_stock_data(symbol, days=days)
        
        logger.info(f"Stock {symbol} data refreshed by user {current_user.id}")
        return updated_stock
    except Exception as e:
        logger.error(f"Failed to refresh stock {symbol} data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh stock data: {str(e)}"
        )
