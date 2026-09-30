"""
MoTA AI-Enabled Scholarship and Fellowship Management System
Main FastAPI Application Entrypoint.

Ministry of Tribal Affairs (MoTA), Government of India.
Smart India Hackathon Prototype.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import uuid

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import check_db_connection
from ai import get_ai_service
from routers import (
    auth_router,
    schemes_router,
    admin_schemes_router,
    applicant_router,
    applications_router,
    documents_router,
    notifications_router,
    processing_router,
    analytics_router,
    integrations_router,
    cases_router,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mota_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown routines."""
    logger.info("Initializing MoTA Scholarship Management System API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Storage Provider: {settings.STORAGE_PROVIDER}")
    logger.info(f"AI Configured: {'Yes' if settings.GOOGLE_AI_API_KEY else 'No (Mock Mode)'}")
    yield
    logger.info("Shutting down MoTA API...")


app = FastAPI(
    title="MoTA Scholarship & Fellowship Management System API",
    description=(
        "Official AI-Enabled Digital Platform for Scholarship and Fellowship Schemes, "
        "Ministry of Tribal Affairs (MoTA), Government of India. "
        "Developed for Smart India Hackathon."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Correlation & Security Headers Middleware (Phase 8 Hardening)
@app.middleware("http")
async def request_correlation_and_security_headers_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response



# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[Req {req_id}] Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred. Please try again later.",
                "request_id": req_id,
            }
        },
        headers={"X-Request-ID": req_id} if req_id != "unknown" else {},
    )


# Health & System Endpoints
@app.get("/health", tags=["System"])
def health_check():
    """System health check endpoint."""
    db_ok = check_db_connection()
    ai_service = get_ai_service()

    return {
        "status": "healthy" if db_ok else "degraded",
        "ministry": "Ministry of Tribal Affairs (MoTA)",
        "environment": settings.ENVIRONMENT,
        "database": db_ok,
        "ai_active": ai_service.is_available,
        "ai_status": ai_service.status_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["System"])
def readiness_check(response: Response):
    """Container readiness probe."""
    db_ok = check_db_connection()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": False}
    return {"status": "ready", "database": True}


@app.get("/", tags=["System"])
def root_info():
    """Root info endpoint providing system summary and official references."""
    return {
        "system": "MoTA AI-Enabled Scholarship and Fellowship Management System",
        "version": "2.0.0",
        "context": "Smart India Hackathon Prototype",
        "official_source": "https://tribal.nic.in/ScholarshiP.aspx",
        "dbt_portal": "https://dbttribal.gov.in/",
        "api_docs": "/docs",
    }


# Phase 1-2: Auth & Schemes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(schemes_router, prefix="/api/v1")
app.include_router(admin_schemes_router, prefix="/api/v1")

# Phase 4: Applicant Portal
app.include_router(applicant_router, prefix="/api/v1")
app.include_router(applications_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(processing_router, prefix="/api/v1")

# Phase 6: Analytics & Dashboards
app.include_router(analytics_router, prefix="/api/v1")

# Phase 7: Government Integration Framework
app.include_router(integrations_router, prefix="/api/v1")

# Phase 9: Case Management & Operations
app.include_router(cases_router, prefix="/api/v1")






