"""Portfolio domain model for STOCKER Pro.

This module defines the core domain entities related to portfolios,
positions, and transactions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from uuid import uuid4

import numpy as np
import pandas as pd

from stocker.domain.stock import Stock, StockData


class TransactionType(str, Enum):
    """Types of portfolio transactions."""
    BUY = "buy"              # Buy transaction
    SELL = "sell"            # Sell transaction
    DIVIDEND = "dividend"    # Dividend payment
    SPLIT = "split"          # Stock split
    DEPOSIT = "deposit"      # Cash deposit
    WITHDRAWAL = "withdrawal"  # Cash withdrawal
    FEE = "fee"              # Fee or commission
    INTEREST = "interest"    # Interest payment
    OTHER = "other"          # Other transaction type


@dataclass
class Transaction:
    """Portfolio transaction.
    
    This class represents a transaction in a portfolio, such as buying or
    selling a stock, receiving a dividend, etc.
    
    Attributes:
        id: Unique transaction ID
        type: Transaction type
        symbol: Stock symbol (if applicable)
        date: Transaction date
        quantity: Number of shares (if applicable)
        price: Price per share (if applicable)
        amount: Total transaction amount
        fees: Transaction fees or commissions
        notes: Additional notes about the transaction
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    type: TransactionType
    symbol: Optional[str] = None
    date: datetime = field(default_factory=datetime.now)
    quantity: float = 0.0
    price: float = 0.0
    amount: float = 0.0
    fees: float = 0.0
    notes: str = ""
    
    def __post_init__(self):
        """Initialize amount if not provided."""
        if self.amount == 0.0 and self.quantity != 0.0 and self.price != 0.0:
            self.amount = self.quantity * self.price
    
    @property
    def net_amount(self) -> float:
        """Calculate the net amount of the transaction (including fees)."""
        if self.type in [TransactionType.BUY, TransactionType.WITHDRAWAL, TransactionType.FEE]:
            return -(self.amount + self.fees)
        elif self.type in [TransactionType.SELL, TransactionType.DIVIDEND, TransactionType.DEPOSIT, TransactionType.INTEREST]:
            return self.amount - self.fees
        else:
            return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the transaction to a dictionary representation."""
        return {
            "id": self.id,
            "type": self.type.value,
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "quantity": self.quantity,
            "price": self.price,
            "amount": self.amount,
            "fees": self.fees,
            "notes": self.notes,
            "net_amount": self.net_amount
        }


@dataclass
class Position:
    """Portfolio position.
    
    This class represents a position in a portfolio, which is a holding of
    a specific stock with a certain quantity and cost basis.
    
    Attributes:
        symbol: Stock symbol
        quantity: Number of shares
        cost_basis: Average cost per share
        open_date: Date when the position was opened
        stock: Stock object (if available)
    """
    symbol: str
    quantity: float
    cost_basis: float
    open_date: datetime = field(default_factory=datetime.now)
    stock: Optional[Stock] = None
    
    @property
    def total_cost(self) -> float:
        """Calculate the total cost of the position."""
        return self.quantity * self.cost_basis
    
    @property
    def current_value(self) -> Optional[float]:
        """Calculate the current value of the position."""
        if self.stock and self.stock.current_price is not None:
            return self.quantity * self.stock.current_price
        return None
    
    @property
    def unrealized_gain_loss(self) -> Optional[float]:
        """Calculate the unrealized gain or loss of the position."""
        current_value = self.current_value
        if current_value is not None:
            return current_value - self.total_cost
        return None
    
    @property
    def unrealized_gain_loss_percent(self) -> Optional[float]:
        """Calculate the unrealized gain or loss percentage of the position."""
        if self.total_cost == 0:
            return None
        
        unrealized_gain_loss = self.unrealized_gain_loss
        if unrealized_gain_loss is not None:
            return (unrealized_gain_loss / self.total_cost) * 100.0
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the position to a dictionary representation."""
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "cost_basis": self.cost_basis,
            "open_date": self.open_date.isoformat(),
            "total_cost": self.total_cost,
            "current_value": self.current_value,
            "unrealized_gain_loss": self.unrealized_gain_loss,
            "unrealized_gain_loss_percent": self.unrealized_gain_loss_percent,
            "stock_name": self.stock.name if self.stock else None
        }


