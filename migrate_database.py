"""
Database Migration Script
Migrates schema and data from source PostgreSQL database to target PostgreSQL database

Usage:
    python migrate_database.py --source <source_db_url> --target <target_db_url>

Example:
    python migrate_database.py \
        --source "postgresql://user:pass@localhost:5432/appdb" \
        --target "postgresql://user:pass@railway.app:5432/railway"
"""

import argparse
import sys
from sqlalchemy import create_engine, inspect, MetaData, Table, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    def __init__(self, source_url: str, target_url: str):
        """Initialize database migrator with source and target URLs"""
        self.source_url = source_url
        self.target_url = target_url
        self.source_engine = None
        self.target_engine = None

    def connect(self):
        """Create database connections"""
        try:
            logger.info("Connecting to source database...")
            self.source_engine = create_engine(self.source_url)
            self.source_engine.connect()
            logger.info("✓ Connected to source database")

            logger.info("Connecting to target database...")
            self.target_engine = create_engine(self.target_url)
            self.target_engine.connect()
            logger.info("✓ Connected to target database")

        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to databases: {e}")
            raise

    def get_table_names(self):
        """Get list of all tables from source database"""
        inspector = inspect(self.source_engine)
        tables = inspector.get_table_names()
        logger.info(f"Found {len(tables)} tables in source database: {', '.join(tables)}")
        return tables

    def migrate_schema(self):
        """Migrate schema from source to target database"""
        logger.info("\n" + "="*60)
        logger.info("STEP 1: MIGRATING SCHEMA")
        logger.info("="*60)

        try:
            # Reflect source schema
            source_metadata = MetaData()
            source_metadata.reflect(bind=self.source_engine)

            # Create all tables in target database
            logger.info("Creating tables in target database...")
            source_metadata.create_all(self.target_engine)
            logger.info("✓ Schema migration completed successfully")

            return True

        except SQLAlchemyError as e:
            logger.error(f"Schema migration failed: {e}")
            return False

    def get_table_dependencies(self):
        """Get tables in dependency order (tables with no foreign keys first)"""
        inspector = inspect(self.source_engine)
        tables = inspector.get_table_names()

        # Simple ordering: tables with no foreign keys first
        tables_with_no_fk = []
        tables_with_fk = []

        for table_name in tables:
            fks = inspector.get_foreign_keys(table_name)
            if not fks:
                tables_with_no_fk.append(table_name)
            else:
                tables_with_fk.append(table_name)

        # Return tables with no FK first, then tables with FK
        return tables_with_no_fk + tables_with_fk

    def migrate_data(self, batch_size=1000):
        """Migrate data from source to target database"""
        logger.info("\n" + "="*60)
        logger.info("STEP 2: MIGRATING DATA")
        logger.info("="*60)

        try:
            # Get tables in dependency order
            table_names = self.get_table_dependencies()

            # Reflect metadata
            source_metadata = MetaData()
            source_metadata.reflect(bind=self.source_engine)

            total_rows = 0

            for table_name in table_names:
                logger.info(f"\nMigrating table: {table_name}")

                table = Table(table_name, source_metadata, autoload_with=self.source_engine)

                # Count rows in source
                with self.source_engine.connect() as source_conn:
                    count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = source_conn.execute(count_query).scalar()

                    if row_count == 0:
                        logger.info(f"  ⊘ Table {table_name} is empty, skipping")
                        continue

                    logger.info(f"  Found {row_count} rows to migrate")

                    # Read data in batches
                    offset = 0
                    migrated = 0

                    while offset < row_count:
                        # Fetch batch from source
                        select_query = table.select().limit(batch_size).offset(offset)
                        rows = source_conn.execute(select_query).fetchall()

                        if not rows:
                            break

                        # Convert to dictionaries
                        rows_dict = [dict(row._mapping) for row in rows]

                        # Insert into target
                        with self.target_engine.connect() as target_conn:
                            target_conn.execute(table.insert(), rows_dict)
                            target_conn.commit()

                        migrated += len(rows)
                        offset += batch_size

                        logger.info(f"  Progress: {migrated}/{row_count} rows ({(migrated/row_count)*100:.1f}%)")

                    total_rows += migrated
                    logger.info(f"  ✓ Migrated {migrated} rows from {table_name}")

            logger.info(f"\n✓ Data migration completed: {total_rows} total rows migrated")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Data migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def update_sequences(self):
        """Update PostgreSQL sequences after data migration"""
        logger.info("\n" + "="*60)
        logger.info("STEP 3: UPDATING SEQUENCES")
        logger.info("="*60)

        try:
            inspector = inspect(self.target_engine)
            tables = inspector.get_table_names()

            with self.target_engine.connect() as conn:
                for table_name in tables:
                    # Check if table has a primary key with sequence
                    pk_columns = inspector.get_pk_constraint(table_name)
                    if pk_columns and pk_columns['constrained_columns']:
                        pk_column = pk_columns['constrained_columns'][0]

                        # Update sequence for this table
                        try:
                            update_seq_query = text(f"""
                                SELECT setval(
                                    pg_get_serial_sequence('{table_name}', '{pk_column}'),
                                    COALESCE((SELECT MAX({pk_column}) FROM {table_name}), 1),
                                    true
                                )
                            """)
                            conn.execute(update_seq_query)
                            logger.info(f"  ✓ Updated sequence for {table_name}.{pk_column}")
                        except Exception as e:
                            logger.warning(f"  ⚠ Could not update sequence for {table_name}.{pk_column}: {e}")

                conn.commit()

            logger.info("✓ Sequence update completed")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Sequence update failed: {e}")
            return False

    def verify_migration(self):
        """Verify that migration was successful"""
        logger.info("\n" + "="*60)
        logger.info("STEP 4: VERIFICATION")
        logger.info("="*60)

        try:
            source_inspector = inspect(self.source_engine)
            target_inspector = inspect(self.target_engine)

            source_tables = set(source_inspector.get_table_names())
            target_tables = set(target_inspector.get_table_names())

            # Check if all tables exist
            if source_tables != target_tables:
                missing = source_tables - target_tables
                extra = target_tables - source_tables
                if missing:
                    logger.error(f"  ✗ Missing tables in target: {missing}")
                if extra:
                    logger.warning(f"  ⚠ Extra tables in target: {extra}")
                return False

            logger.info(f"  ✓ All {len(source_tables)} tables present in target")

            # Check row counts
            all_match = True
            with self.source_engine.connect() as source_conn, \
                 self.target_engine.connect() as target_conn:

                for table_name in source_tables:
                    source_count = source_conn.execute(
                        text(f"SELECT COUNT(*) FROM {table_name}")
                    ).scalar()

                    target_count = target_conn.execute(
                        text(f"SELECT COUNT(*) FROM {table_name}")
                    ).scalar()

                    if source_count != target_count:
                        logger.error(
                            f"  ✗ Row count mismatch in {table_name}: "
                            f"source={source_count}, target={target_count}"
                        )
                        all_match = False
                    else:
                        logger.info(f"  ✓ {table_name}: {source_count} rows")

            if all_match:
                logger.info("\n✓ Verification successful: All data migrated correctly!")
                return True
            else:
                logger.error("\n✗ Verification failed: Data mismatch detected")
                return False

        except SQLAlchemyError as e:
            logger.error(f"Verification failed: {e}")
            return False

    def migrate(self):
        """Execute full migration process"""
        start_time = datetime.now()

        logger.info("\n" + "="*60)
        logger.info("DATABASE MIGRATION STARTED")
        logger.info("="*60)
        logger.info(f"Start time: {start_time}")
        logger.info(f"Source: {self.source_url.split('@')[-1]}")  # Hide credentials
        logger.info(f"Target: {self.target_url.split('@')[-1]}")  # Hide credentials

        try:
            # Connect to databases
            self.connect()

            # Step 1: Migrate schema
            if not self.migrate_schema():
                logger.error("Migration aborted: Schema migration failed")
                return False

            # Step 2: Migrate data
            if not self.migrate_data():
                logger.error("Migration aborted: Data migration failed")
                return False

            # Step 3: Update sequences
            if not self.update_sequences():
                logger.warning("Warning: Sequence update failed (non-critical)")

            # Step 4: Verify migration
            if not self.verify_migration():
                logger.error("Migration completed but verification failed")
                return False

            end_time = datetime.now()
            duration = end_time - start_time

            logger.info("\n" + "="*60)
            logger.info("MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("="*60)
            logger.info(f"Duration: {duration}")
            logger.info(f"End time: {end_time}")

            return True

        except Exception as e:
            logger.error(f"Migration failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Close connections
            if self.source_engine:
                self.source_engine.dispose()
            if self.target_engine:
                self.target_engine.dispose()


def main():
    parser = argparse.ArgumentParser(
        description='Migrate PostgreSQL database schema and data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate from local to Railway
  python migrate_database.py \\
    --source "postgresql://postgres:123@localhost:5432/appdb" \\
    --target "postgresql://user:pass@containers-us-west-1.railway.app:5432/railway"

  # Migrate with environment variables
  export SOURCE_DB="postgresql://postgres:123@localhost:5432/appdb"
  export TARGET_DB="postgresql://user:pass@railway.app:5432/railway"
  python migrate_database.py --source $SOURCE_DB --target $TARGET_DB
        """
    )

    parser.add_argument(
        '--source',
        required=True,
        help='Source database URL (e.g., postgresql://user:pass@host:port/dbname)'
    )

    parser.add_argument(
        '--target',
        required=True,
        help='Target database URL (e.g., postgresql://user:pass@host:port/dbname)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Batch size for data migration (default: 1000)'
    )

    args = parser.parse_args()

    # Confirm before proceeding
    print("\n" + "="*60)
    print("DATABASE MIGRATION")
    print("="*60)
    print(f"Source: {args.source.split('@')[-1]}")
    print(f"Target: {args.target.split('@')[-1]}")
    print("\nWARNING: This will overwrite data in the target database!")

    response = input("\nContinue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        sys.exit(0)

    # Execute migration
    migrator = DatabaseMigrator(args.source, args.target)
    success = migrator.migrate()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
