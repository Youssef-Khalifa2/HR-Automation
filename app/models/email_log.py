"""Email delivery tracking and logging models"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class EmailLog(Base):
    """Track all email sending attempts and delivery status"""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Email details
    to_email = Column(String(255), index=True, nullable=False)
    to_name = Column(String(255))
    from_email = Column(String(255))
    subject = Column(String(500))
    template_name = Column(String(100))

    # Status tracking
    status = Column(String(50), index=True)  # pending, sent, delivered, bounced, failed
    smtp_response = Column(Text)  # SMTP server response
    attempts = Column(Integer, default=0)  # Number of send attempts

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    last_attempt_at = Column(DateTime(timezone=True))

    # Error tracking
    error_message = Column(Text)
    error_type = Column(String(100))  # auth_error, recipient_refused, timeout, etc.

    # Template data for debugging (stored as JSON)
    template_data = Column(JSON)

    # Related submission/interview
    submission_id = Column(Integer, index=True)
    exit_interview_id = Column(Integer, index=True)

    # Delivery verification
    message_id = Column(String(500))  # Email message ID for tracking
    bounce_detected = Column(Boolean, default=False)
    bounce_reason = Column(Text)

    # Rate limiting tracking
    rate_limit_hit = Column(Boolean, default=False)
    retry_after = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<EmailLog(to={self.to_email}, status={self.status}, subject={self.subject[:50]})>"


class EmailDeliveryStats(Base):
    """Track email delivery statistics for monitoring"""
    __tablename__ = "email_delivery_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), index=True, server_default=func.now())

    # Counts
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_bounced = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)

    # By template type
    template_counts = Column(JSON)

    # Error analysis
    error_types = Column(JSON)

    # Rate limiting
    rate_limits_hit = Column(Integer, default=0)

    def __repr__(self):
        return f"<EmailDeliveryStats(date={self.date}, sent={self.total_sent}, delivered={self.total_delivered})>"
