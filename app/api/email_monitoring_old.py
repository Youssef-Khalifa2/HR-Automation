"""API endpoints for email delivery monitoring and management"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from typing import Optional, List
from datetime import datetime, timedelta

from app.database import get_db
from app.core.auth import get_current_hr_user  # Only used for retry endpoint
from app.models.email_log import EmailLog, EmailDeliveryStats
from app.services.email_tracker_sync import EmailDeliveryTrackerSync
from pydantic import BaseModel

router = APIRouter()


class EmailLogResponse(BaseModel):
    id: int
    to_email: str
    to_name: Optional[str]
    subject: Optional[str]
    template_name: Optional[str]
    status: Optional[str]
    attempts: int
    created_at: datetime
    sent_at: Optional[datetime]
    failed_at: Optional[datetime]
    error_type: Optional[str]
    error_message: Optional[str]
    smtp_response: Optional[str]
    submission_id: Optional[int]
    exit_interview_id: Optional[int]

    class Config:
        from_attributes = True


class DeliveryReportResponse(BaseModel):
    period_hours: int
    total_emails: int
    success_rate: float
    status_counts: dict
    error_counts: dict
    template_stats: dict
    generated_at: str


class EmailStatsResponse(BaseModel):
    total_sent_24h: int
    total_failed_24h: int
    total_pending_retry: int
    success_rate_24h: float
    rate_limits_hit_24h: int
    suspicious_failures: int


@router.get("/email-logs", response_model=List[EmailLogResponse])
def get_email_logs(
    status: Optional[str] = Query(None, description="Filter by status"),
    hours: int = Query(24, description="Hours to look back"),
    limit: int = Query(50, description="Max results to return"),
    db: Session = Depends(get_db)
):
    """Get email logs with optional filtering"""

    since = datetime.utcnow() - timedelta(hours=hours)

    query = db.query(EmailLog).filter(EmailLog.created_at >= since)

    if status:
        query = query.filter(EmailLog.status == status)

    logs = query.order_by(EmailLog.created_at.desc()).limit(limit).all()

    return [EmailLogResponse.from_orm(log) for log in logs]


@router.get("/email-logs/{log_id}", response_model=EmailLogResponse)
def get_email_log_detail(
    log_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific email log"""

    log = db.query(EmailLog).filter(EmailLog.id == log_id).first()

    if not log:
        raise HTTPException(status_code=404, detail="Email log not found")

    return EmailLogResponse.from_orm(log)


@router.get("/delivery-report", response_model=DeliveryReportResponse)
def get_delivery_report(
    hours: int = Query(24, description="Hours to analyze"),
    db: Session = Depends(get_db)
):
    """Get comprehensive delivery report"""

    tracker = EmailDeliveryTrackerSync(db)
    report = tracker.get_delivery_report(hours=hours)

    return DeliveryReportResponse(**report)


