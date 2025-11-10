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
    resignation_status: Optional[str] = Query(None, description="Filter by resignation status"),
    exit_interview_status: Optional[str] = Query(None, description="Filter by exit interview status"),
    it_asset_cleared: Optional[bool] = Query(None, description="Filter by IT asset clearance status"),
    medical_card_collected: Optional[bool] = Query(None, description="Filter by medical card collection status"),
    vendor_mail_sent: Optional[bool] = Query(None, description="Filter by vendor notification status"),
    date_from: Optional[str] = Query(None, description="Filter submissions created from this date"),
    date_to: Optional[str] = Query(None, description="Filter submissions created until this date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
    # current_user: User = Depends(get_current_hr_user)  # Temporarily removed for debugging
):
    """List submissions with enhanced filtering options

    Supports filtering by:
    - Resignation status (submitted, leader_approved, chm_approved, etc.)
    - Exit interview status (not_scheduled, scheduled, completed, etc.)
    - IT asset clearance status (cleared or not)
    - Medical card collection status
    - Vendor notification status
    - Date range (created_at)
    """
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
        exit_interview_status=exit_interview_status,
        it_asset_cleared=it_asset_cleared,
        medical_card_collected=medical_card_collected,
        vendor_mail_sent=vendor_mail_sent,
        date_from=date_from_dt,
        date_to=date_to_dt
    )
    return submissions


