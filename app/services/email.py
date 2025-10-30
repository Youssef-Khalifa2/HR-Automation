"""Email service for sending notifications and approval requests"""
import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from dataclasses import dataclass


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


@dataclass
class EmailMessage:
    """Email message data"""
    to_email: str
    to_name: str
    subject: str
    template_name: str
    template_data: Dict[str, Any]


class EmailService:
    """Email service for sending notifications"""

    def __init__(self, config: EmailConfig):
        self.config = config
        self.smtp = aiosmtplib.SMTP(
            hostname=config.host,
            port=config.port,
            use_tls=config.use_tls
        )
        self.jinja_env = Environment(
            loader=FileSystemLoader("app/templates/email"),
            autoescape=True
        )

    async def send_email(self, message: EmailMessage) -> bool:
        """
        Send an email using configured SMTP

        Args:
            message: Email message to send

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Render email template
            html_content = self._render_template(message.template_name, message.template_data)
            text_content = self._render_text_template(message.template_name, message.template_data)

            # Create email message
            email_msg = MIMEMultipart("alternative")
            email_msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            email_msg["To"] = f"{message.to_name} <{message.to_email}>"
            email_msg["Subject"] = message.subject

            # Attach HTML and text parts
            html_part = MIMEText(html_content, "html", "utf-8")
            text_part = MIMEText(text_content, "plain", "utf-8")

            email_msg.attach(text_part)
            email_msg.attach(html_part)

            # Connect and send
            await self.smtp.connect()
            await self.smtp.login(self.config.username, self.config.password)
            await self.smtp.send_message(email_msg)

            print(f"✅ Email sent to {message.to_email}: {message.subject}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email to {message.to_email}: {str(e)}")
            return False

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
        try:
            await self.smtp.quit()
        except:
            pass


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
            to_email=submission_data.get("chm_email", ""),
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

        return EmailMessage(
            to_email=os.getenv("HR_EMAIL", "hr@company.com"),
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
        from_name=settings.SMTP_FROM_NAME
    )

    global email_service
    email_service = EmailService(config)
    return email_service