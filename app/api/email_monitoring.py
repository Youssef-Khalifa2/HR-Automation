"""Simplified synchronous email monitoring endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from app.database import get_db
from app.models.email_log import EmailLog
from app.services.email_tracker_sync import EmailDeliveryTrackerSync
from pydantic import BaseModel

router = APIRouter()


class EmailLogResponse(BaseModel):
    id: int
    to_email: str
    subject: Optional[str]
    template_name: Optional[str]
    status: Optional[str]
    attempts: int
    created_at: datetime
    error_type: Optional[str]
    error_message: Optional[str]

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
    pending_24h: int
    rate_limits_hit_24h: int
    suspicious_failures: int


@router.get("/email-health")
def get_email_health(db: Session = Depends(get_db)):
    """Check email system health"""
    try:
        # Check if tables exist
        db.query(EmailLog).limit(1).first()

        tracker = EmailDeliveryTrackerSync(db)
        report = tracker.get_delivery_report(hours=1)

        health_status = "healthy"
        warnings = []

        if report["success_rate"] < 80:
            health_status = "degraded"
            warnings.append(f"Low success rate: {report['success_rate']}%")

        if report["success_rate"] < 50:
            health_status = "critical"

        return {
            "status": health_status,
            "success_rate_last_hour": report["success_rate"],
            "total_emails_last_hour": report["total_emails"],
            "warnings": warnings,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Email monitoring tables not available",
            "error": str(e)
        }


@router.get("/delivery-report")
def get_delivery_report(
    hours: int = Query(24, description="Hours to analyze"),
    db: Session = Depends(get_db)
):
    """Get comprehensive delivery report"""
    tracker = EmailDeliveryTrackerSync(db)
    return tracker.get_delivery_report(hours=hours)


@router.get("/email-stats")
def get_email_stats(db: Session = Depends(get_db)):
    """Get quick email statistics"""
    tracker = EmailDeliveryTrackerSync(db)
    return tracker.get_email_stats_24h()


@router.get("/failed-emails")
def get_failed_emails(
    hours: int = Query(24, description="Hours to look back"),
    db: Session = Depends(get_db)
):
    """Get all failed emails"""
    tracker = EmailDeliveryTrackerSync(db)
    failed = tracker.get_failed_emails(hours=hours)

    return [
        {
            "id": email.id,
            "to_email": email.to_email,
            "subject": email.subject,
            "template_name": email.template_name,
            "error_type": email.error_type,
            "error_message": email.error_message,
            "attempts": email.attempts,
            "created_at": email.created_at.isoformat() if email.created_at else None,
            "failed_at": email.failed_at.isoformat() if email.failed_at else None
        }
        for email in failed
    ]


@router.get("/suspicious-failures")
def get_suspicious_failures(
    hours: int = Query(24, description="Hours to analyze"),
    db: Session = Depends(get_db)
):
    """Identify suspicious patterns"""
    tracker = EmailDeliveryTrackerSync(db)
    return tracker.get_suspicious_failures(hours=hours)


@router.get("/email-logs")
def get_email_logs(
    status: Optional[str] = Query(None, description="Filter by status"),
    hours: int = Query(24, description="Hours to look back"),
    limit: int = Query(50, description="Max results"),
    db: Session = Depends(get_db)
):
    """Get email logs"""
    since = datetime.utcnow() - timedelta(hours=hours)

    query = db.query(EmailLog).filter(EmailLog.created_at >= since)

    if status:
        query = query.filter(EmailLog.status == status)

    logs = query.order_by(EmailLog.created_at.desc()).limit(limit).all()

    return [EmailLogResponse.from_orm(log) for log in logs]
