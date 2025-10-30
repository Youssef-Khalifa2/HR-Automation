"""Public API endpoints - no authentication required"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from app.database import get_db
from app.crud import create_submission
from app.schemas_all import PublicSubmissionCreate, FeishuWebhookData, SubmissionResponse
from app.services.email import get_email_service, EmailTemplates
from app.core.security import get_approval_token_service
from config import BASE_URL

router = APIRouter(prefix="/api", tags=["public"])


@router.post("/submission", response_model=SubmissionResponse)
async def create_public_submission(
    submission_data: PublicSubmissionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Public submission endpoint for Feishu integration.
    No authentication required - creates a new resignation submission.
    """
    try:
        # Validate submission data
        if not submission_data.employee_name or not submission_data.employee_email:
            raise HTTPException(
                status_code=400,
                detail="Employee name and email are required"
            )

        # Check if submission already exists for this employee
        from app.crud import get_submission_by_email
        existing = get_submission_by_email(db, submission_data.employee_email)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="A resignation submission already exists for this employee"
            )

        # Create the submission using the PublicSubmissionCreate data
        from app.schemas_all import SubmissionCreate
        submission_create = SubmissionCreate(
            employee_name=submission_data.employee_name,
            employee_email=submission_data.employee_email,
            joining_date=submission_data.joining_date,
            submission_date=submission_data.submission_date,
            last_working_day=submission_data.last_working_day
        )
        submission = create_submission(db, submission_create)

        # Send leader approval email in background
        background_tasks.add_task(
            send_leader_approval_email,
            submission.id,
            {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "submission_date": submission.submission_date.strftime("%Y-%m-%d"),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "leader_email": submission_data.leader_email or "youssefkhalifa@51talk.com",
                "leader_name": submission_data.leader_name or "Team Leader",
                "department": submission_data.department,
                "position": submission_data.position,
                "reason": submission_data.reason
            }
        )
        print(f"✅ Created submission {submission.id} for {submission.employee_name}")

        return submission

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create submission: {str(e)}"
        )


@router.post("/feishu/webhook")
async def feishu_webhook(
    webhook_data: FeishuWebhookData,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Feishu webhook endpoint for receiving resignation data.
    Handles Feishu-specific data format and creates submissions.
    """
    try:
        # Convert Feishu data to public submission format
        submission_data = PublicSubmissionCreate(
            employee_name=webhook_data.employee_name,
            employee_email=webhook_data.employee_email,
            joining_date=webhook_data.joining_date,
            submission_date=webhook_data.submission_date,
            last_working_day=webhook_data.last_working_day,
            department=webhook_data.department,
            position=webhook_data.position,
            leader_email=webhook_data.leader_email,
            leader_name=webhook_data.leader_name,
            reason=webhook_data.reason
        )

        # Create submission using the same logic as public endpoint
        if not submission_data.employee_name or not submission_data.employee_email:
            raise HTTPException(
                status_code=400,
                detail="Employee name and email are required"
            )

        # Check for existing submission
        from app.crud import get_submission_by_email
        existing = get_submission_by_email(db, submission_data.employee_email)
        if existing:
            return {
                "success": False,
                "message": "A resignation submission already exists for this employee",
                "submission_id": existing.id
            }

        # Create the submission using the PublicSubmissionCreate data
        from app.schemas_all import SubmissionCreate
        submission_create = SubmissionCreate(
            employee_name=submission_data.employee_name,
            employee_email=submission_data.employee_email,
            joining_date=submission_data.joining_date,
            submission_date=submission_data.submission_date,
            last_working_day=submission_data.last_working_day
        )
        submission = create_submission(db, submission_create)

        # Send leader approval email in background
        background_tasks.add_task(
            send_leader_approval_email,
            submission.id,
            {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "submission_date": submission.submission_date.strftime("%Y-%m-%d"),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "leader_email": submission_data.leader_email or "youssefkhalifa@51talk.com",
                "leader_name": submission_data.leader_name or "Team Leader",
                "department": submission_data.department,
                "position": submission_data.position,
                "reason": submission_data.reason
            }
        )
        print(f"✅ Created submission {submission.id} for {submission.employee_name}")

        return {
            "success": True,
            "message": "Resignation submission created successfully",
            "submission_id": submission.id,
            "employee_name": submission.employee_name,
            "employee_email": submission.employee_email
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feishu webhook failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Public health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}


async def send_leader_approval_email(submission_id: int, additional_data: Dict[str, Any]):
    """
    Send approval email to team leader in background task
    """
    try:
        email_service = get_email_service()
        token_service = get_approval_token_service()

        # Generate approval URL (single link - user will choose approve/reject on the page)
        approval_url = token_service.generate_approval_url(
            submission_id=submission_id,
            action="approve",  # Default action, user can choose on page
            approver_type="leader",
            base_url=BASE_URL
        )

        # Prepare submission data for email
        email_data = {
            "employee_name": additional_data.get("employee_name"),
            "employee_email": additional_data.get("employee_email"),
            "submission_date": additional_data.get("submission_date"),
            "last_working_day": additional_data.get("last_working_day"),
            "leader_email": additional_data.get("leader_email", "youssefkhalifa@51talk.com"),
            "leader_name": additional_data.get("leader_name", "Team Leader")
        }

        # Create and send email
        email_message = EmailTemplates.leader_approval_request(email_data, approval_url)
        await email_service.send_email(email_message)

        print(f"✅ Leader approval email sent for submission {submission_id}")

    except Exception as e:
        print(f"❌ Failed to send leader approval email: {str(e)}")
        # Don't raise - background task shouldn't fail the request