# PRODUCTION READINESS ROADMAP
## HR Automation System - Critical Path to Production

**Status:** 🔴 NOT PRODUCTION READY
**Last Updated:** 2025-11-10
**Target Production Date:** TBD (Minimum 4-6 weeks from now)

---

## 🚨 CRITICAL SECURITY ISSUES (P0) - WEEK 1

### Security - Authentication & Secrets
- [ ] **URGENT** Remove hardcoded SMTP password from config.py (Line 35)
  - **Action:** Move to .env file immediately
  - **Risk:** Password exposed in Git history - ROTATE CREDENTIALS

- [ ] **URGENT** Change default SECRET_KEY and SIGNING_SECRET (Lines 15-16)
  - **Current:** "your-secret-key-change-in-production" (publicly known)
  - **Action:** Generate cryptographically secure keys
  - **Impact:** All existing tokens will be invalidated

- [ ] **URGENT** Re-enable authentication on public endpoints
  - **Files:** `app/api/submissions.py` (Lines 43, 92)
  - **Status:** Currently commented out "for debugging"
  - **Risk:** Anyone can access sensitive employee data

### Security - CORS & Network
- [ ] **URGENT** Fix CORS wildcard to whitelist
  - **File:** `main.py` (Lines 101-107)
  - **Current:** `allow_origins=["*"]` allows any website
  - **Target:** `allow_origins=["http://localhost:5173", "https://hr.51talk.com"]`

### Security - Rate Limiting
- [ ] Add rate limiting to login endpoint
  - **Tool:** Install `slowapi` package
  - **Target:** 5 attempts per minute per IP

- [ ] Add rate limiting to email sending
  - **Target:** 100 emails per hour per user

### Data Integrity - Transactions
- [ ] Add transaction rollbacks on email failures
  - **Files:** All files in `app/api/approvals.py`, `app/api/submissions.py`
  - **Pattern:** Wrap status updates + email sends in single transaction

- [ ] Add database transaction timeout (30s)
  - **File:** `app/database.py`

---

## 🔥 HIGH PRIORITY (P1) - WEEKS 2-3

### Email System Overhaul
- [ ] Implement email queue system (Celery + Redis)
  - **Install:** `celery`, `redis`, `flower` (monitoring)
  - **Config:** Separate celery worker process
  - **Benefit:** Async email sending, automatic retries

- [ ] Add email retry logic (3 attempts, exponential backoff)
  - **Pattern:** 1min, 5min, 30min delays

- [ ] Fix self-sending email issue
  - **Change:** FROM address to `noreply@51talk.com`
  - **Files:** `config.py` (Line 36)

### Monitoring & Logging
- [ ] Setup structured logging (JSON format)
  - **Tool:** `python-json-logger`
  - **Fields:** timestamp, level, request_id, user_id, action

- [ ] Implement log rotation
  - **Tool:** Python `logging.handlers.RotatingFileHandler`
  - **Policy:** 100MB per file, keep 10 files

- [ ] Add comprehensive health checks
  - **Endpoint:** `/health`
  - **Checks:** Database ping, SMTP connection, disk space

- [ ] Setup error tracking (Sentry)
  - **Install:** `sentry-sdk`
  - **Benefit:** Real-time error alerts with stack traces

### Database Hardening
- [ ] Add critical indexes
  ```sql
  CREATE INDEX idx_submissions_resignation_status ON submissions(resignation_status);
  CREATE INDEX idx_submissions_exit_interview_status ON submissions(exit_interview_status);
  CREATE INDEX idx_submissions_employee_email ON submissions(employee_email);
  CREATE INDEX idx_email_logs_submission_id ON email_logs(submission_id);
  CREATE INDEX idx_composite_status_created ON submissions(resignation_status, created_at);
  ```

- [ ] Setup automated database backups
  - **Tool:** pg_dump scheduled via cron
  - **Schedule:** Daily at 2 AM UTC
  - **Retention:** 30 days
  - **Verify:** Weekly restore test

- [ ] Implement Alembic for migrations
  - **Install:** `alembic`
  - **Action:** Initialize and create initial migration from current schema

### Audit & Compliance
- [ ] Add audit logging table
  ```sql
  CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id INTEGER NOT NULL,
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );
  CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
  CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
  ```

- [ ] Implement audit log middleware
  - **Capture:** All POST, PUT, PATCH, DELETE requests
  - **Fields:** User, action, before/after state

---

## ⚙️ MEDIUM PRIORITY (P2) - WEEKS 4-6

### Code Quality
- [ ] Refactor 275-line `resend_approval_request` function
  - **Pattern:** Strategy pattern with handler classes
  - **Files:** `app/api/submissions.py` (Lines 138-412)

- [ ] Extract duplicated email template logic
  - **Create:** `app/services/email_helpers.py`
  - **Target:** DRY principle for email data preparation

