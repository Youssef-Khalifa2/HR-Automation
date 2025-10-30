from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.submission import ResignationStatus, ExitInterviewStatus


class SubmissionBase(BaseModel):
    employee_name: str
    employee_email: EmailStr
    employee_id: str
    department: str
    position: str
    hire_date: datetime
    resignation_date: datetime
    last_working_day: datetime
    in_probation: bool = False
    notice_period_days: int = 30


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionUpdate(BaseModel):
    resignation_status: Optional[ResignationStatus] = None
    exit_interview_status: Optional[ExitInterviewStatus] = None
    medical_card_collected: Optional[bool] = None
    vendor_mail_sent: Optional[bool] = None
    hr_notes: Optional[str] = None


class Submission(SubmissionBase):
    id: int
    resignation_status: ResignationStatus
    exit_interview_status: ExitInterviewStatus
    team_leader_reply: Optional[bool] = None
    chinese_head_reply: Optional[bool] = None
    it_support_reply: Optional[bool] = None
    medical_card_collected: bool
    vendor_mail_sent: bool
    leader_notes: Optional[str] = None
    chm_notes: Optional[str] = None
    hr_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_reminded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubmissionList(BaseModel):
    id: int
    employee_name: str
    employee_email: str
    department: str
    position: str
    resignation_status: ResignationStatus
    exit_interview_status: ExitInterviewStatus
    last_working_day: datetime
    created_at: datetime

    class Config:
        from_attributes = True