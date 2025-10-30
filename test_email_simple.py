#!/usr/bin/env python3
"""
Simple test to check if email sending works
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.email import create_email_service, EmailTemplates
from app.core.security import ApprovalTokenService
from config import SIGNING_SECRET

async def test_email_sending():
    """Test if email sending works"""
    print("🔧 Testing Email Service...")

    try:
        # Initialize email service
        email_service = create_email_service()
        print("✅ Email service initialized")

        # Test email template creation
        submission_data = {
            "employee_name": "Test Employee",
            "employee_email": "test@company.com",
            "submission_date": "2024-10-30",
            "last_working_day": "2024-11-30",
            "leader_email": "youssefkhalifa@51talk.com",
            "leader_name": "Team Leader Youssef"
        }

        token_service = ApprovalTokenService(SIGNING_SECRET)
        approval_url = token_service.generate_approval_url(1, "approve", "leader", "http://localhost:8000")

        email_message = EmailTemplates.leader_approval_request(submission_data, approval_url)
        print(f"✅ Email template created")
        print(f"   To: {email_message.to_email}")
        print(f"   Subject: {email_message.subject}")

        # Try to send email
        print("📤 Attempting to send email...")
        success = await email_service.send_email(email_message)

        if success:
            print("✅ Email sent successfully!")
            print(f"   Check {email_message.to_email} for the approval email")
        else:
            print("❌ Email sending failed")
            print("   This might be due to SMTP configuration issues")

        await email_service.close()
        return success

    except Exception as e:
        print(f"❌ Email test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("📧 Simple Email Test")
    print("=" * 50)

    success = asyncio.run(test_email_sending())

    if success:
        print("\n🎉 Email sending works!")
        print("The approval/rejection emails should be working.")
    else:
        print("\n⚠️ Email sending failed.")
        print("This explains why the workflow test doesn't show email functionality.")
        print("Possible causes:")
        print("  - SMTP server connection issues")
        print("  - Authentication problems")
        print("  - Network/firewall blocking")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())