"""Database model tests"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models import User, Submission, Asset, UserRole, ResignationStatus, ExitInterviewStatus


class TestUserModel:
    """Test User model"""

    def test_create_user(self, db_session):
        """Test creating a user"""
        from app.auth import get_password_hash

        user = User(
            email="test@company.com",
            hashed_password=get_password_hash("testpass"),
            full_name="Test User",
            role=UserRole.HR,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.email == "test@company.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.HR
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_unique_email(self, db_session):
        """Test that user emails must be unique"""
        from app.auth import get_password_hash

        # Create first user
        user1 = User(
            email="duplicate@company.com",
            hashed_password=get_password_hash("testpass"),
            full_name="User 1",
            role=UserRole.HR
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create second user with same email
        user2 = User(
            email="duplicate@company.com",
            hashed_password=get_password_hash("testpass"),
            full_name="User 2",
            role=UserRole.LEADER
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_role_enum(self, db_session):
        """Test user role enumeration"""
        from app.auth import get_password_hash

        roles = [UserRole.HR, UserRole.LEADER, UserRole.CHM, UserRole.IT]

        for role in roles:
            user = User(
                email=f"test_{role.value}@company.com",
                hashed_password=get_password_hash("testpass"),
                full_name=f"Test {role.value}",
                role=role
            )
            db_session.add(user)

        db_session.commit()

        for role in roles:
            user = db_session.query(User).filter(
                User.email == f"test_{role.value}@company.com"
            ).first()
            assert user is not None
            assert user.role == role


class TestSubmissionModel:
    """Test Submission model"""

    def test_create_submission(self, db_session):
        """Test creating a submission"""
        from app.auth import get_password_hash

        # Create user first
        user = User(
            email="hr@company.com",
            hashed_password=get_password_hash("testpass"),
            full_name="HR User",
            role=UserRole.HR
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create submission
        submission = Submission(
            employee_name="John Doe",
            employee_email="john.doe@company.com",
            employee_id="EMP001",
            department="Engineering",
            position="Software Engineer",
            hire_date=datetime(2020, 1, 15),
            resignation_date=datetime(2024, 1, 15),
            last_working_day=datetime(2024, 2, 14),
            in_probation=False,
            notice_period_days=30,
            created_by=user.id
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        assert submission.id is not None
        assert submission.employee_name == "John Doe"
        assert submission.resignation_status == ResignationStatus.SUBMITTED
        assert submission.exit_interview_status == ExitInterviewStatus.NOT_SCHEDULED
        assert submission.created_at is not None

    def test_submission_status_transitions(self, db_session):
        """Test submission status transitions"""
        from app.auth import get_password_hash

        # Create user
        user = User(
            email="hr@company.com",
            hashed_password=get_password_hash("testpass"),
            full_name="HR User",
            role=UserRole.HR
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create submission
        submission = Submission(
            employee_name="Jane Smith",
            employee_email="jane.smith@company.com",
            employee_id="EMP002",
            department="Marketing",
            position="Marketing Manager",
            hire_date=datetime(2021, 3, 15),
            resignation_date=datetime(2024, 1, 20),
            last_working_day=datetime(2024, 2, 19),
            created_by=user.id
        )
        db_session.add(submission)
        db_session.commit()

        # Test status transitions
        submission.resignation_status = ResignationStatus.LEADER_APPROVED
        submission.team_leader_reply = True
        db_session.commit()

        assert submission.resignation_status == ResignationStatus.LEADER_APPROVED
        assert submission.team_leader_reply is True

        submission.resignation_status = ResignationStatus.CHM_APPROVED
        submission.chinese_head_reply = True
        db_session.commit()

        assert submission.resignation_status == ResignationStatus.CHM_APPROVED
        assert submission.chinese_head_reply is True

    def test_submission_with_notes(self, db_session):
        """Test submission with notes"""
        from app.auth import get_password_hash

        # Create user
        user = User(
            email="hr@company.com",
            hashed_password=get_password_hash("testpass"),
            full_name="HR User",
            role=UserRole.HR
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create submission with notes
        submission = Submission(
            employee_name="Bob Johnson",
            employee_email="bob.johnson@company.com",
            employee_id="EMP003",
            department="Sales",
            position="Sales Representative",
            hire_date=datetime(2019, 6, 1),
            resignation_date=datetime(2024, 1, 10),
            last_working_day=datetime(2024, 2, 9),
            leader_notes="Great team player, will be missed",
            chm_notes="Approved for transition",
            exit_interview_notes="Constructive feedback provided",
            created_by=user.id
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        assert submission.leader_notes == "Great team player, will be missed"
        assert submission.chm_notes == "Approved for transition"
        assert submission.exit_interview_notes == "Constructive feedback provided"


class TestAssetModel:
    """Test Asset model"""

    def test_create_asset(self, db_session):
        """Test creating an asset"""
        from app.auth import get_password_hash

        # Create user and submission first
        user = User(
            email="hr@company.com",
            hashed_password=get_password_hash("testpass"),
            full_name="HR User",
            role=UserRole.HR
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        submission = Submission(
            employee_name="Alice Brown",
            employee_email="alice.brown@company.com",
            employee_id="EMP004",
            department="Finance",
            position="Accountant",
            hire_date=datetime(2020, 8, 15),
            resignation_date=datetime(2024, 1, 25),
            last_working_day=datetime(2024, 2, 24),
            created_by=user.id
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        # Create asset
        asset = Asset(
            submission_id=submission.id,
            laptop=True,
            mouse=True,
            headphones=False,
            others="Monitor stand and keyboard",
            approved=True
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)

        assert asset.id is not None
        assert asset.submission_id == submission.id
        assert asset.laptop is True
        assert asset.mouse is True
        assert asset.headphones is False
        assert asset.others == "Monitor stand and keyboard"
        assert asset.approved is True

    def test_asset_submission_relationship(self, db_session):
        """Test asset-submission relationship"""
        from app.auth import get_password_hash

        # Create user and submission
        user = User(
            email="hr@company.com",
            hashed_password=get_password_hash("testpass"),
            full_name="HR User",
            role=UserRole.HR
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        submission = Submission(
            employee_name="Charlie Wilson",
            employee_email="charlie.wilson@company.com",
            employee_id="EMP005",
            department="IT",
            position="Developer",
            hire_date=datetime(2021, 1, 10),
            resignation_date=datetime(2024, 1, 30),
            last_working_day=datetime(2024, 2, 29),
            created_by=user.id
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        # Create asset
        asset = Asset(
            submission_id=submission.id,
            laptop=True,
            mouse=True,
            headphones=True,
            others="None",
            approved=True
        )
        db_session.add(asset)
        db_session.commit()

        # Test relationship
        retrieved_submission = db_session.query(Submission).filter(
            Submission.id == submission.id
        ).first()
        assert retrieved_submission.assets is not None
        assert retrieved_submission.assets.laptop is True
        assert retrieved_submission.assets.approved is True