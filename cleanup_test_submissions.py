"""Quick script to clean up test submissions from database"""
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

def cleanup_test_submissions():
    """Remove all test submissions from the database"""
    print("🧹 Cleaning up test submissions from database...")

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Delete submissions with test email patterns
            patterns = [
                "workflowtest%",
                "localtest%",
                "dbtest_%",
                "phase2test@company.com",
                "feishutest@company.com"
            ]

            total_deleted = 0
            for pattern in patterns:
                if "%" in pattern:
                    # Pattern-based deletion
                    result = conn.execute(text(
                        "DELETE FROM submissions WHERE employee_email LIKE :pattern"
                    ), {"pattern": pattern})
                    deleted_count = result.rowcount
                else:
                    # Exact match deletion
                    result = conn.execute(text(
                        "DELETE FROM submissions WHERE employee_email = :email"
                    ), {"email": pattern})
                    deleted_count = result.rowcount

                total_deleted += deleted_count
                print(f"✅ Deleted {deleted_count} submissions with pattern: {pattern}")

            # Also delete any associated assets
            result = conn.execute(text("""
                DELETE FROM assets WHERE res_id IN (
                    SELECT id FROM submissions WHERE employee_email LIKE 'workflowtest%'
                    OR employee_email LIKE 'localtest%'
                    OR employee_email LIKE 'dbtest_%'
                )
            """))
            assets_deleted = result.rowcount
            if assets_deleted > 0:
                print(f"✅ Deleted {assets_deleted} associated asset records")

            conn.commit()

            if total_deleted == 0:
                print("✅ No test submissions found to delete")
            else:
                print(f"🎉 Successfully cleaned up {total_deleted} test submissions!")

            return True

    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("=== Test Submission Cleanup ===")
    success = cleanup_test_submissions()

    if success:
        print("\n✅ Cleanup completed! You can now run your workflow tests.")
    else:
        print("\n❌ Cleanup failed. Please check the error above.")