"""Tokenized Forms API - email-based forms for HR actions"""

from fastapi import APIRouter, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict
from app.database import get_db
from app.services.tokenized_forms import get_tokenized_form_service, EmailFormTemplates
from app.services.email import get_email_service, EmailTemplates
from app.services.enhanced_email import EnhancedEmailService
from app.crud_exit_interview import schedule_exit_interview, complete_exit_interview
from app.crud import update_submission
from app.schemas_all import SubmissionUpdate
from app.core.auth import get_current_user
from app.models.user import User
from config import BASE_URL
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/forms", tags=["forms"])


# Form data models
class InterviewScheduleForm(BaseModel):
    scheduled_date: str = Field(..., description="Interview date (YYYY-MM-DD)")
    scheduled_time: str = Field(..., description="Interview time (HH:MM)")
    location: str = Field("HR Meeting Room", description="Interview location")
    interviewer: str = Field("HR Representative", description="Interviewer name")


class InterviewFeedbackForm(BaseModel):
    interview_rating: Optional[int] = Field(None, ge=1, le=5, description="Rating 1-5")
    interview_feedback: str = Field(..., min_length=10, description="Interview feedback")
    hr_notes: Optional[str] = Field(None, description="Internal HR notes")


class SkipInterviewForm(BaseModel):
    reason: str = Field(..., description="Reason for skipping interview")
    additional_notes: Optional[str] = Field(None, description="Additional notes")


# HTML form templates
SCHEDULE_INTERVIEW_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Schedule Exit Interview</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin: 20px auto;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
            margin: -40px -40px 40px -40px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        .form-control:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .btn:hover {
            background: #5a67d8;
            transform: translateY(-2px);
        }
        .btn-secondary {
            background: #6c757d;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        .info-box {
            background: #e8f5e8;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .alert-info {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }
        .alert-warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }
        .alert-danger {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 Schedule Exit Interview</h1>
            <p id="employee-name">Loading...</p>
        </div>

        <div id="error-message" class="alert alert-danger" style="display: none;"></div>
        <div id="success-message" class="alert alert-success" style="display: none;"></div>

        <div class="info-box">
            <h3>Interview Details</h3>
            <p><strong>Position:</strong> <span id="employee-position">Loading...</span></p>
            <p><strong>Department:</strong> <span id="employee-department">Loading...</span></p>
            <p><strong>Last Working Day:</strong> <span id="last-working-day">Loading...</span></p>
        </div>

        <form id="scheduleForm">
            <div class="form-group">
                <label for="scheduled_date">Interview Date *</label>
                <input type="date" id="scheduled_date" name="scheduled_date" class="form-control" required>
            </div>

            <div class="form-group">
                <label for="scheduled_time">Interview Time *</label>
                <input type="time" id="scheduled_time" name="scheduled_time" class="form-control" required>
            </div>

            <div class="form-group">
                <label for="location">Interview Location *</label>
                <input type="text" id="location" name="location" class="form-control" value="HR Meeting Room" required>
            </div>

            <div class="form-group">
                <label for="interviewer">Interviewer *</label>
                <input type="text" id="interviewer" name="interviewer" class="form-control" value="HR Representative" required>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <button type="submit" class="btn">Schedule Interview</button>
                <button type="button" class="btn btn-secondary" onclick="skipInterview()" style="margin-left: 10px; background: #ffc107; color: #000;">Skip Interview</button>
                <a href="#" onclick="window.close()" class="btn btn-secondary" style="margin-left: 10px;">Cancel</a>
            </div>
        </form>

        <div class="alert alert-info">
            <strong>💡 Note:</strong> This form allows you to schedule the exit interview without logging into the main system. The interview will also be available in the HR dashboard.
        </div>
    </div>

    <script>
        // Get token from URL
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (!token) {
            document.getElementById('error-message').style.display = 'block';
            document.getElementById('error-message').textContent = 'Invalid or missing token. Please check your email link.';
            document.getElementById('scheduleForm').style.display = 'none';
        } else {
            // Load employee data
            loadEmployeeData(token);
        }

        async function loadEmployeeData(token) {
            try {
                // Get submission data from token
                const response = await fetch(`/api/forms/validate-token?token=${token}`);
                const result = await response.json();

                if (result.valid) {
                    // Populate employee info
                    document.getElementById('employee-name').textContent = `Hi ${result.data.employee_name}!`;
                    document.getElementById('employee-position').textContent = result.data.position || 'Employee';
                    document.getElementById('employee-department').textContent = result.data.department || 'General';
                    document.getElementById('last-working-day').textContent = result.data.last_working_day || 'TBD';

                    // Set minimum date to tomorrow
                    const tomorrow = new Date();
                    tomorrow.setDate(tomorrow.getDate() + 1);
                    document.getElementById('scheduled_date').min = tomorrow.toISOString().split('T')[0];

                    // Handle form submission
                    document.getElementById('scheduleForm').addEventListener('submit', handleSubmit);
                } else {
                    document.getElementById('error-message').style.display = 'block';
                    document.getElementById('error-message').textContent = result.error;
                    document.getElementById('scheduleForm').style.display = 'none';
                }
            } catch (error) {
                document.getElementById('error-message').style.display = 'block';
                document.getElementById('error-message').textContent = 'Failed to load data. Please try again or contact HR.';
                document.getElementById('scheduleForm').style.display = 'none';
                console.error('Error:', error);
            }
        }

        async function handleSubmit(event) {
            event.preventDefault();

            const formData = new FormData(event.target);
            const data = {
                scheduled_date: formData.get('scheduled_date'),
                scheduled_time: formData.get('scheduled_time'),
                location: formData.get('location'),
                interviewer: formData.get('interviewer')
            };

            try {
                const response = await fetch(`/api/forms/schedule-interview?token=${token}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.success) {
                    document.getElementById('success-message').style.display = 'block';
                    document.getElementById('success-message').innerHTML = `
                        <strong>✅ Interview Scheduled Successfully!</strong><br>
                        Date: ${result.interview.scheduled_date}<br>
                        Time: ${result.interview.scheduled_time}<br>
                        Location: ${result.interview.location}<br>
                        An email confirmation has been sent to ${result.employee_name}.
                    `;
                    document.getElementById('scheduleForm').style.display = 'none';

                    // Close window after 3 seconds
                    setTimeout(() => window.close(), 3000);
                } else {
                    document.getElementById('error-message').style.display = 'block';
                    document.getElementById('error-message').textContent = result.error;
                }
            } catch (error) {
                document.getElementById('error-message').style.display = 'block';
                document.getElementById('error-message').textContent = 'Failed to schedule interview. Please try again.';
                console.error('Error:', error);
            }
        }

        async function skipInterview() {
            if (!confirm('Are you sure you want to skip the exit interview?\\n\\nThis will expedite the offboarding process and send the IT assets collection form directly.')) {
                return;
            }

            try {
                const response = await fetch(`/api/forms/skip-interview?token=${token}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        reason: 'Skipped via interview scheduling form - expedited offboarding'
                    })
                });

                const result = await response.json();

                if (result.success) {
                    document.getElementById('success-message').style.display = 'block';
                    document.getElementById('success-message').innerHTML = `
                        <strong>✅ Interview Skipped Successfully!</strong><br>
                        IT department has been notified for assets collection.<br>
                        The offboarding process will continue without an exit interview.
                    `;
                    document.getElementById('scheduleForm').style.display = 'none';

                    // Close window after 3 seconds
                    setTimeout(() => window.close(), 3000);
                } else {
                    document.getElementById('error-message').style.display = 'block';
                    document.getElementById('error-message').textContent = result.error || 'Failed to skip interview. Please try again.';
                }
            } catch (error) {
                document.getElementById('error-message').style.display = 'block';
                document.getElementById('error-message').textContent = 'Failed to skip interview. Please try again.';
                console.error('Error:', error);
            }
        }
    </script>
