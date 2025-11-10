from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ExitInterview(Base):
    __tablename__ = "exit_interviews"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False, unique=True)

    # Scheduling Information
    scheduled_date = Column(DateTime, nullable=True)
    scheduled_time = Column(String(10), nullable=True)  # HH:MM format
    location = Column(String(200), nullable=True)
    interviewer = Column(String(100), nullable=True)

    # Interview Details
    interview_completed = Column(Boolean, nullable=False, default=False)
    interview_feedback = Column(Text, nullable=True)
    interview_rating = Column(Integer, nullable=True)  # 1-5 scale
    interview_type = Column(String(50), nullable=True)  # in-person, virtual, phone
    interview_completed_at = Column(DateTime, nullable=True)  # When interview was marked as completed

    # Follow-up Actions
    hr_notes = Column(Text, nullable=True)
    it_notification_sent = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    interview_completed_at = Column(DateTime, nullable=True)

    # Relationship
    submission = relationship("Submission", back_populates="exit_interview")
    reminders = relationship("ExitInterviewReminder", back_populates="exit_interview")


class ExitInterviewReminder(Base):
    __tablename__ = "exit_interview_reminders"

    id = Column(Integer, primary_key=True, index=True)
    exit_interview_id = Column(Integer, ForeignKey("exit_interviews.id"), nullable=False)

    # Reminder Type
    reminder_type = Column(String(50), nullable=False)  # schedule_interview, submit_feedback, employee_reminder

    # Status
    sent = Column(Boolean, nullable=False, default=False)
    sent_at = Column(DateTime, nullable=True)
    scheduled_for = Column(DateTime, nullable=False)

    # Email details
    recipient_email = Column(String(150), nullable=False)
    recipient_name = Column(String(100), nullable=False)

    # Response tracking
    responded = Column(Boolean, nullable=False, default=False)
    responded_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationship
    exit_interview = relationship("ExitInterview", back_populates="reminders")