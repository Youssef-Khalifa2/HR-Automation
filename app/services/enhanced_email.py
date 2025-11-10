"""Enhanced Email Service with Debugging and Error Recovery"""
import os
import aiosmtplib
import smtplib
import ssl
import socket
import dns.resolver
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from email.utils import formataddr
import traceback

logger = logging.getLogger(__name__)


class EmailDebugger:
    """Email debugging and validation utilities"""

    @staticmethod
    def test_smtp_connection(config) -> Tuple[bool, str]:
        """Test SMTP connection with detailed diagnostics"""
        try:
            logger.info(f"🔧 Testing SMTP connection to {config.host}:{config.port}")

            # Test DNS resolution
            try:
                socket.gethostbyname(config.host)
                logger.info(f"✅ DNS resolution successful for {config.host}")
            except socket.gaierror as e:
                return False, f"DNS resolution failed: {e}"

            # Test SMTP connection
            context = ssl.create_default_context()

            with smtplib.SMTP_SSL(config.host, config.port, context=context, timeout=30) as server:
                server.set_debuglevel(1)  # Enable debug output
                logger.info("🔧 SMTP SSL connection established")

                # Test authentication
                try:
                    server.login(config.username, config.password)
                    logger.info(f"✅ SMTP authentication successful for {config.username}")

                    # Test sending a test email
                    test_msg = MIMEMultipart()
                    test_msg['From'] = formataddr((config.from_name, config.from_email))
                    test_msg['To'] = formataddr(("Test", config.from_email))
                    test_msg['Subject'] = f"Email Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                    body = f"""
This is a test email to verify SMTP configuration.

Test Details:
- SMTP Host: {config.host}:{config.port}
- From: {config.from_email}
- Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- TLS: {config.use_tls}

