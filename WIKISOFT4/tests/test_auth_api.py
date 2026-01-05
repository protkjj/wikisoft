"""
Auth API Endpoint Tests (WIKISOFT4)
"""
import pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, "/Users/kj/Desktop/wiki/WIKISOFT4")

from api.v4.main import app

client = TestClient(app)


class TestLoginEndpoint:
    """Login API tests."""

    def test_login_success_admin(self):
        """Admin login success."""
        response = client.post(
            "/api/v4/auth/login",
            json={"username": "admin", "password": "admin1234!"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["role"] == "admin"

    def test_login_success_user(self):
        """User login success."""
        response = client.post(
            "/api/v4/auth/login",
            json={"username": "user", "password": "user1234!"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "user"

    def test_login_wrong_password(self):
        """Login with wrong password."""
        response = client.post(
            "/api/v4/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )

        assert response.status_code == 401

    def test_login_wrong_username(self):
        """Login with wrong username."""
        response = client.post(
            "/api/v4/auth/login",
            json={"username": "nonexistent", "password": "password"}
        )

        assert response.status_code == 401

    def test_login_missing_fields(self):
        """Login with missing fields."""
        response = client.post(
            "/api/v4/auth/login",
            json={"username": "admin"}
        )

        assert response.status_code == 422  # Validation error


class TestMeEndpoint:
    """Current user API tests."""

    def test_me_with_valid_token(self):
        """Get current user with valid token."""
        # First login
        login_response = client.post(
            "/api/v4/auth/login",
            json={"username": "admin", "password": "admin1234!"}
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/api/v4/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "admin"
        assert data["role"] == "admin"

    def test_me_without_token(self):
        """Get current user without token."""
        response = client.get("/api/v4/auth/me")

        assert response.status_code == 401

    def test_me_with_invalid_token(self):
        """Get current user with invalid token."""
        response = client.get(
            "/api/v4/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


class TestVerifyEndpoint:
    """Token verification API tests."""

    def test_verify_valid_token(self):
        """Verify valid token."""
        login_response = client.post(
            "/api/v4/auth/login",
            json={"username": "admin", "password": "admin1234!"}
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v4/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] == True
        assert data["user"]["id"] == "admin"

    def test_verify_no_token(self):
        """Verify without token."""
        response = client.get("/api/v4/auth/verify")

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] == False


class TestRefreshEndpoint:
    """Token refresh API tests."""

    def test_refresh_token(self):
        """Refresh valid token."""
        # Login first
        login_response = client.post(
            "/api/v4/auth/login",
            json={"username": "admin", "password": "admin1234!"}
        )
        token = login_response.json()["access_token"]

        # Refresh
        response = client.post(
            "/api/v4/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        # New token exists and is valid format
        assert len(data["access_token"]) > 50


class TestLogoutEndpoint:
    """Logout API tests."""

    def test_logout(self):
        """Logout with valid token."""
        login_response = client.post(
            "/api/v4/auth/login",
            json={"username": "admin", "password": "admin1234!"}
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/v4/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "admin"


class TestRegisterEndpoint:
    """Registration API tests."""

    def test_register_new_user(self):
        """Register new user."""
        response = client.post(
            "/api/v4/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "password123!",
                "name": "New User"
            }
        )

        if response.status_code == 200:
            data = response.json()
            assert data["id"] == "newuser"
            assert data["email"] == "newuser@test.com"
        elif response.status_code == 400:
            # User already exists from previous test run
            pass

    def test_register_duplicate_username(self):
        """Register with duplicate username."""
        # First registration
        client.post(
            "/api/v4/auth/register",
            json={
                "username": "duplicate",
                "email": "dup1@test.com",
                "password": "password123!",
                "name": "Dup User"
            }
        )

        # Second registration with same username
        response = client.post(
            "/api/v4/auth/register",
            json={
                "username": "duplicate",
                "email": "dup2@test.com",
                "password": "password123!",
                "name": "Dup User 2"
            }
        )

        assert response.status_code == 400


class TestUsersEndpoint:
    """Admin users endpoint tests."""

    def test_list_users_as_admin(self):
        """List users as admin."""
        login_response = client.post(
            "/api/v4/auth/login",
            json={"username": "admin", "password": "admin1234!"}
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v4/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least admin and user

    def test_list_users_as_user(self):
        """List users as regular user (should fail)."""
        login_response = client.post(
            "/api/v4/auth/login",
            json={"username": "user", "password": "user1234!"}
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v4/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403  # Forbidden


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
