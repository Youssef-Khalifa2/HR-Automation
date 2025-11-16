"""Authentication module - re-export from main auth for backward compatibility"""
# Re-export all authentication functions from main auth module
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    authenticate_user,
    get_current_user,
    create_user,
    # Configuration variables
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    pwd_context,
    security
)

# For backward compatibility - get_current_hr_user removed during auth simplification
# Any endpoint that needs HR access should use get_current_user instead
get_current_hr_user = get_current_user