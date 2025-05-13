"""Stock schemas for STOCKER Pro API.

This module provides Pydantic models for stock-related requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum


class ExchangeEnum(str, Enum):
    """Exchange enumeration.
    
    This enumeration represents the possible stock exchanges.
    """
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    AMEX = "AMEX"
    LSE = "LSE"
    TSX = "TSX"
    OTHER = "OTHER"


class SectorEnum(str, Enum):
    """Sector enumeration.
    
    This enumeration represents the possible stock sectors.
    """
    TECHNOLOGY = "TECHNOLOGY"
    FINANCIAL = "FINANCIAL"
    HEALTHCARE = "HEALTHCARE"
    CONSUMER_CYCLICAL = "CONSUMER_CYCLICAL"
    CONSUMER_DEFENSIVE = "CONSUMER_DEFENSIVE"
    INDUSTRIALS = "INDUSTRIALS"
    ENERGY = "ENERGY"
    UTILITIES = "UTILITIES"
    REAL_ESTATE = "REAL_ESTATE"
    COMMUNICATION_SERVICES = "COMMUNICATION_SERVICES"
    MATERIALS = "MATERIALS"
    OTHER = "OTHER"


class StockPriceBase(BaseModel):
    """Stock price base schema.
    
    This schema represents the base stock price attributes.
    """
    date: datetime = Field(..., description="Price date")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")
    adjusted_close: Optional[float] = Field(None, description="Adjusted closing price")
    
    # Validator to ensure prices are positive
    @validator("open", "high", "low", "close", "adjusted_close")
    def price_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("Price must be positive")
        return v
    
    # Validator to ensure high is greater than or equal to low
    @root_validator
    def high_greater_than_low(cls, values):
        high, low = values.get("high"), values.get("low")
        if high is not None and low is not None and high < low:
            raise ValueError("High price must be greater than or equal to low price")
        return values


class StockPriceCreate(StockPriceBase):
    """Stock price creation schema.
    
    This schema represents a request to create a new stock price.
    """
    pass


class StockPriceResponse(StockPriceBase):
    """Stock price response schema.
    
    This schema represents a stock price in API responses.
    """
    class Config:
        orm_mode = True


class StockBase(BaseModel):
    """Stock base schema.
    
    This schema represents the base stock attributes.
    """
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    name: str = Field(..., min_length=1, max_length=100, description="Stock name")
    exchange: ExchangeEnum = Field(ExchangeEnum.OTHER, description="Stock exchange")
    sector: SectorEnum = Field(SectorEnum.OTHER, description="Stock sector")
    industry: Optional[str] = Field(None, max_length=100, description="Stock industry")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    pe_ratio: Optional[float] = Field(None, description="Price-to-earnings ratio")
    dividend_yield: Optional[float] = Field(None, description="Dividend yield")
    beta: Optional[float] = Field(None, description="Beta value")
    description: Optional[str] = Field(None, description="Stock description")
    
    # Validator to ensure symbol is uppercase
    @validator("symbol")
    def symbol_uppercase(cls, v):
        return v.upper()


class StockCreate(StockBase):
    """Stock creation schema.
    
    This schema represents a request to create a new stock.
    """
    pass


class StockUpdate(BaseModel):
    """Stock update schema.
    
    This schema represents a request to update an existing stock.
    """
    name: Optional[str] = None
    exchange: Optional[ExchangeEnum] = None
    sector: Optional[SectorEnum] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    description: Optional[str] = None


class StockDataResponse(BaseModel):
    """Stock data response schema.
    
    This schema represents stock data with price history in API responses.
    """
    symbol: str
    prices: List[StockPriceResponse]
    timeframe: str = "1d"
    
    class Config:
        orm_mode = True


class StockResponse(StockBase):
    """Stock response schema.
    
    This schema represents a stock in API responses.
    """
    last_updated: Optional[datetime] = None
    data: Optional[StockDataResponse] = None
    
    class Config:
        orm_mode = True
