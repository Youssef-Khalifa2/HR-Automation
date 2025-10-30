"""Authentication tests"""
import pytest
from fastapi import status


class TestAuthentication:
    """Test authentication endpoints"""

    def test_login_success(self, client, hr_user):
        """Test successful login"""
        response = client.post("/api/auth/login", json={
            "email": "hr@test.com",
            "password": "testpass123"
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "hr@test.com"
        assert data["user"]["role"] == "hr"

    def test_login_invalid_email(self, client):
        """Test login with invalid email"""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "testpass123"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_invalid_password(self, client, hr_user):
        """Test login with invalid password"""
        response = client.post("/api/auth/login", json={
            "email": "hr@test.com",
            "password": "wrongpassword"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_inactive_user(self, client, db_session):
        """Test login with inactive user"""
        from app.auth import get_password_hash
        from app.models import User, UserRole

        # Create inactive user
        user = User(
            email="inactive@test.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Inactive User",
            role=UserRole.HR,
            is_active=False
        )
        db_session.add(user)
        db_session.commit()

        response = client.post("/api/auth/login", json={
            "email": "inactive@test.com",
            "password": "testpass123"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Inactive user" in response.json()["detail"]

    def test_token_endpoint_success(self, client, hr_user):
        """Test OAuth2 token endpoint"""
        response = client.post("/api/auth/token", data={
            "username": "hr@test.com",
            "password": "testpass123"
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_valid_token(self, client, hr_token):
        """Test accessing protected endpoint with valid token"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == "hr@test.com"

    def test_non_hr_user_access_denied(self, client, db_session):
        """Test that non-HR users cannot access HR-only endpoints"""
        from app.auth import get_password_hash
        from app.models import User, UserRole

        # Create non-HR user
        user = User(
            email="leader@test.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Team Leader",
            role=UserRole.LEADER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Login as non-HR user
        response = client.post("/api/auth/login", json={
            "email": "leader@test.com",
            "password": "testpass123"
        })
        token = response.json()["access_token"]

        # Try to access HR-only endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/submissions/", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not enough permissions" in response.json()["detail"]