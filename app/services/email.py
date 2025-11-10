"""Email service for sending notifications and approval requests"""
import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import time
import logging
from dataclasses import dataclass
from sqlalchemy.orm import Session


@dataclass
class EmailConfig:
    """Email configuration"""
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True
    from_email: str = ""
    from_name: str = "HR Automation System"
    # Timeout configurations
    connect_timeout: float = 10.0
    socket_timeout: float = 10.0
    # Connection pooling
    pool_size: int = 5
    max_idle_time: float = 300.0  # 5 minutes


@dataclass
class EmailMessage:
    """Email message data"""
    to_email: str
    to_name: str
    subject: str
    template_name: str
    template_data: Dict[str, Any]


class EmailService:
    """Email service for sending notifications with connection pooling"""

    def __init__(self, config: EmailConfig):
        self.config = config
        self._smtp = None
        self._last_used = None
        self._connection_lock = asyncio.Lock()
        self.jinja_env = Environment(
            loader=FileSystemLoader("app/templates/email"),
            autoescape=True
        )
        print(f"[EMAIL] Email service initialized with timeout={config.connect_timeout}s")

    def _create_email_log(self, message: EmailMessage, db: Session) -> int:
        """Create email log entry in database before sending"""
        try:
            from app.models.email_log import EmailLog
            from datetime import datetime

            email_log = EmailLog(
                to_email=message.to_email,
                to_name=message.to_name,
                from_email=self.config.from_email,
                subject=message.subject,
                template_name=message.template_name,
                status='pending',
                attempts=1,
                created_at=datetime.utcnow(),
                last_attempt_at=datetime.utcnow(),
                template_data=message.template_data
            )

            db.add(email_log)
            db.commit()
            db.refresh(email_log)

            return email_log.id
        except Exception as e:
            print(f"[WARN] Failed to create email log: {e}")
            db.rollback()
            return None

    def _update_email_log_success(self, log_id: int, db: Session, smtp_response: str = None):
        """Update email log with success status"""
        try:
            from app.models.email_log import EmailLog
            from datetime import datetime

            email_log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
            if email_log:
                email_log.status = 'sent'
                email_log.sent_at = datetime.utcnow()
                email_log.smtp_response = smtp_response
                db.commit()
        except Exception as e:
            print(f"[WARN] Failed to update email log {log_id}: {e}")
            db.rollback()

    def _update_email_log_failure(self, log_id: int, db: Session, error_message: str, error_type: str = None):
        """Update email log with failure status"""
        try:
            from app.models.email_log import EmailLog
            from datetime import datetime

            email_log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
            if email_log:
                email_log.status = 'failed'
                email_log.failed_at = datetime.utcnow()
                email_log.error_message = error_message
                email_log.error_type = error_type or 'unknown'
                db.commit()
        except Exception as e:
            print(f"[WARN] Failed to update email log {log_id}: {e}")
            db.rollback()

    async def _get_connection(self):
        """Get SMTP connection with connection pooling"""
        async with self._connection_lock:
            # Check if we need to create a new connection
            if (self._smtp is None or
                self._last_used is None or
                time.time() - self._last_used > self.config.max_idle_time):

                print(f"[EMAIL] Creating new SMTP connection to {self.config.host}:{self.config.port}")
                connect_start = time.time()

                # Close old connection if exists
                if self._smtp:
                    try:
                        await self._smtp.quit()
                    except:
                        pass

                # Create new connection with timeout
                self._smtp = aiosmtplib.SMTP(
                    hostname=self.config.host,
                    port=self.config.port,
                    use_tls=self.config.use_tls,
                    timeout=self.config.connect_timeout
                )

                # Connect and login
                await self._smtp.connect()
                await self._smtp.login(self.config.username, self.config.password)

                connect_time = time.time() - connect_start
                print(f"[EMAIL] SMTP connection established in {connect_time:.3f}s")

            self._last_used = time.time()
            return self._smtp

    async def send_email(self, message: EmailMessage) -> bool:
        """
        Send an email using configured SMTP with connection pooling

        Args:
            message: Email message to send

        Returns:
            True if sent successfully, False otherwise
        """
        send_start = time.time()

        # Create database session for logging
        from app.database import SessionLocal
        db = SessionLocal()
        email_log_id = None

        try:
            # Create email log entry before sending
            email_log_id = self._create_email_log(message, db)

            print(f"[EMAIL] Sending email to {message.to_email}: {message.subject}")

            # Render email template
            render_start = time.time()
            html_content = self._render_template(message.template_name, message.template_data)
            text_content = self._render_text_template(message.template_name, message.template_data)
            render_time = time.time() - render_start
            print(f"[EMAIL] Template rendering took {render_time:.3f}s")

            # Create email message
            prep_start = time.time()
            email_msg = MIMEMultipart("alternative")
            email_msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            email_msg["To"] = f"{message.to_name} <{message.to_email}>"
            email_msg["Subject"] = message.subject

            # Attach HTML and text parts
            html_part = MIMEText(html_content, "html", "utf-8")
            text_part = MIMEText(text_content, "plain", "utf-8")

            email_msg.attach(text_part)
            email_msg.attach(html_part)
            prep_time = time.time() - prep_start
            print(f"[EMAIL] Message preparation took {prep_time:.3f}s")

            # Get connection and send
            smtp_start = time.time()
            smtp = await self._get_connection()

            # Ensure connection is active before sending
            if not smtp.is_connected:
                print("[EMAIL] Connection not active, reconnecting...")
                await smtp.connect()
                await smtp.login(self.config.username, self.config.password)

            response = await smtp.send_message(email_msg)
            smtp_time = time.time() - smtp_start
            print(f"[EMAIL] SMTP send took {smtp_time:.3f}s")

            # Update email log with success
            if email_log_id:
                self._update_email_log_success(email_log_id, db, smtp_response=str(response))

            total_time = time.time() - send_start
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[SUCCESS] Email sent to {message.to_email} in {total_time:.3f}s (log_id={email_log_id})")
            return True

        except asyncio.TimeoutError as e:
            total_time = time.time() - send_start
            error_msg = f"Email send timeout after {total_time:.3f}s: {str(e)}"

            # Update email log with failure
            if email_log_id:
                self._update_email_log_failure(email_log_id, db, error_msg, 'timeout')

            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[ERROR] {error_msg} to {message.to_email}")
            return False

        except Exception as e:
            total_time = time.time() - send_start
            error_msg = f"Failed to send email after {total_time:.3f}s: {str(e)}"

            # Classify error type
            error_type = 'unknown'
            if 'authentication' in str(e).lower() or 'auth' in str(e).lower():
                error_type = 'auth_error'
            elif 'refused' in str(e).lower() or 'rejected' in str(e).lower():
                error_type = 'recipient_refused'
            elif 'timeout' in str(e).lower():
                error_type = 'timeout'
            elif 'connection' in str(e).lower():
                error_type = 'connection_error'

            # Update email log with failure
            if email_log_id:
                self._update_email_log_failure(email_log_id, db, error_msg, error_type)

            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[ERROR] {error_msg} to {message.to_email}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

        finally:
            # Always close database session
            db.close()

    async def send_bulk_emails(self, messages: List[EmailMessage]) -> Dict[str, int]:
        """
        Send multiple emails in bulk

        Args:
            messages: List of email messages

        Returns:
            Dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0}

        for message in messages:
            try:
                success = await self.send_email(message)
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                print(f"❌ Bulk email failed: {str(e)}")
                results["failed"] += 1

        return results

    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render HTML email template"""
        try:
            template = self.jinja_env.get_template(f"{template_name}.html")
            return template.render(**data)
        except Exception as e:
            print(f"❌ Template rendering error for {template_name}.html: {str(e)}")
            return self._fallback_template(data)

    def _render_text_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render text email template"""
        try:
            template = self.jinja_env.get_template(f"{template_name}.txt")
            return template.render(**data)
        except Exception as e:
            print(f"❌ Text template rendering error for {template_name}.txt: {str(e)}")
            return self._fallback_text_template(data)

    def _fallback_template(self, data: Dict[str, Any]) -> str:
        """Fallback HTML template if template file not found"""
        return f"""
        <html>
        <body>
            <h2>HR Automation Notification</h2>
            <p>This is an automated notification from the HR Automation System.</p>
            <p>Details:</p>
            <pre>{str(data)}</pre>
            <p><small>Please contact HR if you have any questions.</small></p>
        </body>
        </html>
        """

    def _fallback_text_template(self, data: Dict[str, Any]) -> str:
        """Fallback text template if template file not found"""
        return f"""