</body>
</html>
"""

FEEDBACK_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Submit Interview Feedback</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin: 20px auto;
        }
        .header {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
            margin: -40px -40px 40px -40px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        .form-control:focus {
            outline: none;
            border-color: #28a745;
            box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25);
        }
        textarea.form-control {
            min-height: 150px;
            resize: vertical;
        }
        .select.form-control {
            padding: 12px;
        }
        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .btn:hover {
            background: #218838;
            transform: translateY(-2px);
        }
        .btn-secondary {
            background: #6c757d;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        .rating-container {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin: 20px 0;
        }
        .rating-group {
            text-align: center;
            margin-bottom: 10px;
        }
        .star {
            font-size: 32px;
            color: #ddd;
            cursor: pointer;
            transition: color 0.2s;
            user-select: none;
        }
        .star:hover,
        .star.selected {
            color: #ffc107;
        }
        .info-box {
            background: #d4edda;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .alert-info {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }
        .alert-warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }
        .alert-danger {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Submit Interview Feedback</h1>
            <p id="employee-name">Loading...</p>
        </div>

        <div id="error-message" class="alert alert-danger" style="display: none;"></div>
        <div id="success-message" class="alert alert-success" style="display: none;"></div>

        <div class="info-box">
            <h3>Interview Information</h3>
            <p><strong>Interview Date:</strong> <span id="interview-date">Loading...</span></p>
            <p><strong>Interview Time:</strong> <span id="interview-time">Loading...</span></p>
            <p><strong>Location:</strong> <span id="interview-location">Loading...</span></p>
        </div>

        <form id="feedbackForm">
            <div class="rating-group">
                <label>Interview Rating *</label>
                <div class="rating-container">
                    <span class="star" data-rating="1">★</span>
                    <span class="star" data-rating="2">★</span>
                    <span class="star" data-rating="3">★</span>
                    <span class="star" data-rating="4">★</span>
                    <span class="star" data-rating="5">★</span>
                </div>
                <input type="hidden" id="interview_rating" name="interview_rating">
            </div>

            <div class="form-group">
                <label for="interview_feedback">Interview Feedback *</label>
                <textarea id="interview_feedback" name="interview_feedback" class="form-control"
                          placeholder="Please share your feedback about the interview experience..." required></textarea>
            </div>

            <div class="form-group">
                <label for="hr_notes">HR Notes (Optional)</label>
                <textarea id="hr_notes" name="hr_notes" class="form-control"
                          placeholder="Internal HR notes or follow-up actions..."></textarea>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <button type="submit" class="btn">Submit Feedback</button>
                <a href="#" onclick="window.close()" class="btn btn-secondary" style="margin-left: 10px;">Cancel</a>
            </div>
        </form>

        <div class="alert alert-info">
            <strong>💡 Your Feedback Matters:</strong>
            Your honest feedback helps us improve our workplace for current and future employees.
        </div>
    </div>

    <script>
        // Get token from URL
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (!token) {
            document.getElementById('error-message').style.display = 'block';
            document.getElementById('error-message').textContent = 'Invalid or missing token. Please check your email link.';
            document.getElementById('feedbackForm').style.display = 'none';
        } else {
            // Load interview data
            loadInterviewData(token);
            setupRatingStars();
        }

        function setupRatingStars() {
            const stars = document.querySelectorAll('.star');
            stars.forEach(star => {
                star.addEventListener('click', function() {
                    const rating = parseInt(this.dataset.rating);
                    const ratingInput = document.getElementById('interview_rating');
                    ratingInput.value = rating;

                    // Update star display
                    stars.forEach(s => {
                        s.classList.remove('selected');
                        if (parseInt(s.dataset.rating) <= rating) {
                            s.classList.add('selected');
                        }
                    });
                });

                star.addEventListener('mouseenter', function() {
                    const rating = parseInt(this.dataset.rating);
                    stars.forEach(s => {
                        s.classList.remove('selected');
                        if (parseInt(s.dataset.rating) <= rating) {
                            s.classList.add('selected');
                        }
                    });
                });
            });
        }

        async function loadInterviewData(token) {
            try {
                // Get interview data from token
                const response = await fetch(`/api/forms/validate-interview-token?token=${token}`);
                const result = await response.json();

                if (result.valid) {
                    // Populate interview info
                    document.getElementById('employee-name').textContent = `Thanks ${result.data.employee_name}!`;
                    document.getElementById('interview-date').textContent = result.data.interview_date || 'TBD';
                    document.getElementById('interview-time').textContent = result.data.interview_time || 'TBD';
                    document.getElementById('interview-location').textContent = result.data.interview_location || 'HR Office';

                    // Handle form submission
                    document.getElementById('feedbackForm').addEventListener('submit', handleSubmit);
                } else {
                    document.getElementById('error-message').style.display = 'block';
                    document.getElementById('error-message').textContent = result.error;
                    document.getElementById('feedbackForm').style.display = 'none';
                }
            } catch (error) {
                document.getElementById('error-message').style.display = 'block';
                document.getElementById('error-message').textContent = 'Failed to load data. Please try again or contact HR.';
                document.getElementById('feedbackForm').style.display = 'none';
                console.error('Error:', error);
            }
        }

        async function handleSubmit(event) {
            event.preventDefault();

            const formData = new FormData(event.target);
            const data = {
                interview_rating: formData.get('interview_rating') ? parseInt(formData.get('interview_rating')) : null,
                interview_feedback: formData.get('interview_feedback'),
                hr_notes: formData.get('hr_notes')
            };

            try {
                const response = await fetch(`/api/forms/submit-feedback?token=${token}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.success) {
                    document.getElementById('success-message').style.display = 'block';
                    document.getElementById('success-message').innerHTML = `
                        <strong>✅ Feedback Submitted Successfully!</strong><br>
                        Thank you for your valuable feedback.<br>
                        Your insights will help us improve our workplace.
                    `;
                    document.getElementById('feedbackForm').style.display = 'none';

                    // Close window after 3 seconds
                    setTimeout(() => window.close(), 3000);
                } else {
                    document.getElementById('error-message').style.display = 'block';
                    document.getElementById('error-message').textContent = result.error;
                }
            } catch (error) {
                document.getElementById('error-message').style.display = 'block';
                document.getElementById('error-message').textContent = 'Failed to submit feedback. Please try again.';
                console.error('Error:', error);
            }
        }
    </script>
</body>
</html>
"""