@router.get("/{submission_id}", response_model=SubmissionWithAssets)
def get_submission_endpoint(
    submission_id: int,
    db: Session = Depends(get_db)
    # current_user: User = Depends(get_current_hr_user)  # Temporarily removed for debugging
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


@router.post("/{submission_id}/resend")
async def resend_approval_request(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Intelligently resend the appropriate email based on current submission stage"""
    try:
        import logging
        logger = logging.getLogger(__name__)

        # Get submission
        submission = get_submission(db, submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Import services
        from app.services.leader_mapping import get_leader_mapping
        from app.services.email import get_email_service, EmailTemplates
        from app.core.security import get_approval_token_service
        from app.services.tokenized_forms import get_tokenized_form_service
        from config import BASE_URL, settings

        leader_mapping = get_leader_mapping()
        email_service = get_email_service()
        token_service = get_approval_token_service()
        form_token_service = get_tokenized_form_service()

        email_sent = None
        email_type = None

        # Determine current stage and send appropriate email
        resignation_status = submission.resignation_status
        exit_status = submission.exit_interview_status

        # Stage 1: Waiting for Leader Approval
        if resignation_status in ["submitted", "leader_rejected"]:
            email_type = "Leader Approval Request"

            # Get leader info
            submission_leader_name = getattr(submission, 'team_leader', None)
            leader_email = "youssefkhalifa@51talk.com"
            leader_name = "Team Leader"

            if submission_leader_name:
                leader_info = leader_mapping.get_leader_info(submission_leader_name)
                if leader_info:
                    leader_email = leader_info['leader_email']
                    leader_name = leader_info['leader_name']

            # Generate approval URL
            approval_url = token_service.generate_approval_url(
                submission_id=submission_id,
                action="approve",
                approver_type="leader",
                base_url=BASE_URL
            )

            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "submission_date": submission.submission_date.strftime("%Y-%m-%d"),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "leader_email": leader_email,
                "leader_name": leader_name,
                "department": getattr(submission, 'department', 'General'),
                "position": getattr(submission, 'position', 'Employee')
            }

            email_message = EmailTemplates.leader_approval_request(email_data, approval_url)
            success = await email_service.send_email(email_message)
            email_sent = leader_email

        # Stage 2: Waiting for CHM Approval
        elif resignation_status == "leader_approved":
            email_type = "CHM Approval Request"

            # Get CHM info
            chm_email = "youssefkhalifa458@gmail.com"
            chm_name = "Chinese Head"

            submission_leader_name = getattr(submission, 'team_leader', None)
            if submission_leader_name:
                leader_info = leader_mapping.get_leader_info(submission_leader_name)
                if leader_info and leader_info.get('chm_email'):
                    chm_email = leader_info['chm_email']
                    chm_name = leader_info['chm_name']

            # Generate approval URL
            approval_url = token_service.generate_approval_url(
                submission_id=submission_id,
                action="approve",
                approver_type="chm",
                base_url=BASE_URL
            )

            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "submission_date": submission.submission_date.strftime("%Y-%m-%d"),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "leader_approved": True,
                "leader_notes": submission.team_leader_notes or "",
                "chm_email": chm_email,
                "chm_name": chm_name
            }

            email_message = EmailTemplates.chm_approval_request(email_data, approval_url)
            success = await email_service.send_email(email_message)
            email_sent = chm_email

        # Stage 3: Waiting for Exit Interview Scheduling
        elif resignation_status == "chm_approved" and exit_status == "not_scheduled":
            email_type = "HR Interview Scheduling Request"

            # Generate tokenized form URL for scheduling
            form_data = {
                "submission_id": submission_id,
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "employee_id": getattr(submission, 'employee_id', ''),
                "position": getattr(submission, 'position', 'Employee'),
                "department": getattr(submission, 'department', 'General'),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "submission_date": submission.submission_date.strftime("%Y-%m-%d")
            }

            form_token = form_token_service.generate_secure_token(form_data)
            interview_url = f"{BASE_URL}/api/forms/schedule-interview?token={form_token}"

            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "submission_id": submission_id,
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "submission_date": submission.submission_date.strftime("%Y-%m-%d"),
                "leader_notes": submission.team_leader_notes or "",
                "chinese_head_notes": submission.chinese_head_notes or ""
            }

            email_message = EmailTemplates.hr_interview_scheduling_request(email_data, interview_url)
            success = await email_service.send_email(email_message)
            email_sent = settings.HR_EMAIL

        # Stage 4: Waiting for Interview Feedback Submission
        elif exit_status == "scheduled":
            email_type = "HR Interview Feedback Reminder"

            # Get interview details
            from app.models.exit_interview import ExitInterview
            interview = db.query(ExitInterview).filter(
                ExitInterview.submission_id == submission_id
            ).first()

            if interview:
                from datetime import datetime
                days_overdue = (datetime.utcnow() - interview.scheduled_date).days if interview.scheduled_date else 0

                email_data = {
                    "employee_name": submission.employee_name,
                    "employee_email": submission.employee_email,
                    "department": getattr(submission, 'department', 'General'),
                    "position": getattr(submission, 'position', 'Employee'),
                    "interview_date": interview.scheduled_date.strftime("%Y-%m-%d") if interview.scheduled_date else "",
                    "interview_time": interview.scheduled_time or "",
                    "location": interview.location or "HR Meeting Room",
                    "days_overdue": max(0, days_overdue),
                    "interview_id": interview.id
                }

                email_message = EmailTemplates.hr_submit_feedback_reminder(email_data)
                success = await email_service.send_email(email_message)
                email_sent = settings.HR_EMAIL
            else:
                raise HTTPException(status_code=404, detail="Exit interview not found")

        # Stage 5: Waiting for IT Clearance
        elif resignation_status == "exit_done" and not submission.it_support_reply:
            email_type = "IT Clearance Request"

            # Generate IT clearance form token
            it_clearance_token = form_token_service.generate_secure_token({
                "form_type": "it_clearance",
                "submission_id": submission_id,
                "employee_name": submission.employee_name,
                "created_for": "it_clearance"
            })

            # Create IT clearance form URL
            clearance_form_url = f"{BASE_URL}/api/forms/complete-it-clearance?token={it_clearance_token}"

            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "department": getattr(submission, 'department', 'General'),
                "position": getattr(submission, 'position', 'Employee'),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "submission_id": submission_id
            }

            email_message = EmailTemplates.it_clearance_request(email_data, clearance_form_url)
            success = await email_service.send_email(email_message)
            email_sent = settings.IT_EMAIL

        # Stage 6: Waiting for Medical Card Collection (manual - no email)
        elif resignation_status in ["assets_recorded"] and not submission.medical_card_collected:
            raise HTTPException(
                status_code=400,
                detail="Medical card collection is a manual process. Please mark as collected in the dashboard."
            )

        # Stage 7: Waiting for Vendor Notification
        elif resignation_status == "medical_checked" and not submission.vendor_mail_sent:
            email_type = "Vendor Offboarding Notification"

            # Get vendor email
            vendor_email = leader_mapping.get_vendor_email(
                department=getattr(submission, 'department', None),
                leader_name=getattr(submission, 'team_leader', None)
            )

            if not vendor_email:
                raise HTTPException(status_code=500, detail="Could not determine vendor email")

            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "department": getattr(submission, 'department', 'General'),
                "position": getattr(submission, 'position', 'Employee'),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "submission_id": submission_id,
                "final_notes": ""
            }

            email_message = EmailTemplates.vendor_offboarding_notification(email_data, vendor_email)
            success = await email_service.send_email(email_message)
            email_sent = vendor_email

        # Stage 8: Process Complete
        elif resignation_status == "offboarded":
            raise HTTPException(
                status_code=400,
                detail="Offboarding process is complete. No further emails needed."
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot determine appropriate email for status: {resignation_status}, exit status: {exit_status}"
            )

        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to send {email_type} email")

        logger.info(f"✅ Resent {email_type} for submission {submission_id} to {email_sent}")

        return {
            "message": f"{email_type} resent successfully",
            "submission_id": submission_id,
            "employee_name": submission.employee_name,
            "resignation_status": resignation_status,
            "exit_interview_status": exit_status,
            "email_type": email_type,
            "email_sent_to": email_sent
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to resend email for submission {submission_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to resend email: {str(e)}")


# Phase 3: Corrected Exit Interview Management APIs

@router.get("/exit-interviews/pending-scheduling")
def get_pending_scheduling_interviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Get submissions that need exit interview scheduling"""
    try:
        from app.crud_exit_interview import get_interviews_needing_scheduling
        from datetime import datetime, timezone

        submissions = get_interviews_needing_scheduling(db)

        pending_items = []
        for submission in submissions:
            # Calculate days since approval
            days_since_approval = 0
            if submission.resignation_status == "leader_approved" and submission.updated_at:
                days_since_approval = (datetime.now(timezone.utc) - submission.updated_at).days
            elif submission.resignation_status == "chm_approved" and submission.updated_at:
                days_since_approval = (datetime.now(timezone.utc) - submission.updated_at).days

            pending_items.append({
                "submission_id": submission.id,
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "department": getattr(submission, 'department', 'General'),
                "position": getattr(submission, 'position', 'Employee'),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "resignation_status": submission.resignation_status,
                "days_since_approval": days_since_approval
            })

        return {
            "message": f"Found {len(pending_items)} submissions needing interview scheduling",
            "pending_count": len(pending_items),
            "pending_interviews": pending_items
        }

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get pending scheduling interviews: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get pending scheduling interviews")


@router.post("/exit-interviews/schedule/")
async def schedule_exit_interview(
    schedule_request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Schedule an exit interview for a submission"""
    try:
        submission_id = schedule_request.get("submission_id")
        scheduled_date = schedule_request.get("scheduled_date")
        scheduled_time = schedule_request.get("scheduled_time")
        location = schedule_request.get("location", "HR Meeting Room")
        interviewer = schedule_request.get("interviewer", "HR Representative")

        # Validate submission
        submission = get_submission(db, submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Validate that submission is ready for interview scheduling
        if submission.resignation_status not in ["leader_approved", "chm_approved"]:
            raise HTTPException(
                status_code=400,
                detail="Can only schedule interview after leader approval"
            )

        # Schedule the interview
        from app.crud_exit_interview import schedule_exit_interview
        from datetime import datetime

        # Parse the date and time
        if isinstance(scheduled_date, str):
            scheduled_date = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))

        exit_interview = schedule_exit_interview(
            db=db,
            submission_id=submission_id,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            location=location,
            interviewer=interviewer
        )

        # Send interview invitation email to employee
        from app.services.email import get_email_service, EmailTemplates
        import logging
        logger = logging.getLogger(__name__)

        email_service = get_email_service()

        email_data = {
            "employee_name": submission.employee_name,
            "employee_email": submission.employee_email,
            "scheduled_date": scheduled_date.strftime("%A, %B %d, %Y"),
            "scheduled_time": scheduled_time,
            "location": location,
            "interviewer": interviewer,
            "department": getattr(submission, 'department', 'General'),
            "position": getattr(submission, 'position', 'Employee'),
            "last_working_day": submission.last_working_day.strftime("%Y-%m-%d")
        }

        email_message = EmailTemplates.exit_interview_scheduled(email_data)
        success = await email_service.send_email(email_message)

        if success:
            logger.info(f"Exit interview scheduling email sent to {submission.employee_email} for submission {submission_id}")
        else:
            logger.warning(f"Failed to send exit interview scheduling email for submission {submission_id}")

        return {
            "message": "Exit interview scheduled successfully",
            "interview_id": exit_interview.id,
            "submission_id": submission_id,
            "employee_name": submission.employee_name,
            "employee_email": submission.employee_email,
            "scheduled_date": scheduled_date.strftime("%Y-%m-%d"),
            "scheduled_time": scheduled_time,
            "location": location,
            "interviewer": interviewer,
            "email_sent": success
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to schedule exit interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule exit interview")


@router.get("/exit-interviews/upcoming")
def get_upcoming_interviews(
    days_ahead: int = 7,
    db: Session = Depends(get_db)
    # current_user: User = Depends(get_current_hr_user)  # Temporarily removed for debugging
):
    """Get upcoming exit interviews"""
    try:
        from app.crud_exit_interview import get_upcoming_interviews
        from datetime import datetime
        import logging
        logger = logging.getLogger(__name__)

        interviews = get_upcoming_interviews(db, days_ahead)
        logger.info(f"Found {len(interviews)} upcoming interviews")

        upcoming_list = []
        for interview in interviews:
            try:
                submission = interview.submission
                days_until = (interview.scheduled_date.date() - datetime.utcnow().date()).days

                upcoming_list.append({
                "interview_id": interview.id,
                "submission_id": submission.id,
                "employee_name": submission.employee_name,
                "scheduled_date": interview.scheduled_date.strftime("%Y-%m-%d"),
                "scheduled_time": interview.scheduled_time,
                "location": interview.location,
                "interviewer": interview.interviewer,
                "days_until_interview": days_until,
                "employee_email": submission.employee_email,
                "department": getattr(submission, 'department', 'General')
            })
            except Exception as interview_error:
                logger.error(f"Error processing interview {interview.id}: {str(interview_error)}")
                continue

        return {
            "message": f"Found {len(upcoming_list)} upcoming interviews",
            "upcoming_count": len(upcoming_list),
            "interviews": upcoming_list
        }

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get upcoming interviews: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to get upcoming interviews")


@router.post("/exit-interviews/submit-feedback/")
async def submit_interview_feedback(
    feedback_request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Submit interview feedback and mark interview as complete"""
    try:
        interview_id = feedback_request.get("interview_id")
        interview_feedback = feedback_request.get("interview_feedback")
        interview_rating = feedback_request.get("interview_rating")
        hr_notes = feedback_request.get("hr_notes")

        # Complete the interview
        from app.crud_exit_interview import complete_exit_interview

        exit_interview = complete_exit_interview(
            db=db,
            interview_id=interview_id,
            feedback=interview_feedback,
            rating=interview_rating,
            hr_notes=hr_notes
        )

        if not exit_interview:
            raise HTTPException(status_code=404, detail="Exit interview not found")

        submission = exit_interview.submission

        # Send IT clearance notification
        it_notification_sent = await _send_it_notification(db, submission)

        return {
            "message": "Interview feedback submitted successfully",
            "interview_id": interview_id,
            "submission_id": submission.id,
            "employee_name": submission.employee_name,
            "interview_completed": True,
            "it_notification_sent": it_notification_sent,
            "feedback_submitted": True
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to submit interview feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit interview feedback")


@router.post("/exit-interviews/mark-complete")
async def mark_interview_complete(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Mark an exit interview as completed"""
    try:
        from app.crud_exit_interview import mark_interview_completed
        from app.services.email import get_email_service, EmailTemplates
        from app.models.submission import ResignationStatus

        interview_id = request.get("interview_id")
        if not interview_id:
            raise HTTPException(status_code=400, detail="Interview ID is required")

        # Mark interview as completed
        interview = mark_interview_completed(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        submission = interview.submission

        # Update submission status to trigger IT notification
        submission.resignation_status = ResignationStatus.EXIT_DONE.value
        db.commit()

        # Send IT notification for assets collection
        try:
            from app.services.tokenized_forms import get_tokenized_form_service
            from config import BASE_URL

            email_service = get_email_service()
            form_token_service = get_tokenized_form_service()

            # Generate IT clearance form token
            it_clearance_token = form_token_service.generate_secure_token({
                "form_type": "it_clearance",
                "submission_id": submission.id,
                "employee_name": submission.employee_name,
                "created_for": "it_clearance"
            })

            # Create IT clearance form URL
            clearance_form_url = f"{BASE_URL}/api/forms/complete-it-clearance?token={it_clearance_token}"

            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "department": getattr(submission, 'department', 'General'),
                "position": getattr(submission, 'position', 'Employee'),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "submission_id": submission.id,
                "interview_completed": True,
                "interview_date": interview.scheduled_date.strftime("%Y-%m-%d"),
                "interview_feedback": interview.interview_feedback or "Interview completed"
            }

            email_message = EmailTemplates.it_clearance_request(email_data, clearance_form_url)
            await email_service.send_email(email_message)

        except Exception as email_error:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to send IT notification: {str(email_error)}")

        return {
            "success": True,
            "message": "Interview marked as completed and IT notified",
            "interview_id": interview.id,
            "employee_name": submission.employee_name
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to mark interview as complete: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark interview as complete")


@router.get("/exit-interviews/statistics")
def get_exit_interview_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Get exit interview statistics"""
    try:
        from app.crud_exit_interview import get_interview_statistics

        stats = get_interview_statistics(db)

        return {
            "message": "Exit interview statistics retrieved successfully",
            "statistics": stats
        }

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get interview statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get interview statistics")


@router.post("/{submission_id}/medical-card/")
async def toggle_medical_card(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Mark medical card as collected and update status to medical_checked"""
    try:
        import logging
        logger = logging.getLogger(__name__)

        # Get submission
        submission = get_submission(db, submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Validate prerequisite - assets must be cleared
        if not submission.it_support_reply:
            raise HTTPException(
                status_code=400,
                detail="Cannot mark medical card as collected - IT assets must be cleared first"
            )

        # Update medical card collection status
        submission.medical_card_collected = True
        submission.resignation_status = ResignationStatus.MEDICAL_CHECKED.value

        db.commit()
        db.refresh(submission)

        logger.info(f"✅ Medical card marked as collected for submission {submission_id}")

        return {
            "message": "Medical card marked as collected successfully",
            "submission_id": submission_id,
            "employee_name": submission.employee_name,
            "resignation_status": submission.resignation_status,
            "medical_card_collected": submission.medical_card_collected
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to mark medical card as collected: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark medical card as collected: {str(e)}")


@router.post("/{submission_id}/finalize/")
async def finalize_offboarding(
    submission_id: int,
    finalize_request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Finalize offboarding - send vendor email and mark as offboarded"""
    try:
        import logging
        logger = logging.getLogger(__name__)

        # Get submission
        submission = get_submission(db, submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Validate prerequisites
        if submission.resignation_status != ResignationStatus.MEDICAL_CHECKED.value:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot finalize - current status is {submission.resignation_status}. Status must be 'medical_checked'"
            )

        if not submission.it_support_reply:
            raise HTTPException(
                status_code=400,
                detail="Cannot finalize - IT assets must be cleared"
            )

        if not submission.medical_card_collected:
            raise HTTPException(
                status_code=400,
                detail="Cannot finalize - medical card must be collected"
            )

        # Get vendor email from leader mapping service
        from app.services.leader_mapping import get_leader_mapping
        from app.services.email import get_email_service, EmailTemplates

        leader_mapping = get_leader_mapping()
        vendor_email = leader_mapping.get_vendor_email(
            department=getattr(submission, 'department', None),
            leader_name=submission.team_leader
        )

        if not vendor_email:
            raise HTTPException(
                status_code=500,
                detail="Could not determine vendor email address"
            )

        # Prepare email data
        email_service = get_email_service()
        final_notes = finalize_request.get("final_notes", "")

        email_data = {
            "employee_name": submission.employee_name,
            "employee_email": submission.employee_email,
            "department": getattr(submission, 'department', 'General'),
            "position": getattr(submission, 'position', 'Employee'),
            "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
            "submission_id": submission.id,
            "final_notes": final_notes
        }

        # Send vendor notification email
        email_message = EmailTemplates.vendor_offboarding_notification(email_data, vendor_email)
        email_success = await email_service.send_email(email_message)

        if not email_success:
            logger.warning(f"Failed to send vendor email to {vendor_email} for submission {submission_id}")
            # Continue anyway - we'll mark the email as sent even if delivery failed
            # This allows HR to retry manually if needed

        # Update submission status
        submission.vendor_mail_sent = True
        submission.resignation_status = ResignationStatus.OFFBOARDED.value

        db.commit()
        db.refresh(submission)

        logger.info(f"✅ Offboarding finalized for submission {submission_id}, vendor email sent to {vendor_email}")

        return {
            "message": "Offboarding finalized successfully",
            "submission_id": submission_id,
            "employee_name": submission.employee_name,
            "resignation_status": submission.resignation_status,
            "vendor_email": vendor_email,
            "vendor_mail_sent": submission.vendor_mail_sent,
            "email_sent": email_success
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to finalize offboarding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to finalize offboarding: {str(e)}")


@router.get("/debug-submissions", tags=["debug"])
def debug_submissions(
    db: Session = Depends(get_db)
):
    """Debug endpoint to see all submissions and their status"""
    try:
        from app.models.submission import Submission

        submissions = db.query(Submission).all()

        debug_info = []
        for sub in submissions:
            debug_info.append({
                "id": sub.id,
                "employee_name": sub.employee_name,
                "employee_email": sub.employee_email,
                "resignation_status": sub.resignation_status,
                "exit_interview_status": sub.exit_interview_status,
                "created_at": sub.created_at,
                "last_working_day": sub.last_working_day.strftime("%Y-%m-%d") if sub.last_working_day else None
            })

        return {
            "total_submissions": len(debug_info),
            "submissions": debug_info
        }

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Debug submissions error: {str(e)}")
        return {"error": str(e)}


@router.get("/debug-interviews-table", tags=["debug"])
def debug_interviews_table(db: Session = Depends(get_db)):
    """Debug endpoint to check ExitInterview table"""
    try:
        from app.models.exit_interview import ExitInterview
        import logging
        logger = logging.getLogger(__name__)

        # Check if table exists and has records
        interviews = db.query(ExitInterview).all()
        logger.info(f"ExitInterview table has {len(interviews)} records")

        debug_info = []
        for interview in interviews:
            debug_info.append({
                "id": interview.id,
                "submission_id": interview.submission_id,
                "scheduled_date": interview.scheduled_date.strftime("%Y-%m-%d") if interview.scheduled_date else None,
                "scheduled_time": interview.scheduled_time,
                "interview_completed": interview.interview_completed,
                "completed_at": interview.completed_at.strftime("%Y-%m-%d") if interview.completed_at else None
            })

        return {
            "total_interviews": len(debug_info),
            "interviews": debug_info
        }

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Debug interviews table error: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {"error": str(e), "traceback": traceback.format_exc()}


@router.get("/exit-interviews/pending-feedback")
def get_pending_feedback_interviews(
    db: Session = Depends(get_db)
    # current_user: User = Depends(get_current_hr_user)  # Temporarily removed for debugging
):
    """Get interviews that have passed their scheduled time but haven't been completed"""
    try:
        from app.crud_exit_interview import get_pending_scheduled_interviews
        from datetime import datetime
        import logging
        logger = logging.getLogger(__name__)

        logger.info("Starting get_pending_feedback_interviews")

        # Debug mode removed - now loading actual data

        interviews = get_pending_scheduled_interviews(db)
        logger.info(f"Found {len(interviews)} pending interviews")

        pending_list = []
        for interview in interviews:
            try:
                # Safely get submission with error handling
                submission = interview.submission
                if not submission:
                    logger.warning(f"Interview {interview.id} has no submission, skipping")
                    continue

                # Calculate days overdue safely
                if interview.scheduled_date:
                    days_overdue = (datetime.utcnow() - interview.scheduled_date).days
                else:
                    days_overdue = 0

                pending_list.append({
                    "interview_id": interview.id,
                    "submission_id": submission.id,
                    "employee_name": submission.employee_name,
                    "employee_email": submission.employee_email,
                    "scheduled_date": interview.scheduled_date.strftime("%Y-%m-%d") if interview.scheduled_date else None,
                    "scheduled_time": interview.scheduled_time or "Not set",
                    "location": interview.location or "Not set",
                    "interviewer": interview.interviewer or "HR Representative",
                    "days_overdue": days_overdue,
                    "department": getattr(submission, 'department', 'General')
                })
            except Exception as interview_error:
                logger.error(f"Error processing interview {interview.id}: {str(interview_error)}")
                continue

        logger.info(f"Successfully processed {len(pending_list)} pending interviews")
        return {
            "message": f"Found {len(pending_list)} interviews pending feedback",
            "pending_count": len(pending_list),
            "interviews": pending_list
        }

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get pending feedback interviews: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get pending feedback interviews")


# Helper functions for exit interview workflow

async def _send_it_notification(db: Session, submission):
    """Send IT clearance notification when exit interview is done"""
    try:
        from app.services.email import get_email_service, EmailTemplates
        from app.services.tokenized_forms import get_tokenized_form_service
        from config import BASE_URL, settings
        import logging

        logger = logging.getLogger(__name__)
        email_service = get_email_service()
        form_token_service = get_tokenized_form_service()

        # Generate IT clearance form token
        it_clearance_token = form_token_service.generate_secure_token({
            "form_type": "it_clearance",
            "submission_id": submission.id,
            "employee_name": submission.employee_name,
            "created_for": "it_clearance"
        })

        # Create IT clearance form URL
        clearance_form_url = f"{BASE_URL}/api/forms/complete-it-clearance?token={it_clearance_token}"

        # Get asset details
        from app.crud import get_asset_by_submission
        asset = get_asset_by_submission(db, submission.id)

        email_data = {
            "employee_name": submission.employee_name,
            "employee_email": submission.employee_email,
            "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
            "department": getattr(submission, 'department', 'General'),
            "position": getattr(submission, 'position', 'Employee'),
            "assets": asset.__dict__ if asset else {},
            "submission_id": submission.id
        }

        email_message = EmailTemplates.it_clearance_request(email_data, clearance_form_url)
        success = await email_service.send_email(email_message)

        if success:
            logger.info(f"IT clearance notification sent for submission {submission.id}")
        else:
            logger.warning(f"Failed to send IT clearance notification for submission {submission.id}")

        return success

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send IT notification: {str(e)}")
        return False