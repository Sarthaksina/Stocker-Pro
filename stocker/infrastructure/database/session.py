"""Database session management for STOCKER Pro.

This module provides functions for creating and managing database sessions,
including connection pooling and transaction management.
"""

import os
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create declarative base for SQLAlchemy models
Base = declarative_base()

# Global session factory
_SessionFactory = None


def init_db(connection_string: Optional[str] = None, echo: bool = False) -> Engine:
    """Initialize the database connection and create tables.
    
    Args:
        connection_string: Database connection string (if None, use settings)
        echo: Whether to echo SQL statements
        
    Returns:
        SQLAlchemy engine
    """
    global _SessionFactory
    
    # Get connection string from settings if not provided
    if connection_string is None:
        settings = get_settings()
        connection_string = os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{os.path.join(settings.data_dir, 'stocker.db')}"
        )
    
    # Create engine with connection pooling
    engine = create_engine(
        connection_string,
        echo=echo,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800  # Recycle connections after 30 minutes
    )
    
    # Create session factory
    _SessionFactory = sessionmaker(bind=engine)
    
    # Create tables
    Base.metadata.create_all(engine)
    
    # Log initialization
    logger.info(f"Initialized database connection: {connection_string}")
    
    return engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup.
    
    This function returns a context manager that provides a session and
    automatically commits or rolls back the transaction when the context exits.
    
    Yields:
        SQLAlchemy session
        
    Raises:
        Exception: If an error occurs during the session
    """
    # Initialize database if not already initialized
    if _SessionFactory is None:
        init_db()
    
    # Create session
    session = _SessionFactory()
    
    try:
        # Yield session to the caller
        yield session
        
        # Commit transaction if no exception occurred
        session.commit()
    except Exception as e:
        # Roll back transaction if an exception occurred
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        # Close session
        session.close()


def get_db() -> Session:
    """Get a database session (non-context manager version).
    
    This function returns a session directly, without using a context manager.
    The caller is responsible for committing or rolling back the transaction
    and closing the session.
    
    Returns:
        SQLAlchemy session
    """
    # Initialize database if not already initialized
    if _SessionFactory is None:
        init_db()
    
    # Create and return session
    return _SessionFactory()
