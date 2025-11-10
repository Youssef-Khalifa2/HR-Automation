"""
Automated Workflow Triggers for Exit Interview Process

This service handles:
1. Daily reminders to HR for pending interview scheduling
2. Post-interview reminders to HR for feedback submission
3. Automatic email notifications based on time triggers
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.crud_exit_interview import (
    get_interviews_needing_scheduling,
    get_upcoming_interviews,
    get_pending_scheduled_interviews,
    create_reminder,
    get_pending_reminders,
    mark_reminder_sent
)
from app.crud import get_submission
from app.services.email import get_email_service, EmailTemplates

logger = logging.getLogger(__name__)


class ExitInterviewAutomation:
    """Service for automated exit interview workflow triggers"""

    def __init__(self):
        self.email_service = get_email_service()

    async def run_daily_automation(self):
        """Run all daily automation tasks"""
        logger.info("🤖 Starting daily exit interview automation...")

        try:
            db_gen = get_db()
            db = next(db_gen)

            # Task 1: Send HR reminders for pending interview scheduling
            await self.send_pending_scheduling_reminders(db)

            # Task 2: Send HR reminders for pending interview feedback
            await self.send_pending_feedback_reminders(db)

            # Task 3: Send employee reminders for upcoming interviews (24 hours before)
            await self.send_employee_interview_reminders(db)

            # Task 4: Process any scheduled reminders
            await self.process_scheduled_reminders(db)

            db.close()
            logger.info("✅ Daily automation completed successfully")

        except Exception as e:
            logger.error(f"❌ Automation failed: {str(e)}")

    async def send_pending_scheduling_reminders(self, db: Session):
        """Send reminders to HR for interviews that need scheduling"""
        try:
            logger.info("📋 Checking for pending interview scheduling...")

            # Get submissions that need interview scheduling (approved but not scheduled)
            pending_submissions = get_interviews_needing_scheduling(db)

            if not pending_submissions:
                logger.info("✅ No pending scheduling needed")
                return

            logger.info(f"📋 Found {len(pending_submissions)} submissions needing scheduling")

            hr_email = self._get_hr_email()
            hr_name = "HR Department"

            for submission in pending_submissions:
                # Check if we already sent a reminder recently (avoid spam)
                days_since_approval = 0
                if submission.updated_at:
                    days_since_approval = (datetime.utcnow() - submission.updated_at).days

                # Send reminder if it's been more than 1 day since approval
                if days_since_approval >= 1:
                    await self._send_hr_scheduling_reminder(db, submission, hr_email, hr_name, days_since_approval)

        except Exception as e:
            logger.error(f"❌ Failed to send scheduling reminders: {str(e)}")

    async def send_pending_feedback_reminders(self, db: Session):
        """Send reminders to HR for interviews that need feedback submission"""
        try:
            logger.info("⚠️ Checking for pending interview feedback...")

            # Get interviews that have passed their scheduled time but not completed
            pending_interviews = get_pending_scheduled_interviews(db)

            if not pending_interviews:
                logger.info("✅ No pending feedback needed")
                return

            logger.info(f"⚠️ Found {len(pending_interviews)} interviews needing feedback")

            hr_email = self._get_hr_email()
            hr_name = "HR Department"

            for interview in pending_interviews:
                submission = interview.submission
                days_overdue = (datetime.utcnow() - interview.scheduled_date).days

                # Send reminder if interview is overdue by at least 1 day
                if days_overdue >= 1:
                    await self._send_hr_feedback_reminder(db, interview, submission, hr_email, hr_name, days_overdue)

        except Exception as e:
            logger.error(f"❌ Failed to send feedback reminders: {str(e)}")

    async def send_employee_interview_reminders(self, db: Session):
        """Send reminders to employees for upcoming interviews (24 hours before)"""
        try:
            logger.info("📧 Checking for upcoming interview reminders...")

            # Get interviews scheduled for tomorrow
            tomorrow = datetime.utcnow().date() + timedelta(days=1)
            upcoming_tomorrow = get_upcoming_interviews(db, days_ahead=1)

            # Filter for interviews scheduled exactly for tomorrow
            tomorrow_interviews = [
                interview for interview in upcoming_tomorrow
                if interview.scheduled_date.date() == tomorrow
            ]

            if not tomorrow_interviews:
                logger.info("✅ No interview reminders needed for tomorrow")
                return

            logger.info(f"📧 Sending reminders for {len(tomorrow_interviews)} interviews tomorrow")

            for interview in tomorrow_interviews:
                await self._send_employee_interview_reminder(db, interview)

        except Exception as e:
            logger.error(f"❌ Failed to send employee reminders: {str(e)}")

    async def process_scheduled_reminders(self, db: Session):
        """Process any scheduled reminders that are due"""
        try:
            logger.info("⏰ Processing scheduled reminders...")

            # Get pending reminders that are due
            pending_reminders = get_pending_reminders(db)

            if not pending_reminders:
                logger.info("✅ No scheduled reminders to process")
                return

            logger.info(f"⏰ Processing {len(pending_reminders)} scheduled reminders")

            for reminder in pending_reminders:
                await self._process_scheduled_reminder(db, reminder)

        except Exception as e:
            logger.error(f"❌ Failed to process scheduled reminders: {str(e)}")

    async def _send_hr_scheduling_reminder(self, db: Session, submission, hr_email: str, hr_name: str, days_overdue: int):
        """Send HR reminder for pending interview scheduling"""
        try:
            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "department": getattr(submission, 'department', 'General'),
                "position": getattr(submission, 'position', 'Employee'),
                "submission_id": submission.id,
                "approval_date": submission.updated_at.strftime("%Y-%m-%d") if submission.updated_at else "",
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "current_date": datetime.now().strftime("%B %d, %Y")
            }

            email_message = EmailTemplates.hr_schedule_interview_reminder(email_data)
            success = await self.email_service.send_email(email_message)

            if success:
                logger.info(f"✅ HR scheduling reminder sent for {submission.employee_name}")

                # Create reminder record
                await create_reminder(
                    db=db,
                    exit_interview_id=0, # No interview created yet
                    reminder_type="schedule_interview",
                    recipient_email=hr_email,
                    recipient_name=hr_name,
                    scheduled_for=datetime.utcnow()
                )
            else:
                logger.error(f"❌ Failed to send HR scheduling reminder for {submission.employee_name}")

        except Exception as e:
            logger.error(f"❌ Error sending HR scheduling reminder: {str(e)}")

    async def _send_hr_feedback_reminder(self, db: Session, interview, submission, hr_email: str, hr_name: str, days_overdue: int):
        """Send HR reminder for pending interview feedback"""
        try:
            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "department": getattr(submission, 'department', 'General'),
                "position": getattr(submission, 'position', 'Employee'),
                "interview_date": interview.scheduled_date.strftime("%Y-%m-%d"),
                "interview_time": interview.scheduled_time,
                "location": interview.location,
                "days_overdue": days_overdue,
                "interview_id": interview.id,
                "current_date": datetime.now().strftime("%B %d, %Y")
            }

            email_message = EmailTemplates.hr_submit_feedback_reminder(email_data)
            success = await self.email_service.send_email(email_message)

            if success:
                logger.info(f"✅ HR feedback reminder sent for {submission.employee_name} ({days_overdue} days overdue)")

                # Create reminder record
                await create_reminder(
                    db=db,
                    exit_interview_id=interview.id,
                    reminder_type="submit_feedback",
                    recipient_email=hr_email,
                    recipient_name=hr_name,
                    scheduled_for=datetime.utcnow()
                )
            else:
                logger.error(f"❌ Failed to send HR feedback reminder for {submission.employee_name}")

        except Exception as e:
            logger.error(f"❌ Error sending HR feedback reminder: {str(e)}")

    async def _send_employee_interview_reminder(self, db: Session, interview):
        """Send interview reminder to employee"""
        try:
            submission = interview.submission

            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "scheduled_date": interview.scheduled_date.strftime("%A, %B %d, %Y"),
                "scheduled_time": interview.scheduled_time,
                "location": interview.location,
                "interviewer": interview.interviewer,
                "department": getattr(submission, 'department', 'General'),
                "position": getattr(submission, 'position', 'Employee'),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "current_date": datetime.now().strftime("%B %d, %Y")
            }

            email_message = EmailTemplates.exit_interview_scheduled(email_data)
            success = await self.email_service.send_email(email_message)

            if success:
                logger.info(f"✅ Employee interview reminder sent to {submission.employee_name}")

                # Create reminder record
                await create_reminder(
                    db=db,
                    exit_interview_id=interview.id,
                    reminder_type="employee_reminder",
                    recipient_email=submission.employee_email,
                    recipient_name=submission.employee_name,
                    scheduled_for=datetime.utcnow()
                )
            else:
                logger.error(f"❌ Failed to send employee interview reminder to {submission.employee_name}")

        except Exception as e:
            logger.error(f"❌ Error sending employee interview reminder: {str(e)}")

    async def _process_scheduled_reminder(self, db: Session, reminder):
        """Process a scheduled reminder"""
        try:
            logger.info(f"⏰ Processing reminder {reminder.id}: {reminder.reminder_type}")

            # Mark as sent
            await mark_reminder_sent(db, reminder.id)

            # Here you could add custom logic for different reminder types
            # For now, we just mark them as sent

        except Exception as e:
            logger.error(f"❌ Error processing reminder {reminder.id}: {str(e)}")

    def _get_hr_email(self):
        """Get HR email from configuration"""
        from config import settings
        return settings.HR_EMAIL

    def _get_it_email(self):
        """Get IT email from configuration"""
        from config import settings
        return settings.IT_EMAIL


# Global automation service instance
automation_service = ExitInterviewAutomation()


def get_automation_service() -> ExitInterviewAutomation:
    """Get the global automation service instance"""
    return automation_service


# Cron job runner function
async def run_daily_automation():
    """Main function to run daily automation tasks"""
    service = get_automation_service()
    await service.run_daily_automation()


if __name__ == "__main__":
    # For direct execution (testing)
    asyncio.run(run_daily_automation())