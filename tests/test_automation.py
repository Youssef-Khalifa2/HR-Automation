#!/usr/bin/env python3
"""
Test Exit Interview Automation

This script tests the automated workflow triggers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_automation():
    """Test the automation service"""
    try:
        logger.info("🧪 Testing Exit Interview Automation...")

        # Import the automation service
        from app.services.automation import get_automation_service

        # Get the automation service
        service = get_automation_service()

        # Test HR email configuration
        hr_email = service._get_hr_email()
        it_email = service._get_it_email()

        logger.info(f"✅ HR Email configured: {hr_email}")
        logger.info(f"✅ IT Email configured: {it_email}")

        # Test email service initialization
        from app.services.email import get_email_service
        email_service = get_email_service()
        logger.info("✅ Email service initialized successfully")

        logger.info("🎉 Automation configuration test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Automation test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_automation())
    sys.exit(0 if success else 1)