class PortfolioType(str, Enum):
    """Types of portfolios."""
    PERSONAL = "personal"    # Personal investment portfolio
    RETIREMENT = "retirement"  # Retirement portfolio (e.g., 401k, IRA)
    EDUCATION = "education"  # Education savings portfolio (e.g., 529)
    TRUST = "trust"          # Trust portfolio
    MODEL = "model"          # Model portfolio (not real)
    OTHER = "other"          # Other portfolio type


@dataclass
class Portfolio:
    """Portfolio domain entity.
    
    This class represents a portfolio as a business entity, including
    its positions, transactions, and performance metrics.
    
    Attributes:
        id: Unique portfolio ID
        name: Portfolio name
        description: Portfolio description
        type: Portfolio type
        owner_id: ID of the portfolio owner
        positions: Dictionary of positions (symbol -> Position)
        transactions: List of transactions
        cash_balance: Cash balance in the portfolio
        inception_date: Date when the portfolio was created
        benchmark_symbol: Symbol of the benchmark for performance comparison
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    type: PortfolioType = PortfolioType.PERSONAL
    owner_id: Optional[str] = None
    positions: Dict[str, Position] = field(default_factory=dict)
    transactions: List[Transaction] = field(default_factory=list)
    cash_balance: float = 0.0
    inception_date: datetime = field(default_factory=datetime.now)
    benchmark_symbol: str = "SPY"
    
    @property
    def total_value(self) -> float:
        """Calculate the total value of the portfolio."""
        positions_value = sum(
            position.current_value or 0.0 for position in self.positions.values()
        )
        return positions_value + self.cash_balance
    
    @property
    def total_cost(self) -> float:
        """Calculate the total cost of all positions."""
        return sum(position.total_cost for position in self.positions.values())
    
    @property
    def unrealized_gain_loss(self) -> float:
        """Calculate the total unrealized gain or loss of all positions."""
        return sum(
            position.unrealized_gain_loss or 0.0 for position in self.positions.values()
        )
    
    @property
    def unrealized_gain_loss_percent(self) -> Optional[float]:
        """Calculate the total unrealized gain or loss percentage."""
        if self.total_cost == 0:
            return None
        return (self.unrealized_gain_loss / self.total_cost) * 100.0
    
    @property
    def realized_gain_loss(self) -> float:
        """Calculate the total realized gain or loss from sell transactions."""
        realized_gain_loss = 0.0
        
        for transaction in self.transactions:
            if transaction.type == TransactionType.SELL and transaction.symbol:
                # Find matching buy transactions to calculate cost basis
                # This is a simplified approach; a real implementation would use FIFO, LIFO, etc.
                buy_transactions = [
                    t for t in self.transactions
                    if t.type == TransactionType.BUY and t.symbol == transaction.symbol and t.date <= transaction.date
                ]
                
                if buy_transactions:
                    # Calculate average cost basis from buy transactions
                    total_quantity = sum(t.quantity for t in buy_transactions)
                    total_cost = sum(t.amount for t in buy_transactions)
                    avg_cost_basis = total_cost / total_quantity if total_quantity > 0 else 0
                    
                    # Calculate realized gain/loss for this sell transaction
                    realized_gain_loss += transaction.amount - (transaction.quantity * avg_cost_basis)
        
        return realized_gain_loss
    
    def add_transaction(self, transaction: Transaction) -> None:
        """Add a transaction to the portfolio and update positions and cash balance.
        
        Args:
            transaction: Transaction to add
        """
        self.transactions.append(transaction)
        
        # Update cash balance
        self.cash_balance += transaction.net_amount
        
        # Update positions based on transaction type
        if transaction.type == TransactionType.BUY and transaction.symbol:
            if transaction.symbol in self.positions:
                # Update existing position
                position = self.positions[transaction.symbol]
                new_quantity = position.quantity + transaction.quantity
                new_cost = position.total_cost + transaction.amount
                position.quantity = new_quantity
                position.cost_basis = new_cost / new_quantity if new_quantity > 0 else 0
            else:
                # Create new position
                self.positions[transaction.symbol] = Position(
                    symbol=transaction.symbol,
                    quantity=transaction.quantity,
                    cost_basis=transaction.price,
                    open_date=transaction.date
                )
        
        elif transaction.type == TransactionType.SELL and transaction.symbol:
            if transaction.symbol in self.positions:
                # Update existing position
                position = self.positions[transaction.symbol]
                position.quantity -= transaction.quantity
                
                # Remove position if quantity is zero or negative
                if position.quantity <= 0:
                    del self.positions[transaction.symbol]
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get a position by symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Position object if found, None otherwise
        """
        return self.positions.get(symbol)
    
    def get_transactions(self, symbol: Optional[str] = None) -> List[Transaction]:
        """Get transactions, optionally filtered by symbol.
        
        Args:
            symbol: Stock symbol to filter by (optional)
            
        Returns:
            List of transactions
        """
        if symbol:
            return [t for t in self.transactions if t.symbol == symbol]
        return self.transactions
    
    def get_allocation(self) -> Dict[str, float]:
        """Get the current portfolio allocation as percentages.
        
        Returns:
            Dictionary mapping symbols to allocation percentages
        """
        total = self.total_value
        if total == 0:
            return {}
        
        allocation = {}
        
        # Add positions
        for symbol, position in self.positions.items():
            if position.current_value is not None:
                allocation[symbol] = (position.current_value / total) * 100.0
        
        # Add cash
        allocation["CASH"] = (self.cash_balance / total) * 100.0
        
        return allocation
    
    def get_performance(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Calculate portfolio performance metrics.
        
        Args:
            start_date: Start date for performance calculation
            end_date: End date for performance calculation
            
        Returns:
            Dictionary with performance metrics
        """
        # Use inception date if start_date is not provided
        if start_date is None:
            start_date = self.inception_date
        
        # Use current date if end_date is not provided
        if end_date is None:
            end_date = datetime.now()
        
        # Filter transactions by date range
        transactions_in_range = [
            t for t in self.transactions
            if start_date <= t.date <= end_date
        ]
        
        # Calculate metrics
        deposits = sum(
            t.amount for t in transactions_in_range
            if t.type == TransactionType.DEPOSIT
        )
        withdrawals = sum(
            t.amount for t in transactions_in_range
            if t.type == TransactionType.WITHDRAWAL
        )
        fees = sum(t.fees for t in transactions_in_range)
        dividends = sum(
            t.amount for t in transactions_in_range
            if t.type == TransactionType.DIVIDEND
        )
        
        # Calculate returns
        # This is a simplified calculation; a real implementation would use time-weighted returns
        initial_value = deposits - withdrawals
        if initial_value <= 0:
            return {
                "total_return": 0.0,
                "total_return_percent": 0.0,
                "annualized_return": 0.0,
                "deposits": deposits,
                "withdrawals": withdrawals,
                "fees": fees,
                "dividends": dividends
            }
        
        total_return = self.total_value - initial_value
        total_return_percent = (total_return / initial_value) * 100.0
        
        # Calculate annualized return
        years = (end_date - start_date).days / 365.25
        if years > 0:
            annualized_return = ((1 + (total_return / initial_value)) ** (1 / years) - 1) * 100.0
        else:
            annualized_return = 0.0
        
        return {
            "total_return": total_return,
            "total_return_percent": total_return_percent,
            "annualized_return": annualized_return,
            "deposits": deposits,
            "withdrawals": withdrawals,
            "fees": fees,
            "dividends": dividends
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the portfolio to a dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "owner_id": self.owner_id,
            "positions": [position.to_dict() for position in self.positions.values()],
            "cash_balance": self.cash_balance,
            "inception_date": self.inception_date.isoformat(),
            "benchmark_symbol": self.benchmark_symbol,
            "total_value": self.total_value,
            "total_cost": self.total_cost,
            "unrealized_gain_loss": self.unrealized_gain_loss,
            "unrealized_gain_loss_percent": self.unrealized_gain_loss_percent,
            "allocation": self.get_allocation()
        }
