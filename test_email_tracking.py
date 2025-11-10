"""
Test email sending with database tracking
This will send a test email and verify it appears in email_logs table
"""
import asyncio
from app.services.email import EmailMessage, get_email_service
from config import settings

async def test_email_with_tracking():
    """Send a test email and verify tracking"""

    print("=" * 60)
    print("Testing Email Service with Database Tracking")
    print("=" * 60)
    print()

    # Get email service
    email_service = get_email_service()

    # Create test email message
    test_message = EmailMessage(
        to_email=settings.HR_EMAIL,  # Send to HR email for testing
        to_name="Test Recipient",
        subject="Test Email - Email Tracking Verification",
        template_name="hr_notification",
        template_data={
            "employee_name": "Test Employee",
            "employee_email": "test@example.com",
            "message_type": "test",
            "submission_data": {"test": "data"},
            "current_date": "2025-11-10"
        }
    )

    print(f"Sending test email to: {test_message.to_email}")
    print(f"Subject: {test_message.subject}")
    print()

    # Send email
    success = await email_service.send_email(test_message)

    if success:
        print("[OK] Email sent successfully!")
        print()
        print("Now checking database for email log...")
        print()

        # Check database for the log entry
        import time
        time.sleep(1)  # Give database a moment to commit

        from app.database import SessionLocal
        from app.models.email_log import EmailLog

        db = SessionLocal()
        try:
            # Get most recent email log
            recent_log = db.query(EmailLog).order_by(EmailLog.created_at.desc()).first()

            if recent_log:
                print("[OK] Email log found in database!")
                print("-" * 60)
                print(f"  Log ID:        {recent_log.id}")
                print(f"  To:            {recent_log.to_email}")
                print(f"  Subject:       {recent_log.subject}")
                print(f"  Template:      {recent_log.template_name}")
                print(f"  Status:        {recent_log.status}")
                print(f"  Created:       {recent_log.created_at}")
                print(f"  Sent:          {recent_log.sent_at}")
                print(f"  Attempts:      {recent_log.attempts}")
                if recent_log.error_message:
                    print(f"  Error:         {recent_log.error_message}")
                print("-" * 60)
                print()
                print("[OK] Email tracking is working correctly!")
            else:
                print("[WARN] No email log found in database")
                print("This might mean the database logging failed")
        finally:
            db.close()

    else:
        print("[ERROR] Email sending failed!")
        print()
        print("Checking database for failure log...")
        print()

        from app.database import SessionLocal
        from app.models.email_log import EmailLog

        db = SessionLocal()
        try:
            # Get most recent email log
            recent_log = db.query(EmailLog).order_by(EmailLog.created_at.desc()).first()

            if recent_log:
                print("[OK] Email failure logged in database!")
                print("-" * 60)
                print(f"  Log ID:        {recent_log.id}")
                print(f"  To:            {recent_log.to_email}")
                print(f"  Status:        {recent_log.status}")
                print(f"  Error Type:    {recent_log.error_type}")
                print(f"  Error Message: {recent_log.error_message}")
                print(f"  Failed At:     {recent_log.failed_at}")
                print("-" * 60)
                print()
                print("[OK] Email error tracking is working correctly!")
            else:
                print("[WARN] No email log found in database")
        finally:
            db.close()

    print()
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    # Initialize email service
    from app.services.email import create_email_service
    create_email_service()

    asyncio.run(test_email_with_tracking())
