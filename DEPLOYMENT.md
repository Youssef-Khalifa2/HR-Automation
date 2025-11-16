# HR Automation System - Deployment Guide

Complete guide for deploying the HR Automation System to production.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Option 1: Railway Deployment](#option-1-railway-deployment-recommended)
- [Option 2: Docker Deployment](#option-2-docker-deployment)
- [Database Migration](#database-migration)
- [Environment Variables](#environment-variables)
- [Post-Deployment](#post-deployment)

---

## Prerequisites

### Required
- PostgreSQL database (Railway provides this automatically)
- SendGrid API key OR SMTP credentials
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Optional
- Docker & Docker Compose (for containerized deployment)
- Railway CLI (for Railway deployment)

---

## Option 1: Railway Deployment (Recommended)

### Step 1: Prepare Your Code
```bash
# Ensure all files are committed
git add .
git commit -m "Prepare for deployment"
```

### Step 2: Create Railway Project
1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### Step 3: Add PostgreSQL Database
1. In your Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will create a database and provide connection string

### Step 4: Configure Environment Variables
In Railway dashboard, add these variables to your service:

#### Required Variables
```bash
# Database (automatically set by Railway if using their PostgreSQL)
DATABASE_URL=<your-railway-postgres-url>

# Security (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=<your-secret-key>
SIGNING_SECRET=<your-signing-secret>

# Application URLs
APP_BASE_URL=https://your-app.railway.app
FRONTEND_URL=https://your-frontend-url.com

# Email Provider
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=<your-sendgrid-api-key>

# Email Recipients
HR_EMAIL=hr@your-company.com
HR_EMAIL_CC=manager@your-company.com,supervisor@your-company.com
IT_EMAIL=it@your-company.com

# SMTP From Address (for SendGrid)
SMTP_FROM_EMAIL=noreply@your-company.com
SMTP_FROM_NAME=HR Automation System
```

#### Optional Variables (if using SMTP instead of SendGrid)
```bash
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=465
SMTP_USER=your-smtp-username
SMTP_PASS=your-smtp-password
```

### Step 5: Deploy
Railway will automatically:
1. Detect the `Dockerfile`
2. Build your application
3. Deploy it
4. Assign a public URL

### Step 6: Migrate Database
After first deployment, migrate your local database to Railway:

```bash
# Install required dependencies
pip install sqlalchemy psycopg2-binary

# Run migration
python migrate_database.py \
  --source "postgresql://postgres:123@localhost:5432/appdb" \
  --target "postgresql://user:pass@containers-us-west-xxx.railway.app:5432/railway"
```

### Step 7: Create Admin User
SSH into Railway container or use Railway's console:
```bash
python -c "from app.auth import create_user; from app.database import SessionLocal; db = SessionLocal(); create_user(db, 'hr@company.com', 'your-password', 'HR Admin', 'admin'); db.close()"
```

---

## Option 2: Docker Deployment

### Step 1: Set Up Environment
Create `.env` file in project root:
```bash
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/appdb
SECRET_KEY=your-secret-key-here
SIGNING_SECRET=your-signing-secret-here
APP_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your-sendgrid-api-key
HR_EMAIL=hr@company.com
HR_EMAIL_CC=manager@company.com
IT_EMAIL=it@company.com
SMTP_FROM_EMAIL=noreply@company.com
```

### Step 2: Build and Run
```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Step 3: Access Application
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## Database Migration

### Migrate from Local to Production

```bash
# Install dependencies
pip install sqlalchemy psycopg2-binary

# Run migration script
python migrate_database.py \
  --source "postgresql://user:pass@localhost:5432/local_db" \
  --target "postgresql://user:pass@prod-host:5432/prod_db" \
  --batch-size 1000
```

### What Gets Migrated
- ✅ All table schemas
- ✅ All data (in batches)
- ✅ Foreign key relationships
- ✅ Indexes
- ✅ Sequences (auto-increment IDs)

### Migration Safety
- Script asks for confirmation before proceeding
- Reads from source (no modifications)
- Verifies data integrity after migration
- Shows progress for each table

---

## Environment Variables

### Security Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT token encryption | `<random-32-char-string>` |
| `SIGNING_SECRET` | API request signing | `<random-32-char-string>` |

### Database
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |

### Application URLs
| Variable | Description | Example |
|----------|-------------|---------|
| `APP_BASE_URL` | Backend API URL | `https://api.your-app.com` |
| `FRONTEND_URL` | Frontend application URL | `https://your-app.com` |

### Email Configuration
| Variable | Description | Example |
|----------|-------------|---------|
| `EMAIL_PROVIDER` | Email provider (sendgrid/smtp) | `sendgrid` |
| `SENDGRID_API_KEY` | SendGrid API key | `SG.xxx` |
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `465` |
| `SMTP_USER` | SMTP username | `user@company.com` |
| `SMTP_PASS` | SMTP password | `password` |
| `SMTP_FROM_EMAIL` | Sender email address | `noreply@company.com` |
| `SMTP_FROM_NAME` | Sender name | `HR Automation` |

### Email Recipients
| Variable | Description | Example |
|----------|-------------|---------|
| `HR_EMAIL` | Primary HR email | `hr@company.com` |
| `HR_EMAIL_CC` | CC recipients (comma-separated) | `mgr@company.com,super@company.com` |
| `IT_EMAIL` | IT department email | `it@company.com` |

### Optional Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_AUTO_REMINDERS` | Enable automated reminders | `true` |
| `REMINDER_THRESHOLD_HOURS` | Hours before sending reminders | `24` |
| `ENVIRONMENT` | Environment name | `production` |
| `PORT` | Server port | `8000` |

---

## Post-Deployment

### 1. Create Admin User
```bash
# Via Railway console or SSH
python create_admin_user.py
```

### 2. Configure System Settings
1. Log in to admin panel: `https://your-app.com/admin`
2. Navigate to "Configuration" tab
3. Update:
   - Email settings
   - Vendor email addresses
   - HR/IT email addresses
   - HR Email CC recipients

### 3. Test Email Delivery
1. Create a test resignation submission
2. Verify emails are received
3. Check email logs in database

### 4. Set Up Team Mappings
1. Go to "Team Mapping" tab
2. Add all department mappings:
   - Department name
   - Team leader email
   - CHM email (if applicable)
   - Vendor selection

### 5. Monitor Application
- Check Railway logs for errors
- Monitor email delivery
- Test approval workflows
- Verify exit interview process

---

## Troubleshooting

### Database Connection Issues
```bash
# Test database connection
python -c "from app.database import engine; engine.connect(); print('✓ Connected')"
```

### Email Not Sending
1. Check SendGrid API key is valid
2. Verify sender email is verified in SendGrid
3. Check email logs: `SELECT * FROM email_logs ORDER BY created_at DESC LIMIT 10;`
4. Review Railway logs for error messages

### 500 Internal Server Error
1. Check Railway logs
2. Verify all environment variables are set
3. Ensure database is accessible
4. Check for Python dependency issues

### Migration Failed
1. Verify both source and target databases are accessible
2. Check credentials in connection strings
3. Ensure target database is empty or confirm overwrite
4. Review migration logs for specific table errors

---

## Security Checklist

- [ ] Change default SECRET_KEY and SIGNING_SECRET
- [ ] Use strong database passwords
- [ ] Enable HTTPS (Railway provides this automatically)
- [ ] Restrict database access to application only
- [ ] Keep SendGrid API key secure
- [ ] Regularly update dependencies
- [ ] Monitor access logs
- [ ] Set up database backups (Railway provides automated backups)

---

## Support

For issues or questions:
1. Check Railway logs
2. Review application logs in database
3. Consult this deployment guide
4. Check Railway documentation: https://docs.railway.app

---

## Quick Reference

### Generate Secret Keys
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### View Logs
```bash
# Railway
railway logs

# Docker
docker-compose logs -f backend
```

### Database Backup
```bash
# Railway (automatic backups enabled)
# Manual backup:
pg_dump $DATABASE_URL > backup.sql
```

### Restart Application
```bash
# Railway - via dashboard or CLI
railway restart

# Docker
docker-compose restart backend
```
