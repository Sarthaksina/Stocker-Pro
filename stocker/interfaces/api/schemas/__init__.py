"""API schemas for STOCKER Pro.

This package provides Pydantic models for request and response validation.
"""

from stocker.interfaces.api.schemas.auth import (
    Token,
    TokenData,
    LoginRequest,
    PasswordChangeRequest
)
from stocker.interfaces.api.schemas.users import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserPreferencesUpdate
)
from stocker.interfaces.api.schemas.stocks import (
    StockCreate,
    StockUpdate,
    StockResponse,
    StockPriceCreate,
    StockPriceResponse,
    StockDataResponse
)
from stocker.interfaces.api.schemas.portfolios import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PositionCreate,
    PositionResponse,
    TransactionCreate,
    TransactionResponse,
    PortfolioPerformanceResponse
)
from stocker.interfaces.api.schemas.strategies import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    SignalCreate,
    SignalResponse,
    StrategyRunRequest
)

__all__ = [
    "Token",
    "TokenData",
    "LoginRequest",
    "PasswordChangeRequest",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserPreferencesUpdate",
    "StockCreate",
    "StockUpdate",
    "StockResponse",
    "StockPriceCreate",
    "StockPriceResponse",
    "StockDataResponse",
    "PortfolioCreate",
    "PortfolioUpdate",
    "PortfolioResponse",
    "PositionCreate",
    "PositionResponse",
    "TransactionCreate",
    "TransactionResponse",
    "PortfolioPerformanceResponse",
    "StrategyCreate",
    "StrategyUpdate",
    "StrategyResponse",
    "SignalCreate",
    "SignalResponse",
    "StrategyRunRequest"
]
