"""Submission CRUD tests"""
import pytest
from fastapi import status
from datetime import datetime


class TestSubmissions:
    """Test submission endpoints"""

    def test_create_submission_success(self, client, hr_token):
        """Test successful submission creation"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        submission_data = {
            "employee_name": "Jane Smith",
            "employee_email": "jane.smith@company.com",
            "employee_id": "EMP002",
            "department": "Marketing",
            "position": "Marketing Manager",
            "hire_date": "2021-03-15T10:00:00",
            "resignation_date": "2024-01-20T10:00:00",
            "last_working_day": "2024-02-19T10:00:00",
            "in_probation": False,
            "notice_period_days": 30
        }

        response = client.post("/api/submissions/", json=submission_data, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["employee_name"] == "Jane Smith"
        assert data["employee_email"] == "jane.smith@company.com"
        assert data["resignation_status"] == "submitted"

    def test_create_submission_validation_error(self, client, hr_token):
        """Test submission creation with validation errors"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        invalid_data = {
            "employee_name": "",  # Empty name should fail
            "employee_email": "invalid-email",  # Invalid email
            "employee_id": "EMP003",
            "department": "Sales",
            "position": "Sales Rep"
        }

        response = client.post("/api/submissions/", json=invalid_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_submissions_success(self, client, hr_token, sample_submission):
        """Test listing submissions"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        response = client.get("/api/submissions/", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(s["employee_name"] == "John Doe" for s in data)

    def test_list_submissions_with_filters(self, client, hr_token, sample_submission):
        """Test listing submissions with filters"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        params = {"resignation_status": "submitted", "department": "Engineering"}
        response = client.get("/api/submissions/", params=params, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should return only submissions matching the filters

    def test_get_submission_success(self, client, hr_token, sample_submission):
        """Test getting a specific submission"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        response = client.get(f"/api/submissions/{sample_submission.id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_submission.id
        assert data["employee_name"] == "John Doe"

    def test_get_submission_not_found(self, client, hr_token):
        """Test getting non-existent submission"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        response = client.get("/api/submissions/99999", headers=headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Submission not found" in response.json()["detail"]

    def test_update_submission_success(self, client, hr_token, sample_submission):
        """Test updating a submission"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        update_data = {
            "employee_name": "John Updated",
            "department": "Engineering Updated"
        }

        response = client.patch(
            f"/api/submissions/{sample_submission.id}",
            json=update_data,
            headers=headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["employee_name"] == "John Updated"
        assert data["department"] == "Engineering Updated"

    def test_update_submission_status(self, client, hr_token, sample_submission):
        """Test updating submission status"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        from app.models import ResignationStatus
        update_data = {
            "resignation_status": "leader_approved",
            "team_leader_reply": True,
            "leader_notes": "Employee has been valuable team member"
        }

        response = client.patch(
            f"/api/submissions/{sample_submission.id}",
            json=update_data,
            headers=headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["resignation_status"] == "leader_approved"
        assert data["team_leader_reply"] is True
        assert data["leader_notes"] == "Employee has been valuable team member"

    def test_delete_submission_success(self, client, hr_token, sample_submission):
        """Test deleting a submission"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        response = client.delete(f"/api/submissions/{sample_submission.id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert "deleted successfully" in response.json()["message"]

        # Verify deletion
        response = client.get(f"/api/submissions/{sample_submission.id}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_submission_not_found(self, client, hr_token):
        """Test deleting non-existent submission"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        response = client.delete("/api/submissions/99999", headers=headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Submission not found" in response.json()["detail"]

    def test_submissions_pagination(self, client, hr_token):
        """Test submission pagination"""
        headers = {"Authorization": f"Bearer {hr_token}"}
        params = {"skip": 0, "limit": 10}
        response = client.get("/api/submissions/", params=params, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_unauthorized_access(self, client):
        """Test that unauthorized users cannot access submissions"""
        response = client.get("/api/submissions/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = client.post("/api/submissions/", json={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = client.get("/api/submissions/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED