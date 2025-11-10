"""
Tokenized Email Forms Service

Creates secure tokenized links for HR to perform actions via email
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from app.core.security import get_approval_token_service
from fastapi import HTTPException, status
from app.database import get_db
from app.models.submission import Submission
from app.models.exit_interview import ExitInterview
from app.models.user import User
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class TokenizedFormService:
    """Service for creating and managing tokenized email forms"""

    def __init__(self):
        self.active_tokens = {}  # In-memory token store (consider Redis for production)

    def generate_secure_token(self, data: Dict[str, Any], expires_hours: int = 24) -> str:
        """Generate a secure token with embedded data"""
        # Create a unique identifier
        token_id = secrets.token_urlsafe(32)

        # Create expiration timestamp
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

        # Create token data
        token_data = {
            "token_id": token_id,
            "expires_at": expires_at.isoformat(),
            "data": data,
            "created_at": datetime.utcnow().isoformat()
        }

        # Generate secure token using the approval token service
        approval_service = get_approval_token_service()
        secure_token = approval_service.generate_approval_token(
            submission_id=data.get("submission_id", 0),
            action=f"form_{data.get('form_type', 'unknown')}",
            approver_type="hr",
            additional_data=token_data
        )

        # Store token in memory (for validation)
        self.active_tokens[token_id] = token_data

        logger.info(f"🔑 Generated secure token: {token_id} (expires: {expires_at})")

        return secure_token

    def validate_and_extract_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Validate token and extract embedded data"""
        try:
            # Verify the token using approval token service
            approval_service = get_approval_token_service()
            payload = approval_service.verify_approval_token(token)

            if not payload:
                return False, None, "Invalid token"

            # Extract additional data from the token
            additional_data = payload.get("additional_data", {})
            if not additional_data:
                return False, None, "Token missing form data"

            # Check if this is a form token
            action = payload.get("action", "")
            if not action.startswith("form_"):
                return False, None, "Invalid token type"

            # Token is valid - extract the form data
            form_data = additional_data.get("data", {})
            return True, form_data, "Token valid"

        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return False, None, f"Token validation failed: {str(e)}"

    def cleanup_expired_tokens(self):
        """Clean up expired tokens"""
        current_time = datetime.utcnow()
        expired_tokens = []

        for token_id, token_data in self.active_tokens.items():
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            if current_time > expires_at:
                expired_tokens.append(token_id)

        for token_id in expired_tokens:
            del self.active_tokens[token_id]
            logger.info(f"🧹 Cleaned up expired token: {token_id}")

    def create_interview_scheduling_token(self, submission_id: int, employee_email: str) -> str:
        """Create token for interview scheduling via email"""
        token_data = {
            "form_type": "schedule_interview",
            "action": "schedule_interview",
            "submission_id": submission_id,
            "employee_email": employee_email,
            "created_for": "interview_scheduling"
        }

        return self.generate_secure_token(token_data, expires_hours=72)  # 3 days

    def create_interview_feedback_token(self, interview_id: int, employee_email: str) -> str:
        """Create token for interview feedback via email"""
        token_data = {
            "form_type": "submit_feedback",
            "action": "submit_feedback",
            "interview_id": interview_id,
            "employee_email": employee_email,
            "created_for": "interview_feedback"
        }

        return self.generate_secure_token(token_data, expires_hours=72)  # 3 days

    def create_skip_interview_token(self, submission_id: int, employee_email: str, reason: str) -> str:
        """Create token for skipping interview"""
        token_data = {
            "form_type": "skip_interview",
            "action": "skip_interview",
            "submission_id": submission_id,
            "employee_email": employee_email,
            "reason": reason,
            "created_for": "skip_interview"
        }

        return self.generate_secure_token(token_data, expires_hours=72)  # 3 days


# Global service instance
tokenized_form_service = TokenizedFormService()


def get_tokenized_form_service() -> TokenizedFormService:
    """Get the global tokenized form service instance"""
    return tokenized_form_service


