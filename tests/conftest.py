"""Pytest configuration and fixtures"""
import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.database import get_db, Base
from app.models import User, UserRole

# Test database URL (SQLite in memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def db():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Create test database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def hr_user(db_session):
    """Create HR user for testing"""
    from app.auth import get_password_hash
    user = User(
        email="hr@test.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test HR User",
        role=UserRole.HR,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def hr_token(hr_user, client):
    """Get JWT token for HR user"""
    response = client.post("/api/auth/login", json={
        "email": "hr@test.com",
        "password": "testpass123"
    })
    return response.json()["access_token"]


@pytest.fixture
def sample_submission(db_session, hr_user):
    """Create sample submission for testing"""
    from app.models import Submission, ResignationStatus
    from datetime import datetime

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
        resignation_status=ResignationStatus.SUBMITTED,
        created_by=hr_user.id
    )
    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)
    return submission