// User types
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Submission types
export interface Submission {
  id: number;
  employee_name: string;
  employee_email: string;
  joining_date: string;
  submission_date: string;
  last_working_day: string;
  team_leader_name?: string | null;
  chm_name?: string | null;
  resignation_status: string;
  exit_interview_status: string;
  team_leader_reply: boolean | null;
  team_leader_notes: string | null;
  chinese_head_reply: boolean | null;
  chinese_head_notes: string | null;
  exit_interview_notes: string | null;
  it_support_reply: boolean | null;
  medical_card_collected: boolean;
  vendor_mail_sent: boolean;
  in_probation: boolean;
  notice_period_days: number;
  created_at: string;
  updated_at: string;
  last_reminded_at: string | null;
  assets?: Asset;
  exit_interview?: ExitInterview;
}

export interface SubmissionCreate {
  employee_name: string;
  employee_email: string;
  employee_id: string;
  department: string;
  position: string;
  joining_date: string;
  submission_date: string;
  last_working_day: string;
  team_leader_email: string;
  chm_email: string;
  resignation_reason?: string;
  notice_period_days?: number;
  in_probation?: boolean;
}

// Leader mapping types
export interface LeaderMapping {
  [name: string]: string; // name -> email
}

export interface LeaderInfo {
  leader_name: string;
  leader_email: string;
  chm_name?: string;
  chm_email?: string;
}

export interface SubmissionUpdate {
  employee_name?: string;
  employee_email?: string;
  joining_date?: string;
  submission_date?: string;
  last_working_day?: string;
  resignation_status?: string;
  exit_interview_status?: string;
  team_leader_reply?: boolean;
  team_leader_notes?: string;
  chinese_head_reply?: boolean;
  chinese_head_notes?: string;
  exit_interview_notes?: string;
  it_support_reply?: boolean;
  medical_card_collected?: boolean;
  vendor_mail_sent?: boolean;
}

// Exit Interview types
export interface ExitInterview {
  id: number;
  submission_id: number;
  scheduled_date: string | null;
  scheduled_time: string | null;
  location: string | null;
  interviewer: string | null;
  interview_completed: boolean;
  interview_feedback: string | null;
  interview_rating: number | null;
  interview_type: string | null;
  interview_completed_at: string | null;
  hr_notes: string | null;
  it_notification_sent: boolean;
  created_at: string;
  updated_at: string;
  submission?: Submission;
}

export interface ExitInterviewSchedule {
  submission_id: number;
  scheduled_date: string;
  scheduled_time: string;
  location: string;
  interviewer: string;
  interview_type?: string;
}

export interface ExitInterviewFeedback {
  interview_id: number;
  interview_feedback: string;
  interview_rating: number;
  hr_notes?: string;
}

// Asset types
export interface Asset {
  id: number;
  res_id: number;
  assets_returned: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
  submission?: Submission;
}

export interface AssetCreate {
  assets_returned: boolean;
  notes?: string;
}

export interface AssetUpdate {
  assets_returned?: boolean;
  notes?: string;
}

// Statistics types
export interface DashboardStats {
  total_submissions: number;
  pending_approvals: number;
  completed_this_month: number;
  exit_interviews: number;
}

export interface ExitInterviewStats {
  total: number;
  to_schedule: number;
  upcoming: number;
  completed: number;
}

// Filter types
export interface SubmissionFilters {
  resignation_status?: string;
  date_from?: string;
  date_to?: string;
  skip?: number;
  limit?: number;
}
