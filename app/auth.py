"""Authentication utilities and JWT handling"""
import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# JWT Bearer
security = HTTPBearer()

# For backward compatibility with code that imports pwd_context
class _BCryptContext:
    """Wrapper to maintain compatibility with passlib API"""
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)

    def hash(self, password: str) -> str:
        return get_password_hash(password)

pwd_context = _BCryptContext()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly"""
    # Convert strings to bytes
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password

    try:
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        # Log the error for debugging
        print(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash using bcrypt directly"""
    # Convert password to bytes and generate hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return email"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = verify_token(credentials.credentials)
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


# NO LONGER USED (removed role-based access control)
# def get_current_hr_user(current_user: User = Depends(get_current_user)) -> User:
#     """Ensure current user is HR"""
#     if current_user.role != "hr":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not enough permissions"
#         )
#     return current_user


def create_user(db: Session, email: str, password: str, full_name: str, role: str) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(password)
    db_user = User(
        email=email,
        password_hash=hashed_password,
        full_name=full_name,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user