"""Database initialization script for STOCKER Pro.

This module provides functions for initializing the database with initial data,
including creating tables, seeding default data, and running migrations.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.exc import SQLAlchemyError

from stocker.core.config.settings import get_settings
from stocker.core.exceptions import DataError
from stocker.core.logging import get_logger
from stocker.domain.user import User, UserRole, UserStatus, UserPreferences
from stocker.domain.stock import Stock, Exchange, Sector
from stocker.domain.portfolio import Portfolio, PortfolioType
from stocker.domain.strategy import Strategy, StrategyType, StrategyParameters
from stocker.infrastructure.database.models import (
    UserModel, UserRoleModel, StockModel, PortfolioModel, StrategyModel
)
from stocker.infrastructure.database.repositories import (
    UserRepository, StockRepository, PortfolioRepository, StrategyRepository
)
from stocker.infrastructure.database.session import init_db, get_session

# Initialize logger
logger = get_logger(__name__)


def init_database(connection_string: Optional[str] = None, echo: bool = False) -> None:
    """Initialize the database with tables and seed data.
    
    Args:
        connection_string: Database connection string (if None, use settings)
        echo: Whether to echo SQL statements
        
    Raises:
        DataError: If an error occurs during initialization
    """
    try:
        # Initialize database connection and create tables
        engine = init_db(connection_string, echo)
        
        # Seed initial data
        seed_user_roles()
        seed_admin_user()
        seed_sample_stocks()
        seed_sample_portfolio()
        seed_sample_strategies()
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise DataError(f"Error initializing database: {str(e)}")


def seed_user_roles() -> None:
    """Seed the database with default user roles.
    
    Raises:
        DataError: If an error occurs during seeding
    """
    try:
        with get_session() as session:
            # Check if roles already exist
            existing_roles = session.query(UserRoleModel).all()
            if existing_roles:
                logger.info(f"User roles already exist, skipping seeding")
                return
            
            # Create role models for all UserRole enum values
            roles = [UserRoleModel.from_enum(role) for role in UserRole]
            
            # Add roles to database
            session.add_all(roles)
            session.commit()
            
            logger.info(f"Seeded {len(roles)} user roles")
    except SQLAlchemyError as e:
        logger.error(f"Error seeding user roles: {str(e)}")
        raise DataError(f"Error seeding user roles: {str(e)}")


def seed_admin_user(admin_email: str = "admin@stockerpro.com", 
                   admin_username: str = "admin",
                   admin_password: str = "changeme") -> None:
    """Seed the database with an admin user.
    
    Args:
        admin_email: Admin user email
        admin_username: Admin user username
        admin_password: Admin user password
        
    Raises:
        DataError: If an error occurs during seeding
    """
    try:
        # Check if admin user already exists
        user_repo = UserRepository()
        existing_admin = user_repo.get_by_username(admin_username)
        
        if existing_admin:
            logger.info(f"Admin user already exists, skipping seeding")
            return
        
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            username=admin_username,
            email=admin_email,
            first_name="Admin",
            last_name="User",
            roles={UserRole.ADMIN, UserRole.USER},
            status=UserStatus.ACTIVE,
            preferences=UserPreferences(),
            created_at=datetime.now()
        )
        
        # Create user model
        admin_model = UserModel.from_domain(admin_user)
        
        # Set password hash (in a real app, this would be properly hashed)
        from werkzeug.security import generate_password_hash
        admin_model.password_hash = generate_password_hash(admin_password)
        
        # Save to database
        with get_session() as session:
            # Add user to database
            session.add(admin_model)
            
            # Add roles to user
            admin_role = session.query(UserRoleModel).filter_by(role=UserRole.ADMIN.value).first()
            user_role = session.query(UserRoleModel).filter_by(role=UserRole.USER.value).first()
            
            if admin_role and user_role:
                admin_model.roles.append(admin_role)
                admin_model.roles.append(user_role)
            
            session.commit()
        
        logger.info(f"Seeded admin user: {admin_username}")
    except Exception as e:
        logger.error(f"Error seeding admin user: {str(e)}")
        raise DataError(f"Error seeding admin user: {str(e)}")


def seed_sample_stocks() -> None:
    """Seed the database with sample stocks.
    
    Raises:
        DataError: If an error occurs during seeding
    """
    try:
        # Sample stocks data
        sample_stocks = [
            Stock(
                symbol="AAPL",
                name="Apple Inc.",
                exchange=Exchange.NASDAQ,
                sector=Sector.TECHNOLOGY,
                industry="Consumer Electronics",
                market_cap=2500000000000.0,
                pe_ratio=30.5,
                dividend_yield=0.5,
                beta=1.2,
                description="Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide."
            ),
            Stock(
                symbol="MSFT",
                name="Microsoft Corporation",
                exchange=Exchange.NASDAQ,
                sector=Sector.TECHNOLOGY,
                industry="Software",
                market_cap=2300000000000.0,
                pe_ratio=35.2,
                dividend_yield=0.8,
                beta=0.9,
                description="Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide."
            ),
            Stock(
                symbol="GOOGL",
                name="Alphabet Inc.",
                exchange=Exchange.NASDAQ,
                sector=Sector.TECHNOLOGY,
                industry="Internet Content & Information",
                market_cap=1800000000000.0,
                pe_ratio=28.1,
                dividend_yield=0.0,
                beta=1.1,
                description="Alphabet Inc. provides various products and platforms in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America."
            ),
            Stock(
                symbol="AMZN",
                name="Amazon.com, Inc.",
                exchange=Exchange.NASDAQ,
                sector=Sector.CONSUMER_CYCLICAL,
                industry="Internet Retail",
                market_cap=1700000000000.0,
                pe_ratio=60.3,
                dividend_yield=0.0,
                beta=1.3,
                description="Amazon.com, Inc. engages in the retail sale of consumer products and subscriptions in North America and internationally."
            ),
            Stock(
                symbol="TSLA",
                name="Tesla, Inc.",
                exchange=Exchange.NASDAQ,
                sector=Sector.CONSUMER_CYCLICAL,
                industry="Auto Manufacturers",
                market_cap=800000000000.0,
                pe_ratio=100.5,
                dividend_yield=0.0,
                beta=2.0,
                description="Tesla, Inc. designs, develops, manufactures, leases, and sells electric vehicles, and energy generation and storage systems."
            )
        ]
        
        # Check if stocks already exist
        stock_repo = StockRepository()
        existing_stock = stock_repo.get_by_symbol("AAPL")
        
        if existing_stock:
            logger.info(f"Sample stocks already exist, skipping seeding")
            return
        
        # Save stocks to database
        for stock in sample_stocks:
            stock_repo.create(stock)
        
        logger.info(f"Seeded {len(sample_stocks)} sample stocks")
    except Exception as e:
        logger.error(f"Error seeding sample stocks: {str(e)}")
        raise DataError(f"Error seeding sample stocks: {str(e)}")


def seed_sample_portfolio() -> None:
    """Seed the database with a sample portfolio.
    
    Raises:
        DataError: If an error occurs during seeding
    """
    try:
        # Get admin user
        user_repo = UserRepository()
        admin_user = user_repo.get_by_username("admin")
        
        if not admin_user:
            logger.warning("Admin user not found, skipping portfolio seeding")
            return
        
        # Check if portfolio already exists
        portfolio_repo = PortfolioRepository()
        admin_portfolios = portfolio_repo.get_by_owner(admin_user.id)
        
        if admin_portfolios:
            logger.info(f"Sample portfolio already exists, skipping seeding")
            return
        
        # Create sample portfolio
        sample_portfolio = Portfolio(
            id=str(uuid.uuid4()),
            name="Sample Portfolio",
            description="A sample portfolio for demonstration purposes",
            type=PortfolioType.PERSONAL,
            owner_id=admin_user.id,
            cash_balance=10000.0,
            inception_date=datetime.now() - timedelta(days=30),
            benchmark_symbol="SPY"
        )
        
        # Save portfolio to database
        portfolio_repo.create(sample_portfolio)
        
        # Add some sample positions
        from stocker.domain.portfolio import Position, Transaction, TransactionType
        
        # Add positions through transactions
        transactions = [
            Transaction(
                id=str(uuid.uuid4()),
                type=TransactionType.DEPOSIT,
                date=datetime.now() - timedelta(days=29),
                amount=10000.0,
                notes="Initial deposit"
            ),
            Transaction(
                id=str(uuid.uuid4()),
                type=TransactionType.BUY,
                symbol="AAPL",
                date=datetime.now() - timedelta(days=28),
                quantity=10.0,
                price=150.0,
                amount=1500.0,
                fees=9.99,
                notes="Initial AAPL purchase"
            ),
            Transaction(
                id=str(uuid.uuid4()),
                type=TransactionType.BUY,
                symbol="MSFT",
                date=datetime.now() - timedelta(days=27),
                quantity=5.0,
                price=300.0,
                amount=1500.0,
                fees=9.99,
                notes="Initial MSFT purchase"
            ),
            Transaction(
                id=str(uuid.uuid4()),
                type=TransactionType.BUY,
                symbol="GOOGL",
                date=datetime.now() - timedelta(days=25),
                quantity=2.0,
                price=2800.0,
                amount=5600.0,
                fees=9.99,
                notes="Initial GOOGL purchase"
            )
        ]
        
        # Add transactions to portfolio
        for transaction in transactions:
            portfolio_repo.add_transaction(sample_portfolio.id, transaction)
        
        logger.info(f"Seeded sample portfolio with {len(transactions)} transactions")
    except Exception as e:
        logger.error(f"Error seeding sample portfolio: {str(e)}")
        raise DataError(f"Error seeding sample portfolio: {str(e)}")


def seed_sample_strategies() -> None:
    """Seed the database with sample strategies.
    
    Raises:
        DataError: If an error occurs during seeding
    """
    try:
        # Get admin user
        user_repo = UserRepository()
        admin_user = user_repo.get_by_username("admin")
        
        if not admin_user:
            logger.warning("Admin user not found, skipping strategy seeding")
            return
        
        # Check if strategies already exist
        strategy_repo = StrategyRepository()
        admin_strategies = strategy_repo.get_by_owner(admin_user.id)
        
        if admin_strategies:
            logger.info(f"Sample strategies already exist, skipping seeding")
            return
        
        # Create sample strategies
        from stocker.domain.strategy import MomentumStrategy, MeanReversionStrategy
        
        # Momentum strategy
        momentum_params = StrategyParameters()
        momentum_params.lookback_period = 20
        momentum_params.threshold = 0.05
        momentum_params.symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        
        momentum_strategy = MomentumStrategy(
            id=str(uuid.uuid4()),
            name="Sample Momentum Strategy",
            description="A sample momentum strategy for demonstration purposes",
            parameters=momentum_params,
            owner_id=admin_user.id,
            created_at=datetime.now() - timedelta(days=15),
            updated_at=datetime.now() - timedelta(days=15),
            is_active=True
        )
        
        # Mean reversion strategy
        reversion_params = StrategyParameters()
        reversion_params.lookback_period = 30
        reversion_params.std_dev_threshold = 2.0
        reversion_params.symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        
        reversion_strategy = MeanReversionStrategy(
            id=str(uuid.uuid4()),
            name="Sample Mean Reversion Strategy",
            description="A sample mean reversion strategy for demonstration purposes",
            parameters=reversion_params,
            owner_id=admin_user.id,
            created_at=datetime.now() - timedelta(days=10),
            updated_at=datetime.now() - timedelta(days=10),
            is_active=True
        )
        
        # Save strategies to database
        strategy_repo.create(momentum_strategy)
        strategy_repo.create(reversion_strategy)
        
        logger.info(f"Seeded 2 sample strategies")
    except Exception as e:
        logger.error(f"Error seeding sample strategies: {str(e)}")
        raise DataError(f"Error seeding sample strategies: {str(e)}")


if __name__ == "__main__":
    # Initialize database when script is run directly
    init_database(echo=True)
