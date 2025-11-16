#!/usr/bin/env python3
"""Pre-startup environment check for Railway deployment"""
import os
import sys

print("=" * 80)
print("RAILWAY DEPLOYMENT - PRE-STARTUP CHECK")
print("=" * 80)

# Check critical environment variables
required_vars = {
    "DATABASE_URL": "PostgreSQL database connection string",
    "SECRET_KEY": "JWT token encryption key",
    "SIGNING_SECRET": "API request signing key",
}

optional_vars = {
    "PORT": "Server port (provided by Railway)",
    "RAILWAY_ENVIRONMENT": "Railway environment name",
    "RAILWAY_PUBLIC_DOMAIN": "Railway public domain",
    "EMAIL_PROVIDER": "Email service provider",
    "SENDGRID_API_KEY": "SendGrid API key",
    "HR_EMAIL": "HR department email",
    "IT_EMAIL": "IT department email",
}

print("\n[CHECK] Required Environment Variables:")
missing_required = []
for var, desc in required_vars.items():
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if var in ["SECRET_KEY", "SIGNING_SECRET", "SENDGRID_API_KEY"]:
            display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
        elif var == "DATABASE_URL":
            # Show only host/port
            display_value = value.split('@')[-1] if '@' in value else "localhost"
        else:
            display_value = value
        print(f"  ✓ {var}: {display_value}")
    else:
        print(f"  ✗ {var}: NOT SET - {desc}")
        missing_required.append(var)

print("\n[CHECK] Optional Environment Variables:")
for var, desc in optional_vars.items():
    value = os.getenv(var)
    if value:
        if var in ["SENDGRID_API_KEY"]:
            display_value = f"{value[:8]}...{value[-4:]}"
        else:
            display_value = value
        print(f"  ✓ {var}: {display_value}")
    else:
        print(f"  ○ {var}: Not set - {desc}")

print("\n" + "=" * 80)

if missing_required:
    print(f"⚠️  WARNING: Missing {len(missing_required)} required environment variable(s)")
    print("\nPlease set the following in Railway dashboard:")
    for var in missing_required:
        print(f"  - {var}: {required_vars[var]}")
    print("\nRefer to RAILWAY_SETUP_GUIDE.md for detailed instructions")
    print("\n⚠️  Application will attempt to start with default values")
    print("=" * 80)
else:
    print("✅ All required environment variables are set")
    print("=" * 80)

# Always exit 0 to allow app to start
print("\nProceeding with application startup...")
sys.exit(0)
