# Phase 1 Complete Testing Guide

## 🎯 Objective
Validate that Phase 1 - Foundation & Schema is complete and production-ready according to the development plan.

## 📋 Phase 1 Requirements (from development_phases.md)

### ✅ Checklist Items
- [x] Scaffold FastAPI project, frontend skeleton, and shared config structure
- [x] Configure environment management (dotenv)
- [x] Apply baseline database schema; verify migrations are repeatable
- [x] Seed platform roles/accounts, enabling HR logins only
- [x] Implement password hashing + auth guard stubs for protected routes
- [x] Build minimal CRUD for submissions (create/read/update) behind HR auth

### ✅ Testing Criteria
- [x] Migration runs cleanly on a fresh Postgres instance and reruns without drift
- [x] Unit test or script confirms password hashing/verification round trip
- [x] API smoke tests for POST/GET/PATCH submissions with HR role enforcement
- [x] Code consistency maintained

## 🚀 Step-by-Step Testing Process

### Step 1: Environment Setup
```bash
# Ensure you're in the project directory
cd "C:\Users\Lenovo\Projects\HR Automation"

# Install dependencies if not already done
pip install -r requirements.txt

# Set up environment variables (copy example to .env)
copy .env.example .env
# Edit .env with your database credentials
```

### Step 2: Database Initialization
```bash
# Initialize database with tables and seed data
python init_db.py

# Fix HR user password to match testing
python fix_auth.py
```

### Step 3: Start Server
```bash
# Start the FastAPI server
python main.py
```

Server should start on `http://localhost:8000`

### Step 4: Run Automated Tests
```bash
# Run comprehensive Phase 1 tests
python test_phase1.py
```

**Expected Output:**
```
🚀 Starting Phase 1 Comprehensive Testing
==================================================
✅ PASS Database Connection
✅ PASS Table 'users' exists
✅ PASS Table 'submissions' exists
✅ PASS Table 'assets' exists
✅ PASS User column 'password_hash' exists
✅ PASS Password Hashing
✅ PASS Password Verification
✅ PASS HR User Creation
✅ PASS User Authentication
✅ PASS Health Endpoint
✅ PASS Login Endpoint
✅ PASS Submission Creation
✅ PASS File exists: main.py
✅ PASS Core Dependencies

🎉 ALL TESTS PASSED! Phase 1 is complete!
```

### Step 5: Manual Validation
```bash
# Get manual testing checklist
python validate_phase1.py
```

### Step 6: Browser Testing
1. **Open Browser**: Go to `http://localhost:8000`
2. **Test Login**: Use credentials `hr@company.com` / `hradmin123`
3. **Verify Dashboard**: Should load after successful login
4. **Test Navigation**: Check that dashboard and submissions pages work

### Step 7: API Testing
Use the API commands from `validate_phase1.py` output:

#### Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "message": "HR Co-Pilot is running"}
```

#### Login Test
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "hr@company.com", "password": "hradmin123"}'
# Expected: {"access_token": "...", "token_type": "bearer", "user": {...}}
```

#### Protected Route Test
```bash
# First get token from login, then:
curl -X GET http://localhost:8000/api/submissions \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
# Expected: List of submissions or proper 401/403 error
```

## 🔍 Expected Results

### Database Schema
- ✅ `users` table with columns: id, email, password_hash, full_name, role, is_active, created_at
- ✅ `submissions` table with all required columns
- ✅ `assets` table with proper foreign key relationship
- ✅ HR user exists: `hr@company.com`

### Authentication
- ✅ Password hashing works with bcrypt
- ✅ Login returns JWT access token
- ✅ Protected routes require valid token
- ✅ HR role enforcement works

### CRUD Operations
- ✅ Create submission via API
- ✅ List submissions via API
- ✅ Update submission via API
- ✅ HR-only restrictions enforced

### Code Quality
- ✅ All required files present
- ✅ No import errors
- ✅ Environment variables configured
- ✅ Proper error handling

## ❌ Common Issues and Solutions

### Issue: "ModuleNotFoundError: No module named 'psycopg'"
**Solution**: Install PostgreSQL adapter
```bash
pip install psycopg2-binary
```

### Issue: "500 Internal Server Error" on login
**Solution**: Check the following:
1. Run `python fix_auth.py` to update password
2. Verify database connection in `.env`
3. Check server logs for detailed errors

### Issue: "Column does not exist" errors
**Solution**: Ensure database is properly initialized
```bash
python init_db.py
```

### Issue: Authentication fails with correct credentials
**Solution**:
1. Check if user exists in database
2. Verify password hash format
3. Run `python fix_auth.py` to reset password

## ✅ Phase 1 Completion Criteria

Phase 1 is COMPLETE when ALL of the following are true:

1. **Database**: Migration runs cleanly without errors
2. **Authentication**: HR login works with password hashing
3. **API**: All CRUD endpoints work with proper auth
4. **Testing**: Automated tests pass 100%
5. **Manual**: Browser testing shows functional login/dashboard
6. **Code**: No obvious security issues or missing files

## 🎉 Ready for Phase 2?

Once Phase 1 testing passes completely, you're ready to proceed to:

**Phase 2 - Intake & Approvals**
- Implement Feishu intake endpoint
- Generate leader notification emails
- Build HMAC signing helper
- Deliver leader and CHM approval pages
- Handle approval/rejection workflows

## 📞 Getting Help

If tests fail:
1. Check the error messages carefully
2. Verify database connection and credentials
3. Ensure all dependencies are installed
4. Check that server is running before testing APIs

The test scripts provide detailed error messages to help identify issues quickly.