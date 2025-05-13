"""Strategy schemas for STOCKER Pro API.

This module provides Pydantic models for strategy-related requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum
from uuid import uuid4


class StrategyTypeEnum(str, Enum):
    """Strategy type enumeration.
    
    This enumeration represents the possible strategy types.
    """
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"
    BREAKOUT = "breakout"
    PAIRS_TRADING = "pairs_trading"
    ARBITRAGE = "arbitrage"
    FUNDAMENTAL = "fundamental"
    CUSTOM = "custom"


class SignalTypeEnum(str, Enum):
    """Signal type enumeration.
    
    This enumeration represents the possible signal types.
    """
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class StrategyParameterBase(BaseModel):
    """Strategy parameter base schema.
    
    This schema represents the base strategy parameter attributes.
    """
    name: str = Field(..., min_length=1, max_length=50, description="Parameter name")
    type: str = Field(..., description="Parameter type (int, float, string, bool)")
    value: Any = Field(..., description="Parameter value")
    description: Optional[str] = Field(None, description="Parameter description")
    min_value: Optional[Any] = Field(None, description="Minimum value")
    max_value: Optional[Any] = Field(None, description="Maximum value")
    options: Optional[List[Any]] = Field(None, description="Possible options")


class SignalBase(BaseModel):
    """Signal base schema.
    
    This schema represents the base signal attributes.
    """
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    date: datetime = Field(..., description="Signal date")
    type: SignalTypeEnum = Field(..., description="Signal type")
    confidence: float = Field(..., ge=0, le=1, description="Signal confidence (0-1)")
    price: Optional[float] = Field(None, ge=0, description="Signal price")
    notes: Optional[str] = Field(None, description="Signal notes")
    
    # Validator to ensure symbol is uppercase
    @validator("symbol")
    def symbol_uppercase(cls, v):
        return v.upper()


class SignalCreate(SignalBase):
    """Signal creation schema.
    
    This schema represents a request to create a new signal.
    """
    strategy_id: str = Field(..., description="Strategy ID")
    id: Optional[str] = Field(None, description="Signal ID")
    
    # Generate ID if not provided
    @validator("id", pre=True, always=True)
    def generate_id(cls, v):
        if v is None:
            return str(uuid4())
        return v


class SignalResponse(SignalBase):
    """Signal response schema.
    
    This schema represents a signal in API responses.
    """
    id: str
    strategy_id: str
    
    class Config:
        orm_mode = True


class StrategyBase(BaseModel):
    """Strategy base schema.
    
    This schema represents the base strategy attributes.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Strategy name")
    description: Optional[str] = Field(None, description="Strategy description")
    type: StrategyTypeEnum = Field(..., description="Strategy type")
    creator_id: Optional[str] = Field(None, description="Strategy creator ID")
    is_public: bool = Field(False, description="Whether the strategy is public")
    parameters: Dict[str, StrategyParameterBase] = Field(default_factory=dict, description="Strategy parameters")
    code: Optional[str] = Field(None, description="Strategy code")


class StrategyCreate(StrategyBase):
    """Strategy creation schema.
    
    This schema represents a request to create a new strategy.
    """
    id: Optional[str] = Field(None, description="Strategy ID")
    
    # Generate ID if not provided
    @validator("id", pre=True, always=True)
    def generate_id(cls, v):
        if v is None:
            return str(uuid4())
        return v


class StrategyUpdate(BaseModel):
    """Strategy update schema.
    
    This schema represents a request to update an existing strategy.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[StrategyTypeEnum] = None
    is_public: Optional[bool] = None
    parameters: Optional[Dict[str, StrategyParameterBase]] = None
    code: Optional[str] = None


class StrategyResponse(StrategyBase):
    """Strategy response schema.
    
    This schema represents a strategy in API responses.
    """
    id: str
    created_at: datetime
    last_updated: Optional[datetime] = None
    last_run: Optional[datetime] = None
    signals: Optional[List[SignalResponse]] = Field(default_factory=list)
    
    class Config:
        orm_mode = True


class StrategyRunRequest(BaseModel):
    """Strategy run request schema.
    
    This schema represents a request to run a strategy.
    """
    symbols: Optional[List[str]] = Field(None, description="Symbols to run the strategy on")
    start_date: Optional[datetime] = Field(None, description="Start date for the strategy run")
    end_date: Optional[datetime] = Field(None, description="End date for the strategy run")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Override parameters for this run")
    
    # Validator to ensure symbols are uppercase
    @validator("symbols")
    def symbols_uppercase(cls, v):
        if v is not None:
            return [symbol.upper() for symbol in v]
        return v
