"""Email delivery tracking and verification service"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from email.utils import make_msgid

from app.models.email_log import EmailLog, EmailDeliveryStats

logger = logging.getLogger(__name__)


class EmailDeliveryTracker:
    """Track email delivery status and detect issues"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def log_email_attempt(
        self,
        to_email: str,
        to_name: str,
        from_email: str,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        submission_id: Optional[int] = None,
        exit_interview_id: Optional[int] = None
    ) -> EmailLog:
        """Log a new email sending attempt"""

        # Generate unique message ID for tracking
        message_id = make_msgid(domain=from_email.split('@')[1])

        email_log = EmailLog(
            to_email=to_email,
            to_name=to_name,
            from_email=from_email,
            subject=subject,
            template_name=template_name,
            template_data=template_data,
            status="pending",
            attempts=0,
            message_id=message_id,
            submission_id=submission_id,
            exit_interview_id=exit_interview_id,
            created_at=datetime.utcnow()
        )

        self.db.add(email_log)
        await self.db.commit()
        await self.db.refresh(email_log)

        logger.info(f"📝 Email attempt logged: {email_log.id} -> {to_email}")
        return email_log

    async def mark_sent(
        self,
        email_log_id: int,
        smtp_response: str,
        message_id: Optional[str] = None
    ) -> bool:
        """Mark email as sent successfully by SMTP"""
        result = await self.db.execute(
            select(EmailLog).where(EmailLog.id == email_log_id)
        )
        email_log = result.scalar_one_or_none()

        if not email_log:
            logger.error(f"❌ Email log {email_log_id} not found")
            return False

        email_log.status = "sent"
        email_log.sent_at = datetime.utcnow()
        email_log.last_attempt_at = datetime.utcnow()
        email_log.attempts += 1
        email_log.smtp_response = smtp_response

        if message_id:
            email_log.message_id = message_id

        await self.db.commit()

        logger.info(f"✅ Email {email_log_id} marked as sent: {email_log.to_email}")
        return True

    async def mark_failed(
        self,
        email_log_id: int,
        error_message: str,
        error_type: str
    ) -> bool:
        """Mark email as failed"""
        result = await self.db.execute(
            select(EmailLog).where(EmailLog.id == email_log_id)
        )
        email_log = result.scalar_one_or_none()

        if not email_log:
            logger.error(f"❌ Email log {email_log_id} not found")
            return False

        email_log.status = "failed"
        email_log.failed_at = datetime.utcnow()
        email_log.last_attempt_at = datetime.utcnow()
        email_log.attempts += 1
        email_log.error_message = error_message
        email_log.error_type = error_type

        await self.db.commit()

        logger.error(f"❌ Email {email_log_id} marked as failed: {error_type}")
        return True

    async def mark_bounced(
        self,
        email_log_id: int,
        bounce_reason: str
    ) -> bool:
        """Mark email as bounced"""
        result = await self.db.execute(
            select(EmailLog).where(EmailLog.id == email_log_id)
        )
        email_log = result.scalar_one_or_none()

        if not email_log:
            logger.error(f"❌ Email log {email_log_id} not found")
            return False

        email_log.status = "bounced"
        email_log.bounce_detected = True
        email_log.bounce_reason = bounce_reason
        email_log.failed_at = datetime.utcnow()

        await self.db.commit()

        logger.warning(f"⚠️ Email {email_log_id} bounced: {bounce_reason}")
        return True

    async def mark_rate_limited(
        self,
        email_log_id: int,
        retry_after_seconds: int = 3600
    ) -> bool:
        """Mark email as rate limited"""
        result = await self.db.execute(
            select(EmailLog).where(EmailLog.id == email_log_id)
        )
        email_log = result.scalar_one_or_none()

        if not email_log:
            logger.error(f"❌ Email log {email_log_id} not found")
            return False

        email_log.status = "rate_limited"
        email_log.rate_limit_hit = True
        email_log.retry_after = datetime.utcnow() + timedelta(seconds=retry_after_seconds)
        email_log.last_attempt_at = datetime.utcnow()
        email_log.attempts += 1

        await self.db.commit()

        logger.warning(f"⚠️ Email {email_log_id} rate limited, retry after: {email_log.retry_after}")
        return True

    async def get_failed_emails(
        self,
        hours: int = 24
    ) -> List[EmailLog]:
        """Get all failed emails in the last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours)

        result = await self.db.execute(
            select(EmailLog)
            .where(
                and_(
                    EmailLog.status.in_(["failed", "bounced"]),
                    EmailLog.created_at >= since
                )
            )
            .order_by(EmailLog.created_at.desc())
        )

        return result.scalars().all()

    async def get_pending_retries(self) -> List[EmailLog]:
        """Get emails that should be retried"""
        now = datetime.utcnow()

        result = await self.db.execute(
            select(EmailLog)
            .where(
                and_(
                    EmailLog.status == "rate_limited",
                    EmailLog.retry_after <= now,
                    EmailLog.attempts < 5  # Max 5 attempts
                )
            )
            .order_by(EmailLog.retry_after)
        )

        return result.scalars().all()

    async def get_delivery_report(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get delivery statistics for the last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours)

        # Count by status
        result = await self.db.execute(
            select(
                EmailLog.status,
                func.count(EmailLog.id).label('count')
            )
            .where(EmailLog.created_at >= since)
            .group_by(EmailLog.status)
        )

        status_counts = {row.status: row.count for row in result}

        # Count by error type
        result = await self.db.execute(
            select(
                EmailLog.error_type,
                func.count(EmailLog.id).label('count')
            )
            .where(
                and_(
                    EmailLog.created_at >= since,
                    EmailLog.error_type.isnot(None)
                )
            )
            .group_by(EmailLog.error_type)
        )

        error_counts = {row.error_type: row.count for row in result}

        # Count by template
        result = await self.db.execute(
            select(
                EmailLog.template_name,
                EmailLog.status,
                func.count(EmailLog.id).label('count')
            )
            .where(EmailLog.created_at >= since)
            .group_by(EmailLog.template_name, EmailLog.status)
        )

        template_stats = {}
        for row in result:
            if row.template_name not in template_stats:
                template_stats[row.template_name] = {}
            template_stats[row.template_name][row.status] = row.count

        total = sum(status_counts.values())
        success_rate = (
            (status_counts.get('sent', 0) + status_counts.get('delivered', 0)) / total * 100
            if total > 0 else 0
        )

        return {
            "period_hours": hours,
            "total_emails": total,
            "success_rate": round(success_rate, 2),
            "status_counts": status_counts,
            "error_counts": error_counts,
            "template_stats": template_stats,
            "generated_at": datetime.utcnow().isoformat()
        }

    async def get_suspicious_failures(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Identify suspicious patterns that indicate silent failures:
        - Emails marked as 'sent' but very old (likely never delivered)
        - Multiple failures to same domain
        - Sudden spike in failures
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        suspicious = []

        # Check for old "sent" emails (likely silent failures)
        old_sent_threshold = datetime.utcnow() - timedelta(hours=2)
        result = await self.db.execute(
            select(EmailLog)
            .where(
                and_(
                    EmailLog.status == "sent",
                    EmailLog.sent_at < old_sent_threshold,
                    EmailLog.delivered_at.is_(None)
                )
            )
        )

        old_sent = result.scalars().all()
        if old_sent:
            suspicious.append({
                "type": "likely_silent_failure",
                "count": len(old_sent),
                "description": f"{len(old_sent)} emails marked as 'sent' but no delivery confirmation after 2+ hours",
                "emails": [{"id": e.id, "to": e.to_email, "subject": e.subject} for e in old_sent[:5]]
            })

        # Check for repeated failures to same domain
        result = await self.db.execute(
            select(
                func.split_part(EmailLog.to_email, '@', 2).label('domain'),
                func.count(EmailLog.id).label('count')
            )
            .where(
                and_(
                    EmailLog.created_at >= since,
                    EmailLog.status.in_(["failed", "bounced"])
                )
            )
            .group_by(func.split_part(EmailLog.to_email, '@', 2))
            .having(func.count(EmailLog.id) > 2)
        )

        domain_failures = [(row.domain, row.count) for row in result]
        if domain_failures:
            suspicious.append({
                "type": "domain_blocking",
                "description": "Multiple failures to same domains (possible blocking)",
                "domains": domain_failures
            })

        return suspicious


async def create_daily_stats(db: AsyncSession):
    """Create daily email statistics summary"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Get all emails from today
    result = await db.execute(
        select(EmailLog).where(EmailLog.created_at >= today)
    )

    emails = result.scalars().all()

    # Calculate stats
    total_sent = sum(1 for e in emails if e.status in ["sent", "delivered"])
    total_delivered = sum(1 for e in emails if e.status == "delivered")
    total_bounced = sum(1 for e in emails if e.status == "bounced")
    total_failed = sum(1 for e in emails if e.status == "failed")
    rate_limits_hit = sum(1 for e in emails if e.rate_limit_hit)

    # Template counts
    template_counts = {}
    for email in emails:
        template_counts[email.template_name] = template_counts.get(email.template_name, 0) + 1

    # Error types
    error_types = {}
    for email in emails:
        if email.error_type:
            error_types[email.error_type] = error_types.get(email.error_type, 0) + 1

    stats = EmailDeliveryStats(
        date=today,
        total_sent=total_sent,
        total_delivered=total_delivered,
        total_bounced=total_bounced,
        total_failed=total_failed,
        rate_limits_hit=rate_limits_hit,
        template_counts=template_counts,
        error_types=error_types
    )

    db.add(stats)
    await db.commit()

    logger.info(f"📊 Daily stats created: {total_sent} sent, {total_failed} failed")
    return stats
