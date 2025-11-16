"""Pydantic schemas for Exit Interview management"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ExitInterviewSchedule(BaseModel):
    """Schema for scheduling an exit interview"""
    scheduled_date: datetime
    scheduled_time: str  # HH:MM format
    location: Optional[str] = "HR Meeting Room"
    interviewer: Optional[str] = "HR Representative"
    interview_type: Optional[str] = "in-person"


class ExitInterviewFeedback(BaseModel):
    """Schema for submitting interview feedback"""
    interview_feedback: Optional[str] = None
    reason_to_leave: Optional[str] = None
    hr_notes: Optional[str] = None


class ExitInterviewBase(BaseModel):
    """Base exit interview schema"""
    id: int
    submission_id: int

    # Scheduling Information
    scheduled_date: Optional[datetime] = None
    scheduled_time: Optional[str] = None
    location: Optional[str] = None
    interviewer: Optional[str] = None

    # Interview Details
    interview_completed: bool = False
    interview_feedback: Optional[str] = None
    reason_to_leave: Optional[str] = None
    interview_type: Optional[str] = None

    # Follow-up Actions
    hr_notes: Optional[str] = None
    it_notification_sent: bool = False

    # Timestamps
    created_at: datetime
    updated_at: datetime
    interview_completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExitInterviewWithSubmission(ExitInterviewBase):
    """Exit interview with submission details"""
    employee_name: str
    employee_email: str
    department: Optional[str] = None
    position: Optional[str] = None
    last_working_day: datetime
    resignation_status: str


class ExitInterviewReminderBase(BaseModel):
    """Base reminder schema"""
    id: int
    exit_interview_id: int
    reminder_type: str
    recipient_email: str
    recipient_name: str
    scheduled_for: datetime
    sent: bool = False
    sent_at: Optional[datetime] = None
    responded: bool = False
    responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExitInterviewStatistics(BaseModel):
    """Exit interview statistics"""
    total_submissions: int
    pending_scheduling: int
    scheduled: int
    completed: int
    completion_rate: float


class InterviewSchedulingRequest(BaseModel):
    """Request for HR to schedule an interview"""
    submission_id: int
    scheduled_date: datetime
    scheduled_time: str
    location: Optional[str] = "HR Meeting Room"
    interviewer: Optional[str] = "HR Representative"
    interview_type: Optional[str] = "in-person"


class InterviewFeedbackRequest(BaseModel):
    """Request for HR to submit interview feedback"""
    interview_id: int
    interview_feedback: Optional[str] = None
    reason_to_leave: Optional[str] = None
    hr_notes: Optional[str] = None


# Response schemas for API
class ExitInterviewScheduleResponse(BaseModel):
    """Response after scheduling an interview"""
    message: str
    interview_id: int
    submission_id: int
    employee_name: str
    employee_email: str
    scheduled_date: datetime
    scheduled_time: str
    location: str
    interviewer: str
    email_sent: bool


class ExitInterviewFeedbackResponse(BaseModel):
    """Response after submitting interview feedback"""
    message: str
    interview_id: int
    submission_id: int
    employee_name: str
    interview_completed: bool
    it_notification_sent: bool
    feedback_submitted: bool


class UpcomingInterview(BaseModel):
    """Schema for upcoming interviews display"""
    interview_id: int
    submission_id: int
    employee_name: str
    scheduled_date: datetime
    scheduled_time: str
    location: str
    interviewer: str
    days_until_interview: int


class PendingSchedulingItem(BaseModel):
    """Schema for items that need scheduling"""
    submission_id: int
    employee_name: str
    employee_email: str
    department: Optional[str] = None
    position: Optional[str] = None
    last_working_day: datetime
    resignation_status: str
    days_since_approval: int