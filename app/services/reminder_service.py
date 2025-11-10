"""
Reminder service for sending automated reminders for pending approvals and tasks
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.submission import Submission, ResignationStatus
from app.services.email import get_email_service, EmailMessage
from app.services.leader_mapping import get_leader_mapping
from config import settings

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for managing and sending automated reminders"""

    def __init__(self):
        self.email_service = get_email_service()
        self.leader_mapping = get_leader_mapping()

    def calculate_hours_pending(self, timestamp: datetime) -> int:
        """Calculate hours since a timestamp"""
        if not timestamp:
            return 0
        now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
        delta = now - timestamp
        return int(delta.total_seconds() / 3600)

    def calculate_days_remaining(self, last_working_day: datetime) -> int:
        """Calculate days remaining until last working day"""
        if not last_working_day:
            return 0
        now = datetime.now(last_working_day.tzinfo) if last_working_day.tzinfo else datetime.now()
        delta = last_working_day.date() - now.date()
        return max(0, delta.days)

    def should_send_reminder(self, hours_pending: int, threshold_hours: int = None) -> bool:
        """Determine if a reminder should be sent based on hours pending"""
        if threshold_hours is None:
            threshold_hours = getattr(settings, 'REMINDER_THRESHOLD_HOURS', 24)
        return hours_pending >= threshold_hours

    async def send_leader_approval_reminder(
        self,
        submission: Submission,
        force: bool = False
    ) -> bool:
        """Send reminder to team leader for pending approval

        Args:
            submission: The submission pending approval
            force: If True, send regardless of threshold

        Returns:
            True if reminder was sent, False otherwise
        """
        try:
            # Calculate hours pending
            hours_pending = self.calculate_hours_pending(submission.submission_date)

            # Check if reminder should be sent
            if not force and not self.should_send_reminder(hours_pending):
                logger.info(f"Skipping leader reminder for submission {submission.id} - not enough time elapsed ({hours_pending}h)")
                return False

            # Get leader email
            leader_email = self.leader_mapping.get_leader_email(submission.team_leader)
            if not leader_email:
                logger.error(f"❌ Cannot send leader reminder - no email found for {submission.team_leader}")
                return False

            # Determine urgency (urgent if > 48 hours or < 5 days to last working day)
            days_remaining = self.calculate_days_remaining(submission.last_working_day)
            is_urgent = hours_pending > 48 or days_remaining < 5

            # Create approval URL
            approval_url = f"{settings.FRONTEND_URL}/approvals/leader?token={submission.leader_approval_token}"

            # Prepare email data
            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "submission_date": submission.submission_date.strftime("%B %d, %Y"),
                "last_working_day": submission.last_working_day.strftime("%B %d, %Y"),
                "notice_period_days": submission.notice_period_days,
                "hours_pending": hours_pending,
                "is_urgent": is_urgent,
                "approval_url": approval_url,
                "hr_email": settings.HR_EMAIL
            }

            # Create email message
            email_message = EmailMessage(
                to_email=leader_email,
                to_name=submission.team_leader,
                subject=f"⏰ Reminder: Resignation Approval Needed - {submission.employee_name}",
                template_name="leader_approval_reminder",
                template_data=email_data
            )

            # Send email
            success = await self.email_service.send_email(email_message)

            if success:
                logger.info(f"✅ Leader approval reminder sent for submission {submission.id} to {leader_email}")
            else:
                logger.error(f"❌ Failed to send leader approval reminder for submission {submission.id}")

            return success

        except Exception as e:
            logger.error(f"❌ Error sending leader approval reminder: {str(e)}")
            return False

    async def send_chm_approval_reminder(
        self,
        submission: Submission,
        force: bool = False
    ) -> bool:
        """Send reminder to Chinese Head for pending approval

        Args:
            submission: The submission pending CHM approval
            force: If True, send regardless of threshold

        Returns:
            True if reminder was sent, False otherwise
        """
        try:
            # Calculate hours pending since leader approval
            hours_pending = self.calculate_hours_pending(submission.team_leader_reply_date)

            # Check if reminder should be sent
            if not force and not self.should_send_reminder(hours_pending):
                logger.info(f"Skipping CHM reminder for submission {submission.id} - not enough time elapsed ({hours_pending}h)")
                return False

            # Get CHM info from leader mapping
            leader_info = self.leader_mapping.get_leader_info(submission.team_leader)
            if not leader_info or not leader_info.get('chm_email'):
                logger.error(f"❌ Cannot send CHM reminder - no CHM email found for leader {submission.team_leader}")
                return False

            chm_email = leader_info['chm_email']
            chm_name = leader_info.get('chm_name', 'Chinese Head')

            # Determine urgency
            days_remaining = self.calculate_days_remaining(submission.last_working_day)
            is_urgent = hours_pending > 48 or days_remaining < 5

            # Create approval URL
            approval_url = f"{settings.FRONTEND_URL}/approvals/chm?token={submission.chm_approval_token}"

            # Prepare email data
            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "team_leader": submission.team_leader,
                "submission_date": submission.submission_date.strftime("%B %d, %Y"),
                "last_working_day": submission.last_working_day.strftime("%B %d, %Y"),
                "notice_period_days": submission.notice_period_days,
                "hours_pending": hours_pending,
                "is_urgent": is_urgent,
                "leader_notes": submission.team_leader_notes or "",
                "approval_url": approval_url,
                "hr_email": settings.HR_EMAIL
            }

            # Create email message
            email_message = EmailMessage(
                to_email=chm_email,
                to_name=chm_name,
                subject=f"⏰ Reminder: CHM Approval Needed - {submission.employee_name}",
                template_name="chm_approval_reminder",
                template_data=email_data
            )

            # Send email
            success = await self.email_service.send_email(email_message)

            if success:
                logger.info(f"✅ CHM approval reminder sent for submission {submission.id} to {chm_email}")
            else:
                logger.error(f"❌ Failed to send CHM approval reminder for submission {submission.id}")

            return success

        except Exception as e:
            logger.error(f"❌ Error sending CHM approval reminder: {str(e)}")
            return False

    async def send_it_asset_reminder(
        self,
        submission: Submission,
        force: bool = False
    ) -> bool:
        """Send reminder to IT department for pending asset collection

        Args:
            submission: The submission pending IT asset collection
            force: If True, send regardless of threshold

        Returns:
            True if reminder was sent, False otherwise
        """
        try:
            # Calculate hours pending since exit interview
            hours_pending = self.calculate_hours_pending(submission.exit_interview_completed_date)

            # Check if reminder should be sent
            if not force and not self.should_send_reminder(hours_pending):
                logger.info(f"Skipping IT reminder for submission {submission.id} - not enough time elapsed ({hours_pending}h)")
                return False

            # Calculate days remaining
            days_remaining = self.calculate_days_remaining(submission.last_working_day)
            is_urgent = days_remaining < 5

            # Create clearance URL
            clearance_url = f"{settings.FRONTEND_URL}/approvals/it?token={submission.it_approval_token}"

            # Prepare email data
            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "last_working_day": submission.last_working_day.strftime("%B %d, %Y"),
                "days_remaining": days_remaining,
                "hours_pending": hours_pending,
                "is_urgent": is_urgent,
                "clearance_url": clearance_url,
                "hr_email": settings.HR_EMAIL
            }

            # Create email message
            email_message = EmailMessage(
                to_email=settings.IT_SUPPORT_EMAIL,
                to_name="IT Support Team",
                subject=f"⏰ Reminder: Asset Collection Needed - {submission.employee_name}",
                template_name="it_asset_reminder",
                template_data=email_data
            )

            # Send email
            success = await self.email_service.send_email(email_message)

            if success:
                logger.info(f"✅ IT asset reminder sent for submission {submission.id} to {settings.IT_SUPPORT_EMAIL}")
            else:
                logger.error(f"❌ Failed to send IT asset reminder for submission {submission.id}")

            return success

        except Exception as e:
            logger.error(f"❌ Error sending IT asset reminder: {str(e)}")
            return False

    def get_pending_leader_approvals(self, db: Session, threshold_hours: int = None) -> List[Submission]:
        """Get submissions pending leader approval that need reminders"""
        if threshold_hours is None:
            threshold_hours = getattr(settings, 'REMINDER_THRESHOLD_HOURS', 24)

        threshold_time = datetime.now() - timedelta(hours=threshold_hours)

        return db.query(Submission).filter(
            and_(
                Submission.resignation_status == ResignationStatus.SUBMITTED.value,
                Submission.team_leader_reply.is_(None),
                Submission.submission_date <= threshold_time
            )
        ).all()

    def get_pending_chm_approvals(self, db: Session, threshold_hours: int = None) -> List[Submission]:
        """Get submissions pending CHM approval that need reminders"""
        if threshold_hours is None:
            threshold_hours = getattr(settings, 'REMINDER_THRESHOLD_HOURS', 24)

        threshold_time = datetime.now() - timedelta(hours=threshold_hours)

        return db.query(Submission).filter(
            and_(
                Submission.resignation_status == ResignationStatus.LEADER_APPROVED.value,
                Submission.chinese_head_reply.is_(None),
                Submission.team_leader_reply_date <= threshold_time
            )
        ).all()

    def get_pending_it_clearances(self, db: Session, threshold_hours: int = None) -> List[Submission]:
        """Get submissions pending IT asset clearance that need reminders"""
        if threshold_hours is None:
            threshold_hours = getattr(settings, 'REMINDER_THRESHOLD_HOURS', 24)

        threshold_time = datetime.now() - timedelta(hours=threshold_hours)

        return db.query(Submission).filter(
            and_(
                Submission.resignation_status == ResignationStatus.EXIT_DONE.value,
                Submission.it_support_reply.is_(None),
                Submission.exit_interview_completed_date <= threshold_time
            )
        ).all()

    async def process_pending_reminders(self, db: Session, force: bool = False) -> Dict[str, Any]:
        """Process all pending reminders

        Args:
            db: Database session
            force: If True, send reminders regardless of threshold

        Returns:
            Summary of reminders sent
        """
        logger.info("🔔 Starting reminder processing...")

        results = {
            "leader_reminders": 0,
            "chm_reminders": 0,
            "it_reminders": 0,
            "errors": 0,
            "timestamp": datetime.now().isoformat()
        }

        # Check if reminders are enabled
        if not force and not getattr(settings, 'ENABLE_AUTO_REMINDERS', True):
            logger.info("⚠️ Auto reminders are disabled in config")
            return results

        try:
            # Process leader approval reminders
            pending_leader = self.get_pending_leader_approvals(db)
            logger.info(f"Found {len(pending_leader)} submissions pending leader approval")

            for submission in pending_leader:
                try:
                    if await self.send_leader_approval_reminder(submission, force=force):
                        results["leader_reminders"] += 1
                except Exception as e:
                    logger.error(f"Error sending leader reminder for submission {submission.id}: {str(e)}")
                    results["errors"] += 1

            # Process CHM approval reminders
            pending_chm = self.get_pending_chm_approvals(db)
            logger.info(f"Found {len(pending_chm)} submissions pending CHM approval")

            for submission in pending_chm:
                try:
                    if await self.send_chm_approval_reminder(submission, force=force):
                        results["chm_reminders"] += 1
                except Exception as e:
                    logger.error(f"Error sending CHM reminder for submission {submission.id}: {str(e)}")
                    results["errors"] += 1

            # Process IT asset reminders
            pending_it = self.get_pending_it_clearances(db)
            logger.info(f"Found {len(pending_it)} submissions pending IT clearance")

            for submission in pending_it:
                try:
                    if await self.send_it_asset_reminder(submission, force=force):
                        results["it_reminders"] += 1
                except Exception as e:
                    logger.error(f"Error sending IT reminder for submission {submission.id}: {str(e)}")
                    results["errors"] += 1

            logger.info(f"✅ Reminder processing complete: {results}")
            return results

        except Exception as e:
            logger.error(f"❌ Error processing reminders: {str(e)}")
            results["errors"] += 1
            return results


# Global instance
_reminder_service_instance = None

def get_reminder_service() -> ReminderService:
    """Get global reminder service instance"""
    global _reminder_service_instance
    if _reminder_service_instance is None:
        _reminder_service_instance = ReminderService()
    return _reminder_service_instance
