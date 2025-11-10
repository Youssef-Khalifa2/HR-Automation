"""
Script to create email tracking tables using psycopg2
Run this to set up the email logging and monitoring tables
"""
import psycopg2
from psycopg2 import sql
from config import DATABASE_URL
import sys
import re

def parse_database_url(url):
    """Convert SQLAlchemy URL to psycopg2 connection parameters"""
    # Remove the SQLAlchemy driver part (postgresql+psycopg2:// or postgresql://)
    url = re.sub(r'postgresql\+psycopg2?://', 'postgresql://', url)

    # Parse URL format: postgresql://user:password@host:port/database
    pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
    match = re.match(pattern, url)

    if match:
        user, password, host, port, database = match.groups()
        return {
            'user': user,
            'password': password,
            'host': host,
            'port': port,
            'database': database
        }
    else:
        raise ValueError(f"Invalid DATABASE_URL format: {url}")

def create_email_tracking_tables():
    """Read and execute the SQL file to create email tracking tables"""

    # Read the SQL file
    sql_file_path = 'create_email_tracking_tables.sql'

    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_commands = f.read()

        print(f"[OK] Successfully read {sql_file_path}")

    except FileNotFoundError:
        print(f"[ERROR] Could not find {sql_file_path}")
        print(f"  Make sure you're running this script from the project root directory")
        return False
    except Exception as e:
        print(f"[ERROR] Error reading SQL file: {e}")
        return False

    # Connect to database and execute SQL
    conn = None
    try:
        print(f"\nConnecting to database...")

        # Parse DATABASE_URL to get connection parameters
        conn_params = parse_database_url(DATABASE_URL)
        print(f"  Database: {conn_params['database']}")
        print(f"  Host: {conn_params['host']}:{conn_params['port']}")

        # Connect using parsed parameters
        conn = psycopg2.connect(
            user=conn_params['user'],
            password=conn_params['password'],
            host=conn_params['host'],
            port=conn_params['port'],
            database=conn_params['database']
        )

        print("[OK] Connected to database")

        # Create a cursor
        cur = conn.cursor()

        # Execute the SQL commands
        print(f"\nExecuting SQL commands...")
        cur.execute(sql_commands)

        # Commit the changes
        conn.commit()

        print("[OK] Successfully created email tracking tables")

        # Verify tables were created
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('email_logs', 'email_delivery_stats')
            ORDER BY table_name;
        """)

        tables = cur.fetchall()

        if tables:
            print(f"\n[OK] Verified tables created:")
            for table in tables:
                print(f"  - {table[0]}")

        # Close cursor
        cur.close()

        return True

    except psycopg2.Error as e:
        print(f"\n[ERROR] Database error: {e}")
        if conn:
            conn.rollback()
        return False

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        if conn:
            conn.rollback()
        return False

    finally:
        if conn:
            conn.close()
            print("\n[OK] Database connection closed")


if __name__ == "__main__":
    print("=" * 60)
    print("Email Tracking Tables Setup")
    print("=" * 60)
    print()

    success = create_email_tracking_tables()

    print()
    print("=" * 60)

    if success:
        print("[OK] Setup completed successfully!")
        sys.exit(0)
    else:
        print("[ERROR] Setup failed. Please check the errors above.")
        sys.exit(1)
