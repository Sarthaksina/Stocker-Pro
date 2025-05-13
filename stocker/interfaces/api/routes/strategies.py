"""Strategy routes for STOCKER Pro API.

This module provides route handlers for strategy-related endpoints.
"""

from datetime import datetime, timedelta
from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body

from stocker.core.logging import get_logger
from stocker.domain.user import User
from stocker.interfaces.api.dependencies import (
    get_strategy_service,
    get_stock_service,
    get_current_active_user
)
from stocker.interfaces.api.schemas.strategies import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    SignalCreate,
    SignalResponse,
    StrategyRunRequest
)
from stocker.services.strategy_service import StrategyService
from stocker.services.stock_service import StockService

# Initialize router
router = APIRouter()

# Initialize logger
logger = get_logger(__name__)


@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy_data: StrategyCreate,
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Create a new strategy.
    
    Args:
        strategy_data: Strategy creation data
        strategy_service: Strategy service instance
        current_user: Current authenticated user
        
    Returns:
        Created strategy
        
    Raises:
        HTTPException: If strategy creation fails
    """
    # Set creator ID to current user if not provided
    if not strategy_data.creator_id:
        strategy_data.creator_id = current_user.id
    
    # Check if user is authorized to create strategy for another user
    if strategy_data.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create strategy for another user"
        )
    
    # Create strategy
    strategy = strategy_service.create_strategy(
        name=strategy_data.name,
        description=strategy_data.description,
        type=strategy_data.type.value,
        creator_id=strategy_data.creator_id,
        is_public=strategy_data.is_public,
        parameters={k: v.dict() for k, v in strategy_data.parameters.items()},
        code=strategy_data.code,
        id=strategy_data.id
    )
    
    logger.info(f"Strategy {strategy.id} created by user {current_user.id}")
    return strategy


@router.get("/", response_model=List[StrategyResponse])
async def get_strategies(
    skip: int = Query(0, ge=0, description="Skip N strategies"),
    limit: int = Query(100, ge=1, le=1000, description="Limit to N strategies"),
    creator_id: Optional[str] = Query(None, description="Filter by creator ID"),
    type: Optional[str] = Query(None, description="Filter by strategy type"),
    include_public: bool = Query(True, description="Include public strategies"),
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get all strategies with optional filtering.
    
    Args:
        skip: Number of strategies to skip
        limit: Maximum number of strategies to return
        creator_id: Filter by creator ID
        type: Filter by strategy type
        include_public: Include public strategies
        strategy_service: Strategy service instance
        current_user: Current authenticated user
        
    Returns:
        List of strategies
    """
    # Get strategies
    strategies = strategy_service.get_strategies(
        skip=skip,
        limit=limit,
        creator_id=creator_id,
        type=type,
        include_public=include_public,
        user_id=current_user.id
    )
    
    return strategies


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    include_signals: bool = Query(False, description="Include signals"),
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get a strategy by ID.
    
    Args:
        strategy_id: Strategy ID
        include_signals: Whether to include signals
        strategy_service: Strategy service instance
        current_user: Current authenticated user
        
    Returns:
        Strategy
        
    Raises:
        HTTPException: If strategy not found or access denied
    """
    # Get strategy
    strategy = strategy_service.get_strategy(
        strategy_id=strategy_id,
        include_signals=include_signals
    )
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy with ID {strategy_id} not found"
        )
    
    # Check if user is authorized to view strategy
    if not strategy.is_public and strategy.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this strategy"
        )
    
    return strategy


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_data: StrategyUpdate,
    strategy_id: str = Path(..., description="Strategy ID"),
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Update a strategy.
    
    Args:
        strategy_data: Strategy update data
        strategy_id: Strategy ID
        strategy_service: Strategy service instance
        current_user: Current authenticated user
        
    Returns:
        Updated strategy
        
    Raises:
        HTTPException: If strategy not found or access denied
    """
    # Get strategy
    strategy = strategy_service.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy with ID {strategy_id} not found"
        )
    
    # Check if user is authorized to update strategy
    if strategy.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this strategy"
        )
    
    # Update strategy
    updated_strategy = strategy_service.update_strategy(
        strategy_id=strategy_id,
        name=strategy_data.name,
        description=strategy_data.description,
        type=strategy_data.type.value if strategy_data.type else None,
        is_public=strategy_data.is_public,
        parameters={k: v.dict() for k, v in strategy_data.parameters.items()} if strategy_data.parameters else None,
        code=strategy_data.code
    )
    
    logger.info(f"Strategy {strategy_id} updated by user {current_user.id}")
    return updated_strategy


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Delete a strategy.
    
    Args:
        strategy_id: Strategy ID
        strategy_service: Strategy service instance
        current_user: Current authenticated user
        
    Returns:
        No content
        
    Raises:
        HTTPException: If strategy not found or access denied
    """
    # Get strategy
    strategy = strategy_service.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy with ID {strategy_id} not found"
        )
    
    # Check if user is authorized to delete strategy
    if strategy.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this strategy"
        )
    
    # Delete strategy
    strategy_service.delete_strategy(strategy_id)
    
    logger.info(f"Strategy {strategy_id} deleted by user {current_user.id}")
    return None


@router.post("/{strategy_id}/run", response_model=List[SignalResponse])
async def run_strategy(
    run_request: StrategyRunRequest,
    strategy_id: str = Path(..., description="Strategy ID"),
    strategy_service: StrategyService = Depends(get_strategy_service),
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Run a strategy.
    
    Args:
        run_request: Strategy run request data
        strategy_id: Strategy ID
        strategy_service: Strategy service instance
        stock_service: Stock service instance
        current_user: Current authenticated user
        
    Returns:
        List of signals generated by the strategy
        
    Raises:
        HTTPException: If strategy not found, access denied, or run fails
    """
    # Get strategy
    strategy = strategy_service.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy with ID {strategy_id} not found"
        )
    
    # Check if user is authorized to run strategy
    if not strategy.is_public and strategy.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to run this strategy"
        )
    
    # Check if symbols exist
    if run_request.symbols:
        for symbol in run_request.symbols:
            stock = stock_service.get_stock(symbol)
            if not stock:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Stock with symbol {symbol} not found"
                )
    
    try:
        # Run strategy
        signals = strategy_service.run_strategy(
            strategy_id=strategy_id,
            symbols=run_request.symbols,
            start_date=run_request.start_date,
            end_date=run_request.end_date,
            parameters=run_request.parameters
        )
        
        logger.info(f"Strategy {strategy_id} run by user {current_user.id}")
        return signals
    except Exception as e:
        logger.error(f"Failed to run strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run strategy: {str(e)}"
        )


