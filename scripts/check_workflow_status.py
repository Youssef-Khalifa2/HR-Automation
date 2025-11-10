"""Quick script to check current workflow status"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.submission import Submission, ResignationStatus
from app.models.exit_interview import ExitInterview
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_current_status():
    """Check current state of the workflow"""
    print("Current Workflow Status Check")
    print("="*50)

    try:
        db = next(get_db())

        # Check submissions
        print("\nSUBMISSIONS:")
        submissions = db.query(Submission).all()

        status_counts = {}
        for sub in submissions:
            status = sub.resignation_status
            status_counts[status] = status_counts.get(status, 0) + 1

        if submissions:
            print(f"   Total submissions: {len(submissions)}")
            for status, count in status_counts.items():
                print(f"   • {status}: {count}")

            # Show CHM-approved submissions specifically
            chm_approved = [s for s in submissions if s.resignation_status == ResignationStatus.CHM_APPROVED.value]
            if chm_approved:
                print(f"\nCHM-APPROVED SUBMISSIONS ({len(chm_approved)}):")
                for sub in chm_approved[:5]:  # Show first 5
                    print(f"   • {sub.employee_name} (ID: {sub.id}) - {sub.employee_email}")
                if len(chm_approved) > 5:
                    print(f"   ... and {len(chm_approved) - 5} more")
        else:
            print("   No submissions found")

        # Check ExitInterview records
        print(f"\nEXIT INTERVIEW RECORDS:")
        interviews = db.query(ExitInterview).all()

        if interviews:
            print(f"   Total ExitInterview records: {len(interviews)}")

            scheduled = [i for i in interviews if i.scheduled_date and not i.interview_completed]
            completed = [i for i in interviews if i.interview_completed]

            print(f"   • Scheduled (not completed): {len(scheduled)}")
            print(f"   • Completed: {len(completed)}")

            # Show scheduled interviews
            if scheduled:
                print(f"\nSCHEDULED INTERVIEWS:")
                for interview in scheduled[:5]:
                    print(f"   • {interview.submission.employee_name} - {interview.scheduled_date.strftime('%Y-%m-%d')} at {interview.scheduled_time}")
        else:
            print("   No ExitInterview records found")

        # Check upcoming interviews
        print(f"\nUPCOMING INTERVIEWS (Next 7 days):")
        upcoming = db.query(ExitInterview).filter(
            ExitInterview.scheduled_date >= datetime.utcnow(),
            ExitInterview.scheduled_date <= datetime.utcnow() + timedelta(days=7),
            ExitInterview.interview_completed == False
        ).order_by(ExitInterview.scheduled_date).all()

        if upcoming:
            for interview in upcoming:
                days_until = (interview.scheduled_date - datetime.utcnow()).days
                print(f"   • {interview.submission.employee_name} - {interview.scheduled_date.strftime('%Y-%m-%d')} ({days_until} days from now)")
        else:
            print("   No upcoming interviews in the next 7 days")

        db.close()

    except Exception as e:
        print(f"Error checking status: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_current_status()