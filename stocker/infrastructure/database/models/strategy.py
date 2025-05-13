"""Strategy database model for STOCKER Pro.

This module defines the SQLAlchemy models for strategies and signals,
providing persistence for strategy-related domain entities.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, JSON, Index, Boolean
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from stocker.infrastructure.database.session import Base
from stocker.domain.strategy import Strategy, StrategyType, StrategyParameters, Signal, SignalType


class StrategyModel(Base):
    """SQLAlchemy model for trading strategies.
    
    This model maps to the 'strategies' table in the database and provides
    persistence for Strategy domain entities.
    """
    __tablename__ = "strategies"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    type = Column(String(20), nullable=False)
    parameters = Column(MutableDict.as_mutable(JSON), default=dict)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    performance_metrics = Column(MutableDict.as_mutable(JSON), default=dict)
    metadata = Column(MutableDict.as_mutable(JSON), default=dict)
    
    # Relationships
    owner = relationship("UserModel", back_populates="strategies")
    signals = relationship(
        "SignalModel",
        back_populates="strategy",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index('ix_strategies_owner_id', 'owner_id'),
        Index('ix_strategies_type', 'type'),
    )
    
    @classmethod
    def from_domain(cls, strategy: Strategy) -> "StrategyModel":
        """Create a database model from a domain entity.
        
        Args:
            strategy: Strategy domain entity
            
        Returns:
            StrategyModel database model
        """
        return cls(
            id=strategy.id,
            name=strategy.name,
            description=strategy.description,
            type=strategy.type.value,
            parameters=strategy.parameters.to_dict(),
            owner_id=strategy.owner_id,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at,
            is_active=strategy.is_active,
            performance_metrics=strategy.performance_metrics
        )
    
    def to_domain(self, include_signals: bool = False) -> Strategy:
        """Convert to a domain entity.
        
        Args:
            include_signals: Whether to include signals
            
        Returns:
            Strategy domain entity
        """
        # Create strategy parameters
        parameters = StrategyParameters.from_dict(self.parameters or {})
        
        # Create strategy domain entity based on type
        strategy_type = StrategyType(self.type) if self.type else StrategyType.CUSTOM
        
        # Import specific strategy classes based on type
        from stocker.domain.strategy import MomentumStrategy, MeanReversionStrategy
        
        if strategy_type == StrategyType.MOMENTUM:
            strategy = MomentumStrategy(
                id=self.id,
                name=self.name,
                description=self.description or "",
                parameters=parameters,
                owner_id=self.owner_id,
                created_at=self.created_at,
                updated_at=self.updated_at,
                is_active=self.is_active,
                performance_metrics=self.performance_metrics or {}
            )
        elif strategy_type == StrategyType.MEAN_REVERSION:
            strategy = MeanReversionStrategy(
                id=self.id,
                name=self.name,
                description=self.description or "",
                parameters=parameters,
                owner_id=self.owner_id,
                created_at=self.created_at,
                updated_at=self.updated_at,
                is_active=self.is_active,
                performance_metrics=self.performance_metrics or {}
            )
        else:
            # Generic strategy for other types
            strategy = Strategy(
                id=self.id,
                name=self.name,
                description=self.description or "",
                type=strategy_type,
                parameters=parameters,
                owner_id=self.owner_id,
                created_at=self.created_at,
                updated_at=self.updated_at,
                is_active=self.is_active,
                performance_metrics=self.performance_metrics or {}
            )
        
        # Include signals if requested
        if include_signals and self.signals:
            # Signals would need to be handled separately since they're not stored directly in the Strategy domain entity
            pass
        
        return strategy


class SignalModel(Base):
    """SQLAlchemy model for trading signals.
    
    This model maps to the 'signals' table in the database and provides
    persistence for Signal domain entities.
    """
    __tablename__ = "signals"
    
    id = Column(String(36), primary_key=True)
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)
    symbol = Column(String(10), nullable=False)
    date = Column(DateTime, nullable=False)
    type = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)
    confidence = Column(Float, default=50.0)
    metadata = Column(MutableDict.as_mutable(JSON), default=dict)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    strategy = relationship("StrategyModel", back_populates="signals")
    
    # Indexes
    __table_args__ = (
        Index('ix_signals_strategy_id', 'strategy_id'),
        Index('ix_signals_symbol', 'symbol'),
        Index('ix_signals_date', 'date'),
    )
    
    @classmethod
    def from_domain(cls, signal: Signal) -> "SignalModel":
        """Create a database model from a domain entity.
        
        Args:
            signal: Signal domain entity
            
        Returns:
            SignalModel database model
        """
        return cls(
            id=signal.id,
            strategy_id=signal.strategy_id,
            symbol=signal.symbol,
            date=signal.date,
            type=signal.type.value,
            price=signal.price,
            confidence=signal.confidence,
            metadata=signal.metadata
        )
    
    def to_domain(self) -> Signal:
        """Convert to a domain entity.
        
        Returns:
            Signal domain entity
        """
        return Signal(
            id=self.id,
            strategy_id=self.strategy_id,
            symbol=self.symbol,
            date=self.date,
            type=SignalType(self.type),
            price=self.price,
            confidence=self.confidence,
            metadata=self.metadata or {}
        )
