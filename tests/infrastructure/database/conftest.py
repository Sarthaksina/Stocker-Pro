"""Test configuration for database tests.

This module provides fixtures for database testing.
"""

import os
import pytest
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from stocker.infrastructure.database.session import Base, get_session
from stocker.infrastructure.database.models import (
    UserModel, StockModel, PortfolioModel, StrategyModel
)


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine.
    
    Returns:
        SQLAlchemy engine for testing
    """
    # Use in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    return engine


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a test database session.
    
    Args:
        test_db_engine: Test database engine
        
    Yields:
        SQLAlchemy session for testing
    """
    # Create a new session for each test
    TestSessionLocal = sessionmaker(bind=test_db_engine)
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        # Roll back transaction after each test
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def mock_get_session(test_db_session, monkeypatch):
    """Mock the get_session function to use the test session.
    
    Args:
        test_db_session: Test database session
        monkeypatch: Pytest monkeypatch fixture
    """
    # Create a context manager that yields the test session
    from contextlib import contextmanager
    
    @contextmanager
    def _mock_get_session():
        try:
            yield test_db_session
        finally:
            pass
    
    # Patch the get_session function
    monkeypatch.setattr(
        "stocker.infrastructure.database.session.get_session",
        _mock_get_session
    )
    
    # Also patch the repositories to use the test session
    monkeypatch.setattr(
        "stocker.infrastructure.database.repositories.base.get_session",
        _mock_get_session
    )
