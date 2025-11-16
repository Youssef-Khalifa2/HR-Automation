"""
Pydantic schemas for admin configuration management
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# System Config Schemas
class SystemConfigBase(BaseModel):
    config_key: str
    config_value: Optional[str] = None
    config_type: str = "string"  # string, email, boolean, integer
    category: str = "general"  # general, email, mapping, system
    description: Optional[str] = None
    is_active: bool = True


class SystemConfigCreate(SystemConfigBase):
    pass


class SystemConfigUpdate(BaseModel):
    config_value: Optional[str] = None
    config_type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SystemConfigResponse(SystemConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# Team Mapping Schemas
class TeamMappingBase(BaseModel):
    team_leader_name: str
    team_leader_email: EmailStr
    chinese_head_name: Optional[str] = None
    chinese_head_email: Optional[str] = None  # Changed from EmailStr to str to allow empty strings
    department: Optional[str] = None
    crm: Optional[str] = None
    vendor_email: Optional[str] = None  # Changed from EmailStr to str to allow empty strings
    is_active: bool = True


class TeamMappingCreate(TeamMappingBase):
    pass


class TeamMappingUpdate(BaseModel):
    team_leader_name: Optional[str] = None
    team_leader_email: Optional[EmailStr] = None
    chinese_head_name: Optional[str] = None
    chinese_head_email: Optional[str] = None  # Changed from EmailStr to str to allow empty strings
    department: Optional[str] = None
    crm: Optional[str] = None
    vendor_email: Optional[str] = None  # Changed from EmailStr to str to allow empty strings
    is_active: Optional[bool] = None


class TeamMappingResponse(TeamMappingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# Bulk config update schemas
class EmailConfigUpdate(BaseModel):
    hr_email: Optional[EmailStr] = None
    hr_email_cc: Optional[str] = None  # Comma-separated CC emails
    it_email: Optional[EmailStr] = None
    email_provider: Optional[str] = None  # "sendgrid" or "smtp"
    sendgrid_api_key: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[EmailStr] = None
    smtp_from_name: Optional[str] = None
    vendor_migrate_email: Optional[EmailStr] = None
    vendor_justhr_email_1: Optional[EmailStr] = None
    vendor_justhr_email_2: Optional[EmailStr] = None


class SystemSettingsUpdate(BaseModel):
    app_base_url: Optional[str] = None
    frontend_url: Optional[str] = None
    enable_auto_reminders: Optional[bool] = None
    reminder_threshold_hours: Optional[int] = None
    approval_token_expire_hours: Optional[int] = None


class BulkConfigResponse(BaseModel):
    success: bool
    message: str
    updated_count: int
    configs: list[SystemConfigResponse]
