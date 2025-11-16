"""Approval workflow endpoints"""
from fastapi import APIRouter, HTTPException, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import time
import logging
import asyncio

from app.database import get_db
from app.crud import get_submission, update_submission
from app.schemas_all import ApprovalRequest, ApprovalResponse, SubmissionResponse
from app.core.security import verify_approval_token_for_request, get_approval_token_service
from app.services.email import get_email_service, EmailTemplates
from app.models.submission import ResignationStatus
from config import BASE_URL
import config

router = APIRouter(tags=["approvals"])


@router.post("/approve/{submission_id}")
async def process_approval(
    submission_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Process approval/rejection via secure token
    """
    try:
        # Get form data
        form_data = await request.form()
        action = form_data.get("action")
        notes = form_data.get("notes", "")
        token = form_data.get("token") or request.query_params.get("token")

        if not action or not token:
            raise HTTPException(
                status_code=400,
                detail="Action and token are required"
            )

        if action not in ["approve", "reject"]:
            raise HTTPException(
                status_code=400,
                detail="Action must be 'approve' or 'reject'"
            )

        # Verify token
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Approval request received: submission_id={submission_id}, action={action}")
        token_data = verify_approval_token_for_request(token)
        logger.info(f"Token verified: approver_type={token_data.get('approver_type')}")
        if token_data["submission_id"] != submission_id:
            raise HTTPException(
                status_code=401,
                detail="Token does not match submission"
            )

        # Validate approver type matches expected
        approver_type = token_data["approver_type"]

        # Get submission
        submission = get_submission(db, submission_id)
        if not submission:
            raise HTTPException(
                status_code=404,
                detail="Submission not found"
            )

        # Validate that rejection requires notes
        if action == "reject" and not notes.strip():
            raise HTTPException(
                status_code=400,
                detail="Notes are required when rejecting a resignation"
            )

        # Process approval based on approver type and current status
        result = await process_approval_logic(
            db, submission, action, notes, approver_type, token_data
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process approval: {str(e)}"
        )


@router.get("/approve/leader/{submission_id}", response_class=HTMLResponse)
async def leader_approval_page(
    submission_id: int,
    token: str,
    action: str,
    db: Session = Depends(get_db)
):
    """
    Leader approval page with secure token
    """
    start_time = time.time()
    try:
        print(f"[TIMING] Leader approval page START - submission_id={submission_id}, action={action}")
        print(f"DEBUG: Token (first 50 chars): {token[:50]}...")

        # Verify token
        token_start = time.time()
        token_data = verify_approval_token_for_request(token)
        token_time = time.time() - token_start
        print(f"[TIMING] Token verification took {token_time:.3f}s")
        print(f"DEBUG: Token verified successfully - {token_data}")

        if token_data["submission_id"] != submission_id or token_data["approver_type"] != "leader":
            print(f"DEBUG: Token validation failed - expected submission_id={submission_id}, approver_type=leader")
            raise HTTPException(
                status_code=401,
                detail="Invalid token for leader approval"
            )

        # Get submission
        db_start = time.time()
        submission = get_submission(db, submission_id)
        db_time = time.time() - db_start
        print(f"[TIMING] Database query took {db_time:.3f}s")

        if not submission:
            return HTMLResponse(content="<h2>Submission not found</h2>", status_code=404)

        # Render approval page
        render_start = time.time()
        html_content = generate_approval_page(
            submission=submission,
            approver_type="leader",
            action=action,
            token=token
        )
        render_time = time.time() - render_start
        print(f"[TIMING] HTML rendering took {render_time:.3f}s")

        total_time = time.time() - start_time
        print(f"[TIMING] Leader approval page COMPLETED - Total: {total_time:.3f}s")

        return HTMLResponse(content=html_content)

    except HTTPException:
        raise
    except asyncio.TimeoutError as e:
        total_time = time.time() - start_time
        print(f"[TIMEOUT] Leader approval page timed out after {total_time:.3f}s: {str(e)}")
        return HTMLResponse(
            content=f"<h2>Request Timeout</h2><p>The approval page took too long to load ({total_time:.1f}s). Please try again.</p>",
            status_code=408
        )
    except Exception as e:
        total_time = time.time() - start_time
        print(f"[ERROR] Leader approval page failed after {total_time:.3f}s: {str(e)}")
        import traceback
        traceback.print_exc()

        # Check for specific connection errors
        error_msg = str(e).lower()
        if "connection" in error_msg or "timeout" in error_msg or "network" in error_msg:
            return HTMLResponse(
                content=f"<h2>Connection Error</h2><p>Unable to connect to database or services. Please try again later.</p><p><small>Error: {str(e)}</small></p>",
                status_code=503
            )
        else:
            return HTMLResponse(
                content=f"<h2>Error loading approval page</h2><p>An unexpected error occurred. Please check server logs.</p><p><small>Error: {str(e)}</small></p>",
                status_code=500
            )


@router.get("/approve/chm/{submission_id}", response_class=HTMLResponse)
async def chm_approval_page(
    submission_id: int,
    token: str,
    action: str,
    db: Session = Depends(get_db)
):
    """
    CHM approval page with secure token
    """
    start_time = time.time()
    try:
        print(f"[TIMING] CHM approval page START - submission_id={submission_id}, action={action}")

        # Verify token
        token_start = time.time()
        token_data = verify_approval_token_for_request(token)
        token_time = time.time() - token_start
        print(f"[TIMING] CHM token verification took {token_time:.3f}s")

        if token_data["submission_id"] != submission_id or token_data["approver_type"] != "chm":
            raise HTTPException(
                status_code=401,
                detail="Invalid token for CHM approval"
            )

        # Get submission
        db_start = time.time()
        submission = get_submission(db, submission_id)
        db_time = time.time() - db_start
        print(f"[TIMING] CHM database query took {db_time:.3f}s")

        if not submission:
            return HTMLResponse(content="<h2>Submission not found</h2>", status_code=404)

        # Render approval page
        render_start = time.time()
        html_content = generate_approval_page(
            submission=submission,
            approver_type="chm",
            action=action,
            token=token
        )
        render_time = time.time() - render_start
        print(f"[TIMING] CHM HTML rendering took {render_time:.3f}s")

        total_time = time.time() - start_time
        print(f"[TIMING] CHM approval page COMPLETED - Total: {total_time:.3f}s")

        return HTMLResponse(content=html_content)

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Approval page failed - {str(e)}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(
            content=f"<h2>Error loading approval page: {str(e)}</h2><p>Check server logs for details.</p>",
            status_code=500
        )


async def process_approval_logic(
    db: Session,
    submission,
    action: str,
    notes: str,
    approver_type: str,
    token_data: dict
) -> ApprovalResponse:
    """Process the approval logic and send appropriate emails"""

    try:
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Processing approval: approver_type={approver_type}, action={action}, current_status={submission.resignation_status}")
        current_status = submission.resignation_status
        new_status = current_status
        message = ""

        # Leader approval logic
        if approver_type == "leader":
            logger.info(f"Leader approval logic triggered")
            if current_status != ResignationStatus.SUBMITTED.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot {action} submission in status: {current_status}"
                )

            if action == "approve":
                new_status = ResignationStatus.LEADER_APPROVED.value
                submission.team_leader_reply = True
                submission.team_leader_notes = notes
                message = "Submission approved by Team Leader"

                # Send CHM approval email
                email_sent = await send_chm_approval_email(submission)
                if not email_sent:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"CHM approval email failed for submission {submission.id}, but approval was processed")

            elif action == "reject":
                new_status = ResignationStatus.LEADER_REJECTED.value
                submission.team_leader_reply = False
                submission.team_leader_notes = notes
                message = "Submission rejected by Team Leader"

                # Send HR notification
                await send_hr_notification(submission, "leader_rejected")

        # CHM approval logic
        elif approver_type == "chm":
            if current_status != ResignationStatus.LEADER_APPROVED.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot {action} submission in status: {current_status}"
                )

            if action == "approve":
                new_status = ResignationStatus.CHM_APPROVED.value
                submission.chinese_head_reply = True
                submission.chinese_head_notes = notes
                message = "Submission approved by Chinese Head - Ready for HR processing"

                # Send HR notification
                await send_hr_notification(submission, "chm_approved")

            elif action == "reject":
                new_status = ResignationStatus.CHM_REJECTED.value
                submission.chinese_head_reply = False
                submission.chinese_head_notes = notes
                message = "Submission rejected by Chinese Head"

                # Send HR notification
                await send_hr_notification(submission, "chm_rejected")

        # Update submission
        submission.resignation_status = new_status
        db.commit()
        db.refresh(submission)

        return ApprovalResponse(
            success=True,
            message=message,
            submission_id=submission.id,
            new_status=new_status,
            timestamp=datetime.now()
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Approval processing failed: {str(e)}"
        )


def generate_approval_page(
    submission,
    approver_type: str,
    action: str,
    token: str
) -> str:
    """Generate HTML approval page"""

    title = "Team Leader Approval" if approver_type == "leader" else "Department Head Approval"

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Resignation Request</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; background-color: #f5f5f5; }}
            .container {{ background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; }}
            .employee-info {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
            .info-row {{ margin: 10px 0; }}
            label {{ display: block; margin: 15px 0 5px; font-weight: bold; color: #555; }}
            textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box; min-height: 100px; resize: vertical; }}
            .button-group {{ text-align: center; margin-top: 30px; }}
            button {{ padding: 12px 30px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; margin: 5px; font-weight: bold; }}
            .btn-approve {{ background-color: #28a745; color: white; }}
            .btn-approve:hover {{ background-color: #218838; }}
            .btn-reject {{ background-color: #dc3545; color: white; }}
            .btn-reject:hover {{ background-color: #c82333; }}
            .btn-cancel {{ background-color: #6c757d; color: white; }}
            .btn-cancel:hover {{ background-color: #5a6268; }}
            .success {{ color: #27ae60; text-align: center; padding: 20px; font-size: 18px; }}
            .error {{ color: #c0392b; text-align: center; padding: 20px; }}
            .note {{ background-color: #fff3cd; padding: 15px; border-radius: 4px; margin: 15px 0; border-left: 4px solid #ffc107; }}
            .footer-note {{ text-align: center; margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 {title}</h1>
            <div class="employee-info">
                <div class="info-row"><strong>Employee:</strong> {submission.employee_name}</div>
                <div class="info-row"><strong>Email:</strong> {submission.employee_email}</div>
                <div class="info-row"><strong>Submission Date:</strong> {submission.submission_date.strftime('%B %d, %Y') if hasattr(submission.submission_date, 'strftime') else str(submission.submission_date)}</div>
                <div class="info-row"><strong>Last Working Day:</strong> {submission.last_working_day.strftime('%B %d, %Y') if hasattr(submission.last_working_day, 'strftime') else str(submission.last_working_day)}</div>
            </div>

            <div class="note">
                <strong>💡 Note:</strong> Notes are optional when approving, but <strong>required when rejecting</strong> a resignation request.
            </div>

            <form id="approvalForm" method="post" action="/approve/{submission.id}">
                <input type="hidden" name="token" value="{token}">
                <input type="hidden" name="action" id="actionField" value="">

                <label>Comments/Notes:</label>
                <textarea name="notes" id="notes" placeholder="Please provide any additional comments (required if rejecting)..."></textarea>

                <div class="button-group">
                    <button type="button" class="btn-approve" onclick="submitForm('approve')">
                        ✓ Approve
                    </button>
                    <button type="button" class="btn-reject" onclick="submitForm('reject')">
                        ✗ Reject
                    </button>
                    <button type="button" class="btn-cancel" onclick="window.close()">
                        Cancel
                    </button>
                </div>
            </form>

            <div id="message"></div>

            <div class="footer-note">
                This is a secure approval link. Do not share this URL with others.<br>
                Link expires in 24 hours. For assistance, contact HR.
            </div>
        </div>

        <script>
            function submitForm(action) {{
                const notes = document.getElementById('notes').value.trim();
                const actionField = document.getElementById('actionField');
                const messageDiv = document.getElementById('message');

                if (action === 'reject' && notes === '') {{
                    messageDiv.innerHTML = '<div class="error">❌ Notes are required when rejecting a resignation request.</div>';
                    document.getElementById('notes').focus();
                    return false;
                }}

                // Confirm action
                const confirmMsg = action === 'approve'
                    ? 'Are you sure you want to approve this resignation?'
                    : 'Are you sure you want to reject this resignation?';

                if (confirm(confirmMsg)) {{
                    actionField.value = action;
                    document.getElementById('approvalForm').submit();
                }}
            }}
        </script>
    </body>
    </html>
    """


async def send_chm_approval_email(submission) -> bool:
    """Send approval email to Chinese Head"""
    try:
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Attempting to send CHM approval email for submission {submission.id}")

        email_service = get_email_service()
        token_service = get_approval_token_service()

        # Generate approval URLs
        approval_url = token_service.generate_approval_url(
            submission_id=submission.id,
            action="approve",
            approver_type="chm",
            base_url=BASE_URL
        )

        # Get CHM email directly from submission (stored during creation from CSV mapping)
        chm_email = submission.chm_email
        chm_name = "Chinese Head"

        if not chm_email:
            logger.error(f"❌ No CHM email found in submission {submission.id}! Cannot send CHM approval email.")
            raise ValueError(f"No CHM email found for submission {submission.id}. Please update the submission.")

        logger.info(f"✅ Using CHM email from submission: {chm_email}")

        # Prepare submission data
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

        logger.info(f"Sending CHM approval email to: {chm_email} ({chm_name})")
        logger.debug(f"Email data keys: {list(email_data.keys())}")

        # Create and send email
        email_message = EmailTemplates.chm_approval_request(email_data, approval_url)
        logger.debug(f"EmailMessage created - to_email: {email_message.to_email}")

        success = await email_service.send_email(email_message)
        if success:
            logger.info(f"[SUCCESS] CHM approval email sent for submission {submission.id} to {chm_email} ({chm_name})")
            return True
        else:
            logger.error(f"[ERROR] CHM approval email FAILED for submission {submission.id} to {chm_email}")
            return False

    except Exception as e:
        import traceback
        logger.error(f"[ERROR] Failed to send CHM approval email: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False


async def send_hr_notification(submission, message_type: str):
    """Send simple HR reminder to check platform"""
    try:
        # Send simple platform reminder when CHM approves
        if message_type == "chm_approved":
            from config import settings

            email_service = get_email_service()

            # Simple platform URL - no tokenized forms
            platform_url = f"{settings.FRONTEND_URL}"

            # Prepare email data for simple reminder
            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "submission_id": submission.id,
                "department": getattr(submission, 'department', 'General'),
                "position": getattr(submission, 'position', 'Employee'),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d")
            }

            # Create and send simple reminder email
            email_message = EmailTemplates.hr_exit_interview_reminder(email_data, platform_url)
            await email_service.send_email(email_message)
            print(f"[SUCCESS] HR exit interview reminder sent for submission {submission.id}")

        else:
            # For other message types (rejections), send regular notification
            email_service = get_email_service()
            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "submission_data": {
                    "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                    "leader_notes": submission.team_leader_notes,
                    "chinese_head_notes": submission.chinese_head_notes
                },
                "message_type": message_type
            }
            email_message = EmailTemplates.hr_notification(email_data, message_type)
            await email_service.send_email(email_message)
            print(f"✅ HR notification sent for {message_type} - submission {submission.id}")

    except Exception as e:
        print(f"❌ Failed to send HR notification: {str(e)}")
        import traceback
        traceback.print_exc()