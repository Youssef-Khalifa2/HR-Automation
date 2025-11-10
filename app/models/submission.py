from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.database import Base


class ResignationStatus(str, PyEnum):
    SUBMITTED = "submitted"
    LEADER_APPROVED = "leader_approved"
    LEADER_REJECTED = "leader_rejected"
    CHM_APPROVED = "chm_approved"
    CHM_REJECTED = "chm_rejected"
    EXIT_DONE = "exit_done"
    ASSETS_RECORDED = "assets_recorded"
    MEDICAL_CHECKED = "medical_checked"
    OFFBOARDED = "offboarded"


class ExitInterviewStatus(str, PyEnum):
    NOT_SCHEDULED = "not_scheduled"
    SCHEDULED = "scheduled"
    DONE = "done"
    NO_SHOW = "no_show"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)

    # Employee Information
    employee_name = Column(String(100), nullable=False)
    employee_email = Column(String(150), nullable=False)

    # Dates (matching actual database schema)
    joining_date = Column(DateTime, nullable=False)  # Matches database column
    submission_date = Column(DateTime, nullable=False)  # Matches database column
    last_working_day = Column(DateTime, nullable=False)

    # Status Fields (using SQLAlchemy Enum for type safety)
    resignation_status = Column(String(30), nullable=False, default=ResignationStatus.SUBMITTED.value)
    exit_interview_status = Column(String(30), nullable=False, default=ExitInterviewStatus.NOT_SCHEDULED.value)

    # Approval Responses
    team_leader_reply = Column(Boolean, nullable=True)
    team_leader_notes = Column(Text, nullable=True)
    chinese_head_reply = Column(Boolean, nullable=True)
    chinese_head_notes = Column(Text, nullable=True)
    exit_interview_notes = Column(Text, nullable=True)
    it_support_reply = Column(Boolean, nullable=True)

    # HR Fields
    medical_card_collected = Column(Boolean, nullable=False)
    vendor_mail_sent = Column(Boolean, nullable=False)

    # Probation and Notice (generated columns - read-only)
    in_probation = Column(Boolean, nullable=False, server_default="false")
    notice_period_days = Column(Integer, nullable=False, server_default="30")

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    last_reminded_at = Column(DateTime(timezone=True), nullable=True)  # For reminder system

    # Relationships
    assets = relationship("Asset", back_populates="submission", uselist=False)
    exit_interview = relationship("ExitInterview", back_populates="submission", uselist=False)