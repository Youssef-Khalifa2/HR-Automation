"""Test script to verify configuration is working properly"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("Testing configuration...")

    # Test basic imports
    from config import settings, SIGNING_SECRET, BASE_URL
    print("✅ Config imports successful")

    # Test values
    print(f"✅ SIGNING_SECRET: {SIGNING_SECRET[:10]}... (length: {len(SIGNING_SECRET)})")
    print(f"✅ BASE_URL: {BASE_URL}")

    # Test approval token service
    from app.core.security import ApprovalTokenService
    token_service = ApprovalTokenService(SIGNING_SECRET)
    print("✅ ApprovalTokenService created successfully")

    # Test token generation
    test_token = token_service.generate_approval_token(
        submission_id=1,
        action="approve",
        approver_type="leader"
    )
    print(f"✅ Token generated: {test_token[:50]}...")

    # Test token verification
    decoded = token_service.verify_approval_token(test_token)
    print(f"✅ Token verified: submission_id={decoded.get('submission_id')}")

    print("\n🎉 All configuration tests passed! The system should work properly.")

except Exception as e:
    print(f"❌ Configuration test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)