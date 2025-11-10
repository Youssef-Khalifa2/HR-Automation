import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Unified configuration for HR Co-Pilot application"""

    # Application Settings
    APP_BASE_URL: str = "http://localhost:8000"
    SIGNING_SECRET: str = "your-secret-key-change-in-production"
    SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Timeout Configurations
    HTTP_TIMEOUT: float = 30.0
    SMTP_TIMEOUT: float = 10.0
    SMTP_SOCKET_TIMEOUT: float = 10.0
    DATABASE_TIMEOUT: int = 30
    APPROVAL_PAGE_TIMEOUT: float = 15.0

    # Database Configuration
    DATABASE_URL: str = "postgresql+psycopg://postgres:123@localhost:5432/appdb"

    # Email Configuration
    SMTP_HOST: str = "smtp.qiye.aliyun.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = "youssefkhalifa@51talk.com"
    SMTP_PASS: str = "2jMYVlkFzZaefcLL"
    FROM_ADDR: str = "youssefkhalifa@51talk.com"
    SMTP_FROM_EMAIL: str = "youssefkhalifa@51talk.com"
    SMTP_FROM_NAME: str = "HR Automation System"
    SMTP_USE_TLS: bool = True

    # Email Recipients Configuration
    HR_EMAIL: str = "youssefkhalifa@51talk.com"  # HR department email for all notifications
    IT_EMAIL: str = "youssefkhalifa@51talk.com"  # IT department email for asset clearance

    # IMAP Configuration (future use)
    IMAP_HOST: Optional[str] = None
    IMAP_PORT: Optional[int] = None

    class Config:
        env_file = ".env"


# Create global settings instance
settings = Settings()

# Legacy variable access for backward compatibility
DATABASE_URL = settings.DATABASE_URL
SIGNING_SECRET = settings.SIGNING_SECRET
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
BASE_URL = settings.APP_BASE_URL
HR_EMAIL = settings.HR_EMAIL
CHM_test_mail = "youssefkhalifa458@gmail.com"

# Email configuration (legacy access)
SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
EMAIL = settings.SMTP_USER
PASSWORD = settings.SMTP_PASS
SMTP_FROM_EMAIL = settings.SMTP_FROM_EMAIL
SMTP_FROM_NAME = settings.SMTP_FROM_NAME
SMTP_USE_TLS = settings.SMTP_USE_TLS

# IMAP configuration (legacy access)
IMAP_HOST = settings.IMAP_HOST or "imap.qiye.aliyun.com"
IMAP_PORT = settings.IMAP_PORT or 993

# Development overrides
if os.getenv("SMTP_HOST"):
    SMTP_HOST = os.getenv("SMTP_HOST")
if os.getenv("SMTP_PORT"):
    SMTP_PORT = int(os.getenv("SMTP_PORT"))
if os.getenv("SMTP_EMAIL"):
    EMAIL = os.getenv("SMTP_EMAIL")
if os.getenv("SMTP_PASSWORD"):
    PASSWORD = os.getenv("SMTP_PASSWORD")
if os.getenv("SMTP_FROM_EMAIL"):
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
if os.getenv("SMTP_FROM_NAME"):
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME")
if os.getenv("SMTP_USE_TLS"):
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS").lower() == "true"