@router.post("/{strategy_id}/signals", response_model=SignalResponse, status_code=status.HTTP_201_CREATED)
async def add_signal(
    signal_data: SignalCreate,
    strategy_id: str = Path(..., description="Strategy ID"),
    strategy_service: StrategyService = Depends(get_strategy_service),
    stock_service: StockService = Depends(get_stock_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Add a signal to a strategy.
    
    Args:
        signal_data: Signal creation data
        strategy_id: Strategy ID
        strategy_service: Strategy service instance
        stock_service: Stock service instance
        current_user: Current authenticated user
        
    Returns:
        Created signal
        
    Raises:
        HTTPException: If strategy not found, access denied, or stock not found
    """
    # Get strategy
    strategy = strategy_service.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy with ID {strategy_id} not found"
        )
    
    # Check if user is authorized to update strategy
    if strategy.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this strategy"
        )
    
    # Check if stock exists
    stock = stock_service.get_stock(signal_data.symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol {signal_data.symbol} not found"
        )
    
    # Add signal
    signal = strategy_service.add_signal(
        strategy_id=strategy_id,
        symbol=signal_data.symbol,
        date=signal_data.date,
        signal_type=signal_data.type.value,
        confidence=signal_data.confidence,
        price=signal_data.price,
        notes=signal_data.notes,
        signal_id=signal_data.id
    )
    
    logger.info(f"Signal {signal.id} added to strategy {strategy_id} by user {current_user.id}")
    return signal


@router.get("/{strategy_id}/signals", response_model=List[SignalResponse])
async def get_signals(
    strategy_id: str = Path(..., description="Strategy ID"),
    skip: int = Query(0, ge=0, description="Skip N signals"),
    limit: int = Query(100, ge=1, le=1000, description="Limit to N signals"),
    start_date: Optional[datetime] = Query(None, description="Start date for signals"),
    end_date: Optional[datetime] = Query(None, description="End date for signals"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get all signals for a strategy.
    
    Args:
        strategy_id: Strategy ID
        skip: Number of signals to skip
        limit: Maximum number of signals to return
        start_date: Start date for signals
        end_date: End date for signals
        symbol: Filter by symbol
        signal_type: Filter by signal type
        strategy_service: Strategy service instance
        current_user: Current authenticated user
        
    Returns:
        List of signals
        
    Raises:
        HTTPException: If strategy not found or access denied
    """
    # Get strategy
    strategy = strategy_service.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy with ID {strategy_id} not found"
        )
    
    # Check if user is authorized to view strategy
    if not strategy.is_public and strategy.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this strategy"
        )
    
    # Get signals
    signals = strategy_service.get_signals(
        strategy_id=strategy_id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        symbol=symbol,
        signal_type=signal_type
    )
    
    return signals


@router.delete("/{strategy_id}/signals/{signal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_signal(
    strategy_id: str = Path(..., description="Strategy ID"),
    signal_id: str = Path(..., description="Signal ID"),
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Delete a signal from a strategy.
    
    Args:
        strategy_id: Strategy ID
        signal_id: Signal ID
        strategy_service: Strategy service instance
        current_user: Current authenticated user
        
    Returns:
        No content
        
    Raises:
        HTTPException: If strategy not found, access denied, or signal not found
    """
    # Get strategy
    strategy = strategy_service.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy with ID {strategy_id} not found"
        )
    
    # Check if user is authorized to update strategy
    if strategy.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this strategy"
        )
    
    # Check if signal exists
    signal = strategy_service.get_signal(strategy_id, signal_id)
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal with ID {signal_id} not found in strategy"
        )
    
    # Delete signal
    strategy_service.delete_signal(strategy_id, signal_id)
    
    logger.info(f"Signal {signal_id} deleted from strategy {strategy_id} by user {current_user.id}")
    return None
