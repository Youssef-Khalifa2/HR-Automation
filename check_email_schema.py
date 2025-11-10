"""
Simple script to check if email monitoring database tables exist
"""
import psycopg2
from config import settings

def check_email_tables():
    """Check if email monitoring tables exist in database"""

    print("=" * 60)
    print("Email Monitoring Schema Check")
    print("=" * 60)
    print()

    # Parse database URL
    db_url = settings.DATABASE_URL
    db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")

    # Extract connection parameters
    import re
    pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
    match = re.match(pattern, db_url)

    if not match:
        print("[ERROR] Could not parse database URL")
        return False

    user, password, host, port, database = match.groups()

    try:
        # Connect to database
        print(f"Connecting to database: {database}@{host}:{port}")
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database
        )
        cursor = conn.cursor()
        print("[OK] Connected to database")
        print()

        # Check for email_logs table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'email_logs'
            );
        """)
        email_logs_exists = cursor.fetchone()[0]

        # Check for email_delivery_stats table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'email_delivery_stats'
            );
        """)
        email_stats_exists = cursor.fetchone()[0]

        # Display results
        print("Table Status:")
        print("-" * 60)
        print(f"  email_logs:            {'[EXISTS]' if email_logs_exists else '[MISSING]'}")
        print(f"  email_delivery_stats:  {'[EXISTS]' if email_stats_exists else '[MISSING]'}")
        print()

        if email_logs_exists and email_stats_exists:
            print("[OK] All email monitoring tables exist!")
            print()
            print("Email monitoring endpoints are available at:")
            print("  - http://localhost:8000/api/email-monitoring/email-health")
            print("  - http://localhost:8000/api/email-monitoring/delivery-report")
            print("  - http://localhost:8000/api/email-monitoring/failed-emails")
            result = True
        else:
            print("[NOTICE] Email monitoring tables are missing")
            print()
            print("To enable email monitoring, run:")
            print("  python run_email_tracking_setup.py")
            print()
            print("Note: Email monitoring is OPTIONAL. Your system works fine without it.")
            print("      It's only needed for advanced email delivery tracking.")
            result = False

        cursor.close()
        conn.close()

        print()
        print("=" * 60)
        return result

    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        print()
        print("=" * 60)
        return False


if __name__ == "__main__":
    check_email_tables()
