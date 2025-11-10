#!/usr/bin/env python3
"""
Setup Phase 3 Database Tables

This script creates the exit interview tables needed for Phase 3.
Run this before running the test suite.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from config import DATABASE_URL
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Setup Phase 3 database tables"""
    try:
        logger.info("Setting up Phase 3 database tables...")

        # Create database engine
        engine = create_engine(DATABASE_URL)

        # Read and execute SQL script
        with open("create_exit_interview_tables.sql", "r") as f:
            sql_script = f.read()

        # Split into individual statements
        statements = sql_script.split(';')

        with engine.connect() as conn:
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                        logger.info(f"Executed: {statement[:50]}...")
                    except Exception as e:
                        if "already exists" not in str(e):
                            logger.warning(f"SQL Warning: {e}")

        logger.info("[OK] Phase 3 database setup completed!")
        return True

    except Exception as e:
        logger.error(f"[ERROR] Database setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)