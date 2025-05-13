"""Portfolio schemas for STOCKER Pro API.

This module provides Pydantic models for portfolio-related requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum
from uuid import uuid4


class PortfolioTypeEnum(str, Enum):
    """Portfolio type enumeration.
    
    This enumeration represents the possible portfolio types.
    """
    PERSONAL = "personal"
    RETIREMENT = "retirement"
    EDUCATION = "education"
    CORPORATE = "corporate"
    MODEL = "model"
    WATCHLIST = "watchlist"


class TransactionTypeEnum(str, Enum):
    """Transaction type enumeration.
    
    This enumeration represents the possible transaction types.
    """
    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    FEE = "fee"
    SPLIT = "split"
    TRANSFER = "transfer"


class PositionBase(BaseModel):
    """Position base schema.
    
    This schema represents the base position attributes.
    """
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    quantity: float = Field(..., gt=0, description="Position quantity")
    cost_basis: float = Field(..., ge=0, description="Position cost basis")
    open_date: Optional[datetime] = Field(None, description="Position open date")
    
    # Validator to ensure symbol is uppercase
    @validator("symbol")
    def symbol_uppercase(cls, v):
        return v.upper()


class PositionCreate(PositionBase):
    """Position creation schema.
    
    This schema represents a request to create a new position.
    """
    pass


class PositionResponse(PositionBase):
    """Position response schema.
    
    This schema represents a position in API responses.
    """
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    last_updated: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class TransactionBase(BaseModel):
    """Transaction base schema.
    
    This schema represents the base transaction attributes.
    """
    type: TransactionTypeEnum = Field(..., description="Transaction type")
    symbol: Optional[str] = Field(None, min_length=1, max_length=10, description="Stock symbol")
    date: datetime = Field(..., description="Transaction date")
    quantity: Optional[float] = Field(None, ge=0, description="Transaction quantity")
    price: Optional[float] = Field(None, ge=0, description="Transaction price")
    amount: float = Field(..., description="Transaction amount")
    fees: Optional[float] = Field(0.0, ge=0, description="Transaction fees")
    notes: Optional[str] = Field(None, description="Transaction notes")
    
    # Validator to ensure symbol is uppercase
    @validator("symbol")
    def symbol_uppercase(cls, v):
        if v is not None:
            return v.upper()
        return v
    
    # Validator to ensure buy/sell transactions have symbol, quantity, and price
    @root_validator
    def validate_transaction(cls, values):
        transaction_type = values.get("type")
        symbol = values.get("symbol")
        quantity = values.get("quantity")
        price = values.get("price")
        
        if transaction_type in [TransactionTypeEnum.BUY, TransactionTypeEnum.SELL]:
            if not symbol:
                raise ValueError(f"{transaction_type.value} transaction must have a symbol")
            if quantity is None:
                raise ValueError(f"{transaction_type.value} transaction must have a quantity")
            if price is None:
                raise ValueError(f"{transaction_type.value} transaction must have a price")
        
        return values


class TransactionCreate(TransactionBase):
    """Transaction creation schema.
    
    This schema represents a request to create a new transaction.
    """
    id: Optional[str] = Field(None, description="Transaction ID")
    
    # Generate ID if not provided
    @validator("id", pre=True, always=True)
    def generate_id(cls, v):
        if v is None:
            return str(uuid4())
        return v


class TransactionResponse(TransactionBase):
    """Transaction response schema.
    
    This schema represents a transaction in API responses.
    """
    id: str
    
    class Config:
        orm_mode = True


class PortfolioBase(BaseModel):
    """Portfolio base schema.
    
    This schema represents the base portfolio attributes.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")
    type: PortfolioTypeEnum = Field(PortfolioTypeEnum.PERSONAL, description="Portfolio type")
    owner_id: Optional[str] = Field(None, description="Portfolio owner ID")
    cash_balance: float = Field(0.0, ge=0, description="Portfolio cash balance")
    inception_date: Optional[datetime] = Field(None, description="Portfolio inception date")
    benchmark_symbol: Optional[str] = Field("SPY", description="Portfolio benchmark symbol")


class PortfolioCreate(PortfolioBase):
    """Portfolio creation schema.
    
    This schema represents a request to create a new portfolio.
    """
    id: Optional[str] = Field(None, description="Portfolio ID")
    
    # Generate ID if not provided
    @validator("id", pre=True, always=True)
    def generate_id(cls, v):
        if v is None:
            return str(uuid4())
        return v


class PortfolioUpdate(BaseModel):
    """Portfolio update schema.
    
    This schema represents a request to update an existing portfolio.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[PortfolioTypeEnum] = None
    cash_balance: Optional[float] = None
    benchmark_symbol: Optional[str] = None


class PortfolioResponse(PortfolioBase):
    """Portfolio response schema.
    
    This schema represents a portfolio in API responses.
    """
    id: str
    positions: Optional[Dict[str, PositionResponse]] = Field(default_factory=dict)
    transactions: Optional[List[TransactionResponse]] = Field(default_factory=list)
    last_updated: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class PortfolioPerformanceResponse(BaseModel):
    """Portfolio performance response schema.
    
    This schema represents portfolio performance metrics in API responses.
    """
    current_value: float
    cash_balance: float
    position_value: float
    position_count: int
    period_days: int
    period_return_pct: Optional[float] = None
    period_deposits: float
    period_withdrawals: float
    
    class Config:
        orm_mode = True
