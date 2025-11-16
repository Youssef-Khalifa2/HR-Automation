"""
Script to add HR_EMAIL_CC configuration setting to the database
"""
from app.database import SessionLocal
# Import all models to avoid relationship errors
from app.models import user, submission, asset, exit_interview, config
from app.models.config import SystemConfig
from config import settings

def add_hr_email_cc_config():
    db = SessionLocal()
    try:
        # New configuration entry
        config_data = {
            "config_key": "HR_EMAIL_CC",
            "config_value": settings.HR_EMAIL_CC,
            "config_type": "string",
            "category": "email",
            "description": "Comma-separated CC email addresses for HR notifications",
            "is_active": True
        }

        print("[INFO] Adding HR_EMAIL_CC configuration...")

        # Check if config already exists
        existing = db.query(SystemConfig).filter(
            SystemConfig.config_key == config_data["config_key"]
        ).first()

        if existing:
            print(f"[SKIP] {config_data['config_key']} already exists with value: {existing.config_value}")
            print(f"[INFO] To update it, use the admin interface or update directly in database")
        else:
            new_config = SystemConfig(**config_data)
            db.add(new_config)
            db.commit()
            print(f"[ADD] {config_data['config_key']}: '{config_data['config_value']}'")
            print(f"[SUCCESS] HR_EMAIL_CC configuration added successfully!")

        # Show all HR email configs
        print("\n[INFO] Current HR email configurations:")
        hr_configs = db.query(SystemConfig).filter(
            SystemConfig.category == 'email',
            SystemConfig.config_key.like('HR_%')
        ).all()
        for config in hr_configs:
            print(f"   - {config.config_key}: {config.config_value}")

    except Exception as e:
        print(f"\n[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Adding HR_EMAIL_CC Configuration")
    print("=" * 60)
    add_hr_email_cc_config()
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
