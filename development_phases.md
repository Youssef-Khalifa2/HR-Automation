development_phases.md - HR Co-Pilot (MVP) Delivery Plan

Goal: Provide phase-by-phase guidance for the one-week delivery, including checklists and testing criteria that ensure each slice is production-ready before moving on.

Phase 1 - Foundation & Schema (Day 1)
Checklist
- Scaffold FastAPI project, frontend skeleton, and shared config structure.
- Configure environment management (dotenv or Railway env vars template).
- Apply baseline database schema plus submissions.last_reminded_at; verify migrations are repeatable.
- Seed platform roles/accounts, enabling HR logins only while keeping leader/CHM/IT roles for signed links.
- Implement password hashing + auth guard stubs for protected routes.
- Build minimal CRUD for submissions (create/read/update) behind HR auth.
Testing Criteria
- Migration runs cleanly on a fresh Postgres instance and reruns without drift.
- Unit test or script confirms password hashing/verification round trip.
- API smoke tests for POST/GET/PATCH submissions with HR role enforcement.
- Lint/format passes (ruff/black or equivalent) to maintain consistency.

Phase 2 - Intake & Approvals (Day 2)
Checklist
- Implement Feishu intake endpoint (POST /api/submission) with schema validation.
- Generate leader notification email on submission; wire SMTP credentials in a secrets-safe way.
- Build HMAC signing helper usable across approval and asset flows.
- Deliver leader and CHM approval pages + POST handlers with status transitions and notes requirements.
- Persist team_leader_reply and chinese_head_reply booleans; update resignation_status accordingly.
- Generate CHM email on leader approval, and HR email on CHM approval.
Testing Criteria
- Automated API tests: submission creation, leader approve/reject, CHM approve/reject edge cases.
- Token signing/verification tests (valid, tampered, expired).
- Email smoke: capture outgoing messages locally (e.g., MailHog) ensuring correct recipients/links.
- Negative test ensuring reject without notes is blocked.

Phase 3 - HR Dashboard & Exit Interview (Day 3)
Checklist
- Build HR-facing dashboard elements to view submissions and act on exit interviews.
- Add ability to set exit_interview_status to scheduled/done, updating resignation_status to exit_done.
- Trigger IT notification email when HR marks the interview done.
- Surface exit interview notes/fields in the detailed view.
- Ensure role-based access so only HR can use these screens; other departments interact through signed links only.
Testing Criteria
- UI/UX review: HR login shows correct actions; hidden for non-HR users.
- API tests for scheduling/done transitions and validation on allowed statuses.
- Email smoke verifying IT notification includes correct asset form link.
- Regression test confirming leader/CHM flows remain intact after dashboard changes.

Phase 4 - IT Asset Processing & Finalization (Day 4)
Checklist
- Implement signed asset form (public page) capturing laptop/mouse/headphones, others text, approved boolean.
- Persist assets row (create or update) and sync it_support_reply + resignation_status = assets_recorded.
- Add HR read view for asset details and overall clearance state.
- Implement HR medical card toggle (resignation_status = medical_checked) and finalize action (vendor email, vendor_mail_sent true, resignation_status = offboarded).
- Template vendor email content and confirm SMTP credentials cover vendor domain requirements.
Testing Criteria
- Form validation tests: required fields, token misuse, resubmission handling.
- Database assertions ensuring assets row and submissions.it_support_reply stay in sync.
- End-to-end test from submission -> asset approval -> finalization in a staging DB.
- Email smoke for vendor notification, including failure handling/logging.

Phase 5 - Dashboards & Reminder Engine (Day 5)
Checklist
- Implement dashboard tables with filtering by resignation_status, date range, and asset clearance.
- Add last_reminded_at column handling in ORM and serialization.
- Build POST /api/check_pending job that respects the defined waiting windows and updates last_reminded_at.
- Wire cron/worker entry point (Celery, FastAPI background task, or Railway cron) to call reminder job.
- Harden validation: free-text limits, email format checks, defensive database constraints where easy wins exist.
Testing Criteria
- Unit tests for reminder selection logic across pending states and timing thresholds.
- Integration test simulating repeated cron invocations ensuring deduplication via last_reminded_at.
- UI tests (manual or automated) covering filter combinations and pagination.
- Static analysis or security scan (Bandit, pip-audit) to flag common issues.

Phase 6 - End-to-End & Observability (Day 6)
Checklist
- Run full E2E flow using test mailboxes covering approve/reject branches and reactivation scenarios.
- Capture logs/metrics for key actions (submissions created, reminders sent, vendor emails).
- Verify deployment manifests (Dockerfile/buildpack) include health endpoints and logging configuration.
- Document operational runbooks: configuring SMTP/IMAP, rotating SIGNING_SECRET, handling retries.
- Address deliverability issues (SPF/DKIM/DMARC) discovered during email testing.
Testing Criteria
- E2E automated scenario (e.g., Playwright/Postman collection) with assertions on status transitions and emails.
- Log inspection verifying expected entries for each major event.
- Load smoke (light concurrency) to ensure app handles simultaneous submissions.
- Checklist sign-off that all acceptance criteria items now pass in staging.

Phase 7 - UAT & Production Launch (Day 7)
Checklist
- Schedule UAT session with HR and iterate on feedback (copy, UX adjustments).
- Freeze scope; triage remaining issues into post-MVP backlog.
- Prepare production env: set secrets, database URL, cron schedule, and seed accounts.
- Execute deployment to Railway; run post-deploy smoke covering critical endpoints.
- Communicate launch notes, escalation contacts, and monitoring expectations to stakeholders.
Testing Criteria
- UAT sign-off document (or recorded session notes) confirming flows behave as expected.
- Post-deploy smoke test results captured (submission, leader approve, asset form, finalize).
- Monitoring/alert checks (health endpoint, email bounce notifications) verified operational.
- Final regression ensuring reminder cron runs in production environment.