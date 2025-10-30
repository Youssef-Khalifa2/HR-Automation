"""Submission management endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas_all import (
    SubmissionCreate, SubmissionResponse, SubmissionUpdate,
    SubmissionWithAssets, SubmissionFilter
)
from app.crud import (
    get_submission, get_submissions, create_submission,
    update_submission, delete_submission, get_asset_by_submission
)
from app.auth import get_current_hr_user
from app.models.user import User

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("/", response_model=SubmissionResponse)
def create_submission_endpoint(
    submission: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Create new resignation submission"""
    db_submission = create_submission(db, submission)
    return db_submission


@router.get("/", response_model=List[SubmissionResponse])
def list_submissions(
    resignation_status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """List submissions with optional filters"""
    from datetime import datetime

    # Parse filters
    date_from_dt = None
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format")

    date_to_dt = None
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format")

    submissions = get_submissions(
        db,
        skip=skip,
        limit=limit,
        resignation_status=resignation_status,
        date_from=date_from_dt,
        date_to=date_to_dt
    )
    return submissions


@router.get("/{submission_id}", response_model=SubmissionWithAssets)
def get_submission_endpoint(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Get submission by ID with asset details"""
    submission = get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Get asset details
    asset = get_asset_by_submission(db, submission_id)

    response_data = {
        **submission.__dict__,
        "assets": asset
    }

    return SubmissionWithAssets(**response_data)


@router.patch("/{submission_id}", response_model=SubmissionResponse)
def update_submission_endpoint(
    submission_id: int,
    submission_update: SubmissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Update submission"""
    db_submission = update_submission(db, submission_id, submission_update)
    if not db_submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    return db_submission


@router.delete("/{submission_id}")
def delete_submission_endpoint(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Delete submission"""
    success = delete_submission(db, submission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Submission not found")

    return {"message": "Submission deleted successfully"}