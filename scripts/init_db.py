"""Database initialization script"""
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from app.database import Base, SessionLocal
from app.models.user import User
from app.auth import get_password_hash

def init_database():
    """Initialize database with tables and seed data"""
    print("Initializing database...")

    # Note: Tables already exist, so we won't create them
    print("[+] Using existing database tables")

    # Create session
    db = SessionLocal()

    try:
        # Check if HR user already exists
        hr_user = db.query(User).filter(User.email == "hr@company.com").first()
        if not hr_user:
            # Create default HR user
            hr_user = User(
                email="hr@company.com",
                password_hash=get_password_hash("hr123456"),  # Change this in production
                full_name="HR Administrator",
                role="hr",  # Use string instead of enum
                is_active=True
            )
            db.add(hr_user)
            print("[+] Default HR user created (hr@company.com / hr123456)")

        # Create sample users for testing
        sample_users = [
            {
                "email": "leader@company.com",
                "password": "leader123",
                "full_name": "Team Leader",
                "role": "leader"
            },
            {
                "email": "chm@company.com",
                "password": "chm123",
                "full_name": "Chinese Head Manager",
                "role": "chm"
            },
            {
                "email": "it@company.com",
                "password": "it123",
                "full_name": "IT Support",
                "role": "it"
            }
        ]

        for user_data in sample_users:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing_user:
                user = User(
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    is_active=True
                )
                db.add(user)
                print(f"[+] Sample {user_data['role']} user created ({user_data['email']})")

        db.commit()
        print("[+] Database initialization completed successfully!")

    except Exception as e:
        print(f"[-] Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()