"""Setup script for MailHog local email testing"""
import subprocess
import sys
import time
import requests
from pathlib import Path


def check_mailhog_running():
    """Check if MailHog is already running"""
    try:
        response = requests.get("http://localhost:8025/api/v2/messages", timeout=5)
        return response.status_code == 200
    except:
        return False


def start_mailhog():
    """Start MailHog if available"""
    try:
        # Try to check if mailhog command exists
        result = subprocess.run(["mailhog", "--version"],
                              capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            print("MailHog found, starting...")
            # Start MailHog in background
            subprocess.Popen(["mailhog"],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)

            # Wait a moment for it to start
            time.sleep(2)

            if check_mailhog_running():
                print("MailHog started successfully!")
                print("MailHog Web Interface: http://localhost:8025")
                return True
            else:
                print("Failed to start MailHog")
                return False
        else:
            print("MailHog not found")
            return False

    except subprocess.TimeoutExpired:
        print("MailHog command timed out")
        return False
    except FileNotFoundError:
        print("MailHog not installed")
        return False


def print_mailhog_instructions():
    """Print instructions for installing and using MailHog"""
    print("\nMailHog Setup Instructions:")
    print("=" * 50)
    print("\n1. Install MailHog (choose one option):")
    print("   • Windows: Download from https://github.com/mailhog/MailHog/releases")
    print("   • Or use Docker: docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog")
    print("\n2. Start MailHog before testing email functionality")
    print("\n3. Access MailHog web interface at: http://localhost:8025")
    print("\n4. For development, update your .env file:")
    print("   SMTP_HOST=localhost")
    print("   SMTP_PORT=1025")
    print("   SMTP_USERNAME=")
    print("   SMTP_PASSWORD=")
    print("   SMTP_USE_TLS=false")
    print("\n" + "=" * 50)


def main():
    """Main setup function"""
    print("Setting up MailHog for local email testing...")

    if check_mailhog_running():
        print("MailHog is already running!")
        print("MailHog Web Interface: http://localhost:8025")
        return True

    print("MailHog not detected, attempting to start...")

    if start_mailhog():
        return True
    else:
        print_mailhog_instructions()
        print("\nEmail functionality will be limited until MailHog is set up")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)