SKIP_INTERVIEW_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skip Exit Interview</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin: 20px auto;
        }
        .header {
            background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%);
            color: #333;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
            margin: -40px -40px 40px -40px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        .form-control:focus {
            outline: none;
            border-color: #ffc107;
            box-shadow: 0 0 0 0.2rem rgba(255, 193, 7, 0.25);
        }
        textarea.form-control {
            min-height: 100px;
            resize: vertical;
        }
        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: #ffc107;
            color: #333;
            text-decoration: none;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s;
        }
        .btn:hover {
            background: #e0a800;
            transform: translateY(-2px);
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        .reason-box {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border: 2px solid #dee2e6;
        }
        .info-box {
            background: #fff3cd;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .alert-warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }
        .alert-info {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }
        .alert-danger {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ Skip Exit Interview</h1>
            <p id="employee-name">Loading...</p>
        </div>

        <div id="error-message" class="alert alert-danger" style="display: none;"></div>
        <div id="success-message" class="alert alert-success" style="display: none;"></div>

        <div class="info-box">
            <h3>📋 Skip Interview Request</h3>
            <p><strong>Last Working Day:</strong> <span id="last-working-day">Loading...</span></p>
        </div>

        <div class="reason-box">
            <strong>Reason for Skipping Interview:</strong>
            <p>Please provide a brief reason for skipping the exit interview.</p>
        </div>

        <form id="skipForm">
            <div class="form-group">
                <label for="reason">Reason for Skipping *</label>
                <select id="reason" name="reason" class="form-control" required>
                    <option value="">Select a reason...</option>
                    <option value="Employee not available">Employee not available</option>
                    <option value="Remote employee">Remote employee</option>
                    <option value="Already completed">Exit interview completed elsewhere</option>
                    <option value="Special circumstances">Special circumstances</option>
                    <option value="Other">Other (please specify)</option>
                </select>
            </div>

            <div class="form-group" id="other-reason-group" style="display: none;">
                <label for="other_reason">Please Specify:</label>
                <input type="text" id="other_reason" name="other_reason" class="form-control" placeholder="Please specify the reason...">
            </div>

            <div class="form-group">
                <label for="additional_notes">Additional Notes (Optional)</label>
                <textarea id="additional_notes" name="additional_notes" class="form-control"
                          placeholder="Any additional context or special requirements..."></textarea>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <button type="submit" class="btn">Confirm Skip Interview</button>
                <a href="#" onclick="window.close()" class="btn btn-secondary" style="margin-left: 10px;">Cancel</a>
            </div>
        </form>

        <div class="info-box">
            <h3>ℹ️ What Happens Next:</h3>
            <p>Once you confirm:</p>
            <ul>
                <li>Interview will be marked as skipped</li>
                <li>IT department will be notified immediately</li>
                <li>Asset clearance process will begin</li>
                <li>Your offboarding will continue as normal</li>
            </ul>
        </div>

        <div class="alert alert-warning">
            <strong>⚠️ Important:</strong> This action will expedite your offboarding by skipping the interview process.
        </div>
    </div>

    <script>
        // Handle "Other" reason option
        const reasonSelect = document.getElementById('reason');
        const otherReasonGroup = document.getElementById('other-reason-group');

        reasonSelect.addEventListener('change', function() {
            if (this.value === 'Other') {
                otherReasonGroup.style.display = 'block';
            } else {
                otherReasonGroup.style.display = 'none';
            }
        });

        // Get token from URL
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (!token) {
            document.getElementById('error-message').style.display = 'block';
            document.getElementById('error-message').textContent = 'Invalid or missing token. Please check your email link.';
            document.getElementById('skipForm').style.display = 'none';
        } else {
            // Load employee data
            loadEmployeeData(token);
        }

        async function loadEmployeeData(token) {
            try {
                // Get submission data from token
                const response = await fetch(`/api/forms/validate-skip-token?token=${token}`);
                const result = await response.json();

                if (result.valid) {
                    // Populate employee info
                    document.getElementById('employee-name').textContent = `Hi ${result.data.employee_name}!`;
                    document.getElementById('last-working-day').textContent = result.data.last_working_day || 'TBD';

                    // Handle form submission
                    document.getElementById('skipForm').addEventListener('submit', handleSubmit);
                } else {
                    document.getElementById('error-message').style.display = 'block';
                    document.getElementById('error-message').textContent = result.error;
                    document.getElementById('skipForm').style.display = 'none';
                }
            } catch (error) {
                document.getElementById('error-message').style.display = 'block';
                document.getElementById('error-message').textContent = 'Failed to load data. Please try again or contact HR.';
                document.getElementById('skipForm').style.display = 'none';
                console.error('Error:', error);
            }
        }

        async function handleSubmit(event) {
            event.preventDefault();

            const formData = new FormData(event.target);
            const selectedReason = formData.get('reason');
            const otherReason = formData.get('other_reason');
            const additionalNotes = formData.get('additional_notes');

            // Combine reason
            const finalReason = selectedReason === 'Other' ? otherReason : selectedReason;

            const data = {
                reason: finalReason,
                additional_notes: additionalNotes
            };

            try {
                const response = await fetch(`/api/forms/skip-interview?token=${token}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.success) {
                    document.getElementById('success-message').style.display = 'block';
                    document.getElementById('success-message').innerHTML = `
                        <strong>✅ Interview Skipped Successfully!</strong><br>
                        IT department has been notified and will begin the asset clearance process.<br>
                        Your offboarding will continue as normal.
                    `;
                    document.getElementById('skipForm').style.display = 'none';

                    // Close window after 3 seconds
                    setTimeout(() => window.close(), 3000);
                } else {
                    document.getElementById('error-message').style.display = 'block';
                    document.getElementById('error-message').textContent = result.error;
                }
            } catch (error) {
                document.getElementById('error-message').style.display = 'block';
                document.getElementById('error-message').textContent = 'Failed to skip interview. Please try again.';
                console.error('Error:', error);
            }
        }
    </script>
</body>
</html>
"""

# API endpoints
@router.get("/schedule-interview")
def get_schedule_interview_form(request: Request, token: Optional[str] = None):
    """Serve the interview scheduling form"""
    return HTMLResponse(content=SCHEDULE_INTERVIEW_FORM, media_type="text/html")

@router.get("/submit-feedback")
def get_feedback_form(request: Request, token: str):
    """Serve the feedback submission form"""
    return HTMLResponse(content=FEEDBACK_FORM, media_type="text/html")

@router.get("/skip-interview")
def get_skip_interview_form(request: Request, token: str):
    """Serve the skip interview form"""
    return HTMLResponse(content=SKIP_INTERVIEW_FORM, media_type="text/html")

@router.get("/validate-token")
async def validate_token(request: Request, token: str, db: Session = Depends(get_db)):
    """Validate a token and return embedded data with submission details"""
    try:
        service = get_tokenized_form_service()
        is_valid, token_data, error_msg = service.validate_and_extract_token(token)

        if not is_valid:
            return JSONResponse({
                "valid": False,
                "error": error_msg
            }, status_code=400)

        # Get submission details from database
        submission_id = token_data.get("submission_id")
        if not submission_id:
            return JSONResponse({
                "valid": False,
                "error": "Token missing submission_id"
            }, status_code=400)

        from app.models.submission import Submission
        submission = db.query(Submission).filter(Submission.id == submission_id).first()

        if not submission:
            return JSONResponse({
                "valid": False,
                "error": "Submission not found"
            }, status_code=404)

        # Return token data with submission details
        return JSONResponse({
            "valid": True,
            "data": {
                **token_data,
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "position": getattr(submission, 'position', 'Employee'),
                "department": getattr(submission, 'department', 'General'),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d") if submission.last_working_day else None
            }
        })

    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return JSONResponse({
            "valid": False,
            "error": f"Token validation failed: {str(e)}"
        }, status_code=500)

@router.get("/validate-interview-token")
async def validate_interview_token(request: Request, token: str, db: Session = Depends(get_db)):
    """Validate interview token and return interview data"""
    try:
        service = get_tokenized_form_service()
        is_valid, token_data, error_msg = service.validate_and_extract_token(token)

        if not is_valid:
            return JSONResponse({
                "valid": False,
                "error": error_msg
            }, status_code=400)

        # Verify this is an interview feedback token
        if token_data.get("action") != "submit_feedback":
            return JSONResponse({
                "valid": False,
                "error": "Invalid token type for this endpoint"
            }, status_code=400)

        # Get interview details
        interview_id = token_data.get("interview_id")
        from app.models.exit_interview import ExitInterview
        interview = db.query(ExitInterview).filter(ExitInterview.id == interview_id).first()

        if not interview:
            return JSONResponse({
                "valid": False,
                "error": "Interview not found"
            }, status_code=404)

        submission = interview.submission

        return JSONResponse({
            "valid": True,
            "data": {
                "employee_name": submission.employee_name,
                "interview_date": interview.scheduled_date.strftime("%Y-%m-%d") if interview.scheduled_date else None,
                "interview_time": interview.scheduled_time,
                "interview_location": interview.location,
                "interviewer": interview.interviewer
            }
        })

    except Exception as e:
        logger.error(f"Interview token validation error: {str(e)}")
        return JSONResponse({
            "valid": False,
            "error": f"Interview token validation failed: {str(e)}"
        }, status_code=500)

@router.get("/validate-skip-token")
async def validate_skip_token(request: Request, token: str, db: Session = Depends(get_db)):
    """Validate skip interview token and return submission data"""
    try:
        service = get_tokenized_form_service()
        is_valid, token_data, error_msg = service.validate_and_extract_token(token)

        if not is_valid:
            return JSONResponse({
                "valid": False,
                "error": error_msg
            }, status_code=400)

        # Verify this is a skip interview token
        if token_data.get("action") != "skip_interview":
            return JSONResponse({
                "valid": False,
                "error": "Invalid token type for this endpoint"
            }, status_code=400)

        # Get submission details
        submission_id = token_data.get("submission_id")
        from app.models.submission import Submission
        submission = db.query(Submission).filter(Submission.id == submission_id).first()

        if not submission:
            return JSONResponse({
                "valid": False,
                "error": "Submission not found"
            }, status_code=404)

        return JSONResponse({
            "valid": True,
            "data": {
                "employee_name": submission.employee_name,
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d") if submission.last_working_day else None
            }
        })

    except Exception as e:
        logger.error(f"Skip token validation error: {str(e)}")
        return JSONResponse({
            "valid": False,
            "error": f"Skip token validation failed: {str(e)}"
        }, status_code=500)

@router.post("/schedule-interview")
async def schedule_interview_via_form(
    request: Request,
    token: str,
    form_data: InterviewScheduleForm,
    db: Session = Depends(get_db)
):
    """Handle interview scheduling from email form"""
    try:
        service = get_tokenized_form_service()
        is_valid, token_data, error_msg = service.validate_and_extract_token(token)

        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Verify this is a schedule interview token
        if token_data.get("action") != "schedule_interview":
            raise HTTPException(status_code=400, detail="Invalid token type")

        submission_id = token_data.get("submission_id")
        employee_email = token_data.get("employee_email")

        # Parse datetime
        from datetime import datetime
        scheduled_date = datetime.strptime(form_data.scheduled_date, "%Y-%m-%d")
        scheduled_time = form_data.scheduled_time

        # Schedule the interview
        exit_interview = schedule_exit_interview(
            db=db,
            submission_id=submission_id,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            location=form_data.location,
            interviewer=form_data.interviewer
        )

        # Get submission details
        submission = exit_interview.submission

        # Send confirmation email
        from app.services.email import get_email_service
        email_service = get_email_service()

        email_data = {
            "employee_name": submission.employee_name,
            "employee_email": submission.employee_email,
            "scheduled_date": scheduled_date.strftime("%A, %B %d, %Y"),
            "scheduled_time": scheduled_time,
            "location": form_data.location,
            "interviewer": form_data.interviewer,
            "department": getattr(submission, 'department', 'General'),
            "position": getattr(submission, 'position', 'Employee'),
            "last_working_day": submission.last_working_day.strftime("%Y-%m-%d")
        }

        email_message = EmailTemplates.exit_interview_scheduled(email_data)
        success = await email_service.send_email(email_message)

        logger.info(f"[OK] Interview scheduled via email form for {submission.employee_name}")

        return JSONResponse({
            "success": True,
            "message": "Interview scheduled successfully!",
            "interview": {
                "interview_id": exit_interview.id,
                "scheduled_date": scheduled_date.strftime("%Y-%m-%d"),
                "scheduled_time": scheduled_time,
                "location": form_data.location,
                "interviewer": form_data.interviewer,
                "email_sent": success
            },
            "employee_name": submission.employee_name
        })

    except Exception as e:
        logger.error(f"Error scheduling interview via form: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule interview: {str(e)}")

@router.post("/submit-feedback")
async def submit_feedback_via_form(
    request: Request,
    token: str,
    form_data: InterviewFeedbackForm,
    db: Session = Depends(get_db)
):
    """Handle feedback submission from email form"""
    try:
        service = get_tokenized_form_service()
        is_valid, token_data, error_msg = service.validate_and_extract_token(token)

        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Verify this is a feedback submission token
        if token_data.get("action") != "submit_feedback":
            raise HTTPException(status_code=400, detail="Invalid token type")

        interview_id = token_data.get("interview_id")

        # Complete the interview
        exit_interview = complete_exit_interview(
            db=db,
            interview_id=interview_id,
            feedback=form_data.interview_feedback,
            rating=form_data.interview_rating,
            hr_notes=form_data.hr_notes
        )

        if not exit_interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        submission = exit_interview.submission

        # Get email service and send IT notification
        from app.services.email import get_email_service
        email_service = get_email_service()
        service = get_tokenized_form_service()

        # Generate IT clearance form token
        it_clearance_token = service.generate_secure_token({
            "form_type": "it_clearance",
            "submission_id": submission.id,
            "employee_name": submission.employee_name,
            "created_for": "it_clearance"
        })

        # Create IT clearance form URL
        clearance_form_url = f"{BASE_URL}/api/forms/complete-it-clearance?token={it_clearance_token}"

        email_data = {
            "employee_name": submission.employee_name,
            "employee_email": submission.employee_email,
            "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
            "department": getattr(submission, 'department', 'General'),
            "position": getattr(submission, 'position', 'Employee'),
            "assets": {},  # TODO: Get actual asset data
            "submission_id": submission.id
        }

        email_message = EmailTemplates.it_clearance_request(email_data, clearance_form_url)
        success = await email_service.send_email(email_message)

        logger.info(f"[OK] Feedback submitted via email form for {submission.employee_name}")
        if success:
            logger.info(f"[OK] IT notification sent for {submission.employee_name}")

        return JSONResponse({
            "success": True,
            "message": "Feedback submitted successfully! IT has been notified.",
            "interview": {
                "interview_id": exit_interview.id,
                "rating": form_data.interview_rating,
                "feedback": form_data.interview_feedback,
                "hr_notes": form_data.hr_notes,
                "it_notification_sent": success
            },
            "employee_name": submission.employee_name
        })

    except Exception as e:
        logger.error(f"Error submitting feedback via form: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@router.post("/skip-interview")
async def skip_interview_via_form(
    request: Request,
    token: str,
    form_data: SkipInterviewForm,
    db: Session = Depends(get_db)
):
    """Handle interview skip from email form"""
    try:
        service = get_tokenized_form_service()
        is_valid, token_data, error_msg = service.validate_and_extract_token(token)

        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Verify this is a skip or schedule interview token (both can skip)
        if token_data.get("action") not in ["skip_interview", "schedule_interview"]:
            raise HTTPException(status_code=400, detail="Invalid token type for skipping interview")

        submission_id = token_data.get("submission_id")
        employee_email = token_data.get("employee_email")

        # Update submission status
        from app.crud import update_submission
        from app.schemas_all import SubmissionUpdate
        from app.models.submission import ResignationStatus

        update_data = SubmissionUpdate(
            resignation_status=ResignationStatus.EXIT_DONE.value,
            exit_interview_status="done",
            exit_interview_notes=f"Interview skipped via form. Reason: {form_data.reason}",
            hr_notes=form_data.additional_notes
        )

        updated_submission = update_submission(db, submission_id, update_data)

        # Get submission details
        submission = updated_submission

        # Generate IT clearance token
        from config import settings
        it_clearance_token = service.generate_token(
            data={
                "form_type": "it_clearance",
                "submission_id": submission.id,
                "employee_email": submission.employee_email,
                "created_for": "it_clearance"
            },
            expires_hours=72
        )

        # Create IT clearance form URL
        BASE_URL = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        clearance_form_url = f"{BASE_URL}/api/forms/complete-it-clearance?token={it_clearance_token}"

        # Send IT notification
        from app.services.email import get_email_service, EmailTemplates
        email_service = get_email_service()

        email_data = {
            "employee_name": submission.employee_name,
            "employee_email": submission.employee_email,
            "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
            "department": getattr(submission, 'department', 'General'),
            "position": getattr(submission, 'position', 'Employee'),
            "assets": {},  # TODO: Get actual asset data
            "submission_id": submission.id
        }

        email_message = EmailTemplates.it_clearance_request(email_data, clearance_form_url)
        success = await email_service.send_email(email_message)

        logger.info(f"[OK] Interview skipped via form for {submission.employee_name}")
        if success:
            logger.info(f"[OK] IT notification sent for {submission.employee_name}")

        return JSONResponse({
            "success": True,
            "message": "Interview skipped successfully! IT has been notified.",
            "submission": {
                "id": submission.id,
                "status": submission.resignation_status,
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d")
            },
            "employee_name": submission.employee_name,
            "it_notification_sent": success
        })

    except Exception as e:
        logger.error(f"Error skipping interview via form: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to skip interview: {str(e)}")


# Create a utility function to send tokenized emails
async def send_tokenized_email(
    template_func,
    employee_data: Dict,
    base_url: str,
    token_service = None,
    email_service = None
):
    """Send a tokenized email and return the token"""
    try:
        if not token_service:
            token_service = get_tokenized_form_service()
        if not email_service:
            email_service = get_email_service()

        # Generate token
        token = token_service.generate_secure_token(employee_data, expires_hours=72)

        # Generate email HTML
        email_html = template_func(employee_data, token, base_url)

        # Create email message
        from app.services.email import EmailMessage
        email_message = EmailMessage(
            to_email=employee_data["employee_email"],
            to_name=employee_data["employee_name"],
            subject=f"Action Required: {employee_data['action']}",
            template_name="tokenized_email",
            template_data={"html_content": email_html}
        )

        # Send email
        success = await email_service.send_email(email_message)

        if success:
            logger.info(f"[OK] Tokenized email sent to {employee_data['employee_email']}")
            return token
        else:
            logger.error(f"[ERROR] Failed to send tokenized email to {employee_data['employee_email']}")
            return None

    except Exception as e:
        logger.error(f"Error sending tokenized email: {str(e)}")
        return None


@router.post("/skip-interview-dashboard")
async def skip_interview_dashboard(
    skip_data: dict,
    db: Session = Depends(get_db)
):
    """Handle interview skip from dashboard (not email form)"""
    try:
        from app.crud_exit_interview import create_exit_interview
        from app.models.submission import Submission, ResignationStatus
        from app.services.email import get_email_service, EmailTemplates
        from datetime import datetime
        import logging

        logger = logging.getLogger(__name__)

        submission_id = skip_data.get("submission_id")
        skip_reason = skip_data.get("reason") or skip_data.get("skip_reason") or "HR decided to skip exit interview"

        if not submission_id:
            return {
                "success": False,
                "message": "Submission ID is required"
            }

        # Get submission
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return {
                "success": False,
                "message": "Submission not found"
            }

        logger.info(f"Skipping interview for submission {submission_id}: {submission.employee_name}")

        # Create ExitInterview record if it doesn't exist
        exit_interview = create_exit_interview(db, submission_id)

        # Mark as skipped
        exit_interview.interview_completed = True
        exit_interview.interview_completed_at = datetime.utcnow()
        exit_interview.interview_feedback = f"Interview skipped: {skip_reason}"
        exit_interview.interview_rating = 0  # 0 indicates skipped

        # Update submission status
        submission.resignation_status = ResignationStatus.EXIT_DONE.value
        submission.exit_interview_status = "skipped"

        db.commit()

        # Send IT notification (assets collection)
        try:
            email_service = get_email_service()
            service = get_tokenized_form_service()

            # Generate IT clearance form token
            it_clearance_token = service.generate_secure_token({
                "form_type": "it_clearance",
                "submission_id": submission.id,
                "employee_name": submission.employee_name,
                "created_for": "it_clearance"
            })

            # Create IT clearance form URL
            clearance_form_url = f"{BASE_URL}/api/forms/complete-it-clearance?token={it_clearance_token}"

            email_data = {
                "employee_name": submission.employee_name,
                "employee_email": submission.employee_email,
                "department": getattr(submission, 'department', 'General'),
                "position": getattr(submission, 'position', 'Employee'),
                "last_working_day": submission.last_working_day.strftime("%Y-%m-%d"),
                "submission_id": submission.id,
                "interview_completed": True,
                "interview_date": datetime.now().strftime("%Y-%m-%d"),
                "interview_feedback": f"Interview skipped: {skip_reason}"
            }

            email_message = EmailTemplates.it_clearance_request(email_data, clearance_form_url)
            await email_service.send_email(email_message)
            logger.info(f"IT notification sent for skipped interview: {submission.employee_name}")

        except Exception as email_error:
            logger.warning(f"Failed to send IT notification: {str(email_error)}")

        return {
            "success": True,
            "message": "Interview skipped successfully and IT notified",
            "submission_id": submission.id,
            "employee_name": submission.employee_name
        }

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to skip interview from dashboard: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to skip interview: {str(e)}"
        }


@router.post("/create-interviews-for-chm-approved")
async def create_interviews_for_chm_approved(db: Session = Depends(get_db)):
    """Create ExitInterview records for all CHM-approved submissions that don't have them yet"""
    try:
        from app.models.submission import Submission, ResignationStatus
        from app.crud_exit_interview import create_exit_interview, get_exit_interview_by_submission
        import logging

        logger = logging.getLogger(__name__)

        # Find CHM-approved submissions
        chm_approved_submissions = db.query(Submission).filter(
            Submission.resignation_status == ResignationStatus.CHM_APPROVED.value
        ).all()

        created_count = 0
        for submission in chm_approved_submissions:
            # Check if ExitInterview record already exists
            existing_interview = get_exit_interview_by_submission(db, submission.id)
            if not existing_interview:
                # Create ExitInterview record
                create_exit_interview(db, submission.id)
                created_count += 1
                logger.info(f"Created ExitInterview record for: {submission.employee_name} (ID: {submission.id})")
            else:
                logger.info(f"ExitInterview record already exists for: {submission.employee_name} (ID: {submission.id})")

        return {
            "success": True,
            "message": f"Successfully processed {len(chm_approved_submissions)} CHM-approved submissions",
            "created": created_count,
            "existing": len(chm_approved_submissions) - created_count,
            "total": len(chm_approved_submissions)
        }

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create interview records: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to create interview records: {str(e)}"
        }

# =============================================================================
# IT Asset Clearance Form
# =============================================================================

IT_CLEARANCE_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IT Asset Clearance</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; background-color: #f5f5f5; }
        .container { background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
        .employee-info { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 30px; }
        .info-row { margin: 10px 0; }
        label { display: block; margin: 15px 0 5px; font-weight: bold; color: #555; }
        input[type="text"], input[type="date"], textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box; }
        textarea { min-height: 100px; resize: vertical; }
        .checkbox-group { margin: 20px 0; }
        .checkbox-item { margin: 10px 0; padding: 10px; background-color: #f8f9fa; border-radius: 4px; }
        .checkbox-item input[type="checkbox"] { margin-right: 10px; }
        button { background-color: #2c3e50; color: white; padding: 12px 30px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; width: 100%; margin-top: 20px; }
        button:hover { background-color: #1a252f; }
        .success { color: #27ae60; text-align: center; padding: 20px; font-size: 18px; }
        .error { color: #c0392b; text-align: center; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>IT Asset Clearance Form</h1>
        <div class="employee-info">
            <div class="info-row"><strong>Employee:</strong> {{ employee_name }}</div>
            <div class="info-row"><strong>Email:</strong> {{ employee_email }}</div>
            <div class="info-row"><strong>Last Working Day:</strong> {{ last_working_day }}</div>
        </div>
        <form id="clearanceForm">
            <input type="hidden" name="token" value="{{ token }}">

            <div class="checkbox-group">
                <label>Assets Collected:</label>
                <div class="checkbox-item">
                    <input type="checkbox" name="laptop_collected" required> Laptop/Desktop Computer
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" name="accessories_collected" required> Mouse, Keyboard, Headset
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" name="mobile_collected"> Mobile Device (if applicable)
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" name="access_cards_collected" required> Access Cards/Keys
                </div>
            </div>

            <label>Collection Date:</label>
            <input type="date" name="collection_date" required>

            <label>IT Notes:</label>
            <textarea name="it_notes" placeholder="Any issues or additional notes..."></textarea>

            <label>System Access Disabled:</label>
            <select name="access_disabled" required>
                <option value="">-- Select --</option>
                <option value="yes">Yes - All access disabled</option>
                <option value="no">No - Still pending</option>
            </select>

            <button type="submit">Complete IT Clearance</button>
        </form>
        <div id="message"></div>
    </div>
    <script>
        document.getElementById('clearanceForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                token: formData.get('token'),
                laptop_collected: formData.get('laptop_collected') === 'on',
                accessories_collected: formData.get('accessories_collected') === 'on',
                mobile_collected: formData.get('mobile_collected') === 'on',
                access_cards_collected: formData.get('access_cards_collected') === 'on',
                collection_date: formData.get('collection_date'),
                it_notes: formData.get('it_notes'),
                access_disabled: formData.get('access_disabled') === 'yes'
            };
            try {
                const response = await fetch('/api/forms/complete-it-clearance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                document.getElementById('message').innerHTML = result.success
                    ? '<div class="success">&#10003; IT Clearance completed successfully!</div>'
                    : '<div class="error">' + result.message + '</div>';
                if (result.success) e.target.style.display = 'none';
            } catch (error) {
                document.getElementById('message').innerHTML = '<div class="error">Error: ' + error.message + '</div>';
            }
        });
    </script>
</body>
</html>
"""


@router.get("/complete-it-clearance")
async def show_it_clearance_form(token: str, db: Session = Depends(get_db)):
    """Display IT asset clearance form"""
    try:
        token_service = get_tokenized_form_service()
        is_valid, data, error_msg = token_service.validate_and_extract_token(token)

        if not is_valid or not data:
            return HTMLResponse(f"<html><body><h1>Invalid or expired token</h1><p>{error_msg or 'This link may have expired or is invalid.'}</p></body></html>")

        from app.models.submission import Submission
        submission = db.query(Submission).filter(Submission.id == data["submission_id"]).first()

        if not submission:
            return HTMLResponse("<html><body><h1>Submission not found</h1></body></html>")

        html = IT_CLEARANCE_FORM.replace("{{ employee_name }}", submission.employee_name) \
            .replace("{{ employee_email }}", submission.employee_email) \
            .replace("{{ last_working_day }}", submission.last_working_day.strftime("%Y-%m-%d") if submission.last_working_day else "N/A") \
            .replace("{{ token }}", token)

        return HTMLResponse(html)
    except Exception as e:
        logger.error(f"Error showing IT clearance form: {str(e)}")
        return HTMLResponse(f"<html><body><h1>Error loading form</h1><p>{str(e)}</p></body></html>")


class ITClearanceData(BaseModel):
    token: str
    laptop_collected: bool
    accessories_collected: bool
    mobile_collected: bool
    access_cards_collected: bool
    collection_date: str
    it_notes: str = ""
    access_disabled: bool


@router.post("/complete-it-clearance")
async def submit_it_clearance(data: ITClearanceData, db: Session = Depends(get_db)):
    """Process IT asset clearance form submission"""
    try:
        token_service = get_tokenized_form_service()
        is_valid, token_data, error_msg = token_service.validate_and_extract_token(data.token)

        if not is_valid or not token_data:
            return JSONResponse({"success": False, "message": error_msg or "Invalid or expired token"}, status_code=400)

        from app.models.submission import Submission, ResignationStatus
        from app.models.asset import Asset

        submission = db.query(Submission).filter(Submission.id == token_data["submission_id"]).first()

        if not submission:
            return JSONResponse({"success": False, "message": "Submission not found"}, status_code=404)

        # Create or update Asset record
        asset = db.query(Asset).filter(Asset.res_id == submission.id).first()

        if asset:
            # Update existing asset
            asset.assets_returned = True
            asset.notes = data.it_notes or f"IT clearance completed on {data.collection_date}"
        else:
            # Create new asset record
            asset = Asset(
                res_id=submission.id,
                assets_returned=True,
                notes=data.it_notes or f"IT clearance completed on {data.collection_date}"
            )
            db.add(asset)

        # Update submission IT status
        submission.it_support_reply = True

        # Update resignation status to ASSETS_RECORDED (IT clearance done)
        submission.resignation_status = ResignationStatus.ASSETS_RECORDED.value

        db.commit()
        db.refresh(submission)

        logger.info(f"[OK] IT clearance completed for submission {submission.id} - {submission.employee_name}")
        logger.info(f"[OK] Asset record created/updated: assets_returned=True")
        logger.info(f"[OK] Submission status updated to: {submission.resignation_status}")

        return JSONResponse({
            "success": True,
            "message": "IT clearance completed successfully",
            "submission_status": submission.resignation_status
        })

    except Exception as e:
        logger.error(f"Error processing IT clearance: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
