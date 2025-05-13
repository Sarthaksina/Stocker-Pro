"""Tests for authentication endpoints.

This module contains tests for the authentication-related API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from stocker.domain.user import User
from stocker.services.user_service import UserService


def test_login_success(client: TestClient, test_user: User):
    """Test successful login.
    
    Args:
        client: Test client
        test_user: Test user
    """
    # Test login with username
    response = client.post(
        "/api/auth/login",
        json={"username": test_user.username, "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"] == test_user.id
    assert data["username"] == test_user.username
    
    # Test login with email
    response = client.post(
        "/api/auth/login",
        json={"username": test_user.email, "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_failure(client: TestClient, test_user: User):
    """Test failed login attempts.
    
    Args:
        client: Test client
        test_user: Test user
    """
    # Test login with incorrect password
    response = client.post(
        "/api/auth/login",
        json={"username": test_user.username, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    
    # Test login with non-existent user
    response = client.post(
        "/api/auth/login",
        json={"username": "nonexistentuser", "password": "password123"}
    )
    assert response.status_code == 401


def test_oauth_token_endpoint(client: TestClient, test_user: User):
    """Test OAuth2 token endpoint.
    
    Args:
        client: Test client
        test_user: Test user
    """
    response = client.post(
        "/api/auth/token",
        data={
            "username": test_user.username,
            "password": "password123",
            "grant_type": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user(client: TestClient, user_token_headers: dict, test_user: User):
    """Test getting current user information.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_user: Test user
    """
    response = client.get("/api/auth/me", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email


def test_change_password(client: TestClient, user_token_headers: dict, user_service: UserService, test_user: User):
    """Test changing user password.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        user_service: User service
        test_user: Test user
    """
    # Change password
    response = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "password123",
            "new_password": "newpassword123"
        },
        headers=user_token_headers
    )
    assert response.status_code == 200
    
    # Verify old password no longer works
    response = client.post(
        "/api/auth/login",
        json={"username": test_user.username, "password": "password123"}
    )
    assert response.status_code == 401
    
    # Verify new password works
    response = client.post(
        "/api/auth/login",
        json={"username": test_user.username, "password": "newpassword123"}
    )
    assert response.status_code == 200


def test_change_password_failure(client: TestClient, user_token_headers: dict):
    """Test failed password change attempts.
    
    Args:
        client: Test client
        user_token_headers: User token headers
    """
    # Test with incorrect current password
    response = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        },
        headers=user_token_headers
    )
    assert response.status_code == 400
    
    # Test with same new password
    response = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "password123",
            "new_password": "password123"
        },
        headers=user_token_headers
    )
    assert response.status_code == 422  # Validation error


def test_logout(client: TestClient, user_token_headers: dict):
    """Test user logout.
    
    Args:
        client: Test client
        user_token_headers: User token headers
    """
    response = client.post("/api/auth/logout", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Logged out successfully"
    
    # Note: Since JWT tokens cannot be invalidated without a token blacklist,
    # the token will still be valid after logout. This is just a client-side
    # logout functionality.
