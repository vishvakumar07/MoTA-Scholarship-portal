"""
Application, ApplicationAnswer, ApplicationStatusHistory models.

An application represents a single applicant's submission under a specific
scheme version. It is locked to the scheme_version at submission time.
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


class ApplicationStatus(str, PyEnum):
    """
    Official application states. All transitions are configurable
    via scheme_workflows table  -  NOT hardcoded in business logic.
    """
    DRAFT = "draft"
    SUBMITTED = "submitted"
    DOCUMENT_PROCESSING = "document_processing"
    DOCUMENT_VERIFICATION = "document_verification"
    DEFICIENCY = "deficiency"
    RESUBMITTED = "resubmitted"
    ELIGIBILITY_REVIEW = "eligibility_review"
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    SCRUTINY = "scrutiny"
    SHORTLISTED = "shortlisted"
    SELECTION_REVIEW = "selection_review"
    SELECTED = "selected"
    NOT_SELECTED = "not_selected"
    POST_SELECTION = "post_selection"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"


#  -  - - Application  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class Application(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A scholarship/fellowship application.

    Locked to scheme_version_id at submission  -  scheme rule changes
    after submission do not retroactively affect this application.
    """

    __tablename__ = "applications"

    # Applicant
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Scheme version  -  LOCKED at submission
    scheme_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheme_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Application reference number (human-readable, generated on submission)
    reference_number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True, index=True)

    # Status
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, name="application_status_enum"),
        default=ApplicationStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Timestamps
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Assigned officer
    assigned_officer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Demo flag  -  TEST applications are clearly separated
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Internal notes (officer use only)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    answers: Mapped[list["ApplicationAnswer"]] = relationship("ApplicationAnswer", back_populates="application")
    status_history: Mapped[list["ApplicationStatusHistory"]] = relationship(
        "ApplicationStatusHistory", back_populates="application"
    )

    def __repr__(self) -> str:
        return f"<Application {self.reference_number or self.id} status={self.status}>"




#  -  - - ApplicationAnswer  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class ApplicationAnswer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Answers to dynamic scheme form fields."""

    __tablename__ = "application_answers"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    form_field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheme_form_fields.id", ondelete="RESTRICT"), nullable=False
    )
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    answer_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="answers")


#  -  - - ApplicationStatusHistory  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class ApplicationStatusHistory(Base, UUIDPrimaryKeyMixin):
    """
    Immutable audit trail of every status change.

    This table is append-only. Records are never updated or deleted.
    A database-level trigger enforces immutability.
    """

    __tablename__ = "application_status_history"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(60), nullable=True)
    to_status: Mapped[str] = mapped_column(String(60), nullable=False)
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="status_history")
