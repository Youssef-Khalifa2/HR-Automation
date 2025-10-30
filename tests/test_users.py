"""User management tests"""
import pytest
from fastapi import status


class TestUsers:
    """Test user management endpoints"""

    def test_get_current_user_info(self, client, hr_token, hr_user):
        """Test getting current user information"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        response = client.get("/api/users/me", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == hr_user.email
        assert data["full_name"] == hr_user.full_name
        assert data["role"] == hr_user.role.value

    def test_create_user_success(self, client, hr_token):
        """Test successful user creation"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        user_data = {
            "email": "newuser@company.com",
            "password": "newpass123",
            "full_name": "New User",
            "role": "hr"
        }

        response = client.post("/api/users/", json=user_data, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newuser@company.com"
        assert data["full_name"] == "New User"
        assert data["role"] == "hr"
        assert "password" not in data  # Password should not be returned

    def test_create_user_duplicate_email(self, client, hr_token, hr_user):
        """Test creating user with duplicate email"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        user_data = {
            "email": hr_user.email,  # Duplicate email
            "password": "newpass123",
            "full_name": "Duplicate User",
            "role": "hr"
        }

        response = client.post("/api/users/", json=user_data, headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    def test_create_user_invalid_role(self, client, hr_token):
        """Test creating user with invalid role"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        user_data = {
            "email": "invalid@company.com",
            "password": "newpass123",
            "full_name": "Invalid User",
            "role": "invalid_role"
        }

        response = client.post("/api/users/", json=user_data, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_users_success(self, client, hr_token, hr_user):
        """Test listing users"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        response = client.get("/api/users/", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(user["email"] == hr_user.email for user in data)

    def test_list_users_pagination(self, client, hr_token):
        """Test user list pagination"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        params = {"skip": 0, "limit": 5}
        response = client.get("/api/users/", params=params, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_get_user_by_id_success(self, client, hr_token, hr_user):
        """Test getting user by ID"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        response = client.get(f"/api/users/{hr_user.id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == hr_user.id
        assert data["email"] == hr_user.email

    def test_get_user_not_found(self, client, hr_token):
        """Test getting non-existent user"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        response = client.get("/api/users/99999", headers=headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_create_different_role_users(self, client, hr_token):
        """Test creating users with different roles"""
        headers = {"Authorization": f"Bearer {hr_token}"}

        # Create leader user
        leader_data = {
            "email": "leader@company.com",
            "password": "leader123",
            "full_name": "Team Leader",
            "role": "leader"
        }
        response = client.post("/api/users/", json=leader_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK

        # Create CHM user
        chm_data = {
            "email": "chm@company.com",
            "password": "chm123",
            "full_name": "Chinese Head Manager",
            "role": "chm"
        }
        response = client.post("/api/users/", json=chm_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK

        # Create IT user
        it_data = {
            "email": "it@company.com",
            "password": "it123",
            "full_name": "IT Support",
            "role": "it"
        }
        response = client.post("/api/users/", json=it_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK

    def test_user_creation_validation(self, client, hr_token):
        """Test user creation validation"""
        headers = {"Authorization": f"Bearer {hr_token}"}

        # Test invalid email
        invalid_data = {
            "email": "invalid-email",
            "password": "test123",
            "full_name": "Test User",
            "role": "hr"
        }
        response = client.post("/api/users/", json=invalid_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test missing required fields
        incomplete_data = {
            "email": "test@company.com"
            # Missing password, full_name, role
        }
        response = client.post("/api/users/", json=incomplete_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test short password
        short_password_data = {
            "email": "test@company.com",
            "password": "123",  # Too short
            "full_name": "Test User",
            "role": "hr"
        }
        response = client.post("/api/users/", json=short_password_data, headers=headers)
        # Should succeed (no explicit password length validation in current implementation)
        assert response.status_code == status.HTTP_200_OK