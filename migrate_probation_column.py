#!/usr/bin/env python3
"""
Migration script to convert in_probation and notice_period_days
from GENERATED columns to regular columns with default values
"""
import sys
import os
from sqlalchemy import create_engine, text

def migrate_probation_columns(database_url: str):
    """
    Convert in_probation and notice_period_days from GENERATED columns to regular columns

    Args:
        database_url: PostgreSQL connection string
    """
    print("="*70)
    print("Migration: Convert GENERATED columns to regular columns")
    print("="*70)
    print(f"\nConnecting to database...")

    try:
        engine = create_engine(database_url)

        with engine.connect() as conn:
            print("Connected successfully!\n")

            # Start transaction
            trans = conn.begin()

            try:
                # Step 1: Drop the generated column constraints
                print("Step 1: Dropping GENERATED column constraint for in_probation...")
                conn.execute(text("""
                    ALTER TABLE submissions
                    ALTER COLUMN in_probation DROP EXPRESSION IF EXISTS;
                """))
                print("  [OK] in_probation is now a regular column")

                print("\nStep 2: Dropping GENERATED column constraint for notice_period_days...")
                conn.execute(text("""
                    ALTER TABLE submissions
                    ALTER COLUMN notice_period_days DROP EXPRESSION IF EXISTS;
                """))
                print("  [OK] notice_period_days is now a regular column")

                # Step 3: Set default values
                print("\nStep 3: Setting default value for in_probation...")
                conn.execute(text("""
                    ALTER TABLE submissions
                    ALTER COLUMN in_probation SET DEFAULT false;
                """))
                print("  [OK] Default value set to false")

                print("\nStep 4: Setting default value for notice_period_days...")
                conn.execute(text("""
                    ALTER TABLE submissions
                    ALTER COLUMN notice_period_days SET DEFAULT 30;
                """))
                print("  [OK] Default value set to 30")

                # Step 5: Update existing NULL values (if any)
                print("\nStep 5: Updating any NULL values in existing records...")
                result = conn.execute(text("""
                    UPDATE submissions
                    SET in_probation = false
                    WHERE in_probation IS NULL;
                """))
                print(f"  [OK] Updated {result.rowcount} rows for in_probation")

                result = conn.execute(text("""
                    UPDATE submissions
                    SET notice_period_days = 30
                    WHERE notice_period_days IS NULL;
                """))
                print(f"  [OK] Updated {result.rowcount} rows for notice_period_days")

                # Commit transaction
                trans.commit()

                print("\n" + "="*70)
                print("[SUCCESS] Migration completed successfully!")
                print("="*70)
                print("\nChanges made:")
                print("  - in_probation: GENERATED -> regular column with DEFAULT false")
                print("  - notice_period_days: GENERATED -> regular column with DEFAULT 30")
                print("\nYou can now insert custom values for these columns.")
                print("="*70)

                return True

            except Exception as e:
                trans.rollback()
                print(f"\n[ERROR] Migration failed: {str(e)}")
                print("Transaction rolled back - no changes made")
                import traceback
                traceback.print_exc()
                return False

    except Exception as e:
        print(f"\n[ERROR] Failed to connect to database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("PostgreSQL Schema Migration Tool")
    print("="*70)

    # Get database URL from command line or environment
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    elif os.getenv("DATABASE_URL"):
        database_url = os.getenv("DATABASE_URL")
        print(f"\nUsing DATABASE_URL from environment")
    else:
        print("\nERROR: No database URL provided!")
        print("\nUsage:")
        print("  python migrate_probation_column.py <database_url>")
        print("\nOr set DATABASE_URL environment variable")
        print("\nExample:")
        print('  python migrate_probation_column.py "postgresql://user:pass@host:port/dbname"')
        print("\n" + "="*70)
        return False

    # Mask password in display
    display_url = database_url
    if "@" in database_url:
        parts = database_url.split("@")
        if ":" in parts[0]:
            user_pass = parts[0].split("://")[1]
            if ":" in user_pass:
                display_url = database_url.replace(user_pass.split(":")[1], "****")

    print(f"Database: {display_url}\n")

    # Confirm before proceeding
    response = input("Do you want to proceed with the migration? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("\nMigration cancelled.")
        return False

    print("")
    success = migrate_probation_columns(database_url)

    if success:
        print("\n[DONE] Migration completed successfully!")
        return True
    else:
        print("\n[FAILED] Migration failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
