"""Stock domain model for STOCKER Pro.

This module defines the core domain entities related to stocks and stock data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd


class Exchange(str, Enum):
    """Stock exchange enumeration."""
    NYSE = "NYSE"       # New York Stock Exchange
    NASDAQ = "NASDAQ"   # NASDAQ
    AMEX = "AMEX"       # American Stock Exchange
    BSE = "BSE"         # Bombay Stock Exchange
    NSE = "NSE"         # National Stock Exchange of India
    LSE = "LSE"         # London Stock Exchange
    TSX = "TSX"         # Toronto Stock Exchange
    HKEX = "HKEX"       # Hong Kong Stock Exchange
    SSE = "SSE"         # Shanghai Stock Exchange
    SZSE = "SZSE"       # Shenzhen Stock Exchange
    OTHER = "OTHER"     # Other exchanges


class Sector(str, Enum):
    """Stock sector enumeration."""
    TECHNOLOGY = "Technology"
    HEALTHCARE = "Healthcare"
    FINANCIALS = "Financials"
    CONSUMER_DISCRETIONARY = "Consumer Discretionary"
    CONSUMER_STAPLES = "Consumer Staples"
    INDUSTRIALS = "Industrials"
    ENERGY = "Energy"
    MATERIALS = "Materials"
    UTILITIES = "Utilities"
    REAL_ESTATE = "Real Estate"
    COMMUNICATION_SERVICES = "Communication Services"
    OTHER = "Other"


@dataclass
class StockPrice:
    """Stock price data point.
    
    This class represents a single price data point for a stock,
    typically corresponding to a specific time period (e.g., a day).
    
    Attributes:
        date: Date of the price data
        open: Opening price
        high: Highest price during the period
        low: Lowest price during the period
        close: Closing price
        volume: Trading volume
        adjusted_close: Adjusted closing price (accounting for splits, dividends)
    """
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None
    
    @property
    def range(self) -> float:
        """Calculate the price range for this data point."""
        return self.high - self.low
    
    @property
    def change(self) -> float:
        """Calculate the price change for this data point."""
        return self.close - self.open
    
    @property
    def change_percent(self) -> float:
        """Calculate the percentage price change for this data point."""
        if self.open == 0:
            return 0.0
        return (self.close - self.open) / self.open * 100.0


@dataclass
class StockData:
    """Collection of stock price data.
    
    This class represents a collection of price data points for a stock,
    typically over a period of time.
    
    Attributes:
        symbol: Stock symbol
        prices: List of price data points
        timeframe: Timeframe of the data (e.g., '1d', '1h')
        start_date: Start date of the data
        end_date: End date of the data
        dataframe: Pandas DataFrame representation of the data
    """
    symbol: str
    prices: List[StockPrice] = field(default_factory=list)
    timeframe: str = "1d"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    _dataframe: Optional[pd.DataFrame] = None
    
    def __post_init__(self):
        """Initialize start and end dates if not provided."""
        if self.prices and not self.start_date:
            self.start_date = min(price.date for price in self.prices)
        if self.prices and not self.end_date:
            self.end_date = max(price.date for price in self.prices)
    
    @property
    def dataframe(self) -> pd.DataFrame:
        """Get the data as a pandas DataFrame."""
        if self._dataframe is None:
            # Convert list of StockPrice objects to DataFrame
            data = [
                {
                    "date": price.date,
                    "open": price.open,
                    "high": price.high,
                    "low": price.low,
                    "close": price.close,
                    "volume": price.volume,
                    "adjusted_close": price.adjusted_close or price.close
                }
                for price in self.prices
            ]
            
            if data:
                self._dataframe = pd.DataFrame(data)
                self._dataframe.set_index("date", inplace=True)
                self._dataframe.sort_index(inplace=True)
            else:
                # Empty DataFrame with expected columns
                self._dataframe = pd.DataFrame(
                    columns=["open", "high", "low", "close", "volume", "adjusted_close"]
                )
        
        return self._dataframe
    
    @classmethod
    def from_dataframe(cls, symbol: str, df: pd.DataFrame, timeframe: str = "1d") -> "StockData":
        """Create StockData from a pandas DataFrame.
        
        Args:
            symbol: Stock symbol
            df: DataFrame with stock price data
            timeframe: Timeframe of the data
            
        Returns:
            StockData object
        """
        # Ensure DataFrame has expected columns
        required_columns = ["open", "high", "low", "close", "volume"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"DataFrame must have column: {col}")
        
        # Handle index
        if not isinstance(df.index, pd.DatetimeIndex):
            if "date" in df.columns:
                df = df.set_index("date")
            else:
                raise ValueError("DataFrame must have a DatetimeIndex or a 'date' column")
        
        # Create StockPrice objects
        prices = [
            StockPrice(
                date=row.name,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                adjusted_close=row.get("adjusted_close", row["close"])
            )
            for _, row in df.iterrows()
        ]
        
        # Create StockData object
        stock_data = cls(
            symbol=symbol,
            prices=prices,
            timeframe=timeframe,
            start_date=df.index.min() if not df.empty else None,
            end_date=df.index.max() if not df.empty else None
        )
        
        # Set DataFrame directly to avoid recomputation
        stock_data._dataframe = df
        
        return stock_data
    
    def add_price(self, price: StockPrice) -> None:
        """Add a price data point to the collection.
        
        Args:
            price: Price data point to add
        """
        self.prices.append(price)
        
        # Update start and end dates
        if self.start_date is None or price.date < self.start_date:
            self.start_date = price.date
        if self.end_date is None or price.date > self.end_date:
            self.end_date = price.date
        
        # Invalidate DataFrame cache
        self._dataframe = None
    
    def get_returns(self, period: str = "daily") -> pd.Series:
        """Calculate returns for the stock data.
        
        Args:
            period: Return period ('daily', 'weekly', 'monthly')
            
        Returns:
            Series of returns
        """
        df = self.dataframe
        
        if df.empty:
            return pd.Series(dtype=float)
        
        # Calculate returns based on period
        if period == "daily":
            returns = df["adjusted_close"].pct_change()
        elif period == "weekly":
            returns = df["adjusted_close"].resample("W").last().pct_change()
        elif period == "monthly":
            returns = df["adjusted_close"].resample("M").last().pct_change()
        else:
            raise ValueError(f"Invalid period: {period}. Must be 'daily', 'weekly', or 'monthly'")
        
        return returns.dropna()


@dataclass
class Stock:
    """Stock domain entity.
    
    This class represents a stock as a business entity, including
    its basic information and metadata.
    
    Attributes:
        symbol: Stock symbol
        name: Company name
        exchange: Stock exchange
        sector: Business sector
        industry: Specific industry
        market_cap: Market capitalization
        pe_ratio: Price-to-earnings ratio
        dividend_yield: Dividend yield percentage
        beta: Beta value (market volatility measure)
        description: Company description
        data: Stock price data
    """
    symbol: str
    name: str
    exchange: Exchange = Exchange.NYSE
    sector: Sector = Sector.OTHER
    industry: str = ""
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    description: str = ""
    data: Optional[StockData] = None
    
    @property
    def current_price(self) -> Optional[float]:
        """Get the most recent closing price."""
        if self.data and self.data.prices:
            return max(self.data.prices, key=lambda p: p.date).close
        return None
    
    @property
    def is_large_cap(self) -> bool:
        """Check if the stock is large cap (market cap > $10B)."""
        return self.market_cap is not None and self.market_cap > 10_000_000_000
    
    @property
    def is_mid_cap(self) -> bool:
        """Check if the stock is mid cap ($2B < market cap <= $10B)."""
        return self.market_cap is not None and 2_000_000_000 < self.market_cap <= 10_000_000_000
    
    @property
    def is_small_cap(self) -> bool:
        """Check if the stock is small cap (market cap <= $2B)."""
        return self.market_cap is not None and self.market_cap <= 2_000_000_000
    
    @property
    def is_value_stock(self) -> bool:
        """Check if the stock is a value stock (low P/E ratio)."""
        return self.pe_ratio is not None and self.pe_ratio < 15
    
    @property
    def is_growth_stock(self) -> bool:
        """Check if the stock is a growth stock (high P/E ratio)."""
        return self.pe_ratio is not None and self.pe_ratio > 25
    
    @property
    def is_dividend_stock(self) -> bool:
        """Check if the stock pays dividends."""
        return self.dividend_yield is not None and self.dividend_yield > 0
    
    @property
    def is_high_dividend(self) -> bool:
        """Check if the stock has a high dividend yield (> 3%)."""
        return self.dividend_yield is not None and self.dividend_yield > 3.0
    
    def to_dict(self) -> Dict:
        """Convert the stock to a dictionary representation."""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "exchange": self.exchange.value,
            "sector": self.sector.value,
            "industry": self.industry,
            "market_cap": self.market_cap,
            "pe_ratio": self.pe_ratio,
            "dividend_yield": self.dividend_yield,
            "beta": self.beta,
            "description": self.description,
            "current_price": self.current_price
        }
