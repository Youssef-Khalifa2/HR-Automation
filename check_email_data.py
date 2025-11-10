"""
Quick check to see if any emails are logged in the database
"""
import psycopg2
from config import settings
import re

def check_email_data():
    """Check if email_logs table has any data"""

    print("=" * 60)
    print("Email Logs Data Check")
    print("=" * 60)
    print()

    # Parse database URL
    db_url = settings.DATABASE_URL
    db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")

    pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
    match = re.match(pattern, db_url)

    if not match:
        print("[ERROR] Could not parse database URL")
        return

    user, password, host, port, database = match.groups()

    try:
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database
        )
        cursor = conn.cursor()

        # Count total emails
        cursor.execute("SELECT COUNT(*) FROM email_logs;")
        total_count = cursor.fetchone()[0]

        print(f"Total emails logged: {total_count}")
        print()

        if total_count == 0:
            print("[NOTICE] No emails found in database")
            print()
            print("This means the email service is NOT logging emails.")
            print("Emails are being sent, but not tracked in the database.")
            print()
            print("To enable tracking, the email service needs to be")
            print("integrated with the EmailLog model.")
        else:
            print(f"[OK] Found {total_count} emails in database")
            print()

            # Show status breakdown
            cursor.execute("""
                SELECT status, COUNT(*)
                FROM email_logs
                GROUP BY status
                ORDER BY COUNT(*) DESC;
            """)

            print("Email Status Breakdown:")
            print("-" * 60)
            for row in cursor.fetchall():
                status = row[0] or 'unknown'
                count = row[1]
                print(f"  {status:20s} {count:5d}")

            print()

            # Show recent emails
            cursor.execute("""
                SELECT to_email, subject, status, created_at
                FROM email_logs
                ORDER BY created_at DESC
                LIMIT 5;
            """)

            print("Recent Emails (last 5):")
            print("-" * 60)
            for row in cursor.fetchall():
                to_email = row[0]
                subject = row[1][:40] if row[1] else "No subject"
                status = row[2] or 'unknown'
                created_at = row[3]
                print(f"  To: {to_email}")
                print(f"  Subject: {subject}")
                print(f"  Status: {status}")
                print(f"  Time: {created_at}")
                print()

        cursor.close()
        conn.close()

        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        print("=" * 60)

if __name__ == "__main__":
    check_email_data()
