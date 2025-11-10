"""CRUD operations for Exit Interview management"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from app.models.exit_interview import ExitInterview, ExitInterviewReminder
from app.models.submission import Submission


def create_exit_interview(db: Session, submission_id: int) -> ExitInterview:
    """Create a new exit interview record for a submission"""
    db_exit_interview = ExitInterview(
        submission_id=submission_id
    )
    db.add(db_exit_interview)
    db.commit()
    db.refresh(db_exit_interview)
    return db_exit_interview


def get_exit_interview_by_submission(db: Session, submission_id: int) -> Optional[ExitInterview]:
    """Get exit interview by submission ID"""
    return db.query(ExitInterview).filter(ExitInterview.submission_id == submission_id).first()


def get_exit_interview(db: Session, interview_id: int) -> Optional[ExitInterview]:
    """Get exit interview by ID"""
    return db.query(ExitInterview).filter(ExitInterview.id == interview_id).first()


def schedule_exit_interview(
    db: Session,
    submission_id: int,
    scheduled_date: datetime,
    scheduled_time: str,
    location: str = None,
    interviewer: str = None
) -> ExitInterview:
    """Schedule an exit interview"""
    # Get or create exit interview
    exit_interview = get_exit_interview_by_submission(db, submission_id)
    if not exit_interview:
        exit_interview = create_exit_interview(db, submission_id)

    # Update scheduling details
    exit_interview.scheduled_date = scheduled_date
    exit_interview.scheduled_time = scheduled_time
    exit_interview.location = location or "HR Meeting Room"
    exit_interview.interviewer = interviewer or "HR Representative"
    exit_interview.interview_type = "in-person"  # Default

    # Update submission status to scheduled
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if submission:
        submission.exit_interview_status = "scheduled"

    db.commit()
    db.refresh(exit_interview)
    return exit_interview


def complete_exit_interview(
    db: Session,
    interview_id: int,
    feedback: str = None,
    rating: int = None,
    hr_notes: str = None
) -> ExitInterview:
    """Complete an exit interview and trigger IT notification"""
    exit_interview = db.query(ExitInterview).filter(ExitInterview.id == interview_id).first()
    if not exit_interview:
        return None

    # Update interview details
    exit_interview.interview_completed = True
    exit_interview.interview_feedback = feedback
    exit_interview.interview_rating = rating
    exit_interview.hr_notes = hr_notes
    exit_interview.interview_completed_at = datetime.utcnow()

    # Update submission status
    submission = exit_interview.submission
    if submission:
        submission.exit_interview_status = "done"
        if feedback:
            submission.exit_interview_notes = feedback

    db.commit()
    db.refresh(exit_interview)
    return exit_interview


def get_pending_scheduled_interviews(db: Session) -> List[ExitInterview]:
    """Get interviews that are scheduled but not completed and time has passed"""
    now = datetime.utcnow()
    return db.query(ExitInterview).filter(
        and_(
            ExitInterview.scheduled_date <= now,
            ExitInterview.interview_completed == False
        )
    ).all()


def get_interviews_needing_scheduling(db: Session) -> List[Submission]:
    """Get submissions that need exit interview scheduling"""
    return db.query(Submission).filter(
        and_(
            Submission.resignation_status.in_(["leader_approved", "chm_approved", "chm_done", "exit_done"]),
            Submission.exit_interview_status == "not_scheduled"
        )
    ).all()


def get_upcoming_interviews(db: Session, days_ahead: int = 7) -> List[ExitInterview]:
    """Get upcoming interviews in the next N days"""
    from sqlalchemy import cast, Date

    now = datetime.utcnow().date()  # Use date for comparison
    future_date = now + timedelta(days=days_ahead)

    return db.query(ExitInterview).filter(
        and_(
            cast(ExitInterview.scheduled_date, Date) >= now,
            cast(ExitInterview.scheduled_date, Date) <= future_date,
            ExitInterview.interview_completed == False
        )
    ).all()


def create_reminder(
    db: Session,
    exit_interview_id: int,
    reminder_type: str,
    recipient_email: str,
    recipient_name: str,
    scheduled_for: datetime
) -> ExitInterviewReminder:
    """Create a new reminder"""
    reminder = ExitInterviewReminder(
        exit_interview_id=exit_interview_id,
        reminder_type=reminder_type,
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        scheduled_for=scheduled_for
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


def get_pending_reminders(db: Session) -> List[ExitInterviewReminder]:
    """Get reminders that need to be sent"""
    now = datetime.utcnow()
    return db.query(ExitInterviewReminder).filter(
        and_(
            ExitInterviewReminder.scheduled_for <= now,
            ExitInterviewReminder.sent == False
        )
    ).all()


def mark_reminder_sent(db: Session, reminder_id: int) -> ExitInterviewReminder:
    """Mark a reminder as sent"""
    reminder = db.query(ExitInterviewReminder).filter(ExitInterviewReminder.id == reminder_id).first()
    if reminder:
        reminder.sent = True
        reminder.sent_at = datetime.utcnow()
        db.commit()
        db.refresh(reminder)
    return reminder


def get_interview_statistics(db: Session) -> dict:
    """Get exit interview statistics"""
    # Total interviews (all submissions that have reached approval stage)
    total_count = db.query(ExitInterview).count()

    # Pending scheduling (submissions ready for interview but not yet scheduled)
    to_schedule = db.query(Submission).filter(
        and_(
            Submission.resignation_status.in_(["leader_approved", "chm_approved", "chm_done", "exit_done"]),
            Submission.exit_interview_status == "not_scheduled"
        )
    ).count()

    # Upcoming scheduled interviews
    from sqlalchemy import cast, Date
    now = datetime.utcnow().date()
    upcoming = db.query(ExitInterview).filter(
        and_(
            ExitInterview.scheduled_date.isnot(None),
            cast(ExitInterview.scheduled_date, Date) >= now,
            ExitInterview.interview_completed == False
        )
    ).count()

    # Completed interviews
    completed = db.query(ExitInterview).filter(
        ExitInterview.interview_completed == True
    ).count()

    return {
        "total": total_count,
        "to_schedule": to_schedule,
        "upcoming": upcoming,
        "completed": completed,
        "completion_rate": (completed / total_count * 100) if total_count > 0 else 0
    }


def mark_interview_completed(db: Session, interview_id: int) -> Optional[ExitInterview]:
    """Mark an exit interview as completed"""
    interview = db.query(ExitInterview).filter(ExitInterview.id == interview_id).first()
    if not interview:
        return None

    # Mark interview as completed
    interview.interview_completed = True
    interview.interview_completed_at = datetime.utcnow()

    # Update submission status
    interview.submission.exit_interview_status = "completed"

    db.commit()
    db.refresh(interview)
    return interview