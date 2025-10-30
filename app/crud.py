"""CRUD operations for database models"""
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.user import User
from app.models.submission import Submission
from app.models.asset import Asset
from datetime import datetime

if TYPE_CHECKING:
    from app.schemas_all import SubmissionCreate, SubmissionUpdate, AssetCreate, AssetUpdate


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get list of users"""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user) -> User:
    """Create new user"""
    from app.auth import get_password_hash
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Submission CRUD
def get_submission(db: Session, submission_id: int) -> Optional[Submission]:
    """Get submission by ID"""
    return db.query(Submission).filter(Submission.id == submission_id).first()


def get_submission_by_email(db: Session, email: str) -> Optional[Submission]:
    """Get submission by employee email"""
    return db.query(Submission).filter(Submission.employee_email == email).first()


def get_submissions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    resignation_status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> List[Submission]:
    """Get filtered submissions"""
    query = db.query(Submission)

    if resignation_status:
        query = query.filter(Submission.resignation_status == resignation_status)

    # Note: department filtering removed as column doesn't exist in current DB

    if date_from:
        query = query.filter(Submission.created_at >= date_from)

    if date_to:
        query = query.filter(Submission.created_at <= date_to)

    return query.offset(skip).limit(limit).all()


def create_submission(db: Session, submission) -> Submission:
    """Create new submission"""
    from app.models.submission import ResignationStatus, ExitInterviewStatus

    db_submission = Submission(
        employee_name=submission.employee_name,
        employee_email=submission.employee_email,
        joining_date=submission.joining_date,
        submission_date=submission.submission_date,
        last_working_day=submission.last_working_day,
        resignation_status=ResignationStatus.SUBMITTED.value,
        exit_interview_status=ExitInterviewStatus.NOT_SCHEDULED.value,
        team_leader_reply=None,
        chinese_head_reply=None,
        it_support_reply=None,
        medical_card_collected=False,
        vendor_mail_sent=False
        # Note: in_probation and notice_period_days are generated columns in DB
        # Note: updated_at is handled by database trigger/default
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission


def update_submission(db: Session, submission_id: int, submission) -> Optional[Submission]:
    """Update submission"""
    db_submission = get_submission(db, submission_id)
    if not db_submission:
        return None

    update_data = submission.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_submission, field, value)

    db.commit()
    db.refresh(db_submission)
    return db_submission


def delete_submission(db: Session, submission_id: int) -> bool:
    """Delete submission"""
    db_submission = get_submission(db, submission_id)
    if not db_submission:
        return False

    db.delete(db_submission)
    db.commit()
    return True


# Asset CRUD
def get_asset_by_submission(db: Session, submission_id: int) -> Optional[Asset]:
    """Get asset by submission ID"""
    return db.query(Asset).filter(Asset.res_id == submission_id).first()


def create_asset(db: Session, asset) -> Asset:
    """Create new asset"""
    db_asset = Asset(
        res_id=asset.res_id,  # Match DB column name
        laptop=asset.laptop,
        mouse=asset.mouse,
        headphones=asset.headphones,
        others=asset.others,
        approved=asset.approved
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


def update_asset(db: Session, res_id: int, asset) -> Optional[Asset]:
    """Update asset"""
    db_asset = get_asset_by_submission(db, res_id)
    if not db_asset:
        # Create if doesn't exist
        from app.schemas_all import AssetCreate
        db_asset = create_asset(db, AssetCreate(res_id=res_id, **asset.dict()))
    else:
        update_data = asset.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_asset, field, value)
        db.commit()
        db.refresh(db_asset)

    return db_asset


# Reminder functions - now enabled with last_reminded_at column
def get_pending_reminders(db: Session, hours_threshold: int = 24) -> List[Submission]:
    """Get submissions that need reminder emails

    Args:
        db: Database session
        hours_threshold: Hours to wait before sending reminder

    Returns:
        List of submissions that need reminder emails
    """
    from datetime import datetime, timedelta

    threshold_time = datetime.utcnow() - timedelta(hours=hours_threshold)

    query = db.query(Submission).filter(
        or_(
            # Leader approval pending
            and_(
                Submission.resignation_status == "submitted",
                Submission.team_leader_reply.is_(None),
                or_(
                    Submission.last_reminded_at.is_(None),
                    Submission.last_reminded_at < threshold_time
                )
            ),
            # CHM approval pending
            and_(
                Submission.resignation_status == "leader_approved",
                Submission.chinese_head_reply.is_(None),
                or_(
                    Submission.last_reminded_at.is_(None),
                    Submission.last_reminded_at < threshold_time
                )
            ),
            # IT processing pending
            and_(
                Submission.resignation_status == "exit_done",
                Submission.it_support_reply.is_(None),
                or_(
                    Submission.last_reminded_at.is_(None),
                    Submission.last_reminded_at < threshold_time
                )
            )
        )
    )

    return query.all()


def update_last_reminded(db: Session, submission_id: int) -> bool:
    """Update last reminded timestamp for a submission

    Args:
        db: Database session
        submission_id: ID of the submission

    Returns:
        True if successful, False otherwise
    """
    try:
        submission = get_submission(db, submission_id)
        if not submission:
            return False

        submission.last_reminded_at = datetime.utcnow()
        db.commit()
        return True

    except Exception:
        db.rollback()
        return False