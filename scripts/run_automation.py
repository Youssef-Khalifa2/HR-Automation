#!/usr/bin/env python3
"""
Cron Job Runner for Exit Interview Automation

This script runs the automated workflow triggers for exit interviews.
It can be run manually or scheduled as a cron job.

Usage:
  python run_automation.py

Setup (Linux/Mac):
  # Add to crontab for daily execution at 9 AM:
  0 9 * * * cd /path/to/HR_Automation && python run_automation.py >> automation.log 2>&1

Setup (Windows):
  # Use Task Scheduler to run this script daily at 9 AM
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main automation runner"""
    logger.info("=" * 60)
    logger.info(f"🤖 Starting Exit Interview Automation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        # Import and run the automation service
        from app.services.automation import run_daily_automation
        await run_daily_automation()

        logger.info("=" * 60)
        logger.info("✅ Automation completed successfully")
        logger.info("=" * 60)
        return 0

    except Exception as e:
        logger.error(f"❌ Automation failed: {str(e)}")
        logger.error("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)