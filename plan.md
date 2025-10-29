plan.md - HR Co-Pilot (MVP)

Goal: ship a working offboarding automation by next week. Keep it simple, avoid over-engineering, and only cover the minimum scalability requirements.

0) What we are building (one paragraph)

A tiny web platform plus background jobs that take a Feishu resignation form and walk the submission through approvals (Team Leader then Chinese Head), exit interview, IT/assets review, medical card confirmation, and finalization. Hazem (super user) manages the flow from a dashboard. Emails contain signed links that flip the current step for a single submissions record. IT fills a short asset form. We send a final vendor notification and mark the case complete.

1) Workflow (MVP)

Trigger
Feishu form -> HTTPS POST /api/submission with employee info -> create submissions row (resignation_status = submitted).

Leader approval
Email to Team Leader with approve/reject links.
Approve: optional notes -> resignation_status = leader_approved.
Reject: notes required -> resignation_status = leader_rejected -> stop.

Chinese Head approval
Email with approve/reject links.
Approve: resignation_status = chm_approved.
Reject: notes required -> resignation_status = chm_rejected -> stop.

Exit interview
Email to Hazem with schedule link (optionally include ICS).
Hazem sets exit_interview_status to scheduled once a time is confirmed.
After it happens, Hazem clicks Mark Done -> exit_interview_status = done, resignation_status = exit_done.

IT and assets
Email to IT/Admin with link to Asset Form (signed token).
Form captures laptop, mouse, headphones (booleans), others (free text), approved (overall clearance).
Submitting the form creates or upserts the assets row, updates it_support_reply (true for approved, false for rejected or partial), and sets resignation_status = assets_recorded.
Hazem is notified of the result.

Medical card
Hazem marks Medical Card collected -> medical_card_collected = true, resignation_status = medical_checked.

Finalize
Hazem clicks Finish -> send vendor email, set vendor_mail_sent = true, resignation_status = offboarded.

Reminders
Cron hits POST /api/check_pending every 5 minutes.
Define waiting windows:
- Team Leader pending if resignation_status = submitted and team_leader_reply IS NULL.
- Chinese Head pending if resignation_status = leader_approved and chinese_head_reply IS NULL.
- IT pending if resignation_status = exit_done and it_support_reply IS NULL.
If the current step has been waiting more than 24 hours since updated_at and last_reminded_at (per submission) is more than 24 hours ago, send one reminder email and set last_reminded_at = now().

2) Database (PostgreSQL, MVP)

Start from the prepared SQL schema (users, submissions, assets) and add a nullable submissions.last_reminded_at TIMESTAMPTZ column for reminder deduplication.
Key fields we rely on:
- submissions.resignation_status is the canonical workflow status (values: submitted, leader_approved, leader_rejected, chm_approved, chm_rejected, exit_done, assets_recorded, medical_checked, offboarded).
- submissions.exit_interview_status tracks sub-states for the interview (not_scheduled, scheduled, done, no_show).
- submissions.it_support_reply holds the overall IT decision (true = cleared, false = issue, null = pending).
- assets contains the laptop, mouse, headphones booleans, others text, and approved boolean aligned with the IT form.

3) Platform (UI)

Keep it to four screens.

Login: email + password (hashed) with role check.

Resignation Tracker (home): table of submissions with filters (resignation_status, date range). Actions per row based on role:
- View (all internal roles).
- Mark interview scheduled/done (Hazem).
- Toggle medical card collected (Hazem).
- Finalize (Hazem).

Asset Tracker: grid keyed by resignation_status, it_support_reply, and assets.approved. Hazem and HR can open the IT form view (read-only for them) to review submissions; IT can reach the form via email link but can also log in to the Asset Tracker if needed.

Full view (single submission):
- Employee details + generated fields (in_probation, notice_period_days).
- Current status chips for resignation_status and exit_interview_status.
- Buttons depending on role and current step:
  * Leader/CHM approval (also accessible via email links).
  * Mark interview scheduled/done (Hazem).
  * Open/submit asset form (IT).
  * Medical card toggle (Hazem).
  * Finalize and send vendor mail (Hazem).
- History list showing updated_at changes and key transitions.

Email-only pages (public, signed):
- /approve/leader?token=...&decision=approve|reject (+ optional notes).
- /approve/chm?token=...&decision=approve|reject (+ optional notes).
- /assets/form?token=... (booleans, notes, approved checkbox).
Each renders a confirmation UI, calls the backend, and redirects to a success page.

4) Backend (FastAPI recommended)

Environment variables
- DATABASE_URL
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_ADDR
- IMAP_HOST, IMAP_PORT (for optional future reply parsing)
- APP_BASE_URL (for links)
- SIGNING_SECRET (HMAC for tokens)

