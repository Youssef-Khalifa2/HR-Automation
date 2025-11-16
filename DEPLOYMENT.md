# HR Automation System - Deployment Guide

Complete guide for deploying the HR Automation System to production.

## Quick Start

**For Railway (Recommended):** See **[RAILWAY_SETUP_GUIDE.md](RAILWAY_SETUP_GUIDE.md)** for detailed step-by-step instructions with screenshots and explanations.

**For Docker:** See [Docker Deployment](#docker-deployment) below.

---

## Table of Contents
- [Railway Deployment](#railway-deployment-recommended)
- [Docker Deployment](#docker-deployment)
- [Database Migration](#database-migration)
- [Environment Variables](#environment-variables)
- [Post-Deployment](#post-deployment)
- [Troubleshooting](#troubleshooting)

---

## Railway Deployment (Recommended)

### Why Railway?
- ✅ **Automatic URL detection** - No need to configure APP_BASE_URL
- ✅ **PostgreSQL included** - Database provided and configured automatically
- ✅ **Easy setup** - Deploy in minutes
- ✅ **Auto HTTPS** - SSL certificates included
- ✅ **Automatic backups** - Database backups included

### Quick Setup

1. **Deploy to Railway:**
   ```bash
   git push origin main
   ```
   - Go to [Railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub"
   - Select "HR-Automation" repository

2. **Add PostgreSQL:**
   - Click "New" → "Database" → "PostgreSQL"
   - DATABASE_URL is automatically linked

3. **Set Environment Variables:**
   ```bash
   # Required (Set in Railway dashboard)
   SECRET_KEY=<generate-with-python>
   SIGNING_SECRET=<generate-with-python>
   EMAIL_PROVIDER=sendgrid
   SENDGRID_API_KEY=<your-key>
   SMTP_FROM_EMAIL=noreply@company.com
   HR_EMAIL=hr@company.com
   IT_EMAIL=it@company.com
   ```

4. **Optional Variables:**
   ```bash
   HR_EMAIL_CC=manager@company.com,supervisor@company.com
   SMTP_FROM_NAME=HR Automation System
   ENABLE_AUTO_REMINDERS=true
   ```

**📖 Detailed Instructions:** See **[RAILWAY_SETUP_GUIDE.md](RAILWAY_SETUP_GUIDE.md)** for complete walkthrough.

### Generate Secret Keys

```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# SIGNING_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Variables Railway Provides Automatically

You **DO NOT** need to set these (auto-detected):
- ❌ `APP_BASE_URL` - Auto-detected from Railway domain
- ❌ `FRONTEND_URL` - Auto-detected from Railway domain
- ❌ `DATABASE_URL` - Provided by Railway PostgreSQL
- ❌ `PORT` - Provided by Railway

---

## Docker Deployment

### Using Docker Compose

**1. Create `.env` file:**
```bash
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/appdb
SECRET_KEY=<generated-key>
SIGNING_SECRET=<generated-key>
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=<your-key>
SMTP_FROM_EMAIL=noreply@company.com
HR_EMAIL=hr@company.com
IT_EMAIL=it@company.com
```

**2. Start services:**
```bash
docker-compose up -d
```

**3. Access application:**
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

**4. View logs:**
```bash
docker-compose logs -f backend
```

**5. Stop services:**
```bash
docker-compose down
```

### Using Docker Only

**Build:**
```bash
docker build -t hr-automation .
```

**Run:**
```bash
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="..." \
  -e SIGNING_SECRET="..." \
  -e EMAIL_PROVIDER="sendgrid" \
  -e SENDGRID_API_KEY="..." \
  -e SMTP_FROM_EMAIL="noreply@company.com" \
  -e HR_EMAIL="hr@company.com" \
  -e IT_EMAIL="it@company.com" \
  hr-automation
```

---

## Database Migration

### Migrate Local to Production

**Prerequisites:**
```bash
pip install sqlalchemy psycopg2-binary
```

**Run Migration:**
```bash
python migrate_database.py \
  --source "postgresql://postgres:123@localhost:5432/appdb" \
  --target "<railway-database-url>"
```

**Get Railway Database URL:**
1. Go to Railway dashboard
2. Click PostgreSQL service
3. Go to "Variables" tab
4. Copy `DATABASE_URL` value

**What Gets Migrated:**
- ✅ All table schemas
- ✅ All data (users, submissions, assets, etc.)
- ✅ Foreign key relationships
- ✅ Indexes and constraints
- ✅ Sequences (auto-increment IDs)

**Migration Process:**
1. Connects to both databases
2. Copies schema to target
3. Migrates data in batches (1000 rows)
4. Updates sequences
5. Verifies data integrity
6. Shows summary

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT token encryption | `<32-char-random>` |
| `SIGNING_SECRET` | API signing key | `<32-char-random>` |
| `EMAIL_PROVIDER` | Email service | `sendgrid` or `smtp` |
| `SENDGRID_API_KEY` | SendGrid API key | `SG.xxx...` |
| `SMTP_FROM_EMAIL` | Sender email | `noreply@company.com` |
| `HR_EMAIL` | HR department email | `hr@company.com` |
| `IT_EMAIL` | IT department email | `it@company.com` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HR_EMAIL_CC` | `""` | CC recipients (comma-separated) |
| `SMTP_FROM_NAME` | `HR Automation System` | Email sender name |
| `ENABLE_AUTO_REMINDERS` | `true` | Enable automated reminders |
| `REMINDER_THRESHOLD_HOURS` | `24` | Hours before reminder |

### SMTP Configuration (if not using SendGrid)

| Variable | Description | Example |
|----------|-------------|---------|
| `EMAIL_PROVIDER` | Set to smtp | `smtp` |
| `SMTP_HOST` | SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `465` or `587` |
| `SMTP_USER` | SMTP username | `user@company.com` |
| `SMTP_PASS` | SMTP password | `password` |

### Auto-Detected Variables (Railway Only)

These are automatically configured:

| Variable | Source | Description |
|----------|--------|-------------|
| `APP_BASE_URL` | Auto-detected | Application URL |
| `FRONTEND_URL` | Auto-detected | Frontend URL |
| `DATABASE_URL` | Railway PostgreSQL | Database connection |
| `PORT` | Railway | Server port |
| `RAILWAY_ENVIRONMENT` | Railway | Environment name |

---

## Post-Deployment

### 1. Verify Deployment

**Check health endpoint:**
```bash
curl https://your-app.up.railway.app/api/public/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-..."
}
```

### 2. Create Admin User

**Using Railway CLI:**
```bash
railway run python -c "from app.auth import create_user; from app.database import SessionLocal; db = SessionLocal(); create_user(db, 'hr@company.com', 'YourPassword123', 'HR Admin', 'admin'); print('Admin created!'); db.close()"
```

**Or create script `create_admin.py`:**
```python
from app.auth import create_user
from app.database import SessionLocal

db = SessionLocal()
try:
    create_user(db, "hr@company.com", "YourPassword", "HR Admin", "admin")
    print("✅ Admin user created!")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    db.close()
```

### 3. Configure Application

1. **Login to Admin Panel:**
   - Go to `https://your-app.up.railway.app`
   - Login with admin credentials
   - Navigate to "Admin" tab

2. **Configure Settings:**
   - Update email configuration
   - Set vendor email addresses
   - Configure team mappings

3. **Test Email Delivery:**
   - Create test submission
   - Verify emails are sent

### 4. Set Up Team Mappings

1. Go to "Team Mapping" tab
2. Add departments:
   - Department name
   - Team leader email
   - CHM email (if applicable)
   - Vendor preference

---

## Troubleshooting

### Deployment Fails

**Check Logs:**
```bash
# Railway
railway logs

# Docker
docker-compose logs -f backend
```

**Common Issues:**
- Missing environment variables
- Database connection error
- Invalid SECRET_KEY/SIGNING_SECRET

### Health Check Fails

**Symptoms:**
- Railway shows "Unhealthy"
- Application not starting

**Solutions:**
1. Check DATABASE_URL is set
2. Verify all required env vars
3. Review deploy logs for errors

### Database Connection Error

**Error:** `could not connect to database`

**Solutions:**
1. Verify DATABASE_URL format:
   ```
   postgresql://user:pass@host:port/dbname
   ```
2. Ensure PostgreSQL service is running
3. Check database is linked to app

### Email Not Sending

**Check:**
1. SENDGRID_API_KEY is valid
2. Sender email is verified
3. HR_EMAIL is set correctly
4. Email logs in database:
   ```sql
   SELECT * FROM email_logs ORDER BY created_at DESC LIMIT 10;
   ```

### Cannot Login

**Solutions:**
1. Verify admin user was created
2. Check password is correct
3. Ensure database migration completed
4. Recreate admin user

### URLs Not Working

**If using Railway:**
- App auto-detects Railway domain
- No need to set APP_BASE_URL
- Check Railway logs for "Base URL: https://..."

**If URLs are wrong:**
1. Check environment variables
2. Restart application
3. Verify Railway domain is generated

---

## Quick Reference

### Minimal Required Variables (Railway)

```bash
SECRET_KEY=<generated>
SIGNING_SECRET=<generated>
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=<key>
SMTP_FROM_EMAIL=noreply@company.com
HR_EMAIL=hr@company.com
IT_EMAIL=it@company.com
```

### Health Check Endpoint

```bash
GET /api/public/health
```

### API Documentation

```bash
GET /docs          # Swagger UI
GET /redoc         # ReDoc
```

### Database Backup

**Railway:**
- Automatic backups enabled
- Access via Railway dashboard

**Manual backup:**
```bash
pg_dump $DATABASE_URL > backup.sql
```

---

## Support

**Documentation:**
- [Railway Setup Guide](RAILWAY_SETUP_GUIDE.md) - Detailed Railway instructions
- [Railway Docs](https://docs.railway.app)
- [Docker Documentation](https://docs.docker.com)

**Application:**
- API Docs: `/docs`
- Health Check: `/api/public/health`

---

## Security Checklist

- [ ] Generated strong SECRET_KEY and SIGNING_SECRET
- [ ] Changed default passwords
- [ ] HTTPS enabled (automatic on Railway)
- [ ] Database password is strong
- [ ] SendGrid API key is secure
- [ ] Environment variables not committed to git
- [ ] Admin user created with strong password
- [ ] Regular backups configured

---

**Your application is ready for production!** 🚀

For detailed Railway setup, see **[RAILWAY_SETUP_GUIDE.md](RAILWAY_SETUP_GUIDE.md)**
