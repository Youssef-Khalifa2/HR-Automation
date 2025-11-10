"""
Fix script: Make updated_at column nullable in assets table
"""
from sqlalchemy import create_engine, text
from config import DATABASE_URL

try:
    print("Connecting to PostgreSQL database...")
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print("Making updated_at column nullable...")

        # Make updated_at nullable
        conn.execute(text("ALTER TABLE assets ALTER COLUMN updated_at DROP NOT NULL"))
        conn.commit()

        print("✓ Column updated successfully!")

        # Verify the change
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'assets' AND column_name = 'updated_at'
        """))

        col = result.fetchone()
        if col:
            print(f"\nVerification:")
            print(f"  {col[0]}: {col[1]} - {'NULL' if col[2] == 'YES' else 'NOT NULL'}")

    engine.dispose()
    print("\nDatabase connection closed.")
    print("\n✓ Fix applied successfully! Please restart the backend.")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
