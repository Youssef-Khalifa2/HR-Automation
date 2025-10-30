"""Database models for HR Co-Pilot"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(enum.Enum):
    HR = "hr"
    LEADER = "leader"
    CHM = "chm"
    IT = "it"


class ResignationStatus(enum.Enum):
    SUBMITTED = "submitted"
    LEADER_APPROVED = "leader_approved"
    LEADER_REJECTED = "leader_rejected"
    CHM_APPROVED = "chm_approved"
    CHM_REJECTED = "chm_rejected"
    EXIT_DONE = "exit_done"
    ASSETS_RECORDED = "assets_recorded"
    MEDICAL_CHECKED = "medical_checked"
    OFFBOARDED = "offboarded"


class ExitInterviewStatus(enum.Enum):
    NOT_SCHEDULED = "not_scheduled"
    SCHEDULED = "scheduled"
    DONE = "done"
    NO_SHOW = "no_show"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Match existing DB column
    full_name = Column(String(120), nullable=False)  # Match existing DB length
    role = Column(String(10), nullable=False)  # Use string instead of enum to match existing DB
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Note: updated_at column doesn't exist in current DB, so we'll skip it

    # Relationships
    submissions = relationship("Submission", back_populates="created_by_user")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)

    # Employee information (matching existing DB)
    employee_name = Column(String(100), nullable=False)
    employee_email = Column(String(150), nullable=False)
    # Note: employee_id, department, position don't exist in current DB, will skip for now

    # Employment details (matching existing DB names)
    joining_date = Column(DateTime, nullable=False)  # Called hire_date in our model
    submission_date = Column(DateTime, nullable=False)  # Called resignation_date in our model
    last_working_day = Column(DateTime, nullable=False)
    in_probation = Column(Boolean, nullable=False)  # Computed column in DB
    notice_period_days = Column(Integer, nullable=False)  # Computed column in DB

    # Workflow status
    resignation_status = Column(String(30), nullable=False)  # Use string instead of enum
    exit_interview_status = Column(String(30), nullable=False)  # Use string instead of enum

    # Approval tracking
    team_leader_reply = Column(Boolean, nullable=True)  # True=approve, False=reject
    chinese_head_reply = Column(Boolean, nullable=True)  # True=approve, False=reject
    it_support_reply = Column(Boolean, nullable=True)  # True=cleared, False=issue

    # Medical and finalization
    medical_card_collected = Column(Boolean, nullable=False)
    vendor_mail_sent = Column(Boolean, nullable=False)

    # Notes and communication
    team_leader_notes = Column(Text, nullable=True)  # Match existing DB name
    chinese_head_notes = Column(Text, nullable=True)  # Match existing DB name
    exit_interview_notes = Column(Text, nullable=True)

    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    # Note: last_reminded_at doesn't exist in current DB

    # Foreign keys
    # created_by doesn't exist in current DB, will skip for now

    # Relationships
    assets = relationship("Asset", back_populates="submission")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    res_id = Column(Integer, nullable=False)  # This is the foreign key to submissions

    # Asset items
    laptop = Column(Boolean, nullable=True)
    mouse = Column(Boolean, nullable=True)
    headphones = Column(Boolean, nullable=True)
    others = Column(Text, nullable=True)

    # Approval status
    approved = Column(Boolean, nullable=True)

    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    submission = relationship("Submission", back_populates="assets")