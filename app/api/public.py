"""Public API endpoints - no authentication required"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from app.database import get_db
from app.crud import create_submission
from app.schemas_all import PublicSubmissionCreate, FeishuWebhookData, SubmissionResponse
from app.services.email import get_email_service, EmailTemplates
from app.services.submission_validator import get_submission_validator
from app.core.security import get_approval_token_service
from app.models.config import TeamMapping
from config import BASE_URL

router = APIRouter(prefix="/api/public", tags=["public"])


@router.post("/submission", response_model=SubmissionResponse)
async def create_public_submission(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Public submission endpoint for Feishu integration.
    No authentication required - creates a new resignation submission.
    """
    import logging
    import json
    logger = logging.getLogger(__name__)

    # Debug: Get raw request body before FastAPI validation
    try:
        body = await request.body()
        body_text = body.decode('utf-8')

        logger.info("="*60)
        logger.info("📥 SUBMISSION REQUEST RECEIVED")
        logger.info(f"   Request Headers: {dict(request.headers)}")
        logger.info(f"   Raw Body: {body_text}")

        # Try to parse JSON manually
        try:
            json_data = json.loads(body_text)
            logger.info(f"   Parsed JSON: {json.dumps(json_data, indent=2)}")

            # Convert Feishu date format (YYYY/MM/DD) to ISO datetime format
            date_fields = ['joining_date', 'submission_date', 'last_working_day']
            for field in date_fields:
                if field in json_data and json_data[field]:
                    original_date = json_data[field]
                    try:
                        # Convert YYYY/MM/DD to YYYY-MM-DD
                        if '/' in original_date and len(original_date) == 10:
                            # Feishu format: YYYY/MM/DD
                            converted_date = original_date.replace('/', '-')
                            # Add time component for ISO format
                            iso_date = f"{converted_date}T00:00:00"
                            json_data[field] = iso_date
                            logger.info(f"   🔄 Converted {field}: {original_date} → {iso_date}")
                        elif '/' in original_date and len(original_date.split('/')) == 3:
                            # Format like 2025/10/12
                            parts = original_date.split('/')
                            if len(parts[0]) == 4:  # YYYY/MM/DD
                                iso_date = f"{original_date.replace('/', '-')}T00:00:00"
                                json_data[field] = iso_date
                                logger.info(f"   🔄 Converted {field}: {original_date} → {iso_date}")
                    except Exception as e:
                        logger.warning(f"   ⚠️  Could not convert {field} '{original_date}': {e}")

        except json.JSONDecodeError as e:
            logger.error(f"   ❌ JSON decode error: {e}")
            logger.error(f"   Raw body that failed: {body_text}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid JSON", "details": str(e)}
            )

    except Exception as e:
        logger.error(f"   ❌ Error reading request body: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to read request", "details": str(e)}
        )

    # Now parse with FastAPI validation
    try:
        submission_data = PublicSubmissionCreate(**json_data)
        logger.info(f"   ✅ FastAPI validation passed")
    except Exception as e:
        logger.error(f"   ❌ FastAPI validation error: {e}")
        logger.error(f"   JSON that failed validation: {json_data}")
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")

    try:
        # Validate submission data
        if not submission_data.employee_name or not submission_data.employee_email:
            raise HTTPException(
                status_code=400,
                detail="Employee name and email are required"
            )

        # Enhanced validation - check if employee can submit new resignation
        validator = get_submission_validator()
        can_submit, reason_message, existing_info = validator.can_submit_new_resignation(db, submission_data.employee_email)

        if not can_submit:
            raise HTTPException(
                status_code=409,
                detail=reason_message
            )

        # Log that we're allowing the submission
        logger.info(f"✅ Submission allowed: {reason_message}")
        if existing_info:
            logger.info(f"📋 Previous submission: {existing_info}")

        # ALWAYS use leader name to get email from database mapping (ignore submitted leader_email)
        leader_name = submission_data.leader_name
        leader_email = None
        chm_email = None
        chm_name = None

        logger.info(f"   Using leader_name: '{leader_name}' (ignoring submitted leader_email)")

        # Look up leader info from database
        if leader_name:
            # Query database for leader mapping
            mapping = db.query(TeamMapping).filter(
                TeamMapping.is_active == True,
                TeamMapping.team_leader_name == leader_name
            ).first()

            if mapping:
                leader_email = mapping.team_leader_email
                chm_email = mapping.chinese_head_email
                chm_name = mapping.chinese_head_name
                logger.info(f"✅ Leader mapped: {leader_name} → {leader_email}")
                logger.info(f"✅ CHM mapped: {chm_name} → {chm_email}")
            else:
                logger.error(f"❌ Leader '{leader_name}' not found in database mapping!")
                raise HTTPException(
                    status_code=400,
                    detail=f"Leader '{leader_name}' not found in the team mapping. Please contact HR to update the mapping."
                )
        else:
            logger.error(f"❌ No leader_name provided in submission!")
            raise HTTPException(
                status_code=400,
                detail="Leader name is required. Please select your team leader."
            )

        # Create the submission with leader/CHM emails stored
        from app.schemas_all import SubmissionCreate
        submission_create = SubmissionCreate(
            employee_name=submission_data.employee_name,
            employee_email=submission_data.employee_email,
            employee_id=getattr(submission_data, 'employee_id', None),
            department=submission_data.department,
            team_leader_email=leader_email,
            chm_email=chm_email,
            joining_date=getattr(submission_data, 'joining_date', None),
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
                "leader_email": leader_email,
                "leader_name": leader_name,
                "department": submission_data.department,
                "reason": getattr(submission_data, 'reason', None)
            }
        )
        logger.info(f"✅ Submission created: ID {submission.id}")
        logger.info(f"   Employee: {submission.employee_name}")
        logger.info(f"   Leader email: {leader_email}")
        logger.info("="*60)

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

        # Enhanced validation - check if employee can submit new resignation
        validator = get_submission_validator()
        can_submit, reason_message, existing_info = validator.can_submit_new_resignation(db, submission_data.employee_email)

        if not can_submit:
            return {
                "success": False,
                "message": reason_message,
                "existing_submission": existing_info
            }

        # Log that we're allowing the submission
        logger.info(f"✅ Feishu webhook submission allowed: {reason_message}")
        if existing_info:
            logger.info(f"📋 Previous submission: {existing_info}")

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
                "leader_email": leader_email,
                "leader_name": submission_data.leader_name or "Team Leader",
                "department": submission_data.department,
                "reason": getattr(submission_data, 'reason', None)
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


