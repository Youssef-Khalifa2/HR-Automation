"""
Script to add new email configuration settings to the database
"""
from app.database import SessionLocal
# Import all models to avoid relationship errors
from app.models import user, submission, asset, exit_interview, config
from app.models.config import SystemConfig
from config import settings

def add_email_configs():
    db = SessionLocal()
    try:
        # New configuration entries
        new_configs = [
            {
                "config_key": "EMAIL_PROVIDER",
                "config_value": settings.EMAIL_PROVIDER,
                "config_type": "string",
                "category": "email",
                "description": "Email provider to use (sendgrid or smtp)",
                "is_active": True
            },
            {
                "config_key": "SMTP_USER",
                "config_value": settings.SMTP_USER,
                "config_type": "string",
                "category": "email",
                "description": "SMTP username for authentication",
                "is_active": True
            },
            {
                "config_key": "SMTP_PASSWORD",
                "config_value": settings.SMTP_PASS,
                "config_type": "string",
                "category": "email",
                "description": "SMTP password for authentication",
                "is_active": True
            },
            {
                "config_key": "VENDOR_MIGRATE_EMAIL",
                "config_value": "hrcrm@migratebusiness.com",
                "config_type": "email",
                "category": "vendor",
                "description": "Email address for Migrate Business vendor",
                "is_active": True
            },
            {
                "config_key": "VENDOR_JUSTHR_EMAIL_1",
                "config_value": "r.kandil@jhr-services.com",
                "config_type": "email",
                "category": "vendor",
                "description": "Just HR primary email address",
                "is_active": True
            },
            {
                "config_key": "VENDOR_JUSTHR_EMAIL_2",
                "config_value": "m.khaled@jhr-services.com",
                "config_type": "email",
                "category": "vendor",
                "description": "Just HR secondary email address",
                "is_active": True
            }
        ]

        print("[INFO] Adding new email configuration settings...")

        for config_data in new_configs:
            # Check if config already exists
            existing = db.query(SystemConfig).filter(
                SystemConfig.config_key == config_data["config_key"]
            ).first()

            if existing:
                print(f"[SKIP] {config_data['config_key']} already exists")
            else:
                new_config = SystemConfig(**config_data)
                db.add(new_config)
                print(f"[ADD] {config_data['config_key']}: {config_data['config_value']}")

        db.commit()
        print("\n[SUCCESS] All new email configurations added successfully!")

        # Show all email configs
        print("\n[INFO] Current email configurations:")
        all_configs = db.query(SystemConfig).filter(
            SystemConfig.category.in_(['email', 'vendor'])
        ).all()
        for config in all_configs:
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
    print("Adding New Email Configuration Settings")
    print("=" * 60)
    add_email_configs()
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
