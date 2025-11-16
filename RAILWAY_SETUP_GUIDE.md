# Railway Deployment - Step-by-Step Guide

Complete guide to deploying HR Automation System on Railway.app from scratch.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Step 1: Create Railway Account](#step-1-create-railway-account)
- [Step 2: Create New Project](#step-2-create-new-project)
- [Step 3: Add PostgreSQL Database](#step-3-add-postgresql-database)
- [Step 4: Configure Environment Variables](#step-4-configure-environment-variables)
- [Step 5: Deploy Application](#step-5-deploy-application)
- [Step 6: Migrate Database](#step-6-migrate-database)
- [Step 7: Create Admin User](#step-7-create-admin-user)
- [Step 8: Configure Application](#step-8-configure-application)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

✅ GitHub account with your code repository
✅ SendGrid account and API key (or SMTP credentials)
✅ Local database backup (if migrating data)

---

## Step 1: Create Railway Account

1. Go to [Railway.app](https://railway.app)
2. Click **"Start a New Project"** or **"Login"**
3. Sign up/login with GitHub
4. Authorize Railway to access your GitHub repositories

---

## Step 2: Create New Project

1. **On Railway Dashboard:**
   - Click **"New Project"**
   - Select **"Deploy from GitHub repo"**

2. **Select Repository:**
   - Choose **"HR-Automation"** from the list
   - If not visible, click **"Configure GitHub App"** to grant access

3. **Initial Deployment:**
   - Railway will detect your Dockerfile
   - Click **"Deploy Now"**
   - ⚠️ First deployment will fail (needs database and environment variables)

---

## Step 3: Add PostgreSQL Database

1. **In Your Project:**
   - Click **"New"** button (top right)
   - Select **"Database"**
   - Choose **"PostgreSQL"**

2. **Railway Automatically:**
   - Creates PostgreSQL instance
   - Generates DATABASE_URL
   - Links it to your service

3. **Verify Database:**
   - Click on PostgreSQL service
   - Go to **"Variables"** tab
   - You should see `DATABASE_URL` variable

4. **Link Database to Service:**
   - Click on your app service (not database)
   - Go to **"Variables"** tab
   - DATABASE_URL should appear automatically
   - If not, click **"New Variable"** → **"Add Reference"** → Select PostgreSQL's DATABASE_URL

---

## Step 4: Configure Environment Variables

### 4.1 Access Variables Tab

1. Click on your **app service** (not the database)
2. Go to **"Variables"** tab
3. Click **"New Variable"**

### 4.2 Required Variables

Add these variables one by one:

#### Security Keys (Generate These First)

**On your local computer, run:**
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate SIGNING_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**In Railway, add:**

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `SECRET_KEY` | `<paste-generated-key>` | JWT token encryption |
| `SIGNING_SECRET` | `<paste-generated-key>` | API request signing |

#### Email Configuration

**For SendGrid (Recommended):**

| Variable Name | Value | Example |
|--------------|-------|---------|
| `EMAIL_PROVIDER` | `sendgrid` | sendgrid |
| `SENDGRID_API_KEY` | `<your-api-key>` | SG.xxx... |
| `SMTP_FROM_EMAIL` | `<sender-email>` | noreply@company.com |
| `SMTP_FROM_NAME` | `HR Automation System` | HR Automation System |

**For SMTP (Alternative):**

| Variable Name | Value | Example |
|--------------|-------|---------|
| `EMAIL_PROVIDER` | `smtp` | smtp |
| `SMTP_HOST` | `<smtp-server>` | smtp.gmail.com |
| `SMTP_PORT` | `465` or `587` | 465 |
| `SMTP_USER` | `<email>` | user@company.com |
| `SMTP_PASS` | `<password>` | your-password |
| `SMTP_FROM_EMAIL` | `<sender-email>` | noreply@company.com |
| `SMTP_FROM_NAME` | `HR Automation System` | HR Automation System |

#### Email Recipients

| Variable Name | Value | Example |
|--------------|-------|---------|
| `HR_EMAIL` | `<hr-email>` | hr@company.com |
| `HR_EMAIL_CC` | `<cc-emails>` | manager@company.com,supervisor@company.com |
| `IT_EMAIL` | `<it-email>` | it@company.com |

#### Optional Variables

| Variable Name | Default | Description |
|--------------|---------|-------------|
| `ENABLE_AUTO_REMINDERS` | `true` | Enable/disable reminders |
| `REMINDER_THRESHOLD_HOURS` | `24` | Hours before sending reminder |

### 4.3 How to Add Each Variable

For each variable above:

1. Click **"New Variable"**
2. Enter **Variable Name** (exactly as shown)
3. Enter **Value**
4. Click **"Add"**
5. Repeat for next variable

### 4.4 Variables You DON'T Need to Set

These are **AUTO-DETECTED** by the app:

- ❌ `APP_BASE_URL` - Auto-detected from Railway
- ❌ `FRONTEND_URL` - Auto-detected from Railway
- ❌ `DATABASE_URL` - Provided by Railway PostgreSQL
- ❌ `PORT` - Provided by Railway
- ❌ `RAILWAY_ENVIRONMENT` - Provided by Railway

---

## Step 5: Deploy Application

### 5.1 Trigger Deployment

After adding all variables:
1. Variables are saved automatically
2. Railway will trigger a new deployment
3. Click **"Deployments"** tab to watch progress

### 5.2 Monitor Deployment

**Watch the logs:**
1. Click on the latest deployment
2. View **Build Logs** - Should show Docker building
3. View **Deploy Logs** - Should show application starting
4. Look for: `"HR Automation System - Configuration"` output

**Successful deployment shows:**
```
Environment: production
Base URL: https://your-app.up.railway.app
Database: containers-us-west-xxx.railway.app:5432/railway
Email Provider: sendgrid
HR Email: hr@company.com
```

### 5.3 Get Your Application URL

1. Go to **"Settings"** tab
2. Scroll to **"Networking"**
3. Click **"Generate Domain"**
4. Your app URL: `https://your-app-name.up.railway.app`

---

## Step 6: Migrate Database

### 6.1 Get Railway Database URL

1. Click on **PostgreSQL** service
2. Go to **"Variables"** tab
3. Find and copy the `DATABASE_URL` value
   - Format: `postgresql://postgres:password@host:port/railway`

### 6.2 Run Migration Script

**On your local computer:**

```bash
# Navigate to project directory
cd "HR Automation"

# Install dependencies (if not already done)
pip install sqlalchemy psycopg2-binary

# Run migration
python migrate_database.py \
  --source "postgresql://postgres:123@localhost:5432/appdb" \
  --target "postgresql://postgres:password@host:port/railway"
```

**Replace:**
- Source: Your local database URL
- Target: Railway DATABASE_URL (from step 6.1)

**Migration will:**
- ✅ Copy all table schemas
- ✅ Migrate all data in batches
- ✅ Update sequences (auto-increment IDs)
- ✅ Verify data integrity

---

## Step 7: Create Admin User

### 7.1 Using Railway CLI (Recommended)

**Install Railway CLI:**
```bash
npm install -g @railway/cli
```

**Login and run command:**
```bash
# Login
railway login

# Link to your project
railway link

# Create admin user
railway run python -c "from app.auth import create_user; from app.database import SessionLocal; db = SessionLocal(); create_user(db, 'hr@company.com', 'YourPassword123', 'HR Admin', 'admin'); print('Admin user created!'); db.close()"
```

### 7.2 Alternative: Using Python Script

Create file `create_admin.py`:
```python
from app.auth import create_user
from app.database import SessionLocal

db = SessionLocal()
try:
    create_user(
        db=db,
        email="hr@company.com",
        password="YourSecurePassword123",
        full_name="HR Admin",
        role="admin"
    )
    print("✅ Admin user created successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    db.close()
```

**Run on Railway:**
```bash
railway run python create_admin.py
```

---

## Step 8: Configure Application

### 8.1 Login to Admin Panel

1. Go to your app URL: `https://your-app.up.railway.app`
2. Login with admin credentials
3. Navigate to **"Admin"** tab

### 8.2 Configure Settings

**In Admin Panel:**

1. **Email Configuration**
   - Verify email provider settings
   - Update vendor email addresses:
     - Migrate Business email
     - Just HR emails (primary & secondary)

2. **Team Mappings**
   - Add department mappings
   - Assign team leaders
   - Configure CHM emails
   - Set vendor preferences

3. **Test Email**
   - Create a test submission
   - Verify emails are sent successfully

---

## Verification

### ✅ Checklist

- [ ] Application URL is accessible
- [ ] Health check passes: `https://your-app.up.railway.app/api/public/health`
- [ ] Login works with admin credentials
- [ ] Database connection successful
- [ ] Admin panel accessible
- [ ] Email sending works
- [ ] All team mappings configured

### Test Endpoints

```bash
# Health check
curl https://your-app.up.railway.app/api/public/health

# API documentation
https://your-app.up.railway.app/docs
```

---

## Troubleshooting

### Deployment Fails

**Check Build Logs:**
1. Go to **"Deployments"** tab
2. Click failed deployment
3. View logs for errors

**Common Issues:**
- Missing environment variables
- Invalid DATABASE_URL format
- Docker build errors

### Health Check Fails

**Check Deploy Logs:**
```
Application not responding on port $PORT
```

**Solution:**
- Ensure app binds to `0.0.0.0:$PORT`
- Check for Python errors in logs
- Verify DATABASE_URL is set

### Database Connection Error

**Error:** `could not connect to server`

**Check:**
1. DATABASE_URL is set correctly
2. PostgreSQL service is running
3. Database is linked to app service

**Fix:**
1. Go to PostgreSQL service
2. Go to **"Variables"**
3. Copy DATABASE_URL
4. Go to app service → **"Variables"**
5. Add/update DATABASE_URL

### Email Not Sending

**Check:**
1. SendGrid API key is valid
2. Sender email is verified in SendGrid
3. HR_EMAIL is set correctly

**View Logs:**
```bash
railway logs
```

Look for email-related errors

### Cannot Login

**Check:**
1. Admin user was created (Step 7)
2. Password is correct
3. Database migration completed

**Recreate Admin User:**
```bash
railway run python create_admin.py
```

---

## Environment Variables Quick Reference

### Minimal Required Variables

```bash
# Security (Generate these!)
SECRET_KEY=<generated-key>
SIGNING_SECRET=<generated-key>

# Email (SendGrid)
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=<your-key>
SMTP_FROM_EMAIL=noreply@company.com

# Recipients
HR_EMAIL=hr@company.com
IT_EMAIL=it@company.com
```

### Complete Variables List

```bash
# Security
SECRET_KEY=<generated>
SIGNING_SECRET=<generated>

# Email Provider
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=<key>

# Email Sending
SMTP_FROM_EMAIL=noreply@company.com
SMTP_FROM_NAME=HR Automation System

# Recipients
HR_EMAIL=hr@company.com
HR_EMAIL_CC=manager@company.com,supervisor@company.com
IT_EMAIL=it@company.com

# Optional
ENABLE_AUTO_REMINDERS=true
REMINDER_THRESHOLD_HOURS=24
```

---

## Next Steps

After successful deployment:

1. ✅ Configure team mappings
2. ✅ Test submission workflow
3. ✅ Verify email notifications
4. ✅ Set up monitoring
5. ✅ Configure backups (Railway provides automatic backups)

---

## Support

**Railway Documentation:**
- [Railway Docs](https://docs.railway.app)
- [Environment Variables](https://docs.railway.app/develop/variables)
- [PostgreSQL](https://docs.railway.app/databases/postgresql)

**Application Issues:**
- Check Railway logs: `railway logs`
- Review deploy logs in Railway dashboard
- See main DEPLOYMENT.md for additional help

---

**Deployment Complete!** 🎉

Your HR Automation System is now running on Railway.
