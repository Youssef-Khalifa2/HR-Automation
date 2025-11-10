"""Synchronous email delivery tracking service"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from app.models.email_log import EmailLog, EmailDeliveryStats

logger = logging.getLogger(__name__)


class EmailDeliveryTrackerSync:
    """Synchronous tracker for email delivery status"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_delivery_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get delivery statistics for the last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours)

        # Count by status
        status_query = self.db.query(
            EmailLog.status,
            func.count(EmailLog.id).label('count')
        ).filter(
            EmailLog.created_at >= since
        ).group_by(EmailLog.status)

        status_counts = {row.status or 'unknown': row.count for row in status_query.all()}

        # Count by error type
        error_query = self.db.query(
            EmailLog.error_type,
            func.count(EmailLog.id).label('count')
        ).filter(
            and_(
                EmailLog.created_at >= since,
                EmailLog.error_type.isnot(None)
            )
        ).group_by(EmailLog.error_type)

        error_counts = {row.error_type: row.count for row in error_query.all()}

        # Count by template
        template_query = self.db.query(
            EmailLog.template_name,
            func.count(EmailLog.id).label('count')
        ).filter(
            EmailLog.created_at >= since
        ).group_by(EmailLog.template_name)

        template_stats = {row.template_name or 'unknown': row.count for row in template_query.all()}

        # Calculate totals
        total_emails = sum(status_counts.values())
        total_sent = status_counts.get('sent', 0)
        total_failed = status_counts.get('failed', 0)

        success_rate = (total_sent / total_emails * 100) if total_emails > 0 else 0

        return {
            "period_hours": hours,
            "total_emails": total_emails,
            "success_rate": round(success_rate, 2),
            "status_counts": status_counts,
            "error_counts": error_counts,
            "template_stats": template_stats,
            "generated_at": datetime.utcnow().isoformat()
        }

    def get_failed_emails(self, hours: int = 24) -> List[EmailLog]:
        """Get all failed emails in the last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours)

        failed = self.db.query(EmailLog).filter(
            and_(
                EmailLog.created_at >= since,
                EmailLog.status == 'failed'
            )
        ).order_by(EmailLog.created_at.desc()).all()

        return failed

    def get_suspicious_failures(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Identify suspicious patterns indicating silent failures"""
        since = datetime.utcnow() - timedelta(hours=hours)

        # Find emails that appear sent but might have failed silently
        suspicious = self.db.query(EmailLog).filter(
            and_(
                EmailLog.created_at >= since,
                EmailLog.status == 'sent',
                EmailLog.smtp_response.like('%queued%')  # Example: queued but not delivered
            )
        ).all()

        return [
            {
                "id": email.id,
                "to_email": email.to_email,
                "subject": email.subject,
                "created_at": email.created_at.isoformat() if email.created_at else None,
                "smtp_response": email.smtp_response,
                "reason": "Queued but no delivery confirmation"
            }
            for email in suspicious
        ]

    def get_email_stats_24h(self) -> Dict[str, int]:
        """Quick stats for last 24 hours"""
        since_24h = datetime.utcnow() - timedelta(hours=24)

        total_sent = self.db.query(func.count(EmailLog.id)).filter(
            and_(
                EmailLog.created_at >= since_24h,
                EmailLog.status == 'sent'
            )
        ).scalar() or 0

        total_failed = self.db.query(func.count(EmailLog.id)).filter(
            and_(
                EmailLog.created_at >= since_24h,
                EmailLog.status == 'failed'
            )
        ).scalar() or 0

        pending = self.db.query(func.count(EmailLog.id)).filter(
            and_(
                EmailLog.created_at >= since_24h,
                EmailLog.status == 'pending'
            )
        ).scalar() or 0

        rate_limits = self.db.query(func.count(EmailLog.id)).filter(
            and_(
                EmailLog.created_at >= since_24h,
                EmailLog.error_type == 'rate_limit'
            )
        ).scalar() or 0

        return {
            "total_sent_24h": total_sent,
            "total_failed_24h": total_failed,
            "pending_24h": pending,
            "rate_limits_hit_24h": rate_limits,
            "suspicious_failures": 0  # Simplified for now
        }
