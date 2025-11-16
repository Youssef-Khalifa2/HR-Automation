"""HR Co-Pilot FastAPI Application"""
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import time
import logging
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.api import auth, submissions, users, public, approvals, mapping, forms, assets, reminders, email_monitoring, admin
from app.schemas_all import *  # Import all schemas from consolidated file
# Import all models to ensure they are registered with SQLAlchemy
from app.models import user, submission, asset, exit_interview, config
from app.core.security import ApprovalTokenService
from app.services.email import create_email_service
from config import SIGNING_SECRET

# Configure logging with UTF-8 encoding
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

file_handler = logging.FileHandler('hr_copilot.log', mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)

# Get logger for this module
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    startup_start = time.time()
    print("[STARTUP] Starting HR Co-Pilot...")
    print(f"[STARTUP] Database engine initialized: {engine.url}")

    # Initialize services
    global approval_token_service, email_service

    # Initialize approval token service
    token_start = time.time()
    try:
        approval_token_service = ApprovalTokenService(SIGNING_SECRET)
        token_time = time.time() - token_start
        print(f"[STARTUP] [OK] Approval token service initialized in {token_time:.3f}s")
    except Exception as e:
        print(f"[STARTUP] [ERROR] Failed to initialize approval token service: {e}")
        raise

    # Initialize email service
    email_start = time.time()
    try:
        print("[STARTUP] Initializing email service...")
        email_service = create_email_service()
        email_time = time.time() - email_start
        print(f"[STARTUP] [OK] Email service initialized in {email_time:.3f}s")
    except Exception as e:
        email_time = time.time() - email_start
        print(f"[STARTUP] [ERROR] Email service initialization failed after {email_time:.3f}s: {e}")
        print("[STARTUP] Email functionality will be limited until properly configured")
        import traceback
        traceback.print_exc()

    startup_total = time.time() - startup_start
    print(f"[STARTUP] [OK] HR Co-Pilot startup complete in {startup_total:.3f}s")
    print("[STARTUP] Server ready to handle requests")

    yield

    # Shutdown
    print("[SHUTDOWN] Shutting down HR Co-Pilot...")
    if email_service:
        try:
            await email_service.close()
            print("[SHUTDOWN] Email service closed")
        except Exception as e:
            print(f"[SHUTDOWN] Error closing email service: {e}")
    print("[SHUTDOWN] Shutdown complete")


# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="HR Co-Pilot",
    description="HR offboarding automation platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend dev server
        "http://localhost:3000",  # Alternative frontend port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(submissions.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(assets.router)  # Asset management routes
app.include_router(public.router)  # Public routes (no auth required)
app.include_router(approvals.router)  # Approval workflow routes
app.include_router(mapping.router)  # Leader mapping routes
app.include_router(forms.router)  # Tokenized email forms routes
app.include_router(reminders.router)  # Reminder automation routes
app.include_router(email_monitoring.router, prefix="/api/email-monitoring", tags=["Email Monitoring"])  # Email delivery tracking
app.include_router(admin.router)  # Admin configuration routes (requires admin auth)


# React SPA routes - commented out old Jinja2 template routes
# @app.get("/")
# def home(request: Request):
#     """Home page - redirect to login or dashboard"""
#     return templates.TemplateResponse("index.html", {"request": request, "show_sidebar": False})


# @app.get("/dashboard")
# def dashboard(request: Request):
#     """Dashboard page for authenticated users"""
#     return templates.TemplateResponse("dashboard.html", {
#         "request": request,
#         "show_sidebar": True,
#         "current_user": {"full_name": "HR User"}  # Placeholder, will be replaced with actual user auth
#     })


# @app.get("/submissions")
# def submissions(request: Request):
#     """Submissions page for managing resignation requests"""
#     return templates.TemplateResponse("submissions.html", {
#         "request": request,
#         "show_sidebar": True,
#         "current_user": {"full_name": "HR User"}  # Placeholder, will be replaced with actual user auth
#     })


# @app.get("/exit-interviews")
# def exit_interviews(request: Request):
#     """Exit interview management dashboard"""
#     return templates.TemplateResponse("exit_interviews.html", {
#         "request": request,
#         "show_sidebar": True,
#         "current_user": {"full_name": "HR User"}  # Placeholder, will be replaced with actual user auth
#     })


# Serve React SPA
# Note: Build frontend first with: cd frontend && npm run build
# Then copy frontend/dist to a location accessible by FastAPI
# For development, use Vite dev server on port 5173
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve React SPA for all non-API routes"""
    # Skip API routes, health checks, and approval/form routes
    if (full_path.startswith("api/") or
        full_path.startswith("approve/") or
        full_path.startswith("health") or
        full_path.startswith("static/") or
        full_path.startswith("debug")):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")

    # In production, serve from frontend/dist
    # For now, return a message to use Vite dev server
    return {
        "message": "React SPA is served via Vite dev server during development",
        "dev_server": "http://localhost:5173",
        "note": "In production, serve from frontend/dist"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "HR Co-Pilot is running"}


@app.get("/health/email")
def email_health_check():
    """Email service health check endpoint"""
    try:
        from app.services.email import get_email_service

        email_service = get_email_service()

        # Check if email service is initialized
        if email_service is None:
            return {
                "status": "unhealthy",
                "email_service": "not_initialized",
                "message": "Email service failed to initialize"
            }

        # Check SMTP configuration
        return {
            "status": "healthy",
            "email_service": "initialized",
            "smtp_host": email_service.config.host,
            "smtp_port": email_service.config.port,
            "smtp_user": email_service.config.username,
            "from_email": email_service.config.from_email,
            "message": "Email service is properly configured"
        }

    except Exception as e:
        logger.error(f"Email health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "email_service": "error",
            "error": str(e),
            "message": "Email service configuration error"
        }


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools_config():
    """Chrome DevTools configuration endpoint"""
    json_file_path = os.path.join("static", ".well-known", "appspecific", "com.chrome.devtools.json")

    if os.path.exists(json_file_path):
        with open(json_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return JSONResponse(content=content, media_type="application/json")
    else:
        # Fallback response if file doesn't exist
        return JSONResponse(
            content={
                "protocol-version": "1.1",
                "allowed-origins": ["*"],
                "description": "HR Co-Pilot Development Server - Chrome DevTools Integration"
            },
            media_type="application/json"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)