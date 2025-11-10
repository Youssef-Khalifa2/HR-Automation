"""Improved email service with delivery tracking and verification"""
import os
import aiosmtplib
import asyncio
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid, formataddr
from jinja2 import Environment, FileSystemLoader
from typing import Optional, Dict, Any
from datetime import datetime
import time
import re

from app.services.email import EmailConfig, EmailMessage
from app.services.email_delivery_tracker import EmailDeliveryTracker
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ImprovedEmailService:
    """
    Enhanced email service with comprehensive delivery tracking,
    better error handling, and rate limit protection
    """

    def __init__(self, config: EmailConfig, db_session: AsyncSession):
        self.config = config
        self.db = db_session
        self.tracker = EmailDeliveryTracker(db_session)
        self._smtp = None
        self._last_used = None
        self._send_count = 0
        self._send_window_start = time.time()

        # Rate limiting configuration
        self.max_emails_per_hour = 100  # Adjust based on your Aliyun limit
        self.max_emails_per_minute = 10

        self.jinja_env = Environment(
            loader=FileSystemLoader("app/templates/email"),
            autoescape=True
        )

        logger.info(f"[EMAIL] Improved email service initialized")

    async def send_email(
        self,
        message: EmailMessage,
        submission_id: Optional[int] = None,
        exit_interview_id: Optional[int] = None,
        max_retries: int = 3
    ) -> bool:
        """
        Send email with comprehensive tracking and delivery verification

        Args:
            message: Email message to send
            submission_id: Related submission ID (optional)
            exit_interview_id: Related exit interview ID (optional)
            max_retries: Maximum number of retry attempts

        Returns:
            True if email was sent successfully, False otherwise
        """

        # Step 1: Validate email address
        if not self._validate_email_format(message.to_email):
            logger.error(f"❌ Invalid email format: {message.to_email}")
            return False

        # Step 2: Check rate limits
        if not await self._check_rate_limit():
            logger.warning(f"⚠️ Rate limit reached, queueing email to {message.to_email}")
            # Log as rate limited
            email_log = await self.tracker.log_email_attempt(
                to_email=message.to_email,
                to_name=message.to_name,
                from_email=self.config.from_email,
                subject=message.subject,
                template_name=message.template_name,
                template_data=message.template_data,
                submission_id=submission_id,
                exit_interview_id=exit_interview_id
            )
            await self.tracker.mark_rate_limited(email_log.id, retry_after_seconds=3600)
            return False

        # Step 3: Log email attempt
        email_log = await self.tracker.log_email_attempt(
            to_email=message.to_email,
            to_name=message.to_name,
            from_email=self.config.from_email,
            subject=message.subject,
            template_name=message.template_name,
            template_data=message.template_data,
            submission_id=submission_id,
            exit_interview_id=exit_interview_id
        )

        logger.info(f"[EMAIL #{email_log.id}] Sending to {message.to_email}: {message.subject}")

        # Step 4: Render templates
        try:
            html_content = self._render_template(message.template_name, message.template_data)
            text_content = self._render_text_template(message.template_name, message.template_data)
        except Exception as e:
            error_msg = f"Template rendering failed: {str(e)}"
            logger.error(f"[EMAIL #{email_log.id}] {error_msg}")
            await self.tracker.mark_failed(email_log.id, error_msg, "template_error")
            return False

        # Step 5: Create email message with unique Message-ID
        try:
            email_msg = MIMEMultipart("alternative")
            email_msg["From"] = formataddr((self.config.from_name, self.config.from_email))
            email_msg["To"] = formataddr((message.to_name, message.to_email))
            email_msg["Subject"] = message.subject
            email_msg["Message-ID"] = email_log.message_id

            # Add headers for better deliverability
            email_msg["X-Mailer"] = "HR Automation System v2.0"
            email_msg["X-Priority"] = "3"
            email_msg["Precedence"] = "bulk"
            email_msg["List-Unsubscribe"] = f"<mailto:{self.config.from_email}?subject=unsubscribe>"

            # Attach text and HTML parts
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")

            email_msg.attach(text_part)
            email_msg.attach(html_part)

        except Exception as e:
            error_msg = f"Message construction failed: {str(e)}"
            logger.error(f"[EMAIL #{email_log.id}] {error_msg}")
            await self.tracker.mark_failed(email_log.id, error_msg, "construction_error")
            return False

        # Step 6: Send email with retry logic
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[EMAIL #{email_log.id}] Attempt {attempt}/{max_retries}")

                # Get/create SMTP connection
                smtp = await self._get_smtp_connection()

                # Send email
                send_start = time.time()
                response = await smtp.send_message(email_msg)
                send_duration = time.time() - send_start

                logger.info(f"[EMAIL #{email_log.id}] ✅ SMTP accepted email in {send_duration:.2f}s")
                logger.info(f"[EMAIL #{email_log.id}] SMTP Response: {response}")

                # Mark as sent
                await self.tracker.mark_sent(
                    email_log.id,
                    smtp_response=str(response),
                    message_id=email_log.message_id
                )

                # Update rate limiting counter
                self._update_rate_limit_counter()

                # Success!
                logger.info(f"[EMAIL #{email_log.id}] ✅ Email sent successfully to {message.to_email}")
                return True

            except aiosmtplib.SMTPAuthenticationError as e:
                error_msg = f"SMTP authentication failed: {str(e)}"
                error_type = "auth_error"
                logger.error(f"[EMAIL #{email_log.id}] ❌ {error_msg}")

                # Auth errors are not retriable
                await self.tracker.mark_failed(email_log.id, error_msg, error_type)
                await self._close_smtp_connection()  # Close bad connection
                return False

            except aiosmtplib.SMTPRecipientsRefused as e:
                error_msg = f"Recipient refused: {str(e)}"
                error_type = "recipient_refused"
                logger.error(f"[EMAIL #{email_log.id}] ❌ {error_msg}")

                # Recipient errors are not retriable
                await self.tracker.mark_failed(email_log.id, error_msg, error_type)
                return False

            except aiosmtplib.SMTPDataError as e:
                # Check if it's a rate limit error
                if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                    error_msg = f"Rate limit hit: {str(e)}"
                    error_type = "rate_limit"
                    logger.warning(f"[EMAIL #{email_log.id}] ⚠️ {error_msg}")

                    await self.tracker.mark_rate_limited(email_log.id, retry_after_seconds=3600)
                    return False
                else:
                    error_msg = f"SMTP data error: {str(e)}"
                    error_type = "smtp_data_error"
                    logger.error(f"[EMAIL #{email_log.id}] ❌ {error_msg}")

                    if attempt == max_retries:
                        await self.tracker.mark_failed(email_log.id, error_msg, error_type)
                        return False

            except aiosmtplib.SMTPServerDisconnected as e:
                error_msg = f"Server disconnected: {str(e)}"
                error_type = "server_disconnected"
                logger.warning(f"[EMAIL #{email_log.id}] ⚠️ {error_msg}")

                # Close and retry
                await self._close_smtp_connection()

                if attempt == max_retries:
                    await self.tracker.mark_failed(email_log.id, error_msg, error_type)
                    return False

            except asyncio.TimeoutError as e:
                error_msg = f"Connection timeout: {str(e)}"
                error_type = "timeout"
                logger.error(f"[EMAIL #{email_log.id}] ❌ {error_msg}")

                # Close and retry
                await self._close_smtp_connection()

                if attempt == max_retries:
                    await self.tracker.mark_failed(email_log.id, error_msg, error_type)
                    return False

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                error_type = "unexpected_error"
                logger.error(f"[EMAIL #{email_log.id}] ❌ {error_msg}")
                import traceback
                logger.error(f"[EMAIL #{email_log.id}] Traceback: {traceback.format_exc()}")

                if attempt == max_retries:
                    await self.tracker.mark_failed(email_log.id, error_msg, error_type)
                    return False

            # Wait before retry (exponential backoff)
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.info(f"[EMAIL #{email_log.id}] Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

        # All retries failed
        return False

    def _validate_email_format(self, email: str) -> bool:
        """Validate email format using regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    async def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_time = time.time()

        # Reset counter if window has passed (1 hour)
        if current_time - self._send_window_start > 3600:
            self._send_count = 0
            self._send_window_start = current_time

        # Check hourly limit
        if self._send_count >= self.max_emails_per_hour:
            logger.warning(f"⚠️ Hourly rate limit reached: {self._send_count}/{self.max_emails_per_hour}")
            return False

        return True

    def _update_rate_limit_counter(self):
        """Update rate limiting counter after successful send"""
        self._send_count += 1
        logger.debug(f"[RATE LIMIT] Sent: {self._send_count}/{self.max_emails_per_hour} this hour")

    async def _get_smtp_connection(self):
        """Get or create SMTP connection with connection pooling"""
        # Close stale connections (older than 5 minutes)
        if self._smtp and self._last_used:
            if time.time() - self._last_used > 300:
                logger.info("[SMTP] Closing stale connection")
                await self._close_smtp_connection()

        # Create new connection if needed
        if not self._smtp:
            logger.info(f"[SMTP] Creating new connection to {self.config.host}:{self.config.port}")

            self._smtp = aiosmtplib.SMTP(
                hostname=self.config.host,
                port=self.config.port,
                use_tls=self.config.use_tls,
                timeout=30
            )

            await self._smtp.connect()
            await self._smtp.login(self.config.username, self.config.password)

            logger.info("[SMTP] Connection established and authenticated")

        self._last_used = time.time()
        return self._smtp

    async def _close_smtp_connection(self):
        """Close SMTP connection"""
        if self._smtp:
            try:
                await self._smtp.quit()
            except:
                pass
            finally:
                self._smtp = None
                self._last_used = None
                logger.info("[SMTP] Connection closed")

    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render HTML email template"""
        try:
            template = self.jinja_env.get_template(f"{template_name}.html")
            return template.render(**data)
        except Exception as e:
            logger.error(f"Template rendering error for {template_name}.html: {str(e)}")
            raise

    def _render_text_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render text email template"""
        try:
            template = self.jinja_env.get_template(f"{template_name}.txt")
            return template.render(**data)
        except Exception as e:
            logger.error(f"Text template rendering error for {template_name}.txt: {str(e)}")
            # Fallback to plain text version
            return f"HR Automation Notification\n\nDetails: {str(data)}"

    async def get_delivery_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get delivery report from tracker"""
        return await self.tracker.get_delivery_report(hours=hours)

    async def get_failed_emails(self, hours: int = 24):
        """Get failed emails from tracker"""
        return await self.tracker.get_failed_emails(hours=hours)

    async def retry_pending_emails(self):
        """Retry emails that were rate limited and are ready for retry"""
        pending = await self.tracker.get_pending_retries()

        logger.info(f"[RETRY] Found {len(pending)} emails to retry")

        success_count = 0
        for email_log in pending:
            # Reconstruct email message
            message = EmailMessage(
                to_email=email_log.to_email,
                to_name=email_log.to_name,
                subject=email_log.subject,
                template_name=email_log.template_name,
                template_data=email_log.template_data
            )

            # Retry sending
            success = await self.send_email(
                message,
                submission_id=email_log.submission_id,
                exit_interview_id=email_log.exit_interview_id
            )

            if success:
                success_count += 1

        logger.info(f"[RETRY] Successfully resent {success_count}/{len(pending)} emails")
        return success_count

    async def close(self):
        """Cleanup resources"""
        await self._close_smtp_connection()
