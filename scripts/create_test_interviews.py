"""Test script for exit interview workflow - creates CHM-approved submissions"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.submission import Submission, ResignationStatus
from app.crud_exit_interview import create_exit_interview
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_submissions(db: Session, count: int = 10):
    """Create test submissions with CHM approval"""
    created_submissions = []

    # Sample data for realistic test submissions
    test_data = [
        {
            "employee_name": "John Smith",
            "employee_email": "john.smith@company.com",
            "joining_date": datetime(2020, 5, 15),
            "submission_date": datetime.now() - timedelta(days=5),
            "last_working_day": datetime.now() + timedelta(days=14),
            "department": "Engineering",
            "position": "Senior Developer"
        },
        {
            "employee_name": "Sarah Johnson",
            "employee_email": "sarah.johnson@company.com",
            "joining_date": datetime(2019, 3, 20),
            "submission_date": datetime.now() - timedelta(days=3),
            "last_working_day": datetime.now() + timedelta(days=10),
            "department": "Marketing",
            "position": "Marketing Manager"
        },
        {
            "employee_name": "Michael Chen",
            "employee_email": "michael.chen@company.com",
            "joining_date": datetime(2021, 1, 10),
            "submission_date": datetime.now() - timedelta(days=7),
            "last_working_day": datetime.now() + timedelta(days=21),
            "department": "Finance",
            "position": "Financial Analyst"
        },
        {
            "employee_name": "Emily Davis",
            "employee_email": "emily.davis@company.com",
            "joining_date": datetime(2020, 8, 1),
            "submission_date": datetime.now() - timedelta(days=2),
            "last_working_day": datetime.now() + timedelta(days=8),
            "department": "HR",
            "position": "HR Specialist"
        },
        {
            "employee_name": "Robert Wilson",
            "employee_email": "robert.wilson@company.com",
            "joining_date": datetime(2018, 11, 15),
            "submission_date": datetime.now() - timedelta(days=4),
            "last_working_day": datetime.now() + timedelta(days=18),
            "department": "Operations",
            "position": "Operations Manager"
        },
        {
            "employee_name": "Lisa Anderson",
            "employee_email": "lisa.anderson@company.com",
            "joining_date": datetime(2019, 7, 20),
            "submission_date": datetime.now() - timedelta(days=6),
            "last_working_day": datetime.now() + timedelta(days=12),
            "department": "Sales",
            "position": "Sales Executive"
        },
        {
            "employee_name": "David Martinez",
            "employee_email": "david.martinez@company.com",
            "joining_date": datetime(2021, 2, 1),
            "submission_date": datetime.now() - timedelta(days=1),
            "last_working_day": datetime.now() + timedelta(days=15),
            "department": "Engineering",
            "position": "DevOps Engineer"
        },
        {
            "employee_name": "Jennifer Taylor",
            "employee_email": "jennifer.taylor@company.com",
            "joining_date": datetime(2020, 4, 10),
            "submission_date": datetime.now() - timedelta(days=8),
            "last_working_day": datetime.now() + timedelta(days=25),
            "department": "Customer Service",
            "position": "Customer Service Lead"
        },
        {
            "employee_name": "Christopher Lee",
            "employee_email": "christopher.lee@company.com",
            "joining_date": datetime(2018, 9, 5),
            "submission_date": datetime.now() - timedelta(days=5),
            "last_working_day": datetime.now() + timedelta(days=16),
            "department": "IT",
            "position": "System Administrator"
        },
        {
            "employee_name": "Amanda Brown",
            "employee_email": "amanda.brown@company.com",
            "joining_date": datetime(2019, 12, 15),
            "submission_date": datetime.now() - timedelta(days=3),
            "last_working_day": datetime.now() + timedelta(days=11),
            "department": "Product",
            "position": "Product Manager"
        }
    ]

    for i in range(min(count, len(test_data))):
        data = test_data[i]

        # Create submission with CHM approval status
        submission = Submission(
            employee_name=data["employee_name"],
            employee_email=data["employee_email"],
            joining_date=data["joining_date"],
            submission_date=data["submission_date"],
            last_working_day=data["last_working_day"],
            resignation_status=ResignationStatus.CHM_APPROVED.value,  # Directly set to CHM approved
            team_leader_reply=True,
            chinese_head_reply=True,
            team_leader_name="Test Leader",
            chinese_head_name="Test CHM",
            team_leader_notes="Approved by test workflow",
            chinese_head_notes="CHM approved for test purposes",
            exit_interview_status="not_scheduled"
        )

        db.add(submission)
        db.commit()
        db.refresh(submission)

        created_submissions.append(submission)
        logger.info(f"✅ Created CHM-approved submission: {submission.employee_name} (ID: {submission.id})")

    return created_submissions

def create_exit_interviews_for_submissions(db: Session, submissions):
    """Create ExitInterview records for CHM-approved submissions"""
    interview_records = []

    for submission in submissions:
        # Create ExitInterview record
        exit_interview = create_exit_interview(db, submission.id)
        interview_records.append(exit_interview)

        logger.info(f"📅 Created ExitInterview record: {submission.employee_name} -> Interview ID: {exit_interview.id}")

    return interview_records

def create_scheduled_interviews(db: Session, interview_records):
    """Schedule some interviews for testing"""
    scheduled_count = 0
    current_time = datetime.utcnow()

    for i, interview in enumerate(interview_records[:5]):  # Schedule first 5 interviews
        # Schedule interviews on different future dates
        future_date = current_time + timedelta(days=i+1)
        future_time = f"{10 + i}:00"  # 10:00, 11:00, 12:00, etc.

        # Update the interview record with scheduling details
        interview.scheduled_date = future_date
        interview.scheduled_time = future_time
        interview.location = f"HR Meeting Room {i+1}"
        interview.interviewer = "HR Representative"
        interview.interview_type = "in-person"

        db.commit()
        db.refresh(interview)

        scheduled_count += 1
        logger.info(f"📋 Scheduled interview: {interview.submission.employee_name} on {future_date.strftime('%Y-%m-%d')} at {future_time}")

    return scheduled_count

def print_workflow_summary(db: Session):
    """Print summary of the created workflow data"""
    print("\n" + "="*80)
    print("📊 WORKFLOW TEST DATA SUMMARY")
    print("="*80)

    # Count submissions by status
    from sqlalchemy import func

    total_submissions = db.query(Submission).count()
    chm_approved = db.query(Submission).filter(
        Submission.resignation_status == ResignationStatus.CHM_APPROVED.value
    ).count()

    print(f"📋 Total Submissions: {total_submissions}")
    print(f"✅ CHM Approved: {chm_approved}")

    # Count ExitInterview records
    from app.models.exit_interview import ExitInterview

    total_interviews = db.query(ExitInterview).count()
    scheduled_interviews = db.query(ExitInterview).filter(
        ExitInterview.scheduled_date.isnot(None),
        ExitInterview.interview_completed == False
    ).count()
    completed_interviews = db.query(ExitInterview).filter(
        ExitInterview.interview_completed == True
    ).count()

    print(f"📅 Total ExitInterview Records: {total_interviews}")
    print(f"📅 Scheduled (Not Completed): {scheduled_interviews}")
    print(f"✅ Completed: {completed_interviews}")

    # Show upcoming interviews
    upcoming = db.query(ExitInterview).filter(
        ExitInterview.scheduled_date >= datetime.utcnow(),
        ExitInterview.interview_completed == False
    ).order_by(ExitInterview.scheduled_date).limit(5).all()

    print(f"\n📆 Upcoming Interviews (Next 5):")
    for interview in upcoming:
        print(f"   • {interview.submission.employee_name} - {interview.scheduled_date.strftime('%Y-%m-%d')} at {interview.scheduled_time} ({interview.location})")

    print("\n" + "="*80)
    print("🚀 WORKFLOW READY FOR TESTING")
    print("="*80)
    print("✅ CHM-approved submissions created")
    print("✅ ExitInterview records created")
    print("✅ Some interviews scheduled")
    print("✅ Ready for scheduling and feedback testing")
    print("="*80)

def main():
    """Main function to create test data"""
    print("🚀 Creating Exit Interview Workflow Test Data")
    print("="*60)

    try:
        # Get database session
        db = next(get_db())

        # Create test submissions with CHM approval
        print("\n📋 Creating CHM-approved submissions...")
        submissions = create_test_submissions(db, count=10)

        # Create ExitInterview records
        print(f"\n📅 Creating ExitInterview records for {len(submissions)} submissions...")
        interview_records = create_exit_interviews_for_submissions(db, submissions)

        # Schedule some interviews
        print(f"\n📋 Scheduling interviews for testing...")
        scheduled_count = create_scheduled_interviews(db, interview_records)

        # Print summary
        print_workflow_summary(db)

        # Close database session
        db.close()

        print(f"\n✅ Test data creation completed successfully!")
        print(f"📋 {len(submissions)} CHM-approved submissions ready")
        print(f"📅 {len(interview_records)} ExitInterview records created")
        print(f"📅 {scheduled_count} interviews scheduled")
        print(f"\n🌐 You can now test the exit interview workflow at:")
        print(f"   http://localhost:8000/exit-interviews")
        print(f"\n📧 The email-based interview scheduling system is ready to test!")

    except Exception as e:
        print(f"\n❌ Error creating test data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)