If you receive this email, SMTP configuration is working correctly.
                    """

                    test_msg.attach(MIMEText(body, 'plain'))

                    server.send_message(test_msg)
                    logger.info("✅ Test email sent successfully")
                    return True, "All tests passed"

                except smtplib.SMTPAuthenticationError as e:
                    return False, f"SMTP authentication failed: {e}"
                except smtplib.SMTPRecipientsRefused as e:
                    return False, f"Recipient refused: {e}"
                except Exception as e:
                    return False, f"Email sending failed: {e}"

        except smtplib.SMTPConnectError as e:
            return False, f"SMTP connection failed: {e}"
        except ssl.SSLError as e:
            return False, f"SSL/TLS error: {e}"
        except socket.timeout as e:
            return False, f"Connection timeout: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    @staticmethod
    def check_email_format(email: str) -> Tuple[bool, str]:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, f"Invalid email format: {email}"
        return True, "Email format is valid"

    @staticmethod
    def check_domain_mx_record(email: str) -> Tuple[bool, str]:
        """Check if domain has MX records"""
        try:
            domain = email.split('@')[1]
            records = dns.resolver.resolve(domain, 'MX')
            logger.info(f"✅ MX records found for {domain}: {[str(r) for r in records]}")
            return True, f"MX records found for {domain}"
        except dns.resolver.NoAnswer:
            return False, f"No MX records found for {domain}"
        except Exception as e:
            return False, f"MX record check failed: {e}"


class EnhancedEmailService:
    """Enhanced email service with debugging and error recovery"""

    def __init__(self, config):
        self.config = config
        self.jinja_env = Environment(
            loader=FileSystemLoader("app/templates/email"),
            autoescape=True
        )
        self.debugger = EmailDebugger()
        self.email_queue = []
        self.failed_emails = []

    async def send_email_with_debugging(self, message, max_retries=3):
        """Send email with comprehensive debugging and retry logic"""

        # Validate email format
        email_valid, email_msg = self.debugger.check_email_format(message.to_email)
        if not email_valid:
            logger.error(f"❌ Invalid email format: {message.to_email}")
            return False

        # Check MX records
        mx_valid, mx_msg = self.debugger.check_domain_mx_record(message.to_email)
        if not mx_valid:
            logger.warning(f"⚠️ {mx_msg}")

        logger.info(f"📧 Preparing to send email to {message.to_email}")
        logger.info(f"📧 Subject: {message.subject}")
        logger.info(f"📧 Template: {message.template_name}")

        # Render email content
        try:
            html_content = self._render_template(message.template_name, message.template_data)
            text_content = self._render_text_template(message.template_name, message.template_data)
            logger.info(f"📧 Templates rendered successfully")
        except Exception as e:
            logger.error(f"❌ Template rendering failed: {e}")
            logger.error(f"❌ Template data: {message.template_data}")
            return False

        # Create email message
        try:
            email_msg = MIMEMultipart("alternative")
            email_msg["From"] = formataddr((self.config.from_name, self.config.from_email))
            email_msg["To"] = formataddr((message.to_name, message.to_email))
            email_msg["Subject"] = message.subject

            # Add headers for debugging
            email_msg["X-Mailer"] = "HR Automation System"
            email_msg["X-Priority"] = "3"  # Normal priority

            # Attach HTML and text parts
            html_part = MIMEText(html_content, "html", "utf-8")
            text_part = MIMEText(text_content, "plain", "utf-8")

            email_msg.attach(text_part)
            email_msg.attach(html_part)

            logger.info(f"📧 Email message constructed successfully")

        except Exception as e:
            logger.error(f"❌ Email message construction failed: {e}")
            return False

        # Send email with retry logic
        for attempt in range(max_retries):
            try:
                logger.info(f"📧 Attempt {attempt + 1}/{max_retries} to send email")

                # Create SMTP connection
                context = ssl.create_default_context()
                context.check_hostname = False  # Skip hostname check for testing
                context.verify_mode = ssl.CERT_NONE  # Skip certificate verification for testing

                with aiosmtplib.SMTP(
                    hostname=self.config.host,
                    port=self.config.port,
                    use_tls=self.config.use_tls,
                    timeout=30,
                    start_tls=self.config.use_tls,
                    tls_context=context
                ) as smtp:

                    logger.info(f"📧 Connecting to SMTP server {self.config.host}:{self.config.port}")

                    # Login
                    await smtp.login(self.config.username, self.config.password)
                    logger.info(f"📧 SMTP login successful")

                    # Send email
                    response = await smtp.send_message(email_msg)
                    logger.info(f"📧 Email sent successfully! Server response: {response}")

                    # Log success
                    logger.info(f"✅ Email sent successfully to {message.to_email}")

                    # Store in success queue
                    self.email_queue.append({
                        "to": message.to_email,
                        "subject": message.subject,
                        "sent_at": datetime.now(),
                        "status": "sent"
                    })

                    return True

            except aiosmtplib.SMTPAuthenticationError as e:
                logger.error(f"❌ SMTP Authentication Error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    self._log_failure(message, f"Authentication failed: {e}")

            except aiosmtplib.SMTPRecipientsRefused as e:
                logger.error(f"❌ Recipient Refused (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    self._log_failure(message, f"Recipient refused: {e}")

            except aiosmtplib.SMTPServerDisconnected as e:
                logger.error(f"❌ Server Disconnected (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self._log_failure(message, f"Server disconnected: {e}")

            except Exception as e:
                logger.error(f"❌ Unexpected Error (attempt {attempt + 1}): {e}")
                logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                if attempt == max_retries - 1:
                    self._log_failure(message, f"Unexpected error: {e}")

            # Wait before retry (except last attempt)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"📧 Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)

        return False

    def _log_failure(self, message, error_msg):
        """Log failed email for debugging"""
        failure_record = {
            "to": message.to_email,
            "subject": message.subject,
            "template": message.template_name,
            "failed_at": datetime.now(),
            "error": error_msg,
            "data": message.template_data
        }

        self.failed_emails.append(failure_record)

        logger.error(f"❌ EMAIL FAILED - Details:")
        logger.error(f"   To: {message.to_email}")
        logger.error(f"   Subject: {message.subject}")
        logger.error(f"   Template: {message.template_name}")
        logger.error(f"   Error: {error_msg}")
        logger.error(f"   Data: {message.template_data}")

        # Save to file for later analysis
        self._save_failure_to_file(failure_record)

    def _save_failure_to_file(self, failure_record):
        """Save failed email record to file"""
        try:
            import json
            with open("email_failures.json", "a") as f:
                json.dump(failure_record, f, default=str)
                f.write("\n")
        except Exception as e:
            logger.error(f"Failed to save failure record: {e}")

    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render HTML email template"""
        try:
            template = self.jinja_env.get_template(f"{template_name}.html")
            return template.render(**data)
        except Exception as e:
            logger.error(f"Template rendering error for {template_name}.html: {str(e)}")
            return self._fallback_template(data)

    def _render_text_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render text email template"""
        try:
            template = self.jinja_env.get_template(f"{template_name}.txt")
            return template.render(**data)
        except Exception as e:
            logger.error(f"Text template rendering error for {template_name}.txt: {str(e)}")
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

    def get_failure_report(self) -> str:
        """Get detailed report of failed emails"""
        if not self.failed_emails:
            return "No failed emails recorded."

        report = "EMAIL FAILURE REPORT\n"
        report += "=" * 50 + "\n"
        report += f"Total Failed: {len(self.failed_emails)}\n\n"

        for i, failure in enumerate(self.failed_emails, 1):
            report += f"FAILURE #{i}:\n"
            report += f"  Time: {failure['failed_at']}\n"
            report += f"  To: {failure['to']}\n"
            report += f"  Subject: {failure['subject']}\n"
            report += f"  Template: {failure['template']}\n"
            report += f"  Error: {failure['error']}\n"
            report += "-" * 30 + "\n"

        return report

    def test_email_configuration(self) -> bool:
        """Test the email configuration"""
        return self.debugger.test_smtp_connection(self.config)[0]


# Test function for email debugging
async def test_email_system():
    """Test the email system with detailed logging"""
    from config import settings
    from app.services.email import EmailConfig

    # Create email config
    config = EmailConfig(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASS,
        use_tls=settings.SMTP_USE_TLS,
        from_email=settings.SMTP_FROM_EMAIL,
        from_name=settings.SMTP_FROM_NAME
    )

    # Create enhanced service
    service = EnhancedEmailService(config)

    # Test configuration
    if service.test_email_configuration():
        logger.info("✅ Email configuration test passed")

        # Send test email
        from app.services.enhanced_email import EmailMessage

        test_msg = EmailMessage(
            to_email=settings.SMTP_FROM_EMAIL,
            to_name="Test User",
            subject="Email System Test",
            template_name="test",
            template_data={"test": "data"}
        )

        success = await service.send_email_with_debugging(test_msg)

        if success:
            logger.info("✅ Test email sent successfully")
            logger.info(f"📊 Check your inbox at: {settings.SMTP_FROM_EMAIL}")
        else:
            logger.error("❌ Test email failed")
            logger.error(service.get_failure_report())

        return success
    else:
        logger.error("❌ Email configuration test failed")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_email_system())