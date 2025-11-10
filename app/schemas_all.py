"""Pydantic schemas for request/response models"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str  # Use string instead of enum


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None




# Submission schemas
class SubmissionBase(BaseModel):
    employee_name: str
    employee_email: EmailStr
    joining_date: datetime  # Called hire_date in our original design
    submission_date: datetime  # Called resignation_date in our original design
    last_working_day: datetime


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionUpdate(BaseModel):
    employee_name: Optional[str] = None
    employee_email: Optional[EmailStr] = None
    joining_date: Optional[datetime] = None
    submission_date: Optional[datetime] = None
    last_working_day: Optional[datetime] = None
    resignation_status: Optional[str] = None
    exit_interview_status: Optional[str] = None
    team_leader_reply: Optional[bool] = None
    chinese_head_reply: Optional[bool] = None
    it_support_reply: Optional[bool] = None
    medical_card_collected: Optional[bool] = None
    vendor_mail_sent: Optional[bool] = None
    team_leader_notes: Optional[str] = None  # Match DB column name
    chinese_head_notes: Optional[str] = None  # Match DB column name
    exit_interview_notes: Optional[str] = None


class SubmissionResponse(SubmissionBase):
    id: int
    resignation_status: str
    exit_interview_status: str
    team_leader_reply: Optional[bool]
    chinese_head_reply: Optional[bool]
    it_support_reply: Optional[bool]
    medical_card_collected: bool
    vendor_mail_sent: bool
    team_leader_notes: Optional[str]  # Match DB column name
    chinese_head_notes: Optional[str]  # Match DB column name
    exit_interview_notes: Optional[str]
    in_probation: bool  # Computed column
    notice_period_days: int  # Computed column
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Asset schemas
class AssetBase(BaseModel):
    assets_returned: Optional[bool] = False
    notes: Optional[str] = None


class AssetCreate(AssetBase):
    pass  # res_id comes from URL path parameter, not request body


class AssetUpdate(BaseModel):
    assets_returned: Optional[bool] = None
    notes: Optional[str] = None


class AssetResponse(AssetBase):
    id: int
    res_id: int  # Match DB column name
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubmissionWithAssets(SubmissionResponse):
    assets: Optional[AssetResponse] = None


# Login schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# Filter schemas
class SubmissionFilter(BaseModel):
    resignation_status: Optional[str] = None
    exit_interview_status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = 0
    limit: int = 100


# Public Submission schemas (for Feishu integration)
class PublicSubmissionCreate(BaseModel):
    """Schema for public submission creation (no auth required)"""
    employee_name: str
    employee_email: EmailStr
    joining_date: datetime
    submission_date: datetime
    last_working_day: datetime
    department: Optional[str] = None
    position: Optional[str] = None
    leader_email: Optional[EmailStr] = None
    leader_name: Optional[str] = None
    reason: Optional[str] = None  # Reason for resignation

    class Config:
        from_attributes = True


class FeishuWebhookData(BaseModel):
    """Schema for Feishu webhook data"""
    employee_name: str
    employee_email: EmailStr
    joining_date: datetime
    submission_date: datetime
    last_working_day: datetime
    department: Optional[str] = None
    position: Optional[str] = None
    leader_email: Optional[EmailStr] = None
    leader_name: Optional[str] = None
    reason: Optional[str] = None

    class Config:
        from_attributes = True


# Approval schemas
class ApprovalRequest(BaseModel):
    """Schema for approval/rejection requests"""
    action: str  # "approve" or "reject"
    notes: Optional[str] = None  # Required for rejection

    class Config:
        from_attributes = True


class ApprovalResponse(BaseModel):
    """Schema for approval response"""
    success: bool
    message: str
    submission_id: int
    new_status: str
    timestamp: datetime

    class Config:
        from_attributes = True