"""
Enhanced Submission Validation Service

Allows multiple submissions when previous ones are rejected
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from app.crud import get_submission_by_email
from app.models.submission import ResignationStatus


class SubmissionValidator:
    """Enhanced submission validation logic"""

    @staticmethod
    def can_submit_new_resignation(db: Session, employee_email: str) -> tuple[bool, str, Optional[dict]]:
        """
        Check if employee can submit a new resignation submission.

        Returns:
            (can_submit, reason_message, existing_submission_info)
        """

        # Get all submissions for this employee
        existing_submission = get_submission_by_email(db, employee_email)

        if not existing_submission:
            # No previous submission - can submit
            return True, "No previous submission found", None

        # Check the status of existing submission
        submission_data = {
            "id": existing_submission.id,
            "status": existing_submission.resignation_status,
            "submission_date": existing_submission.submission_date,
            "last_working_day": existing_submission.last_working_day
        }

        # Define rejected statuses
        rejected_statuses = [
            ResignationStatus.LEADER_REJECTED.value,
            ResignationStatus.CHM_REJECTED.value
        ]

        # Define completed/offboarded statuses
        completed_statuses = [
            ResignationStatus.EXIT_DONE.value,
            ResignationStatus.ASSETS_RECORDED.value,
            ResignationStatus.MEDICAL_CHECKED.value,
            ResignationStatus.OFFBOARDED.value
        ]

        # Define active/pending statuses
        active_statuses = [
            ResignationStatus.SUBMITTED.value,
            ResignationStatus.LEADER_APPROVED.value,
            ResignationStatus.CHM_APPROVED.value
        ]

        # Check if previous submission was rejected
        if existing_submission.resignation_status in rejected_statuses:
            return True, f"Previous submission was rejected ({existing_submission.resignation_status}). New submission allowed.", submission_data

        # Check if previous submission is still active
        if existing_submission.resignation_status in active_statuses:
            return False, f"Active resignation already exists ({existing_submission.resignation_status}). Please wait for approval or rejection.", submission_data

        # Check if previous submission was completed
        if existing_submission.resignation_status in completed_statuses:
            # Allow new submission if last working day is in the past
            if existing_submission.last_working_day < datetime.utcnow():
                return True, "Previous resignation completed. New submission allowed.", submission_data
            else:
                return False, f"Previous resignation not yet completed. Last working day: {existing_submission.last_working_day.strftime('%Y-%m-%d')}", submission_data

        # Default case - allow submission
        return True, "New submission allowed", submission_data

    @staticmethod
    def get_all_submissions_for_employee(db: Session, employee_email: str) -> List[dict]:
        """Get all submissions for an employee with their status"""
        # This would require a custom query since get_submission_by_email returns only one
        from app.models.submission import Submission

        submissions = db.query(Submission).filter(
            Submission.employee_email == employee_email
        ).order_by(Submission.submission_date.desc()).all()

        return [
            {
                "id": sub.id,
                "status": sub.resignation_status,
                "submission_date": sub.submission_date,
                "last_working_day": sub.last_working_day,
                "exit_interview_status": sub.exit_interview_status,
                "created_at": sub.created_at
            }
            for sub in submissions
        ]

    @staticmethod
    def get_latest_approved_submission(db: Session, employee_email: str) -> Optional[dict]:
        """Get the most recent approved submission for an employee"""
        from app.models.submission import Submission

        # Find the latest submission that was approved by both leader and CHM
        submission = db.query(Submission).filter(
            and_(
                Submission.employee_email == employee_email,
                Submission.team_leader_reply == True,
                Submission.chinese_head_reply == True,
                Submission.resignation_status.in_([
                    ResignationStatus.CHM_APPROVED.value,
                    ResignationStatus.EXIT_DONE.value,
                    ResignationStatus.ASSETS_RECORDED.value,
                    ResignationStatus.MEDICAL_CHECKED.value,
                    ResignationStatus.OFFBOARDED.value
                ])
            )
        ).order_by(Submission.submission_date.desc()).first()

        if submission:
            return {
                "id": submission.id,
                "status": submission.resignation_status,
                "submission_date": submission.submission_date,
                "last_working_day": submission.last_working_day,
                "exit_interview_status": submission.exit_interview_status
            }

        return None


# Global validator instance
submission_validator = SubmissionValidator()


def get_submission_validator() -> SubmissionValidator:
    """Get the global submission validator instance"""
    return submission_validator