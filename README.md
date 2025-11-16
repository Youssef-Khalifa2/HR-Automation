# HR Automation System

Complete HR resignation workflow automation system with approval chains, exit interviews, asset tracking, and vendor notifications.

## Features

### Core Functionality
- ✅ **Resignation Submission** - Employee self-service resignation forms
- ✅ **Multi-level Approvals** - Leader → CHM → HR approval chain
- ✅ **Exit Interviews** - Automated scheduling and feedback collection
- ✅ **Asset Tracking** - Company asset return monitoring
- ✅ **Vendor Integration** - Automated notifications to HR service vendors (Migrate Business, Just HR)
- ✅ **Email Notifications** - SendGrid/SMTP email delivery with tracking
- ✅ **Automated Reminders** - Smart reminder system for pending actions
- ✅ **Team Mapping** - Department-to-leader mapping configuration
- ✅ **Admin Dashboard** - Centralized configuration management

### Technical Features
- **Authentication** - JWT-based user authentication
- **Role Management** - Simplified authentication (admin/hr unified)
- **Email CC Support** - Multiple HR recipients with CC functionality
- **Configurable Settings** - All settings manageable from admin interface
- **Email Tracking** - Full email delivery tracking and logging
- **Responsive UI** - Modern React-based interface
- **Database-driven Config** - Dynamic configuration without code changes

## Tech Stack

### Backend
- **Python 3.11+** with FastAPI
- **PostgreSQL** database
- **SQLAlchemy** ORM
- **SendGrid/SMTP** for email delivery
- **JWT** authentication

### Frontend
- **React 18** with TypeScript
- **Vite** build tool
- **TanStack Query** for state management
- **Tailwind CSS** for styling
- **React Router** for navigation

## Quick Start

### Local Development

1. **Clone repository**
```bash
git clone <your-repo-url>
cd "HR Automation"
```

2. **Set up backend**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Run migrations and start server
uvicorn main:app --reload
```

3. **Set up frontend**
```bash
cd frontend
npm install
npm run dev
```

4. **Access application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete deployment instructions including:
- Railway deployment (recommended)
- Docker containerization
- Database migration
- Environment variables
- Production setup

## Database Migration

Migrate from local to production database:

```bash
python migrate_database.py \
  --source "postgresql://user:pass@localhost:5432/local_db" \
  --target "postgresql://user:pass@prod-host:5432/prod_db"
```

## Configuration

All configuration is managed through the admin interface at `/admin`:

- **Email Settings** - SendGrid/SMTP configuration
- **Email Recipients** - HR, IT, and CC recipients
- **Team Mappings** - Department to leader assignments
- **Vendor Emails** - Migrate Business and Just HR contacts
- **System Settings** - Application URLs and reminder configuration

## Project Structure

```
HR Automation/
├── app/                    # Backend application
│   ├── api/               # API endpoints
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   ├── templates/         # Email templates
│   └── core/              # Core utilities
├── frontend/              # React frontend
│   └── src/
│       ├── components/    # UI components
│       ├── pages/         # Page components
│       └── hooks/         # React hooks
├── Assets/                # Static assets
├── Dockerfile             # Backend container
├── docker-compose.yml     # Local development
├── railway.toml           # Railway configuration
├── migrate_database.py    # Database migration tool
└── requirements.txt       # Python dependencies
```

## Environment Variables

Required environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Security
SECRET_KEY=<random-secret-key>
SIGNING_SECRET=<random-signing-secret>

# Application
APP_BASE_URL=https://your-api-url.com
FRONTEND_URL=https://your-frontend-url.com

# Email
EMAIL_PROVIDER=sendgrid  # or smtp
SENDGRID_API_KEY=<your-key>
HR_EMAIL=hr@company.com
HR_EMAIL_CC=manager@company.com,supervisor@company.com
IT_EMAIL=it@company.com
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete list.

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Security

- JWT-based authentication
- Password hashing with bcrypt
- Environment-based secrets
- HTTPS enforcement in production
- SQL injection protection via ORM
- XSS protection in frontend

## License

Proprietary - All rights reserved

## Support

For deployment issues, see [DEPLOYMENT.md](DEPLOYMENT.md)
