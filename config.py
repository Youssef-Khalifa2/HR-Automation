import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()


def get_base_url() -> str:
    """Auto-detect base URL from Railway or environment"""
    # Check for explicit configuration first
    if os.getenv("APP_BASE_URL"):
        return os.getenv("APP_BASE_URL")

    # Auto-detect Railway deployment
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if railway_domain:
        return f"https://{railway_domain}"

    railway_static = os.getenv("RAILWAY_STATIC_URL")
    if railway_static:
        return railway_static

    # Default to localhost for development
    port = os.getenv("PORT", "8000")
    return f"http://localhost:{port}"


def get_frontend_url() -> str:
    """Auto-detect frontend URL"""
    # Check for explicit configuration first
    if os.getenv("FRONTEND_URL"):
        return os.getenv("FRONTEND_URL")

    # For Railway, frontend might be same as backend or separate deployment
    # If not specified, use the base URL (same domain)
    return get_base_url()


class Settings(BaseSettings):
    """Unified configuration for HR Co-Pilot application"""

    # Application Settings
    APP_BASE_URL: str = get_base_url()
    SIGNING_SECRET: str = os.getenv("SIGNING_SECRET", "dev-signing-secret-change-in-production")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", os.getenv("RAILWAY_ENVIRONMENT", "development"))

    # Timeout Configurations
    HTTP_TIMEOUT: float = 30.0
    SMTP_TIMEOUT: float = 10.0
    SMTP_SOCKET_TIMEOUT: float = 10.0
    DATABASE_TIMEOUT: int = 30
    APPROVAL_PAGE_TIMEOUT: float = 15.0

    # Database Configuration (Railway provides this automatically)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:123@localhost:5432/appdb")

    # Email Configuration
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "sendgrid")  # Options: sendgrid, smtp
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")

    # SMTP Configuration (Fallback)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.qiye.aliyun.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", "")
    FROM_ADDR: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "HR Automation System")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() == "true"

    # Email Recipients Configuration
    HR_EMAIL: str = os.getenv("HR_EMAIL", "hr@company.com")
    HR_EMAIL_CC: str = os.getenv("HR_EMAIL_CC", "")  # Comma-separated CC emails for HR notifications
    IT_EMAIL: str = os.getenv("IT_EMAIL", "it@company.com")
    IT_SUPPORT_EMAIL: str = os.getenv("IT_EMAIL", "it@company.com")

    # Frontend Configuration (auto-detected)
    FRONTEND_URL: str = get_frontend_url()

    # Reminder System Configuration
    ENABLE_AUTO_REMINDERS: bool = os.getenv("ENABLE_AUTO_REMINDERS", "True").lower() == "true"
    REMINDER_THRESHOLD_HOURS: int = int(os.getenv("REMINDER_THRESHOLD_HOURS", "24"))
    REMINDER_CHECK_INTERVAL_MINUTES: int = 60  # How often to check for pending items (for cron)

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
HR_EMAIL_CC = settings.HR_EMAIL_CC

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

# Print configuration on startup (helpful for debugging Railway deployments)
if __name__ == "__main__" or os.getenv("RAILWAY_ENVIRONMENT"):
    print("=" * 60)
    print("HR Automation System - Configuration")
    print("=" * 60)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Base URL: {settings.APP_BASE_URL}")
    print(f"Frontend URL: {settings.FRONTEND_URL}")
    print(f"Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'Not configured'}")
    print(f"Email Provider: {settings.EMAIL_PROVIDER}")
    print(f"HR Email: {settings.HR_EMAIL}")
    if settings.HR_EMAIL_CC:
        print(f"HR Email CC: {settings.HR_EMAIL_CC}")
    print("=" * 60)
