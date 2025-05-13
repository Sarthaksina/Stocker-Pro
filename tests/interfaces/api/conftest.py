"""Test configuration for STOCKER Pro API tests.

This module provides fixtures for testing the STOCKER Pro API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Dict, Any

from stocker.interfaces.api.app import create_app
from stocker.infrastructure.database.models.base import Base
from stocker.infrastructure.database.session import get_db
from stocker.domain.user import User, UserRole
from stocker.services.user_service import UserService
from stocker.interfaces.api.dependencies import create_access_token


# Create test database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test.
    
    Yields:
        SQLAlchemy Session: Database session
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app.
    
    Args:
        db: Database session
        
    Yields:
        TestClient: FastAPI test client
    """
    # Override the get_db dependency
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    # Create app
    app = create_app()
    
    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def user_service(db: Session) -> UserService:
    """Create a user service instance.
    
    Args:
        db: Database session
        
    Returns:
        UserService: User service instance
    """
    return UserService(db)


@pytest.fixture(scope="function")
def test_user(user_service: UserService) -> User:
    """Create a test user.
    
    Args:
        user_service: User service instance
        
    Returns:
        User: Test user
    """
    return user_service.create_user(
        username="testuser",
        email="test@example.com",
        password="password123",
        first_name="Test",
        last_name="User",
        roles=[UserRole.USER]
    )


@pytest.fixture(scope="function")
def test_admin(user_service: UserService) -> User:
    """Create a test admin user.
    
    Args:
        user_service: User service instance
        
    Returns:
        User: Test admin user
    """
    return user_service.create_user(
        username="testadmin",
        email="admin@example.com",
        password="password123",
        first_name="Test",
        last_name="Admin",
        roles=[UserRole.ADMIN]
    )


@pytest.fixture(scope="function")
def user_token_headers(test_user: User) -> Dict[str, str]:
    """Create authorization headers for a test user.
    
    Args:
        test_user: Test user
        
    Returns:
        Dict[str, str]: Authorization headers
    """
    access_token = create_access_token(
        data={
            "sub": test_user.id,
            "username": test_user.username,
            "roles": [role.value for role in test_user.roles]
        }
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def admin_token_headers(test_admin: User) -> Dict[str, str]:
    """Create authorization headers for a test admin user.
    
    Args:
        test_admin: Test admin user
        
    Returns:
        Dict[str, str]: Authorization headers
    """
    access_token = create_access_token(
        data={
            "sub": test_admin.id,
            "username": test_admin.username,
            "roles": [role.value for role in test_admin.roles]
        }
    )
    return {"Authorization": f"Bearer {access_token}"}