class EmailFormTemplates:
    """Templates for email-based forms"""

    @staticmethod
    def generate_interview_scheduling_email(employee_data: Dict, token: str, base_url: str) -> str:
        """Generate HTML email for interview scheduling"""

        form_url = f"{base_url}/forms/schedule-interview?token={token}"

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Schedule Exit Interview</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f8f9fa;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                    margin: -30px -30px 30px -30px;
                }}
                .form-group {{
                    margin-bottom: 20px;
                }}
                .form-group label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                    color: #555;
                }}
                .form-control {{
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    font-size: 14px;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    border: none;
                    cursor: pointer;
                    font-size: 14px;
                }}
                .btn:hover {{
                    background: #5a6fd8;
                }}
                .btn-secondary {{
                    background: #6c757d;
                }}
                .btn-secondary:hover {{
                    background: #5a6268;
                }}
                .info-box {{
                    background: #e3f2fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    border-left: 4px solid #667eea;
                }}
                .alert {{
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .alert-warning {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                }}
                .alert-info {{
                    background: #d1ecf1;
                    border: 1px solid #bee5eb;
                    color: #0c5460;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📅 Schedule Exit Interview</h2>
                    <p>Hi {employee_data['employee_name']}!</p>
                </div>

                <div class="info-box">
                    <h3>Interview Details</h3>
                    <p><strong>Employee:</strong> {employee_data['employee_name']}</p>
                    <p><strong>Position:</strong> {employee_data.get('position', 'Employee')}</p>
                    <p><strong>Department:</strong> {employee_data.get('department', 'General')}</p>
                    <p><strong>Last Working Day:</strong> {employee_data.get('last_working_day', 'N/A')}</p>
                </div>

                <div class="alert alert-info">
                    <strong>💡 Quick Option:</strong> You can schedule the interview right here without logging into the system, or click the button below to open the full dashboard.
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{form_url}" class="btn">Schedule Interview Now</a>
                    <a href="{base_url}/dashboard" class="btn btn-secondary" style="margin-left: 10px;">Open Dashboard</a>
                </div>

                <div class="alert alert-warning">
                    <strong>⚠️ Security Note:</strong> This link is unique to you and will expire in 3 days for your security.
                </div>

                <p style="text-align: center; color: #666; font-size: 12px; margin-top: 30px;">
                    <small>If you have any questions, please contact HR directly.</small>
                </p>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def generate_feedback_submission_email(employee_data: Dict, token: str, base_url: str) -> str:
        """Generate HTML email for feedback submission"""

        form_url = f"{base_url}/forms/submit-feedback?token={token}"

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Submit Interview Feedback</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f8f9fa;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                    margin: -30px -30px 30px -30px;
                }}
                .form-group {{
                    margin-bottom: 20px;
                }}
                .form-group label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                    color: #555;
                }}
                .form-control {{
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    font-size: 14px;
                }}
                textarea.form-control {{
                    min-height: 120px;
                    resize: vertical;
                }}
                select.form-control {{
                    padding: 10px;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: #28a745;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    border: none;
                    cursor: pointer;
                    font-size: 14px;
                }}
                .btn:hover {{
                    background: #218838;
                }}
                .btn-secondary {{
                    background: #6c757d;
                }}
                .btn-secondary:hover {{
                    background: #5a6268;
                }}
                .info-box {{
                    background: #d4edda;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    border-left: 4px solid #28a745;
                }}
                .rating-container {{
                    display: flex;
                    gap: 10px;
                    justify-content: center;
                    margin: 10px 0;
                }}
                .star {{
                    font-size: 24px;
                    color: #ddd;
                    cursor: pointer;
                    transition: color 0.2s;
                }}
                .star:hover,
                .star.selected {{
                    color: #ffc107;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📝 Submit Interview Feedback</h2>
                    <p>Thanks {employee_data['employee_name']} for your interview!</p>
                </div>

                <div class="info-box">
                    <h3>Interview Information</h3>
                    <p><strong>Interview Date:</strong> {employee_data.get('interview_date', 'TBD')}</p>
                    <p><strong>Interview Time:</strong> {employee_data.get('interview_time', 'TBD')}</p>
                    <p><strong>Location:</strong> {employee_data.get('location', 'HR Office')}</p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{form_url}" class="btn">Submit Feedback Now</a>
                    <a href="{base_url}/dashboard" class="btn btn-secondary" style="margin-left: 10px;">Open Dashboard</a>
                </div>

                <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <strong>💡 What to Include:</strong>
                    <ul style="margin: 10px 0 10px 20px;">
                        <li>Your overall experience with the company</li>
                        <li>Reasons for leaving</li>
                        <li>What you enjoyed about your role</li>
                        <li>Suggestions for improvement</li>
                        <li>Your future plans</li>
                    </ul>
                </div>

                <div style="text-align: center; color: #666; font-size: 12px; margin-top: 30px;">
                    <small>This link is unique to you and expires in 3 days. Your feedback is valuable for improving our workplace!</small>
                </p>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def generate_skip_interview_email(employee_data: Dict, token: str, base_url: str, reason: str) -> str:
        """Generate HTML email for skipping interview"""

        form_url = f"{base_url}/forms/skip-interview?token={token}"

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Skip Exit Interview</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f8f9fa;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%);
                    color: #333;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                    margin: -30px -30px 30px -30px;
                }}
                .info-box {{
                    background: #fff3cd;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                    border-left: 4px solid #ffc107;
                }}
                .form-group {{
                    margin-bottom: 20px;
                }}
                .form-group label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                    color: #555;
                }}
                .form-control {{
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    font-size: 14px;
                }}
                textarea.form-control {{
                    min-height: 100px;
                    resize: vertical;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: #ffc107;
                    color: #333;
                    text-decoration: none;
                    border-radius: 5px;
                    border: none;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: bold;
                }}
                .btn:hover {{
                    background: #e0a800;
                }}
                .btn-secondary {{
                    background: #6c757d;
                    color: white;
                }}
                .btn-secondary:hover {{
                    background: #5a6268;
                }}
                .reason-box {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    border: 1px solid #dee2e6;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>⚡ Skip Exit Interview</h2>
                    <p>Hi {employee_data['employee_name']}!</p>
                </div>

                <div class="info-box">
                    <h3>📋 Skip Interview Request</h3>
                    <p><strong>Reason:</strong> {reason}</p>
                    <p><strong>Last Working Day:</strong> {employee_data.get('last_working_day', 'N/A')}</p>
                </div>

                <div class="reason-box">
                    <strong>Additional Notes (Optional):</strong>
                    <p>Please provide any additional context or special requirements for this case.</p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{form_url}" class="btn">Confirm Skip Interview</a>
                    <a href="{base_url}/dashboard" class="btn btn-secondary" style="margin-left: 10px;">Cancel</a>
                </div>

                <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #667eea;">
                    <strong>ℹ️ What Happens Next:</strong>
                    <p>Once you confirm, the system will:</p>
                    <ul style="margin: 10px 0 10px 20px;">
                        <li>Mark interview as skipped</li>
                        <li>Notify IT department immediately</li>
                        <li>Process asset clearance</li>
                        <li>Complete offboarding workflow</li>
                    </ul>
                </div>

                <div style="text-align: center; color: #666; font-size: 12px; margin-top: 30px;">
                    <small>This link is unique to you and expires in 3 days.</small>
                </p>
            </div>
        </body>
        </html>
        """