@router.get("/debug-submissions")
def debug_submissions_public(db: Session = Depends(get_db)):
    """Public debug endpoint to see all submissions and their status"""
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


@router.get("/debug-interviews")
def debug_interviews_public(db: Session = Depends(get_db)):
    """Public debug endpoint to check ExitInterview table"""
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
                "completed_at": interview.interview_completed_at.strftime("%Y-%m-%d") if interview.interview_completed_at else None
            })

        return {
            "total_interviews": len(debug_info),
            "interviews": debug_info
        }

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Debug interviews error: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {"error": str(e), "traceback": traceback.format_exc()}


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
            "leader_email": additional_data.get("leader_email"),
            "leader_name": additional_data.get("leader_name", "Team Leader")
        }

        # Create and send email
        email_message = EmailTemplates.leader_approval_request(email_data, approval_url)
        await email_service.send_email(email_message)

        print(f"[SUCCESS] Leader approval email sent for submission {submission_id}")

    except Exception as e:
        print(f"[ERROR] Failed to send leader approval email: {str(e)}")
        # Don't raise - background task shouldn't fail the request


@router.get("/submissions/{employee_email}")
def get_employee_submissions(
    employee_email: str,
    db: Session = Depends(get_db)
):
    """
    Get all submissions for a specific employee
    """
    try:
        logger.info(f"📋 Retrieving submission history for: {employee_email}")

        validator = get_submission_validator()
        submissions = validator.get_all_submissions_for_employee(db, employee_email)

        if not submissions:
            return {
                "success": True,
                "message": "No submissions found for this employee",
                "submissions": []
            }

        return {
            "success": True,
            "message": f"Found {len(submissions)} submissions",
            "submissions": submissions
        }

    except Exception as e:
        logger.error(f"Error retrieving submissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve submissions")