-- Email tracking and monitoring tables
-- Run this SQL to create the email logging tables

-- Email logs table for tracking all email sending attempts
CREATE TABLE IF NOT EXISTS email_logs (
    id SERIAL PRIMARY KEY,

    -- Email details
    to_email VARCHAR(255) NOT NULL,
    to_name VARCHAR(255),
    from_email VARCHAR(255),
    subject VARCHAR(500),
    template_name VARCHAR(100),

    -- Status tracking
    status VARCHAR(50),  -- pending, sent, delivered, bounced, failed, rate_limited
    smtp_response TEXT,
    attempts INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    last_attempt_at TIMESTAMP WITH TIME ZONE,

    -- Error tracking
    error_message TEXT,
    error_type VARCHAR(100),

    -- Template data (JSON)
    template_data JSONB,

    -- Related records
    submission_id INTEGER REFERENCES submissions(id),
    exit_interview_id INTEGER REFERENCES exit_interviews(id),

    -- Delivery verification
    message_id VARCHAR(500),
    bounce_detected BOOLEAN DEFAULT FALSE,
    bounce_reason TEXT,

    -- Rate limiting
    rate_limit_hit BOOLEAN DEFAULT FALSE,
    retry_after TIMESTAMP WITH TIME ZONE
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_email_logs_to_email ON email_logs(to_email);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);
CREATE INDEX IF NOT EXISTS idx_email_logs_created_at ON email_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_logs_submission_id ON email_logs(submission_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_exit_interview_id ON email_logs(exit_interview_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_retry_after ON email_logs(retry_after) WHERE status = 'rate_limited';

-- Email delivery statistics table
CREATE TABLE IF NOT EXISTS email_delivery_stats (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Counts
    total_sent INTEGER DEFAULT 0,
    total_delivered INTEGER DEFAULT 0,
    total_bounced INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,

    -- By template type (JSON)
    template_counts JSONB,

    -- Error analysis (JSON)
    error_types JSONB,

    -- Rate limiting
    rate_limits_hit INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_email_delivery_stats_date ON email_delivery_stats(date DESC);

-- Add comment to tables
COMMENT ON TABLE email_logs IS 'Tracks all email sending attempts with delivery status and error details';
COMMENT ON TABLE email_delivery_stats IS 'Daily aggregated statistics for email delivery monitoring';

-- Sample queries for monitoring

-- Get delivery report for last 24 hours
-- SELECT
--     status,
--     COUNT(*) as count,
--     ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
-- FROM email_logs
-- WHERE created_at >= NOW() - INTERVAL '24 hours'
-- GROUP BY status
-- ORDER BY count DESC;

-- Get failed emails with details
-- SELECT
--     id,
--     to_email,
--     subject,
--     error_type,
--     error_message,
--     attempts,
--     created_at
-- FROM email_logs
-- WHERE status IN ('failed', 'bounced')
--     AND created_at >= NOW() - INTERVAL '24 hours'
-- ORDER BY created_at DESC
-- LIMIT 20;

-- Get emails pending retry
-- SELECT
--     id,
--     to_email,
--     subject,
--     attempts,
--     retry_after,
--     error_message
-- FROM email_logs
-- WHERE status = 'rate_limited'
--     AND retry_after <= NOW()
--     AND attempts < 5
-- ORDER BY retry_after;

-- Check for suspicious patterns (emails stuck in 'sent' status)
-- SELECT
--     id,
--     to_email,
--     subject,
--     sent_at,
--     NOW() - sent_at as age
-- FROM email_logs
-- WHERE status = 'sent'
--     AND delivered_at IS NULL
--     AND sent_at < NOW() - INTERVAL '2 hours'
-- ORDER BY sent_at;