HR Automation Notification

This is an automated notification from the HR Automation System.

Details:
{str(data)}

Please contact HR if you have any questions.
        """

    async def close(self):
        """Close SMTP connection"""
        async with self._connection_lock:
            if self._smtp:
                try:
                    print("[EMAIL] Closing SMTP connection")
                    await self._smtp.quit()
                    self._smtp = None
                    self._last_used = None
                    print("[EMAIL] SMTP connection closed")
                except Exception as e:
                    print(f"[EMAIL] Error closing SMTP connection: {e}")
                    self._smtp = None
                    self._last_used = None


class EmailTemplates:
    """Email template definitions and data preparation"""

    @staticmethod
    def leader_approval_request(submission_data: Dict[str, Any], approval_url: str) -> EmailMessage:
        """Create leader approval request email"""
        return EmailMessage(
            to_email=submission_data.get("leader_email", ""),
            to_name=submission_data.get("leader_name", "Team Leader"),
            subject=f"Approval Required: Resignation of {submission_data['employee_name']}",
            template_name="leader_approval",
            template_data={
                "employee_name": submission_data["employee_name"],
                "employee_email": submission_data["employee_email"],
                "submission_date": submission_data.get("submission_date", ""),
                "last_working_day": submission_data.get("last_working_day", ""),
                "approval_url": approval_url,
                "reject_url": approval_url.replace("action=approve", "action=reject"),
                "current_date": datetime.now().strftime("%B %d, %Y")
            }
        )

    @staticmethod
    def chm_approval_request(submission_data: Dict[str, Any], approval_url: str) -> EmailMessage:
        """Create CHM approval request email"""
        return EmailMessage(
            to_email=submission_data.get("chm_email", "youssefkhalifa458@gmail.com"),
            to_name=submission_data.get("chm_name", "Chinese Head"),
            subject=f"CHM Approval Required: Resignation of {submission_data['employee_name']}",
            template_name="chm_approval",
            template_data={
                "employee_name": submission_data["employee_name"],
                "employee_email": submission_data["employee_email"],
                "leader_approved": submission_data.get("leader_approved", True),
                "leader_notes": submission_data.get("leader_notes", ""),
                "submission_date": submission_data.get("submission_date", ""),
                "last_working_day": submission_data.get("last_working_day", ""),
                "approval_url": approval_url,
                "reject_url": approval_url.replace("action=approve", "action=reject"),
                "current_date": datetime.now().strftime("%B %d, %Y")
            }
        )

    @staticmethod
    def hr_notification(submission_data: Dict[str, Any], message_type: str) -> EmailMessage:
        """Create HR notification email"""
        subjects = {
            "chm_approved": f"CHM Approved: Resignation of {submission_data['employee_name']}",
            "chm_rejected": f"CHM Rejected: Resignation of {submission_data['employee_name']}",
            "leader_rejected": f"Leader Rejected: Resignation of {submission_data['employee_name']}",
            "new_submission": f"New Submission: {submission_data['employee_name']}"
        }

        # Import from unified config
        from config import settings

        return EmailMessage(
            to_email=settings.HR_EMAIL,
            to_name="HR Department",
            subject=subjects.get(message_type, "HR Notification: Resignation Update"),
            template_name="hr_notification",
            template_data={
                "employee_name": submission_data["employee_name"],
                "employee_email": submission_data["employee_email"],
                "message_type": message_type,
                "submission_data": submission_data,
                "current_date": datetime.now().strftime("%B %d, %Y")
            }
        )

    # Phase 3: Corrected Exit Interview Email Templates

    @staticmethod
    def exit_interview_scheduled(submission_data: Dict[str, Any]) -> EmailMessage:
        """Create exit interview scheduled notification for employee"""
        return EmailMessage(
            to_email=submission_data["employee_email"],
            to_name=submission_data["employee_name"],
            subject=f"Exit Interview Scheduled - {submission_data['scheduled_date']}",
            template_name="exit_interview_scheduled",
            template_data={
                "employee_name": submission_data["employee_name"],
                "department": submission_data.get("department", "General"),
                "position": submission_data.get("position", "Employee"),
                "scheduled_date": submission_data["scheduled_date"],
                "scheduled_time": submission_data["scheduled_time"],
                "location": submission_data["location"],
                "interviewer": submission_data["interviewer"],
                "last_working_day": submission_data.get("last_working_day", ""),
                "current_date": datetime.now().strftime("%B %d, %Y")
            }
        )

    @staticmethod
    def hr_schedule_interview_reminder(submission_data: Dict[str, Any]) -> EmailMessage:
        """Create reminder for HR to schedule exit interview"""
        # Import from unified config
        from config import settings

        return EmailMessage(
            to_email=settings.HR_EMAIL,
            to_name="HR Department",
            subject=f"Action Required: Schedule Exit Interview for {submission_data['employee_name']}",
            template_name="hr_schedule_interview_reminder",
            template_data={
                "employee_name": submission_data["employee_name"],
                "employee_email": submission_data["employee_email"],
                "department": submission_data.get("department", "General"),
                "position": submission_data.get("position", "Employee"),
                "submission_id": submission_data.get("submission_id", ""),
                "approval_date": submission_data.get("approval_date", ""),
                "last_working_day": submission_data.get("last_working_day", ""),
                "current_date": datetime.now().strftime("%B %d, %Y"),
                "skip_url": submission_data.get("skip_url", None)
            }
        )

    @staticmethod
    def hr_submit_feedback_reminder(submission_data: Dict[str, Any]) -> EmailMessage:
        """Create reminder for HR to submit interview feedback"""
        # Import from unified config
        from config import settings

        return EmailMessage(
            to_email=settings.HR_EMAIL,
            to_name="HR Department",
            subject=f"Action Required: Submit Interview Feedback for {submission_data['employee_name']}",
            template_name="hr_submit_feedback_reminder",
            template_data={
                "employee_name": submission_data["employee_name"],
                "employee_email": submission_data["employee_email"],
                "department": submission_data.get("department", "General"),
                "position": submission_data.get("position", "Employee"),
                "interview_date": submission_data.get("interview_date", ""),
                "interview_time": submission_data.get("interview_time", ""),
                "location": submission_data.get("location", ""),
                "days_overdue": submission_data.get("days_overdue", 0),
                "interview_id": submission_data.get("interview_id", ""),
                "current_date": datetime.now().strftime("%B %d, %Y")
            }
        )

    @staticmethod
    def it_clearance_request(submission_data: Dict[str, Any], clearance_form_url: str = "") -> EmailMessage:
        """Create IT clearance request notification"""
        # Import from unified config
        from config import settings

        return EmailMessage(
            to_email=settings.IT_EMAIL,
            to_name="IT Support Team",
            subject=f"IT Clearance Required: {submission_data['employee_name']}",
            template_name="it_clearance_request",
            template_data={
                "employee_name": submission_data["employee_name"],
                "employee_email": submission_data["employee_email"],
                "department": submission_data.get("department", "General"),
                "position": submission_data.get("position", "Employee"),
                "last_working_day": submission_data.get("last_working_day", ""),
                "submission_id": submission_data.get("submission_id", ""),
                "clearance_form_url": clearance_form_url,
                "current_date": datetime.now().strftime("%B %d, %Y")
            }
        )

    @staticmethod
    def vendor_offboarding_notification(submission_data: Dict[str, Any], vendor_email: str) -> EmailMessage:
        """Create vendor notification for completed offboarding"""
        return EmailMessage(
            to_email=vendor_email,
            to_name="Vendor HR Team",
            subject=f"Employee Offboarding Complete - {submission_data['employee_name']}",
            template_name="vendor_notification",
            template_data={
                "employee_name": submission_data["employee_name"],
                "employee_email": submission_data["employee_email"],
                "department": submission_data.get("department", "General"),
                "position": submission_data.get("position", "Employee"),
                "last_working_day": submission_data.get("last_working_day", ""),
                "submission_id": submission_data.get("submission_id", ""),
                "final_notes": submission_data.get("final_notes", ""),
                "current_date": datetime.now().strftime("%B %d, %Y")
            }
        )

    @staticmethod
    def hr_interview_scheduling_request(submission_data: Dict[str, Any], interview_url: str) -> EmailMessage:
        """Create HR interview scheduling request email with form"""
        # Import from unified config
        from config import settings

        return EmailMessage(
            to_email=settings.HR_EMAIL,
            to_name="HR Department",
            subject=f"Action Required: Schedule Exit Interview for {submission_data['employee_name']}",
            template_name="hr_interview_scheduling_request",
            template_data={
                "employee_name": submission_data["employee_name"],
                "employee_email": submission_data["employee_email"],
                "submission_id": submission_data["submission_id"],
                "last_working_day": submission_data.get("last_working_day", ""),
                "submission_date": submission_data.get("submission_date", ""),
                "leader_notes": submission_data.get("leader_notes", ""),
                "chinese_head_notes": submission_data.get("chinese_head_notes", ""),
                "interview_scheduling_url": interview_url,
                "current_date": datetime.now().strftime("%B %d, %Y")
            }
        )


# Global email service instance
email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the global email service instance"""
    if email_service is None:
        raise RuntimeError("Email service not initialized")
    return email_service


def create_email_service() -> EmailService:
    """Create and configure email service from environment variables"""
    # Import from unified config
    from config import settings

    config = EmailConfig(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASS,
        use_tls=settings.SMTP_USE_TLS,
        from_email=settings.SMTP_FROM_EMAIL,
        from_name=settings.SMTP_FROM_NAME,
        connect_timeout=settings.SMTP_TIMEOUT,
        socket_timeout=settings.SMTP_SOCKET_TIMEOUT
    )

    global email_service
    email_service = EmailService(config)
    return email_service