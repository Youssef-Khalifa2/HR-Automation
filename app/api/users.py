"""User management endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas_all import UserCreate, UserResponse
from app.crud import get_user, get_user_by_email, get_users, create_user
from app.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
def create_user_endpoint(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new user (HR only)"""
    # Check if user already exists
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    return create_user(db, user)


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List users (HR only)"""
    users = get_users(db, skip=skip, limit=limit)
    return users


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID (HR only)"""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user