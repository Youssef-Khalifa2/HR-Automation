# Schedule Interview Button - Token Error Fix

## Issue

When clicking "Schedule Interview" button, you're seeing:
```json
{"detail":[{"type":"missing","loc":["query","token"],"msg":"Field required","input":null}]}
```

## Root Cause Analysis

There are TWO different ways to schedule interviews:

### 1. Dashboard Modal (For HR Users - Authenticated)
- **Location**: Dashboard → Submissions list → Click "Schedule interview" action
- **Endpoint**: `/api/submissions/exit-interviews/schedule/`
- **Authentication**: Requires HR user login (cookie-based)
- **How it works**: Opens a modal with a form, submits directly to authenticated endpoint
- **Status**: Working correctly after trailing slash fix

### 2. Email Link Form (For External Access - Token-based)
- **Location**: Email sent to HR with link to schedule interview
- **Endpoint**: `/api/forms/schedule-interview?token=XXX`
- **Authentication**: Uses security token in URL
- **How it works**: Opens standalone HTML form that requires token parameter
- **Problem**: This endpoint REQUIRES a token parameter

## The Error You're Seeing

The error is coming from trying to access `/api/forms/schedule-interview` WITHOUT the token parameter.

**This happens when:**
1. You're clicking an email link that's malformed (missing token)
2. You're trying to access the form URL directly without the token
3. There's a button/link somewhere that's calling this endpoint incorrectly

## Solutions

### For Dashboard Users (HR Staff)
**Use the dashboard modal** - it's already authenticated and doesn't need a token:
1. Log into dashboard at http://localhost:5173
2. Find submission in the list
3. Click "Schedule interview" button
4. Fill out the modal form
5. Click "Schedule Interview"

This works because you're already authenticated as an HR user.

### For Email Links (External Users)
The email link MUST include the token:
```
http://localhost:8000/api/forms/schedule-interview?token=VALID_TOKEN_HERE
```

The token is automatically generated when the approval workflow sends emails.

## Quick Test

### Test Dashboard Schedule Interview (Should Work):
1. Open http://localhost:5173
2. Log in with HR credentials
3. Go to Submissions
4. Find a submission with status "CHM Approved" and exit interview "Not Scheduled"
5. Click the "Schedule interview" button in the actions column
6. Fill out the form in the modal
7. Click "Schedule Interview"
8. Should get success message

### If You're Still Seeing the Token Error:

**Option 1**: You're clicking the wrong link
- Make sure you're using the dashboard modal, not trying to access `/api/forms/schedule-interview` directly

**Option 2**: The email link is broken
- Check the email sent by the system
- The URL should have `?token=XXX` at the end
- If missing, there's a bug in the email template URL generation

**Option 3**: Disable token requirement for GET (Show form without validation)
We can make the form accessible without token for viewing, but still require it for submission.

## What I Fixed

1. **Dashboard Endpoint**: Added trailing slash to match backend route definition
   - Changed: `/submissions/exit-interviews/schedule`
   - To: `/submissions/exit-interviews/schedule/`

2. **File**: `templates/dashboard.html` line 381

## Testing Steps

1. **Clear browser cache** (important!)
2. **Refresh dashboard** at http://localhost:5173
3. **Click "Schedule interview"** button on any CHM-approved submission
4. **Fill out the form** in the modal
5. **Submit** - should work without token error

If you still see the token error, **please tell me exactly where you're clicking**:
- Are you clicking from the dashboard?
- Are you clicking from an email link?
- Are you typing a URL directly in the browser?

This will help me identify the exact source of the problem.

---

**Fixed**: 2025-11-10
**Files Modified**: `templates/dashboard.html`
