"""Stock database model for STOCKER Pro.

This module defines the SQLAlchemy models for stocks and stock prices,
providing persistence for stock data and related entities.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from stocker.infrastructure.database.session import Base
from stocker.domain.stock import Stock, StockPrice, StockData, Exchange, Sector


class StockModel(Base):
    """SQLAlchemy model for stocks.
    
    This model maps to the 'stocks' table in the database and provides
    persistence for Stock domain entities.
    """
    __tablename__ = "stocks"
    
    symbol = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    exchange = Column(String(20), nullable=False, default="NYSE")
    sector = Column(String(50), nullable=False, default="OTHER")
    industry = Column(String(100))
    market_cap = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    description = Column(Text)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    metadata = Column(MutableDict.as_mutable(JSON), default=dict)
    
    # Relationships
    prices = relationship(
        "StockPriceModel",
        back_populates="stock",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index('ix_stocks_exchange', 'exchange'),
        Index('ix_stocks_sector', 'sector'),
    )
    
    @classmethod
    def from_domain(cls, stock: Stock) -> "StockModel":
        """Create a database model from a domain entity.
        
        Args:
            stock: Stock domain entity
            
        Returns:
            StockModel database model
        """
        return cls(
            symbol=stock.symbol,
            name=stock.name,
            exchange=stock.exchange.value,
            sector=stock.sector.value,
            industry=stock.industry,
            market_cap=stock.market_cap,
            pe_ratio=stock.pe_ratio,
            dividend_yield=stock.dividend_yield,
            beta=stock.beta,
            description=stock.description
        )
    
    def to_domain(self, include_prices: bool = False) -> Stock:
        """Convert to a domain entity.
        
        Args:
            include_prices: Whether to include price data
            
        Returns:
            Stock domain entity
        """
        # Create stock domain entity
        stock = Stock(
            symbol=self.symbol,
            name=self.name,
            exchange=Exchange(self.exchange) if self.exchange else Exchange.OTHER,
            sector=Sector(self.sector) if self.sector else Sector.OTHER,
            industry=self.industry or "",
            market_cap=self.market_cap,
            pe_ratio=self.pe_ratio,
            dividend_yield=self.dividend_yield,
            beta=self.beta,
            description=self.description or ""
        )
        
        # Include price data if requested
        if include_prices and self.prices:
            prices = [price.to_domain() for price in self.prices]
            stock.data = StockData(
                symbol=self.symbol,
                prices=prices,
                timeframe="1d"  # Default timeframe
            )
        
        return stock


class StockPriceModel(Base):
    """SQLAlchemy model for stock prices.
    
    This model maps to the 'stock_prices' table in the database and provides
    persistence for StockPrice domain entities.
    """
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), ForeignKey("stocks.symbol"), nullable=False)
    date = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    adjusted_close = Column(Float, nullable=True)
    timeframe = Column(String(10), default="1d")
    
    # Relationships
    stock = relationship("StockModel", back_populates="prices")
    
    # Indexes
    __table_args__ = (
        Index('ix_stock_prices_symbol_date', 'symbol', 'date', unique=True),
        Index('ix_stock_prices_date', 'date'),
    )
    
    @classmethod
    def from_domain(cls, price: StockPrice, symbol: str) -> "StockPriceModel":
        """Create a database model from a domain entity.
        
        Args:
            price: StockPrice domain entity
            symbol: Stock symbol
            
        Returns:
            StockPriceModel database model
        """
        return cls(
            symbol=symbol,
            date=price.date,
            open=price.open,
            high=price.high,
            low=price.low,
            close=price.close,
            volume=price.volume,
            adjusted_close=price.adjusted_close
        )
    
    def to_domain(self) -> StockPrice:
        """Convert to a domain entity.
        
        Returns:
            StockPrice domain entity
        """
        return StockPrice(
            date=self.date,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
            adjusted_close=self.adjusted_close
        )
