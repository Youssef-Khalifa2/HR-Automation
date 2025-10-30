"""HR Co-Pilot FastAPI Application"""
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.api import auth, submissions, users, public, approvals
from app.schemas_all import *  # Import all schemas from consolidated file
from app.core.security import ApprovalTokenService
from app.services.email import create_email_service
from config import SIGNING_SECRET


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting HR Co-Pilot...")

    # Initialize services
    global approval_token_service, email_service

    # Initialize approval token service
    try:
        approval_token_service = ApprovalTokenService(SIGNING_SECRET)
        print("✅ Approval token service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize approval token service: {e}")
        raise

    # Initialize email service
    try:
        email_service = create_email_service()
        print("Email service initialized")
    except Exception as e:
        print(f"Email service initialization failed: {e}")
        print("Email functionality will be limited until properly configured")

    print("HR Co-Pilot startup complete")

    yield

    # Shutdown
    print("Shutting down HR Co-Pilot...")
    if email_service:
        await email_service.close()
    print("Shutdown complete")


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
    allow_origins=["*"],  # Configure appropriately for production
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
app.include_router(public.router)  # Public routes (no auth required)
app.include_router(approvals.router)  # Approval workflow routes


@app.get("/")
def home(request: Request):
    """Home page - redirect to login or dashboard"""
    return templates.TemplateResponse("index.html", {"request": request, "show_sidebar": False})


@app.get("/dashboard")
def dashboard(request: Request):
    """Dashboard page for authenticated users"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "show_sidebar": True,
        "current_user": {"full_name": "HR User"}  # Placeholder, will be replaced with actual user auth
    })


@app.get("/submissions")
def submissions(request: Request):
    """Submissions page for managing resignation requests"""
    return templates.TemplateResponse("submissions.html", {
        "request": request,
        "show_sidebar": True,
        "current_user": {"full_name": "HR User"}  # Placeholder, will be replaced with actual user auth
    })


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "HR Co-Pilot is running"}


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