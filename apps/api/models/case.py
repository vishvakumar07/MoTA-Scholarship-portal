"""
Case Management & Operational Workflow Models - Phase 9.

Models:
- CaseNote: Officer-only internal notes and observations on an application.
- CaseAssignment: Historical and active officer case assignments with operational priority.
- CaseTimelineEvent: Unified operational timeline events tracking the application lifecycle.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CasePriority(str, PyEnum):
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class CaseAssignmentStatus(str, PyEnum):
    ASSIGNED = "assigned"
    REASSIGNED = "reassigned"
    UNASSIGNED = "unassigned"
    COMPLETED = "completed"


class TimelineEventType(str, PyEnum):
    APPLICATION_CREATED = "APPLICATION_CREATED"
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_PROCESSING_STARTED = "DOCUMENT_PROCESSING_STARTED"
    DOCUMENT_PROCESSING_COMPLETED = "DOCUMENT_PROCESSING_COMPLETED"
    DOCUMENT_REVIEW_STARTED = "DOCUMENT_REVIEW_STARTED"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED"
    DOCUMENT_REJECTED = "DOCUMENT_REJECTED"
    DEFICIENCY_RAISED = "DEFICIENCY_RAISED"
    DEFICIENCY_RESPONDED = "DEFICIENCY_RESPONDED"
    DEFICIENCY_RESOLVED = "DEFICIENCY_RESOLVED"
    APPLICATION_RESUBMITTED = "APPLICATION_RESUBMITTED"
    OFFICER_ASSIGNED = "OFFICER_ASSIGNED"
    OFFICER_REASSIGNED = "OFFICER_REASSIGNED"
    CASE_NOTE_ADDED = "CASE_NOTE_ADDED"
    ELIGIBILITY_EVALUATED = "ELIGIBILITY_EVALUATED"
    GOVERNMENT_VERIFICATION_REQUESTED = "GOVERNMENT_VERIFICATION_REQUESTED"
    GOVERNMENT_VERIFICATION_UPDATED = "GOVERNMENT_VERIFICATION_UPDATED"
    SELECTION_DECISION_RECORDED = "SELECTION_DECISION_RECORDED"
    APPLICATION_STATUS_CHANGED = "APPLICATION_STATUS_CHANGED"


# ---------------------------------------------------------------------------
# CaseNote
# ---------------------------------------------------------------------------
class CaseNote(Base, UUIDPrimaryKeyMixin):
    """
    Officer-only case note.
    Internal observations, scrutiny remarks, and administrative annotations.
    Hidden from applicant view.
    """

    __tablename__ = "case_notes"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


# ---------------------------------------------------------------------------
# CaseAssignment
# ---------------------------------------------------------------------------
class CaseAssignment(Base, UUIDPrimaryKeyMixin):
    """
    Officer case assignment and operational priority tracking.
    """

    __tablename__ = "case_assignments"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_to_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assigned_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    status: Mapped[CaseAssignmentStatus] = mapped_column(
        SAEnum(CaseAssignmentStatus, name="case_assignment_status_enum"),
        default=CaseAssignmentStatus.ASSIGNED,
        nullable=False,
        index=True,
    )
    priority: Mapped[CasePriority] = mapped_column(
        SAEnum(CasePriority, name="case_priority_enum"),
        default=CasePriority.NORMAL,
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


# ---------------------------------------------------------------------------
# CaseTimelineEvent
# ---------------------------------------------------------------------------
class CaseTimelineEvent(Base, UUIDPrimaryKeyMixin):
    """
    Unified operational timeline tracking user-facing and officer-level events.
    """

    __tablename__ = "case_timeline_events"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    actor_type: Mapped[str] = mapped_column(String(40), default="system", nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Privacy / security boundary
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    event_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