Routes (minimal)

Public (email links):
- POST /api/approve/leader -> body { token, decision, notes? }.
- POST /api/approve/chm -> body { token, decision, notes? }.
- POST /api/assets/submit -> body { token, laptop, mouse, headphones, others, approved }.

Feishu trigger:
- POST /api/submission -> creates submission, sends leader email.

Dashboard:
- GET /api/submissions -> list with filters.
- GET /api/submissions/:id -> detail.
- PATCH /api/submissions/:id -> role-restricted updates:
  * Hazem: exit_interview_status, medical_card_collected, vendor_mail_sent, resignation_status.
  * IT: updates via assets/submit endpoint (no direct PATCH).

Jobs:
- POST /api/check_pending -> cron entry point.
- Optional: IMAP poll endpoint for future enhancements.

Email sending (Aliyun SMTP):
- Plain text plus light HTML multipart.
- Subject format: [OFFBOARD <token>] <short title>.
- Links: APP_BASE_URL + signed token.
- One recipient per message.
- DKIM/SPF/DMARC configured on the domain once.

Token signing:
- token = base64url(json { submission_id, step, exp }) + "." + HMAC.
- Verify on inbound; if expired or the step does not match the current status, show "link expired".

Business logic outline:
- Feishu POST -> create submission, send leader email, resignation_status = submitted.
- Leader approve -> team_leader_reply = true, resignation_status = leader_approved, email CHM.
- Leader reject -> team_leader_reply = false, store notes, resignation_status = leader_rejected.
- CHM approve -> chinese_head_reply = true, resignation_status = chm_approved, email Hazem to schedule interview.
- CHM reject -> chinese_head_reply = false, store notes, resignation_status = chm_rejected.
- Hazem schedules interview -> exit_interview_status = scheduled (optional).
- Hazem marks interview done -> exit_interview_status = done, resignation_status = exit_done, email IT.
- IT submits assets -> upsert assets row, set it_support_reply = approved (true or false), resignation_status = assets_recorded, notify Hazem.
- Hazem toggles medical card -> medical_card_collected = true, resignation_status = medical_checked.
- Hazem finalizes -> send vendor email, vendor_mail_sent = true, resignation_status = offboarded.

Reminders (cron details):
- Every 5 minutes evaluate submissions in waiting states (submitted, leader_approved, exit_done).
- If waiting more than 24 hours for the responsible actor (leader, CHM, IT) and last_reminded_at is null or > 24 hours ago, send reminder and update last_reminded_at.
- last_reminded_at lives on submissions (nullable timestamp to be added in the migration).

5) Security (MVP level)

- Password hashing (bcrypt) for platform users.
- Signed tokens for email links with 14-day expiry.
- Server-side role checks on every mutation.
- Basic input validation; limit free text lengths (notes, others).
- Log token failures for investigation.

6) Deployment plan (Railway)

- Create PostgreSQL instance and run schema SQL.
- Deploy FastAPI container (Dockerfile or Python buildpack).
- Set environment variables; expose port 8000.
- Add cron to call POST /api/check_pending every 5 minutes.
- Point Feishu automation to POST /api/submission.
- Test email deliverability from Railway IPs; adjust SPF/DKIM if needed.

7) Timeline (one week)

- Day 1: Repo scaffold, DB schema migration, auth (users), basic CRUD for submissions.
- Day 2: Email helper + token signing; implement Feishu POST + leader email; leader/CHM approval endpoints + pages.
- Day 3: Hazem dashboard actions; exit interview scheduling/done flow + IT notification.
- Day 4: Asset form + submit; status transitions; vendor email + finalize endpoint.
- Day 5: Dashboard tables and filters; reminder cron with last_reminded_at; polish validation.
- Day 6: End-to-end test with sample mailbox; fix deliverability; add simple logging.
- Day 7: UAT with Hazem; tweak copy; deploy to production.

8) Acceptance checklist

- Feishu submission creates record with resignation_status = submitted and sends leader email.
- Leader approve/reject works with required notes rules and updates resignation_status.
- CHM approve/reject works and notifies Hazem on approval.
- Hazem can schedule and mark the interview done; IT receives asset form link.
- IT can submit asset statuses; Hazem is notified; resignation_status updates to assets_recorded.
- Hazem can mark medical card collected and finalize; vendor email goes out; resignation_status = offboarded.
- Dashboard shows accurate statuses, including exit_interview_status, and filters operate correctly.
- Reminders fire after 24 hours of inactivity for pending actors without duplication.
- All links require valid tokens and respect role/step alignment.
