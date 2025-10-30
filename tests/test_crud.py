"""CRUD operations tests"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.crud import (
    get_user, get_user_by_email, create_user,
    get_submission, get_submissions, create_submission, update_submission, delete_submission,
    get_asset_by_submission, create_asset, update_asset
)
from app.models import User, Submission, Asset, UserRole, ResignationStatus
from app.schemas import UserCreate, SubmissionCreate, AssetCreate, AssetUpdate


class TestUserCRUD:
    """Test User CRUD operations"""

    def test_get_user_by_id(self, db_session):
        """Test getting user by ID"""
        from app.auth import get_password_hash

        user = User(
            email="test@company.com",
            hashed_password=get_password_hash("testpass"),
            full_name="Test User",
            role=UserRole.HR
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        retrieved_user = get_user(db_session, user.id)
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.email == "test@company.com"

    def test_get_user_by_email(self, db_session):
        """Test getting user by email"""
        from app.auth import get_password_hash

        user = User(
            email="emailtest@company.com",
            hashed_password=get_password_hash("testpass"),
            full_name="Email Test User",
            role=UserRole.HR
        )
        db_session.add(user)
        db_session.commit()

        retrieved_user = get_user_by_email(db_session, "emailtest@company.com")
        assert retrieved_user is not None
        assert retrieved_user.email == "emailtest@company.com"

    def test_create_user_crud(self, db_session):
        """Test creating user through CRUD"""
        user_data = UserCreate(
            email="crudtest@company.com",
            password="testpass123",
            full_name="CRUD Test User",
            role=UserRole.HR
        )

        created_user = create_user(db_session, user_data)
        assert created_user is not None
        assert created_user.email == "crudtest@company.com"
        assert created_user.full_name == "CRUD Test User"
        assert created_user.role == UserRole.HR
        assert created_user.id is not None

    def test_get_users_list(self, db_session):
        """Test getting list of users"""
        from app.auth import get_password_hash

        # Create multiple users
        for i in range(5):
            user = User(
                email=f"listtest{i}@company.com",
                hashed_password=get_password_hash("testpass"),
                full_name=f"List Test User {i}",
                role=UserRole.HR
            )
            db_session.add(user)

        db_session.commit()

        users = get_users(db_session, skip=0, limit=10)
        assert len(users) >= 5


class TestSubmissionCRUD:
    """Test Submission CRUD operations"""

    def test_create_submission_crud(self, db_session):
        """Test creating submission through CRUD"""
        submission_data = SubmissionCreate(
            employee_name="CRUD Test Employee",
            employee_email="crudemp@company.com",
            employee_id="CRUD001",
            department="Testing",
            position="Test Engineer",
            hire_date=datetime(2020, 1, 1),
            resignation_date=datetime(2024, 1, 1),
            last_working_day=datetime(2024, 1, 31),
            in_probation=False,
            notice_period_days=30
        )

        created_submission = create_submission(db_session, submission_data)
        assert created_submission is not None
        assert created_submission.employee_name == "CRUD Test Employee"
        assert created_submission.employee_email == "crudemp@company.com"
        assert created_submission.resignation_status == ResignationStatus.SUBMITTED
        assert created_submission.id is not None

    def test_get_submission_by_id(self, db_session):
        """Test getting submission by ID"""
        submission_data = SubmissionCreate(
            employee_name="Get Test Employee",
            employee_email="getemp@company.com",
            employee_id="GET001",
            department="Testing",
            position="Test Engineer",
            hire_date=datetime(2020, 1, 1),
            resignation_date=datetime(2024, 1, 1),
            last_working_day=datetime(2024, 1, 31)
        )

        created_submission = create_submission(db_session, submission_data)
        retrieved_submission = get_submission(db_session, created_submission.id)

        assert retrieved_submission is not None
        assert retrieved_submission.id == created_submission.id
        assert retrieved_submission.employee_name == "Get Test Employee"

    def test_update_submission(self, db_session):
        """Test updating submission"""
        submission_data = SubmissionCreate(
            employee_name="Update Test Employee",
            employee_email="updateemp@company.com",
            employee_id="UPDATE001",
            department="Testing",
            position="Test Engineer",
            hire_date=datetime(2020, 1, 1),
            resignation_date=datetime(2024, 1, 1),
            last_working_day=datetime(2024, 1, 31)
        )

        created_submission = create_submission(db_session, submission_data)

        update_data = SubmissionUpdate(
            employee_name="Updated Employee Name",
            department="Updated Department",
            resignation_status=ResignationStatus.LEADER_APPROVED,
            team_leader_reply=True,
            leader_notes="Good employee"
        )

        updated_submission = update_submission(db_session, created_submission.id, update_data)
        assert updated_submission is not None
        assert updated_submission.employee_name == "Updated Employee Name"
        assert updated_submission.department == "Updated Department"
        assert updated_submission.resignation_status == ResignationStatus.LEADER_APPROVED
        assert updated_submission.team_leader_reply is True
        assert updated_submission.leader_notes == "Good employee"

    def test_delete_submission(self, db_session):
        """Test deleting submission"""
        submission_data = SubmissionCreate(
            employee_name="Delete Test Employee",
            employee_email="deleteemp@company.com",
            employee_id="DELETE001",
            department="Testing",
            position="Test Engineer",
            hire_date=datetime(2020, 1, 1),
            resignation_date=datetime(2024, 1, 1),
            last_working_day=datetime(2024, 1, 31)
        )

        created_submission = create_submission(db_session, submission_data)

        # Verify it exists
        assert get_submission(db_session, created_submission.id) is not None

        # Delete it
        success = delete_submission(db_session, created_submission.id)
        assert success is True

        # Verify it's gone
        assert get_submission(db_session, created_submission.id) is None

    def test_get_submissions_with_filters(self, db_session):
        """Test getting submissions with filters"""
        # Create submissions with different statuses
        submissions_data = [
            SubmissionCreate(
                employee_name=f"Filter Test {i}",
                employee_email=f"filter{i}@company.com",
                employee_id=f"FILTER{i:03d}",
                department="Engineering" if i % 2 == 0 else "Marketing",
                position="Engineer" if i % 2 == 0 else "Manager",
                hire_date=datetime(2020, 1, 1),
                resignation_date=datetime(2024, 1, 1),
                last_working_day=datetime(2024, 1, 31)
            )
            for i in range(10)
        ]

        created_submissions = []
        for data in submissions_data:
            submission = create_submission(db_session, data)
            created_submissions.append(submission)

        # Update some submissions to different statuses
        update_submission(db_session, created_submissions[0].id,
                         SubmissionUpdate(resignation_status=ResignationStatus.LEADER_APPROVED))
        update_submission(db_session, created_submissions[1].id,
                         SubmissionUpdate(resignation_status=ResignationStatus.CHM_APPROVED))

        # Test filters
        engineering_submissions = get_submissions(db_session, department="Engineering")
        assert len(engineering_submissions) == 5

        submitted_submissions = get_submissions(db_session,
                                               resignation_status=ResignationStatus.SUBMITTED)
        assert len(submitted_submissions) >= 8  # At least 8 should still be submitted


class TestAssetCRUD:
    """Test Asset CRUD operations"""

    def test_create_asset_crud(self, db_session):
        """Test creating asset through CRUD"""
        # Create submission first
        submission_data = SubmissionCreate(
            employee_name="Asset Test Employee",
            employee_email="assetemp@company.com",
            employee_id="ASSET001",
            department="IT",
            position="Developer",
            hire_date=datetime(2020, 1, 1),
            resignation_date=datetime(2024, 1, 1),
            last_working_day=datetime(2024, 1, 31)
        )
        submission = create_submission(db_session, submission_data)

        # Create asset
        asset_data = AssetCreate(
            submission_id=submission.id,
            laptop=True,
            mouse=True,
            headphones=False,
            others="USB-C hub",
            approved=True
        )

        created_asset = create_asset(db_session, asset_data)
        assert created_asset is not None
        assert created_asset.submission_id == submission.id
        assert created_asset.laptop is True
        assert created_asset.approved is True

    def test_get_asset_by_submission(self, db_session):
        """Test getting asset by submission ID"""
        # Create submission
        submission_data = SubmissionCreate(
            employee_name="Asset Get Test",
            employee_email="assetget@company.com",
            employee_id="ASSETGET001",
            department="Finance",
            position="Accountant",
            hire_date=datetime(2020, 1, 1),
            resignation_date=datetime(2024, 1, 1),
            last_working_day=datetime(2024, 1, 31)
        )
        submission = create_submission(db_session, submission_data)

        # Create asset
        asset_data = AssetCreate(
            submission_id=submission.id,
            laptop=True,
            mouse=False,
            headphones=True,
            others="External monitor",
            approved=True
        )
        created_asset = create_asset(db_session, asset_data)

        # Retrieve asset
        retrieved_asset = get_asset_by_submission(db_session, submission.id)
        assert retrieved_asset is not None
        assert retrieved_asset.id == created_asset.id
        assert retrieved_asset.laptop is True
        assert retrieved_asset.mouse is False
        assert retrieved_asset.headphones is True

    def test_update_asset(self, db_session):
        """Test updating asset"""
        # Create submission
        submission_data = SubmissionCreate(
            employee_name="Asset Update Test",
            employee_email="assetupdate@company.com",
            employee_id="ASSETUPD001",
            department="HR",
            position="HR Manager",
            hire_date=datetime(2020, 1, 1),
            resignation_date=datetime(2024, 1, 1),
            last_working_day=datetime(2024, 1, 31)
        )
        submission = create_submission(db_session, submission_data)

        # Create asset
        asset_data = AssetCreate(
            submission_id=submission.id,
            laptop=True,
            mouse=False,
            headphones=False,
            others="",
            approved=False
        )
        create_asset(db_session, asset_data)

        # Update asset
        update_data = AssetUpdate(
            mouse=True,
            headphones=True,
            others="Docking station and extra cables",
            approved=True
        )

        updated_asset = update_asset(db_session, submission.id, update_data)
        assert updated_asset is not None
        assert updated_asset.laptop is True  # Unchanged
        assert updated_asset.mouse is True
        assert updated_asset.headphones is True
        assert updated_asset.others == "Docking station and extra cables"
        assert updated_asset.approved is True