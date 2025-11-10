#!/usr/bin/env python3
"""
Phase 3 Exit Interview Workflow Test

This test validates the complete Phase 3 exit interview workflow:
1. HR gets reminder to schedule exit interview
2. HR schedules interview → employee gets notification
3. After interview time → HR gets reminder to submit feedback
4. HR submits feedback → IT gets clearance notification
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from datetime import datetime, timedelta
from app.database import get_db, engine, Base
from app.crud import create_submission, get_submission
from app.crud_exit_interview import (
    create_exit_interview, schedule_exit_interview,
    complete_exit_interview, get_interviews_needing_scheduling,
    get_upcoming_interviews, get_pending_scheduled_interviews
)
from app.services.email import get_email_service, EmailTemplates
from app.auth import get_password_hash
from app.models.user import User
from app.models.submission import Submission, ResignationStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase3_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Phase3ExitInterviewTest:
    def __init__(self):
        self.test_results = []
        self.test_data = {}
        self.db = None

    def log_test(self, test_name, success, error_message=None):
        """Log test result"""
        status = "[PASS]" if success else "[FAIL]"
        message = f"{status} - {test_name}"
        if error_message:
            message += f": {error_message}"
        logger.info(message)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "error": error_message
        })

    async def setup_test_environment(self):
        """Setup test environment with database and test data"""
        try:
            logger.info("Setting up Phase 3 test environment...")

            # Create tables
            from app.models.exit_interview import ExitInterview, ExitInterviewReminder
            Base.metadata.create_all(bind=engine)

            # Get database session
            db_gen = get_db()
            self.db = next(db_gen)

            # Create test HR user
            hr_user = User(
                email="hr_test@company.com",
                password_hash=get_password_hash("testpass123"),
                full_name="Test HR User",
                role="hr"
            )
            self.db.add(hr_user)
            self.db.commit()
            self.test_data["hr_user"] = hr_user

            # Create test submission with leader approval
            from app.schemas_all import SubmissionCreate
            test_submission = SubmissionCreate(
                employee_name="John Doe",
                employee_email="john.doe@company.com",
                joining_date=datetime.now() - timedelta(days=365),
                submission_date=datetime.now(),
                last_working_day=datetime.now() + timedelta(days=30),
                department="Engineering",
                position="Software Engineer"
            )

            submission = create_submission(self.db, test_submission)

            # Manually set to leader_approved for testing
            submission.resignation_status = ResignationStatus.LEADER_APPROVED.value
            self.db.commit()
            self.db.refresh(submission)

            self.test_data["submission"] = submission
            logger.info("[OK] Test environment setup completed")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Setup failed: {str(e)}")
            return False

    async def test_01_database_models(self):
        """Test 1: Verify database models are created correctly"""
        try:
            logger.info("Testing 1: Database Models...")

            # Test ExitInterview model
            from app.models.exit_interview import ExitInterview

            # Create exit interview record
            exit_interview = create_exit_interview(self.db, self.test_data["submission"].id)

            self.test_data["exit_interview"] = exit_interview

            assert exit_interview is not None
            assert exit_interview.submission_id == self.test_data["submission"].id
            assert exit_interview.interview_completed == False

            self.log_test("Exit Interview Model Creation", True)
            return True

        except Exception as e:
            self.log_test("Exit Interview Model Creation", False, str(e))
            return False

    async def test_02_pending_scheduling_detection(self):
        """Test 2: Detect submissions needing interview scheduling"""
        try:
            logger.info("Testing 2: Pending Scheduling Detection...")

            pending_submissions = get_interviews_needing_scheduling(self.db)

            # Should find our test submission
            test_found = False
            for sub in pending_submissions:
                if sub.id == self.test_data["submission"].id:
                    test_found = True
                    break

            assert test_found, "Test submission should be found in pending scheduling"
            assert len(pending_submissions) >= 1, "Should find at least one submission needing scheduling"

            self.log_test("Pending Scheduling Detection", True)
            return True

        except Exception as e:
            self.log_test("Pending Scheduling Detection", False, str(e))
            return False

    async def test_03_interview_scheduling(self):
        """Test 3: Schedule an exit interview"""
        try:
            logger.info("Testing 3: Interview Scheduling...")

            # Schedule interview for tomorrow
            scheduled_date = datetime.now() + timedelta(days=1)
            scheduled_time = "14:30"
            location = "HR Conference Room A"
            interviewer = "Jane Smith (HR Manager)"

            exit_interview = schedule_exit_interview(
                db=self.db,
                submission_id=self.test_data["submission"].id,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                location=location,
                interviewer=interviewer
            )

            assert exit_interview is not None
            assert exit_interview.scheduled_date == scheduled_date
            assert exit_interview.scheduled_time == scheduled_time
            assert exit_interview.location == location
            assert exit_interview.interviewer == interviewer

            # Verify submission status updated
            submission = get_submission(self.db, self.test_data["submission"].id)
            assert submission.exit_interview_status == "scheduled"

            self.test_data["scheduled_interview"] = exit_interview
            self.log_test("Interview Scheduling", True)
            return True

        except Exception as e:
            self.log_test("Interview Scheduling", False, str(e))
            return False

    async def test_04_employee_notification_email(self):
        """Test 4: Send interview scheduling email to employee"""
        try:
            logger.info("Testing 4: Employee Notification Email...")

            # Get email service
            from config import settings
            from app.services.email import create_email_service

            email_service = create_email_service()

            # Prepare email data
            exit_interview = self.test_data["scheduled_interview"]
            submission = self.test_data["submission"]

            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "scheduled_date": exit_interview.scheduled_date.strftime("%A, %B %d, %Y"),
                "scheduled_time": exit_interview.scheduled_time,
                "location": exit_interview.location,
                "interviewer": exit_interview.interviewer,
                "department": getattr(submission, 'department', 'General'),
                "position": getattr(submission, 'position', 'Employee'),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d")
            }

            # Create email
            email_message = EmailTemplates.exit_interview_scheduled(email_data)

            # Verify email content
            assert email_message.to_email == submission.employee_email
            assert exit_interview.scheduled_date.strftime("%A, %B %d, %Y") in email_message.subject
            assert email_message.template_name == "exit_interview_scheduled"

            self.log_test("Employee Notification Email", True)
            return True

        except Exception as e:
            self.log_test("Employee Notification Email", False, str(e))
            return False

    async def test_05_upcoming_interviews_detection(self):
        """Test 5: Detect upcoming interviews"""
        try:
            logger.info("Testing 5: Upcoming Interviews Detection...")

            upcoming_interviews = get_upcoming_interviews(self.db, days_ahead=7)

            # Should find our scheduled interview
            test_found = False
            for interview in upcoming_interviews:
                if interview.id == self.test_data["scheduled_interview"].id:
                    test_found = True
                    break

            assert test_found, "Scheduled interview should be found in upcoming interviews"

            self.log_test("Upcoming Interviews Detection", True)
            return True

        except Exception as e:
            self.log_test("Upcoming Interviews Detection", False, str(e))
            return False

    async def test_06_interview_completion(self):
        """Test 6: Complete interview with feedback"""
        try:
            logger.info("Testing 6: Interview Completion...")

            # Simulate interview completion
            feedback = "Employee provided valuable feedback about management style and career development opportunities."
            rating = 4
            hr_notes = "Employee showed professionalism during the interview. Key insights about team communication."

            exit_interview = complete_exit_interview(
                db=self.db,
                interview_id=self.test_data["scheduled_interview"].id,
                feedback=feedback,
                rating=rating,
                hr_notes=hr_notes
            )

            assert exit_interview is not None
            assert exit_interview.interview_completed == True
            assert exit_interview.interview_feedback == feedback
            assert exit_interview.interview_rating == rating
            assert exit_interview.hr_notes == hr_notes
            assert exit_interview.interview_completed_at is not None

            # Verify submission status updated
            submission = get_submission(self.db, self.test_data["submission"].id)
            assert submission.exit_interview_status == "done"
            assert submission.exit_interview_notes == feedback

            self.test_data["completed_interview"] = exit_interview
            self.log_test("Interview Completion", True)
            return True

        except Exception as e:
            self.log_test("Interview Completion", False, str(e))
            return False

    async def test_07_it_notification_email(self):
        """Test 7: Send IT clearance notification"""
        try:
            logger.info("Testing 7: IT Notification Email...")

            # Prepare IT notification data
            submission = self.test_data["submission"]

            # Get asset details (mock)
            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "department": getattr(submission, 'department', 'General'),
                "position": getattr(submission, 'position', 'Employee'),
                "assets": {
                    "laptop": True,
                    "mouse": True,
                    "headphones": False,
                    "others": None
                },
                "submission_id": submission.id
            }

            # Create IT notification email
            email_message = EmailTemplates.it_clearance_request(email_data)

            # Verify email content
            assert email_message.to_email == "it-support@company.com"
            assert email_message.to_name == "IT Support Team"
            assert submission.employee_name in email_message.subject
            assert email_message.template_name == "it_clearance_request"

            self.log_test("IT Notification Email", True)
            return True

        except Exception as e:
            self.log_test("IT Notification Email", False, str(e))
            return False

    async def test_08_workflow_statistics(self):
        """Test 8: Generate workflow statistics"""
        try:
            logger.info("Testing 8: Workflow Statistics...")

            from app.crud_exit_interview import get_interview_statistics

            stats = get_interview_statistics(self.db)

            assert "total_submissions" in stats
            assert "pending_scheduling" in stats
            assert "scheduled" in stats
            assert "completed" in stats
            assert "completion_rate" in stats

            # Should have at least our test data
            assert stats["total_submissions"] >= 1
            assert stats["completed"] >= 1

            self.log_test("Workflow Statistics", True)
            return True

        except Exception as e:
            self.log_test("Workflow Statistics", False, str(e))
            return False

    async def run_all_tests(self):
        """Run all Phase 3 tests"""
        logger.info("Starting Phase 3 Exit Interview Workflow Tests")
        logger.info("=" * 60)

        # Setup test environment
        if not await self.setup_test_environment():
            return False

        # Run all tests
        tests = [
            self.test_01_database_models,
            self.test_02_pending_scheduling_detection,
            self.test_03_interview_scheduling,
            self.test_04_employee_notification_email,
            self.test_05_upcoming_interviews_detection,
            self.test_06_interview_completion,
            self.test_07_it_notification_email,
            self.test_08_workflow_statistics
        ]

        for test in tests:
            try:
                await test()
            except Exception as e:
                logger.error(f"Test {test.__name__} failed with exception: {str(e)}")

        # Print results summary
        logger.info("=" * 60)
        logger.info("TEST RESULTS SUMMARY")

        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)

        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {total - passed}")
        logger.info(f"Success Rate: {(passed/total*100):.1f}%")

        if total - passed > 0:
            logger.info("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"  - {result['test']}: {result.get('error', 'Unknown error')}")

        logger.info("=" * 60)
        if passed == total:
            logger.info("ALL TESTS PASSED! Phase 3 implementation is ready.")
        else:
            logger.info("Some tests failed. Please review and fix issues.")

        return passed == total

    def cleanup(self):
        """Clean up test data"""
        try:
            if self.db:
                self.db.close()
            logger.info("Test cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")


async def main():
    """Main test execution"""
    test = Phase3ExitInterviewTest()

    try:
        success = await test.run_all_tests()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        return 1
    finally:
        test.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)