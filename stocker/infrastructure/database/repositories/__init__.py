"""Repository implementations for STOCKER Pro.

This package provides repository implementations for data access patterns,
following the repository pattern to abstract database operations.
"""

from stocker.infrastructure.database.repositories.base import BaseRepository
from stocker.infrastructure.database.repositories.user import UserRepository
from stocker.infrastructure.database.repositories.stock import StockRepository
from stocker.infrastructure.database.repositories.portfolio import PortfolioRepository
from stocker.infrastructure.database.repositories.strategy import StrategyRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "StockRepository",
    "PortfolioRepository",
    "StrategyRepository"
]
