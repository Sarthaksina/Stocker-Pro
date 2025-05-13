"""Portfolio database model for STOCKER Pro.

This module defines the SQLAlchemy models for portfolios, positions, and transactions,
providing persistence for portfolio-related domain entities.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, JSON, Index, Enum
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from stocker.infrastructure.database.session import Base
from stocker.domain.portfolio import Portfolio, Position, Transaction, PortfolioType, TransactionType


class PortfolioModel(Base):
    """SQLAlchemy model for portfolios.
    
    This model maps to the 'portfolios' table in the database and provides
    persistence for Portfolio domain entities.
    """
    __tablename__ = "portfolios"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    type = Column(String(20), nullable=False, default="personal")
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    cash_balance = Column(Float, nullable=False, default=0.0)
    inception_date = Column(DateTime, default=datetime.now)
    benchmark_symbol = Column(String(10), default="SPY")
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    metadata = Column(MutableDict.as_mutable(JSON), default=dict)
    
    # Relationships
    owner = relationship("UserModel", back_populates="portfolios")
    positions = relationship(
        "PositionModel",
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )
    transactions = relationship(
        "TransactionModel",
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index('ix_portfolios_owner_id', 'owner_id'),
    )
    
    @classmethod
    def from_domain(cls, portfolio: Portfolio) -> "PortfolioModel":
        """Create a database model from a domain entity.
        
        Args:
            portfolio: Portfolio domain entity
            
        Returns:
            PortfolioModel database model
        """
        return cls(
            id=portfolio.id,
            name=portfolio.name,
            description=portfolio.description,
            type=portfolio.type.value,
            owner_id=portfolio.owner_id,
            cash_balance=portfolio.cash_balance,
            inception_date=portfolio.inception_date,
            benchmark_symbol=portfolio.benchmark_symbol
        )
    
    def to_domain(self, include_positions: bool = True, include_transactions: bool = True) -> Portfolio:
        """Convert to a domain entity.
        
        Args:
            include_positions: Whether to include positions
            include_transactions: Whether to include transactions
            
        Returns:
            Portfolio domain entity
        """
        # Create portfolio domain entity
        portfolio = Portfolio(
            id=self.id,
            name=self.name,
            description=self.description or "",
            type=PortfolioType(self.type) if self.type else PortfolioType.PERSONAL,
            owner_id=self.owner_id,
            cash_balance=self.cash_balance,
            inception_date=self.inception_date,
            benchmark_symbol=self.benchmark_symbol or "SPY"
        )
        
        # Include positions if requested
        if include_positions and self.positions:
            for position_model in self.positions:
                position = position_model.to_domain()
                portfolio.positions[position.symbol] = position
        
        # Include transactions if requested
        if include_transactions and self.transactions:
            portfolio.transactions = [tx.to_domain() for tx in self.transactions]
        
        return portfolio


class PositionModel(Base):
    """SQLAlchemy model for portfolio positions.
    
    This model maps to the 'positions' table in the database and provides
    persistence for Position domain entities.
    """
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(36), ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)
    cost_basis = Column(Float, nullable=False, default=0.0)
    open_date = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    metadata = Column(MutableDict.as_mutable(JSON), default=dict)
    
    # Relationships
    portfolio = relationship("PortfolioModel", back_populates="positions")
    
    # Indexes
    __table_args__ = (
        Index('ix_positions_portfolio_id_symbol', 'portfolio_id', 'symbol', unique=True),
    )
    
    @classmethod
    def from_domain(cls, position: Position, portfolio_id: str) -> "PositionModel":
        """Create a database model from a domain entity.
        
        Args:
            position: Position domain entity
            portfolio_id: Portfolio ID
            
        Returns:
            PositionModel database model
        """
        return cls(
            portfolio_id=portfolio_id,
            symbol=position.symbol,
            quantity=position.quantity,
            cost_basis=position.cost_basis,
            open_date=position.open_date
        )
    
    def to_domain(self) -> Position:
        """Convert to a domain entity.
        
        Returns:
            Position domain entity
        """
        return Position(
            symbol=self.symbol,
            quantity=self.quantity,
            cost_basis=self.cost_basis,
            open_date=self.open_date
        )


class TransactionModel(Base):
    """SQLAlchemy model for portfolio transactions.
    
    This model maps to the 'transactions' table in the database and provides
    persistence for Transaction domain entities.
    """
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True)
    portfolio_id = Column(String(36), ForeignKey("portfolios.id"), nullable=False)
    type = Column(String(20), nullable=False)
    symbol = Column(String(10), nullable=True)
    date = Column(DateTime, default=datetime.now)
    quantity = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    amount = Column(Float, nullable=False)
    fees = Column(Float, default=0.0)
    notes = Column(Text)
    metadata = Column(MutableDict.as_mutable(JSON), default=dict)
    
    # Relationships
    portfolio = relationship("PortfolioModel", back_populates="transactions")
    
    # Indexes
    __table_args__ = (
        Index('ix_transactions_portfolio_id', 'portfolio_id'),
        Index('ix_transactions_date', 'date'),
        Index('ix_transactions_symbol', 'symbol'),
    )
    
    @classmethod
    def from_domain(cls, transaction: Transaction, portfolio_id: str) -> "TransactionModel":
        """Create a database model from a domain entity.
        
        Args:
            transaction: Transaction domain entity
            portfolio_id: Portfolio ID
            
        Returns:
            TransactionModel database model
        """
        return cls(
            id=transaction.id,
            portfolio_id=portfolio_id,
            type=transaction.type.value,
            symbol=transaction.symbol,
            date=transaction.date,
            quantity=transaction.quantity,
            price=transaction.price,
            amount=transaction.amount,
            fees=transaction.fees,
            notes=transaction.notes
        )
    
    def to_domain(self) -> Transaction:
        """Convert to a domain entity.
        
        Returns:
            Transaction domain entity
        """
        return Transaction(
            id=self.id,
            type=TransactionType(self.type),
            symbol=self.symbol,
            date=self.date,
            quantity=self.quantity,
            price=self.price,
            amount=self.amount,
            fees=self.fees,
            notes=self.notes or ""
        )
