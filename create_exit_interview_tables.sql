-- Create exit_interviews table
CREATE TABLE IF NOT EXISTS exit_interviews (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER UNIQUE NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,

    -- Scheduling Information
    scheduled_date TIMESTAMP,
    scheduled_time VARCHAR(10),  -- HH:MM format
    location VARCHAR(200),
    interviewer VARCHAR(100),

    -- Interview Details
    interview_completed BOOLEAN DEFAULT FALSE,
    interview_feedback TEXT,
    interview_rating INTEGER,  -- 1-5 scale
    interview_type VARCHAR(50),  -- in-person, virtual, phone

    -- Follow-up Actions
    hr_notes TEXT,
    it_notification_sent BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interview_completed_at TIMESTAMP
);

-- Create exit_interview_reminders table
CREATE TABLE IF NOT EXISTS exit_interview_reminders (
    id SERIAL PRIMARY KEY,
    exit_interview_id INTEGER NOT NULL REFERENCES exit_interviews(id) ON DELETE CASCADE,

    -- Reminder Type
    reminder_type VARCHAR(50) NOT NULL,  -- schedule_interview, submit_feedback, employee_reminder

    -- Status
    sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    scheduled_for TIMESTAMP NOT NULL,

    -- Email details
    recipient_email VARCHAR(150) NOT NULL,
    recipient_name VARCHAR(100) NOT NULL,

    -- Response tracking
    responded BOOLEAN DEFAULT FALSE,
    responded_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_exit_interviews_submission_id ON exit_interviews(submission_id);
CREATE INDEX IF NOT EXISTS idx_exit_interviews_scheduled_date ON exit_interviews(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_exit_interview_reminders_interview_id ON exit_interview_reminders(exit_interview_id);
CREATE INDEX IF NOT EXISTS idx_exit_interview_reminders_scheduled_for ON exit_interview_reminders(scheduled_for);

-- Create trigger to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_exit_interviews_updated_at BEFORE UPDATE ON exit_interviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exit_interview_reminders_updated_at BEFORE UPDATE ON exit_interview_reminders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();