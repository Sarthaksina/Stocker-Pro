"""Tests for user endpoints.

This module contains tests for the user-related API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from stocker.domain.user import User, UserRole
from stocker.services.user_service import UserService


def test_create_user(client: TestClient, admin_token_headers: dict):
    """Test creating a new user.
    
    Args:
        client: Test client
        admin_token_headers: Admin token headers
    """
    # Create user
    response = client.post(
        "/api/users/",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "roles": ["user"]
        },
        headers=admin_token_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["first_name"] == "New"
    assert data["last_name"] == "User"
    assert "password" not in data
    assert "user" in data["roles"]


def test_create_user_validation(client: TestClient, admin_token_headers: dict, test_user: User):
    """Test user creation validation.
    
    Args:
        client: Test client
        admin_token_headers: Admin token headers
        test_user: Existing test user
    """
    # Test with existing username
    response = client.post(
        "/api/users/",
        json={
            "username": test_user.username,
            "email": "unique@example.com",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "roles": ["user"]
        },
        headers=admin_token_headers
    )
    assert response.status_code == 400
    
    # Test with existing email
    response = client.post(
        "/api/users/",
        json={
            "username": "uniqueuser",
            "email": test_user.email,
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "roles": ["user"]
        },
        headers=admin_token_headers
    )
    assert response.status_code == 400
    
    # Test with weak password
    response = client.post(
        "/api/users/",
        json={
            "username": "uniqueuser",
            "email": "unique@example.com",
            "password": "weak",
            "first_name": "New",
            "last_name": "User",
            "roles": ["user"]
        },
        headers=admin_token_headers
    )
    assert response.status_code == 422  # Validation error


def test_create_user_unauthorized(client: TestClient, user_token_headers: dict):
    """Test creating a user without admin privileges.
    
    Args:
        client: Test client
        user_token_headers: Regular user token headers
    """
    response = client.post(
        "/api/users/",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "roles": ["user"]
        },
        headers=user_token_headers
    )
    assert response.status_code == 403


def test_get_users(client: TestClient, admin_token_headers: dict, test_user: User, test_admin: User):
    """Test getting all users.
    
    Args:
        client: Test client
        admin_token_headers: Admin token headers
        test_user: Test user
        test_admin: Test admin user
    """
    response = client.get("/api/users/", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least test_user and test_admin
    
    # Check if test_user and test_admin are in the response
    user_ids = [user["id"] for user in data]
    assert test_user.id in user_ids
    assert test_admin.id in user_ids


def test_get_users_unauthorized(client: TestClient, user_token_headers: dict):
    """Test getting all users without admin privileges.
    
    Args:
        client: Test client
        user_token_headers: Regular user token headers
    """
    response = client.get("/api/users/", headers=user_token_headers)
    assert response.status_code == 403


def test_get_user(client: TestClient, user_token_headers: dict, admin_token_headers: dict, test_user: User):
    """Test getting a user by ID.
    
    Args:
        client: Test client
        user_token_headers: Regular user token headers
        admin_token_headers: Admin token headers
        test_user: Test user
    """
    # Test getting own user data
    response = client.get(f"/api/users/{test_user.id}", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["username"] == test_user.username
    
    # Test admin getting user data
    response = client.get(f"/api/users/{test_user.id}", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id


def test_get_user_unauthorized(client: TestClient, user_token_headers: dict, test_admin: User):
    """Test getting another user's data without admin privileges.
    
    Args:
        client: Test client
        user_token_headers: Regular user token headers
        test_admin: Test admin user
    """
    response = client.get(f"/api/users/{test_admin.id}", headers=user_token_headers)
    assert response.status_code == 403


def test_update_user(client: TestClient, user_token_headers: dict, test_user: User):
    """Test updating a user.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_user: Test user
    """
    # Update user
    response = client.put(
        f"/api/users/{test_user.id}",
        json={
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com"
        },
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"
    assert data["email"] == "updated@example.com"


def test_update_user_roles(client: TestClient, admin_token_headers: dict, test_user: User):
    """Test updating user roles as admin.
    
    Args:
        client: Test client
        admin_token_headers: Admin token headers
        test_user: Test user
    """
    # Update user roles
    response = client.put(
        f"/api/users/{test_user.id}",
        json={
            "roles": ["user", "manager"]
        },
        headers=admin_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "user" in data["roles"]
    assert "manager" in data["roles"]


def test_update_user_roles_unauthorized(client: TestClient, user_token_headers: dict, test_user: User):
    """Test updating user roles without admin privileges.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_user: Test user
    """
    # Try to update roles as non-admin
    response = client.put(
        f"/api/users/{test_user.id}",
        json={
            "roles": ["user", "admin"]
        },
        headers=user_token_headers
    )
    assert response.status_code == 403


def test_update_user_preferences(client: TestClient, user_token_headers: dict, test_user: User):
    """Test updating user preferences.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_user: Test user
    """
    # Update preferences
    response = client.put(
        f"/api/users/{test_user.id}/preferences",
        json={
            "theme": "dark",
            "language": "fr",
            "timezone": "Europe/Paris",
            "notifications_enabled": False
        },
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["preferences"]["theme"] == "dark"
    assert data["preferences"]["language"] == "fr"
    assert data["preferences"]["timezone"] == "Europe/Paris"
    assert data["preferences"]["notifications_enabled"] is False


def test_delete_user(client: TestClient, admin_token_headers: dict, user_service: UserService):
    """Test deleting a user.
    
    Args:
        client: Test client
        admin_token_headers: Admin token headers
        user_service: User service
    """
    # Create a user to delete
    user_to_delete = user_service.create_user(
        username="deleteme",
        email="delete@example.com",
        password="password123",
        roles=[UserRole.USER]
    )
    
    # Delete user
    response = client.delete(f"/api/users/{user_to_delete.id}", headers=admin_token_headers)
    assert response.status_code == 204
    
    # Verify user is deleted
    deleted_user = user_service.get_user_by_id(user_to_delete.id)
    assert deleted_user is None


def test_delete_user_unauthorized(client: TestClient, user_token_headers: dict, test_admin: User):
    """Test deleting a user without admin privileges.
    
    Args:
        client: Test client
        user_token_headers: User token headers
        test_admin: Test admin user
    """
    response = client.delete(f"/api/users/{test_admin.id}", headers=user_token_headers)
    assert response.status_code == 403


def test_delete_self(client: TestClient, admin_token_headers: dict, test_admin: User):
    """Test deleting own user account.
    
    Args:
        client: Test client
        admin_token_headers: Admin token headers
        test_admin: Test admin user
    """
    # Try to delete own account
    response = client.delete(f"/api/users/{test_admin.id}", headers=admin_token_headers)
    assert response.status_code == 400