@router.get("/email-stats", response_model=EmailStatsResponse)
async def get_email_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get quick email statistics for dashboard"""

    since_24h = datetime.utcnow() - timedelta(hours=24)

    # Total sent in last 24 hours
    result = await db.execute(
        select(func.count(EmailLog.id))
        .where(
            and_(
                EmailLog.created_at >= since_24h,
                EmailLog.status.in_(["sent", "delivered"])
            )
        )
    )
    total_sent = result.scalar() or 0

    # Total failed in last 24 hours
    result = await db.execute(
        select(func.count(EmailLog.id))
        .where(
            and_(
                EmailLog.created_at >= since_24h,
                EmailLog.status.in_(["failed", "bounced"])
            )
        )
    )
    total_failed = result.scalar() or 0

    # Pending retry
    result = await db.execute(
        select(func.count(EmailLog.id))
        .where(
            and_(
                EmailLog.status == "rate_limited",
                EmailLog.retry_after <= datetime.utcnow(),
                EmailLog.attempts < 5
            )
        )
    )
    total_pending_retry = result.scalar() or 0

    # Rate limits hit
    result = await db.execute(
        select(func.count(EmailLog.id))
        .where(
            and_(
                EmailLog.created_at >= since_24h,
                EmailLog.rate_limit_hit == True
            )
        )
    )
    rate_limits_hit = result.scalar() or 0

    # Suspicious failures (emails marked sent but no delivery confirmation after 2+ hours)
    old_sent_threshold = datetime.utcnow() - timedelta(hours=2)
    result = await db.execute(
        select(func.count(EmailLog.id))
        .where(
            and_(
                EmailLog.status == "sent",
                EmailLog.sent_at < old_sent_threshold,
                EmailLog.delivered_at.is_(None)
            )
        )
    )
    suspicious_failures = result.scalar() or 0

    # Calculate success rate
    total = total_sent + total_failed
    success_rate = (total_sent / total * 100) if total > 0 else 0

    return EmailStatsResponse(
        total_sent_24h=total_sent,
        total_failed_24h=total_failed,
        total_pending_retry=total_pending_retry,
        success_rate_24h=round(success_rate, 2),
        rate_limits_hit_24h=rate_limits_hit,
        suspicious_failures=suspicious_failures
    )


@router.get("/failed-emails")
async def get_failed_emails(
    hours: int = Query(24, description="Hours to look back"),
    db: AsyncSession = Depends(get_db)
):
    """Get all failed emails with details"""

    tracker = EmailDeliveryTracker(db)
    failed = await tracker.get_failed_emails(hours=hours)

    return [
        {
            "id": email.id,
            "to_email": email.to_email,
            "subject": email.subject,
            "template_name": email.template_name,
            "error_type": email.error_type,
            "error_message": email.error_message,
            "attempts": email.attempts,
            "created_at": email.created_at.isoformat(),
            "failed_at": email.failed_at.isoformat() if email.failed_at else None,
            "submission_id": email.submission_id,
            "exit_interview_id": email.exit_interview_id
        }
        for email in failed
    ]


@router.get("/suspicious-failures")
async def get_suspicious_failures(
    hours: int = Query(24, description="Hours to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """Identify suspicious patterns that indicate silent failures"""

    tracker = EmailDeliveryTracker(db)
    suspicious = await tracker.get_suspicious_failures(hours=hours)

    return {
        "total_suspicious": len(suspicious),
        "patterns": suspicious,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.post("/retry-failed-emails")
async def retry_failed_emails(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_hr_user)
):
    """
    Retry all emails that were rate limited and are ready for retry

    This should typically be called by a scheduled job, not manually
    """

    from app.services.improved_email_service import ImprovedEmailService
    from app.services.email import create_email_service
    from config import settings

    # Create email service
    config = create_email_service().config
    email_service = ImprovedEmailService(config, db)

    # Retry pending emails
    success_count = await email_service.retry_pending_emails()

    return {
        "message": f"Retried {success_count} emails successfully",
        "success_count": success_count
    }


@router.get("/email-health")
def get_email_health(
    db: Session = Depends(get_db)
):
    """
    Get overall email system health status
    Returns warnings if there are issues
    """

    try:
        # Check if tables exist first
        db.query(EmailLog).limit(1).first()
    except Exception as e:
        return {
            "status": "warning",
            "message": "Email tracking tables not created yet",
            "instructions": "Run: python run_email_tracking_setup.py",
            "error": str(e)
        }

    tracker = EmailDeliveryTrackerSync(db)

    # Get recent stats
    report = tracker.get_delivery_report(hours=1)
    suspicious = tracker.get_suspicious_failures(hours=24)

    # Calculate health metrics
    health_status = "healthy"
    warnings = []
    errors = []

    # Check success rate
    if report["success_rate"] < 80:
        health_status = "degraded"
        warnings.append(f"Low success rate: {report['success_rate']}%")

    if report["success_rate"] < 50:
        health_status = "critical"
        errors.append(f"Critical: Success rate below 50% ({report['success_rate']}%)")

    # Check for suspicious failures
    if suspicious:
        for pattern in suspicious:
            if pattern["type"] == "likely_silent_failure":
                health_status = "degraded"
                warnings.append(f"Detected {pattern['count']} likely silent failures")

    # Check for rate limiting
    rate_limit_count = report["status_counts"].get("rate_limited", 0)
    if rate_limit_count > 10:
        health_status = "degraded"
        warnings.append(f"High rate limiting: {rate_limit_count} emails queued")

    # Check for authentication errors
    auth_errors = report["error_counts"].get("auth_error", 0)
    if auth_errors > 0:
        health_status = "critical"
        errors.append(f"SMTP authentication failures detected: {auth_errors}")

    return {
        "status": health_status,
        "timestamp": datetime.utcnow().isoformat(),
        "success_rate_1h": report["success_rate"],
        "total_emails_1h": report["total_emails"],
        "warnings": warnings,
        "errors": errors,
        "suspicious_patterns": len(suspicious)
    }
