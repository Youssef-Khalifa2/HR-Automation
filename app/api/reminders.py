"""
Reminders API endpoints for automated reminder management
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.core.auth import get_current_hr_user
from app.services.reminder_service import get_reminder_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.post("/check-pending/")
async def check_pending_reminders(
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
) -> Dict[str, Any]:
    """
    Manually trigger reminder check for all pending approvals

    This endpoint checks for:
    - Pending leader approvals
    - Pending CHM approvals
    - Pending IT asset clearances

    And sends reminder emails where appropriate.

    Args:
        force: If True, send reminders regardless of threshold hours

    Returns:
        Summary of reminders sent including counts for each type
    """
    try:
        logger.info(f"🔔 Manual reminder check initiated by user {current_user.email} (force={force})")

        reminder_service = get_reminder_service()
        results = await reminder_service.process_pending_reminders(db, force=force)

        return {
            "status": "success",
            "message": "Reminder check completed",
            "results": results
        }

    except Exception as e:
        logger.error(f"❌ Error processing reminders: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process reminders: {str(e)}"
        )


@router.get("/status/")
async def get_reminder_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
) -> Dict[str, Any]:
    """
    Get current status of pending items that may need reminders

    Returns counts of:
    - Submissions pending leader approval
    - Submissions pending CHM approval
    - Submissions pending IT asset clearance

    Does not send any emails, just returns statistics.
    """
    try:
        from config import settings

        reminder_service = get_reminder_service()

        # Get pending items
        threshold_hours = getattr(settings, 'REMINDER_THRESHOLD_HOURS', 24)

        pending_leader = reminder_service.get_pending_leader_approvals(db, threshold_hours)
        pending_chm = reminder_service.get_pending_chm_approvals(db, threshold_hours)
        pending_it = reminder_service.get_pending_it_clearances(db, threshold_hours)

        # Calculate statistics
        leader_details = []
        for sub in pending_leader:
            hours_pending = reminder_service.calculate_hours_pending(sub.submission_date)
            leader_details.append({
                "id": sub.id,
                "employee_name": sub.employee_name,
                "team_leader": sub.team_leader,
                "hours_pending": hours_pending,
                "submission_date": sub.submission_date.isoformat()
            })

        chm_details = []
        for sub in pending_chm:
            hours_pending = reminder_service.calculate_hours_pending(sub.team_leader_reply_date)
            chm_details.append({
                "id": sub.id,
                "employee_name": sub.employee_name,
                "team_leader": sub.team_leader,
                "hours_pending": hours_pending,
                "leader_approved_date": sub.team_leader_reply_date.isoformat() if sub.team_leader_reply_date else None
            })

        it_details = []
        for sub in pending_it:
            hours_pending = reminder_service.calculate_hours_pending(sub.exit_interview_completed_date)
            days_remaining = reminder_service.calculate_days_remaining(sub.last_working_day)
            it_details.append({
                "id": sub.id,
                "employee_name": sub.employee_name,
                "hours_pending": hours_pending,
                "days_remaining": days_remaining,
                "exit_completed_date": sub.exit_interview_completed_date.isoformat() if sub.exit_interview_completed_date else None
            })

        return {
            "status": "success",
            "threshold_hours": threshold_hours,
            "auto_reminders_enabled": getattr(settings, 'ENABLE_AUTO_REMINDERS', True),
            "pending_counts": {
                "leader_approvals": len(pending_leader),
                "chm_approvals": len(pending_chm),
                "it_clearances": len(pending_it),
                "total": len(pending_leader) + len(pending_chm) + len(pending_it)
            },
            "pending_details": {
                "leader_approvals": leader_details,
                "chm_approvals": chm_details,
                "it_clearances": it_details
            }
        }

    except Exception as e:
        logger.error(f"❌ Error getting reminder status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get reminder status: {str(e)}"
        )


@router.post("/send-leader-reminder/{submission_id}/")
async def send_leader_reminder(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
) -> Dict[str, Any]:
    """Send a manual reminder to the team leader for a specific submission"""
    try:
        from app.crud import get_submission

        submission = get_submission(db, submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        if submission.resignation_status != "submitted":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot send leader reminder - status is {submission.resignation_status}"
            )

        reminder_service = get_reminder_service()
        success = await reminder_service.send_leader_approval_reminder(submission, force=True)

        if success:
            return {
                "status": "success",
                "message": f"Leader reminder sent for submission {submission_id}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send reminder")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sending leader reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-chm-reminder/{submission_id}/")
async def send_chm_reminder(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
) -> Dict[str, Any]:
    """Send a manual reminder to the CHM for a specific submission"""
    try:
        from app.crud import get_submission

        submission = get_submission(db, submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        if submission.resignation_status != "leader_approved":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot send CHM reminder - status is {submission.resignation_status}"
            )

        reminder_service = get_reminder_service()
        success = await reminder_service.send_chm_approval_reminder(submission, force=True)

        if success:
            return {
                "status": "success",
                "message": f"CHM reminder sent for submission {submission_id}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send reminder")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sending CHM reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-it-reminder/{submission_id}/")
async def send_it_reminder(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
) -> Dict[str, Any]:
    """Send a manual reminder to IT for a specific submission"""
    try:
        from app.crud import get_submission

        submission = get_submission(db, submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        if submission.resignation_status != "exit_done":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot send IT reminder - status is {submission.resignation_status}"
            )

        reminder_service = get_reminder_service()
        success = await reminder_service.send_it_asset_reminder(submission, force=True)

        if success:
            return {
                "status": "success",
                "message": f"IT reminder sent for submission {submission_id}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send reminder")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sending IT reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
