"""Fix HR user password and test authentication"""
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models.user import User
from app.auth import get_password_hash, authenticate_user

def fix_hr_password():
    """Update HR user password to hradmin123"""
    db = SessionLocal()

    try:
        # Get HR user
        hr_user = db.query(User).filter(User.email == "hr@company.com").first()
        if hr_user:
            print(f"Found HR user: {hr_user.email}")
            print(f"Current password hash: {hr_user.password_hash[:50]}...")

            # Update password to hradmin123
            new_password = "hradmin123"
            hr_user.password_hash = get_password_hash(new_password)
            db.commit()
            print(f"✓ Updated HR password to: {new_password}")

            # Test authentication with new password
            print("\n=== Testing Authentication ===")
            test_user = authenticate_user(db, "hr@company.com", new_password)
            if test_user:
                print("✓ Authentication successful!")
                print(f"  User: {test_user.email}")
                print(f"  Role: {test_user.role}")
                print(f"  Active: {test_user.is_active}")
            else:
                print("✗ Authentication failed!")

        else:
            print("HR user not found!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_hr_password()