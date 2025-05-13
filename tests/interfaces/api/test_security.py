"""Tests for STOCKER Pro API security features.

This module contains tests for the security features of the STOCKER Pro API,
including authentication, rate limiting, and security headers.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from stocker.core.config.settings import get_settings
from stocker.interfaces.api.app import create_app
from stocker.interfaces.api.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    is_token_expired,
    validate_password_strength
)
from stocker.interfaces.api.middleware.rate_limit import RateLimitMiddleware
from stocker.interfaces.api.middleware.security import SecurityHeadersMiddleware


@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    return create_app()


@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI application."""
    return TestClient(test_app)


class TestPasswordSecurity:
    """Test password security functions."""
    
    def test_password_hashing(self):
        """Test that password hashing and verification work correctly."""
        # Test password hashing
        password = "SecurePassword123"
        hashed = get_password_hash(password)
        
        # Verify the hash is different from the original password
        assert hashed != password
        
        # Verify the password against the hash
        assert verify_password(password, hashed) is True
        
        # Verify incorrect password fails
        assert verify_password("WrongPassword", hashed) is False
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Test strong password
        result = validate_password_strength("StrongPassword123")
        assert result["success"] is True
        
        # Test password too short
        result = validate_password_strength("Short1")
        assert result["success"] is False
        assert "length" in result["message"]
        
        # Test password without uppercase
        result = validate_password_strength("weakpassword123")
        assert result["success"] is False
        assert "uppercase" in result["message"]
        
        # Test password without lowercase
        result = validate_password_strength("ALLCAPS123")
        assert result["success"] is False
        assert "lowercase" in result["message"]
        
        # Test password without digits
        result = validate_password_strength("NoDigitsHere")
        assert result["success"] is False
        assert "digit" in result["message"]


class TestJWTTokens:
    """Test JWT token functions."""
    
    def test_access_token_creation(self):
        """Test that access tokens are created correctly."""
        # Create token data
        data = {"sub": "user123", "username": "testuser"}
        
        # Create access token
        token = create_access_token(data)
        
        # Decode token
        payload = decode_token(token)
        
        # Verify token data
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["token_type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        assert "nbf" in payload
    
    def test_refresh_token_creation(self):
        """Test that refresh tokens are created correctly."""
        # Create token data
        data = {"sub": "user123", "username": "testuser"}
        
        # Create refresh token
        token = create_refresh_token(data)
        
        # Decode token
        payload = decode_token(token)
        
        # Verify token data
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["token_type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
        assert "nbf" in payload
    
    def test_token_expiration(self):
        """Test token expiration checking."""
        # Create token data
        data = {"sub": "user123"}
        
        # Create token with short expiration
        token = create_access_token(data, expires_delta=timedelta(seconds=1))
        
        # Token should not be expired initially
        assert is_token_expired(token) is False
        
        # Wait for token to expire
        time.sleep(2)
        
        # Token should be expired now
        assert is_token_expired(token) is True


class TestSecurityMiddleware:
    """Test security middleware."""
    
    def test_security_headers(self, client):
        """Test that security headers are added to responses."""
        # Make a request to the API
        response = client.get("/health")
        
        # Check security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        
        assert "Referrer-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers
    
    def test_version_header(self, client):
        """Test that version header is added to responses."""
        # Make a request to the API
        response = client.get("/health")
        
        # Check version header
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == get_settings().version


class TestRateLimiting:
    """Test rate limiting middleware."""
    
    def test_rate_limiting(self):
        """Test that rate limiting works correctly."""
        # Create a simple test app with rate limiting
        app = FastAPI()
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "success"}
        
        # Add rate limiting middleware with low limit
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=2  # Very low limit for testing
        )
        
        # Create test client
        client = TestClient(app)
        
        # First request should succeed
        response1 = client.get("/test")
        assert response1.status_code == 200
        
        # Second request should succeed
        response2 = client.get("/test")
        assert response2.status_code == 200
        
        # Third request should be rate limited
        response3 = client.get("/test")
        assert response3.status_code == 429
        assert "Too many requests" in response3.text
        assert "Retry-After" in response3.headers


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_endpoint(self, client, monkeypatch):
        """Test the login endpoint."""
        # Mock the user service
        mock_user = MagicMock()
        mock_user.id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.roles = ["user"]
        
        # Mock the authenticate_user method
        async def mock_authenticate(username, password):
            if username == "testuser" and password == "password123":
                return mock_user
            return None
        
        # Apply the mock
        with patch("stocker.services.user_service.UserService.authenticate_user", 
                  side_effect=mock_authenticate):
            # Test successful login
            response = client.post(
                "/api/auth/token",
                data={"username": "testuser", "password": "password123"}
            )
            
            # Check response
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
            
            # Test failed login
            response = client.post(
                "/api/auth/token",
                data={"username": "testuser", "password": "wrongpassword"}
            )
            
            # Check response
            assert response.status_code == 401
            assert "detail" in response.json()
    
    @pytest.mark.asyncio
    async def test_refresh_token_endpoint(self, client, monkeypatch):
        """Test the refresh token endpoint."""
        # Create a valid refresh token
        refresh_token = create_refresh_token({"sub": "user123", "username": "testuser"})
        
        # Mock the user service
        mock_user = MagicMock()
        mock_user.id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.roles = ["user"]
        
        # Mock the get_user_by_id method
        async def mock_get_user(user_id):
            if user_id == "user123":
                return mock_user
            return None
        
        # Apply the mock
        with patch("stocker.services.user_service.UserService.get_user_by_id", 
                  side_effect=mock_get_user):
            # Test successful token refresh
            response = client.post(
                "/api/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            
            # Check response
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
            
            # Test with invalid token
            response = client.post(
                "/api/auth/refresh",
                json={"refresh_token": "invalid-token"}
            )
            
            # Check response
            assert response.status_code == 401
            assert "detail" in response.json()
