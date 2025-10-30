# HR Co-Pilot - Employee Offboarding Automation

Phase 1 implementation of the HR Co-Pilot MVP, an automated employee resignation workflow management system.

## Overview

HR Co-Pilot streamlines the employee offboarding process through:
- Automated workflow management
- Role-based approval systems
- Real-time status tracking
- Centralized dashboard for HR personnel

## Features (Phase 1)

### ✅ Completed
- **Authentication System**: JWT-based login for HR personnel
- **User Management**: Role-based access control (HR, Leader, CHM, IT)
- **Submission CRUD**: Create, read, update, delete resignation submissions
- **Dashboard**: Real-time statistics and recent activity
- **Database Models**: Complete schema for users, submissions, and assets
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Comprehensive Testing**: Unit, integration, and API tests
- **Responsive UI**: Mobile-friendly Bootstrap interface

### 🚧 Planned (Phase 2+)
- Email notifications and approval links
- Asset management and tracking
- Exit interview scheduling
- Automated reminder system
- Advanced reporting and analytics

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Conda environment (HR_Resignation)

### Installation

1. **Clone and setup**:
   ```bash
   cd "HR Automation"
   python setup.py
   ```

2. **Manual setup** (if setup.py fails):
   ```bash
   # Activate conda environment
   conda activate HR_Resignation

   # Install dependencies
   pip install -r requirements.txt

   # Initialize database
   python init_db.py

   # Run tests
   python -m pytest tests/ -v
   ```

3. **Start the application**:
   ```bash
   uvicorn main:app --reload
   ```

4. **Access the application**:
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Default Login Credentials
- **Email**: hr@company.com
- **Password**: hr123456

## Project Structure

```
HR Automation/
├── app/                    # Application core
│   ├── __init__.py
│   ├── api/               # API endpoints
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── submissions.py # Submission CRUD
│   │   └── users.py       # User management
│   ├── auth.py            # Authentication utilities
│   ├── crud.py            # Database operations
│   ├── database.py        # Database configuration
│   ├── models.py          # SQLAlchemy models
│   └── schemas.py         # Pydantic schemas
├── static/                # Static assets
├── templates/             # Jinja2 templates
│   ├── base.html          # Base template
│   ├── dashboard.html     # Dashboard page
│   ├── index.html         # Login page
│   └── submissions.html   # Submissions management
├── tests/                 # Test suite
│   ├── conftest.py        # Test configuration
│   ├── test_auth.py       # Authentication tests
│   ├── test_crud.py       # CRUD operations tests
│   ├── test_models.py     # Model tests
│   ├── test_submissions.py # Submission tests
│   └── test_users.py      # User tests
├── config.py              # Configuration
├── init_db.py            # Database initialization
├── main.py               # FastAPI application
├── requirements.txt      # Dependencies
├── refined_wireframes.md # Implementation guide
└── setup.py              # Setup script
```

## Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/hr_copilot

# Application
APP_BASE_URL=http://localhost:8000
SECRET_KEY=your-jwt-secret-key
SIGNING_SECRET=your-signing-secret

# Email (for Phase 2)
SMTP_HOST=smtp.qiye.aliyun.com
SMTP_PORT=465
SMTP_USER=your-email@company.com
SMTP_PASS=your-password
```

### Database Setup
1. Create PostgreSQL database: `createdb hr_copilot`
2. Update `config.py` with your database URL
3. Run initialization: `python init_db.py`

## API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/token` - OAuth2 token endpoint

### User Management
- `GET /api/users/me` - Current user info
- `GET /api/users/` - List users (HR only)
- `POST /api/users/` - Create user (HR only)
- `GET /api/users/{id}` - Get user by ID (HR only)

### Submission Management
- `GET /api/submissions/` - List submissions with filters
- `POST /api/submissions/` - Create submission
- `GET /api/submissions/{id}` - Get submission details
- `PATCH /api/submissions/{id}` - Update submission
- `DELETE /api/submissions/{id}` - Delete submission

### Health Check
- `GET /health` - Application health status

## Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
python -m pytest tests/test_auth.py -v          # Authentication tests
python -m pytest tests/test_submissions.py -v   # Submission tests
python -m pytest tests/test_models.py -v        # Model tests
```

### Test Coverage
```bash
python -m pytest tests/ --cov=app --cov-report=html
```

## Database Schema

### Users Table
- `id` - Primary key
- `email` - Unique email address
- `hashed_password` - Bcrypt hash
- `full_name` - User display name
- `role` - Enum: hr, leader, chm, it
- `is_active` - Boolean status
- `created_at`, `updated_at` - Timestamps

### Submissions Table
- Employee information (name, email, id, department, position)
- Employment details (hire_date, resignation_date, last_working_day)
- Workflow status (resignation_status, exit_interview_status)
- Approval tracking (team_leader_reply, chinese_head_reply, it_support_reply)
- Notes and timestamps
- Foreign key to users table

### Assets Table
- `submission_id` - Foreign key
- Asset items (laptop, mouse, headphones, others)
- Approval status
- Timestamps

## Development

### Code Quality
```bash
# Linting
ruff check app/ tests/

# Formatting
black app/ tests/

# Type checking
mypy app/
```

### Adding New Features
1. Update models in `app/models.py`
2. Create Pydantic schemas in `app/schemas.py`
3. Implement CRUD operations in `app/crud.py`
4. Add API endpoints in `app/api/`
5. Create corresponding tests in `tests/`
6. Update frontend templates as needed

## Security Considerations

- ✅ Password hashing with bcrypt
- ✅ JWT token authentication
- ✅ Role-based access control
- ✅ Input validation and sanitization
- ✅ SQL injection prevention via SQLAlchemy
- ⚠️ Configure HTTPS in production
- ⚠️ Set up proper CORS origins
- ⚠️ Use environment-specific secret keys

## Deployment

### Development
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Railway)
1. Set environment variables in Railway dashboard
2. Configure DATABASE_URL for PostgreSQL
3. Set SECRET_KEY and SIGNING_SECRET
4. Deploy the application
5. Run health checks: `GET /health`

## Troubleshooting

### Common Issues

**Database Connection Errors**
- Check PostgreSQL is running
- Verify DATABASE_URL in config.py
- Ensure database exists: `createdb hr_copilot`

**Import Errors**
- Activate HR_Resignation conda environment
- Install dependencies: `pip install -r requirements.txt`

**Authentication Failures**
- Check user exists and is active
- Verify password is correct
- Check JWT secret key configuration

**Test Failures**
- Ensure test database is accessible
- Check all dependencies are installed
- Verify database schema is up to date

## Contributing

1. Follow PEP 8 style guidelines
2. Write tests for new features
3. Update documentation
4. Use meaningful commit messages
5. Ensure all tests pass before submitting

## License

This project is proprietary to the organization. All rights reserved.

## Support

For technical support or questions:
- Check the troubleshooting section
- Review the API documentation at `/docs`
- Contact the development team

---

**Phase 1 Complete** ✅
- Core application infrastructure
- Authentication and authorization
- Basic CRUD operations
- Responsive web interface
- Comprehensive test coverage

Ready for Phase 2 development: Email integration and workflow automation.