"""Database migration script to add last_reminded_at column to submissions table"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from config import DATABASE_URL

def add_last_reminded_at_column():
    """Add last_reminded_at column to submissions table"""
    print("🔄 Adding last_reminded_at column to submissions table...")

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'submissions'
                AND column_name = 'last_reminded_at'
            """)).fetchone()

            if result:
                print("✅ Column 'last_reminded_at' already exists")
                return True

            # Add the column
            conn.execute(text("""
                ALTER TABLE submissions
                ADD COLUMN last_reminded_at TIMESTAMPTZ NULL
            """))

            conn.commit()
            print("✅ Successfully added 'last_reminded_at' column to submissions table")
            return True

    except Exception as e:
        print(f"❌ Failed to add column: {str(e)}")
        return False
    finally:
        engine.dispose()

def verify_column_added():
    """Verify that the column was added successfully"""
    print("🔍 Verifying column was added...")

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'submissions'
                AND column_name = 'last_reminded_at'
            """)).fetchone()

            if result:
                print(f"✅ Column verified: {result.column_name} ({result.data_type}, nullable={result.is_nullable})")
                return True
            else:
                print("❌ Column not found after creation")
                return False

    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("=== Database Migration: Add last_reminded_at Column ===")

    success = add_last_reminded_at_column()
    if success:
        verify_column_added()
        print("\n🎉 Migration completed successfully!")
        print("You can now use the reminder functionality in Phase 2.")
    else:
        print("\n❌ Migration failed. Please check the error above and try again.")