"""API routes for STOCKER Pro.

This package provides route handlers for the STOCKER Pro API.
"""

from stocker.interfaces.api.routes.auth import router as auth_router
from stocker.interfaces.api.routes.users import router as user_router
from stocker.interfaces.api.routes.stocks import router as stock_router
from stocker.interfaces.api.routes.portfolios import router as portfolio_router
from stocker.interfaces.api.routes.strategies import router as strategy_router

__all__ = [
    "auth_router",
    "user_router",
    "stock_router",
    "portfolio_router",
    "strategy_router"
]