### Testing
- [ ] Add unit tests for email service (Target: 80% coverage)
  - **Tool:** `pytest`, `pytest-cov`
  - **Files:** `tests/test_email_service.py`

- [ ] Add integration tests for approval workflow
  - **Test:** Complete submission → leader → CHM → HR flow

- [ ] Add E2E tests with Playwright
  - **Scenarios:** Full user journey through dashboard

### GDPR Compliance
- [ ] Add employee data export endpoint
  - **Endpoint:** `GET /api/submissions/{id}/export`
  - **Format:** JSON and PDF

- [ ] Implement data retention policies
  - **Rule:** Delete submissions 7 years after last_working_day
  - **Tool:** Scheduled job (daily)

- [ ] Add consent tracking
  - **Table:** `user_consents`
  - **Fields:** user_id, policy_version, consented_at

### Performance
- [ ] Implement Redis caching layer
  - **Cache:** Leader mappings, user sessions
  - **TTL:** 1 hour for mappings, 30 min for sessions

- [ ] Optimize database connection pool
  - **Current:** pool_size=10, max_overflow=20
  - **Target:** pool_size=20, max_overflow=30

- [ ] Add database query performance monitoring
  - **Tool:** `sqlalchemy-utils` or custom middleware

### Deployment
- [ ] Create Dockerfile for backend
  - **Base:** python:3.11-slim
  - **Size:** < 500MB

- [ ] Create docker-compose.yml for local development
  - **Services:** backend, frontend, postgres, redis, celery

- [ ] Create CI/CD pipeline (GitHub Actions)
  - **Steps:** Lint → Test → Build → Deploy
  - **Environments:** dev, staging, production

---

## 📋 CHECKLIST PROGRESS

### Week 1 (P0 - Critical Security)
- [ ] 0/10 completed

### Week 2-3 (P1 - High Priority)
- [ ] 0/15 completed

### Week 4-6 (P2 - Medium Priority)
- [ ] 0/20 completed

---

## 🎯 SUCCESS CRITERIA FOR PRODUCTION

### Security ✅
- [x] All secrets in environment variables (not code)
- [x] Authentication enabled on all endpoints
- [x] CORS whitelist configured
- [x] Rate limiting implemented
- [x] Input validation on all endpoints
- [x] HTTPS enforced in production

### Reliability ✅
- [x] Email queue with retry logic
- [x] Database transaction rollbacks
- [x] Circuit breakers for external services
- [x] Automated database backups
- [x] Health checks monitoring

### Observability ✅
- [x] Structured logging
- [x] Error tracking (Sentry)
- [x] Performance monitoring (APM)
- [x] Audit logs for compliance
- [x] Alerting configured

### Testing ✅
- [x] Unit tests (>80% coverage)
- [x] Integration tests
- [x] E2E tests
- [x] Load tests completed
- [x] Security tests (penetration testing)

### Compliance ✅
- [x] GDPR features implemented
- [x] Data retention policies
- [x] Audit trail complete
- [x] Privacy policy accepted
- [x] Data export capabilities

---

## 🚀 DEPLOYMENT TIMELINE

| Week | Focus | Deliverables |
|------|-------|--------------|
| 1 | Security Hardening | Secrets rotated, Auth fixed, CORS fixed |
| 2 | Email System | Queue implemented, Retries working |
| 3 | Monitoring | Logging, Sentry, Health checks |
| 4 | Database | Backups, Indexes, Migrations |
| 5 | Testing | Unit + Integration tests |
| 6 | Compliance | GDPR features, Audit logs |
| 7 | Performance | Caching, Optimization |
| 8 | Deployment | Docker, CI/CD, Staging deployment |

---

## ⚠️ KNOWN RISKS

1. **Credential Rotation Impact**
   - Risk: Existing tokens invalidated
   - Mitigation: Schedule during maintenance window, notify users

2. **Database Migration**
   - Risk: Downtime during migration
   - Mitigation: Test on staging, prepare rollback script

3. **Email Queue Transition**
   - Risk: Emails lost during cutover
   - Mitigation: Drain old queue, dual-write period

---

## 📞 SUPPORT & ESCALATION

**For Production Deployment:**
- Security Review: Required before go-live
- Load Testing: 1000 concurrent users
- Penetration Testing: Third-party audit
- Legal Review: GDPR compliance sign-off
- Business Continuity: Disaster recovery plan

**Team Requirements:**
- DevOps: Infrastructure setup
- QA: Test plan execution
- Security: Penetration testing
- Legal: Compliance review
- Product: UAT sign-off

---

**Document Owner:** Development Team
**Stakeholders:** CTO, CISO, Legal, HR Department
**Review Frequency:** Weekly during development, Daily near go-live
