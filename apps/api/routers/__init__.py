"""Routers package exports."""

from routers.auth import router as auth_router
from routers.schemes import router as schemes_router
from routers.admin_schemes import router as admin_schemes_router
from routers.applicant import router as applicant_router
from routers.applications import router as applications_router
from routers.documents import router as documents_router
from routers.notifications import router as notifications_router
from routers.processing import router as processing_router
from routers.analytics import router as analytics_router
from routers.integrations import router as integrations_router

__all__ = [
    "auth_router",
    "schemes_router",
    "admin_schemes_router",
    "applicant_router",
    "applications_router",
    "documents_router",
    "notifications_router",
    "processing_router",
    "analytics_router",
    "integrations_router",
]

from routers.cases import router as cases_router
