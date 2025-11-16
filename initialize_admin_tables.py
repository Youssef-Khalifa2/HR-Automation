"""
Initialize admin configuration tables in the database
This script creates the system_config and team_mapping tables if they don't exist
"""
from sqlalchemy import text
from app.database import SessionLocal, engine, Base
from app.models.config import SystemConfig, TeamMapping
# Import all models to ensure they're registered
from app.models import user, submission, asset, exit_interview, config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_admin_tables():
    """Create admin configuration tables"""
    try:
        logger.info("Creating admin configuration tables...")

        # Create tables using SQLAlchemy Base metadata
        Base.metadata.create_all(bind=engine)

        logger.info("✅ Admin tables created successfully!")
        logger.info("   - system_config table")
        logger.info("   - team_mapping table")

        # Check if tables exist
        db = SessionLocal()
        try:
            config_count = db.query(SystemConfig).count()
            mapping_count = db.query(TeamMapping).count()

            logger.info(f"\n📊 Current data:")
            logger.info(f"   System Config entries: {config_count}")
            logger.info(f"   Team Mapping entries: {mapping_count}")

        finally:
            db.close()

        return True

    except Exception as e:
        logger.error(f"❌ Failed to create admin tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def seed_default_config():
    """Seed default configuration values from environment"""
    try:
        from config import settings

        db = SessionLocal()

        try:
            logger.info("\n🌱 Seeding default configuration values...")

            # Check if config already exists
            existing_count = db.query(SystemConfig).count()
            if existing_count > 0:
                logger.info(f"   Configuration already exists ({existing_count} entries). Skipping seed.")
                return True

            # Default configurations to seed
            default_configs = [
                {
                    "config_key": "HR_EMAIL",
                    "config_value": settings.HR_EMAIL,
                    "config_type": "email",
                    "category": "email",
                    "description": "Primary HR contact email address"
                },
                {
                    "config_key": "IT_EMAIL",
                    "config_value": settings.IT_EMAIL,
                    "config_type": "email",
                    "category": "email",
                    "description": "IT support email address"
                },
                {
                    "config_key": "SENDGRID_API_KEY",
                    "config_value": settings.SENDGRID_API_KEY,
                    "config_type": "string",
                    "category": "email",
                    "description": "SendGrid API key for email delivery"
                },
                {
                    "config_key": "SMTP_HOST",
                    "config_value": settings.SMTP_HOST,
                    "config_type": "string",
                    "category": "email",
                    "description": "SMTP server host"
                },
                {
                    "config_key": "SMTP_PORT",
                    "config_value": str(settings.SMTP_PORT),
                    "config_type": "integer",
                    "category": "email",
                    "description": "SMTP server port"
                },
                {
                    "config_key": "SMTP_FROM_EMAIL",
                    "config_value": settings.SMTP_FROM_EMAIL,
                    "config_type": "email",
                    "category": "email",
                    "description": "From email address for outgoing emails"
                },
                {
                    "config_key": "SMTP_FROM_NAME",
                    "config_value": settings.SMTP_FROM_NAME,
                    "config_type": "string",
                    "category": "email",
                    "description": "From name for outgoing emails"
                },
                {
                    "config_key": "APP_BASE_URL",
                    "config_value": settings.APP_BASE_URL,
                    "config_type": "string",
                    "category": "system",
                    "description": "Application base URL"
                },
                {
                    "config_key": "FRONTEND_URL",
                    "config_value": settings.FRONTEND_URL,
                    "config_type": "string",
                    "category": "system",
                    "description": "Frontend application URL"
                },
                {
                    "config_key": "ENABLE_AUTO_REMINDERS",
                    "config_value": str(settings.ENABLE_AUTO_REMINDERS),
                    "config_type": "boolean",
                    "category": "system",
                    "description": "Enable automated reminder system"
                },
                {
                    "config_key": "REMINDER_THRESHOLD_HOURS",
                    "config_value": str(settings.REMINDER_THRESHOLD_HOURS),
                    "config_type": "integer",
                    "category": "system",
                    "description": "Hours before sending first reminder"
                }
            ]

            # Insert default configurations
            for config_data in default_configs:
                config = SystemConfig(**config_data, updated_by="system_init")
                db.add(config)

            db.commit()
            logger.info(f"✅ Seeded {len(default_configs)} default configuration values")

            return True

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to seed default config: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Failed to seed default config: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Admin Configuration Database Initialization")
    print("=" * 60)

    # Create tables
    if initialize_admin_tables():
        print("\n✅ Tables created successfully")

        # Seed default configuration
        if seed_default_config():
            print("✅ Default configuration seeded successfully")
        else:
            print("⚠️  Failed to seed default configuration")

        print("\n" + "=" * 60)
        print("Initialization complete!")
        print("=" * 60)
    else:
        print("\n❌ Failed to initialize tables")
        exit(1)
