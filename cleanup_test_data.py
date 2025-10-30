#!/usr/bin/env python3
"""
Clean up test data from Phase 2 testing
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database import SessionLocal
from app.crud import get_submission_by_email

def cleanup_test_data():
    """Clean up test submissions"""
    db = SessionLocal()
    try:
        # Test emails to clean up
        test_emails = [
            "phase2test@company.com",
            "feishutest@company.com",
            "dbtest@company.com",
            "workflowtest@company.com",
            "rejectiontest@company.com",
            "testemployee@company.com",
            "testemployee2@company.com",
            "testemployee3@company.com",
            "testemployee4@company.com"
        ]

        cleaned_count = 0
        for email in test_emails:
            submission = get_submission_by_email(db, email)
            if submission:
                db.delete(submission)
                cleaned_count += 1
                print(f"✅ Deleted test submission: {email}")

        db.commit()
        print(f"\n🧹 Cleanup complete! Removed {cleaned_count} test submissions")

    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🧹 Cleaning up Phase 2 test data...")
    cleanup_test_data()
    print("✅ Test data cleanup completed!")