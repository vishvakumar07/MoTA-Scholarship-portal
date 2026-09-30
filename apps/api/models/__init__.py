"""
Models package -- exports all ORM models for Alembic autodiscovery.
"""

from models.base import Base
from models.user import User, Role, Permission, RolePermission, UserRole, RefreshToken
from models.applicant import ApplicantProfile, ApplicantEducation
from models.scheme import (
    Scheme,
    SchemeVersion,
    SchemeRule,
    SchemeDocument,
    SchemeFormField,
    SchemeWorkflow,
    SchemeSelectionCriteria,
)
from models.application import Application, ApplicationAnswer, ApplicationStatusHistory
from models.document import Document, DocumentExtractedFields, DocumentVerificationResult
from models.workflow import EligibilityResult, Deficiency, SelectionResult
from models.system import (
    Notification,
    AuditLog,
    KnowledgeDocument,
    KnowledgeChunk,
    AIAnalysisResult,
)
from models.gov_verification import GovernmentVerification, GovernmentVerificationAttempt

__all__ = [
    "Base",
    # Auth
    "User", "Role", "Permission", "RolePermission", "UserRole", "RefreshToken",
    # Applicant
    "ApplicantProfile", "ApplicantEducation",
    # Scheme
    "Scheme", "SchemeVersion", "SchemeRule", "SchemeDocument",
    "SchemeFormField", "SchemeWorkflow", "SchemeSelectionCriteria",
    # Application
    "Application", "ApplicationAnswer", "ApplicationStatusHistory",
    # Document
    "Document", "DocumentExtractedFields", "DocumentVerificationResult",
    # Workflow
    "EligibilityResult", "Deficiency", "SelectionResult",
    # System
    "Notification", "AuditLog", "KnowledgeDocument", "KnowledgeChunk", "AIAnalysisResult",
    # Phase 7: Government Verification
    "GovernmentVerification", "GovernmentVerificationAttempt",
]

from models.case import (
    CaseNote,
    CaseAssignment,
    CaseTimelineEvent,
    CasePriority,
    CaseAssignmentStatus,
    TimelineEventType,
)
