"""
Workflow models: EligibilityResult, Deficiency, SelectionResult.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EligibilityDecision(str, PyEnum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    PENDING_DOCUMENTS = "pending_documents"
    PENDING_REVIEW = "pending_review"


class DeficiencyStatus(str, PyEnum):
    OPEN = "open"
    RESPONDED = "responded"
    CLOSED = "closed"
    EXPIRED = "expired"


class SelectionDecision(str, PyEnum):
    SELECTED = "selected"
    NOT_SELECTED = "not_selected"
    WAITLISTED = "waitlisted"


# -------------------------------------------------------------------
# EligibilityResult
# -------------------------------------------------------------------
class EligibilityResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Rule engine eligibility assessment result.

    The deterministic rule engine, NOT the AI, produces this result.
    The rule engine output is checked by an officer before a final decision.
    Full explainability per rule version evaluated is stored in rule_results.
    """

    __tablename__ = "eligibility_results"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    scheme_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheme_versions.id", ondelete="RESTRICT"), nullable=False
    )

    decision: Mapped[EligibilityDecision] = mapped_column(
        SAEnum(EligibilityDecision, name="eligibility_decision_enum"), nullable=False
    )
    
    # Detailed rule-by-rule evaluation results array storing rule_id, field, operator, expected_value, actual_value, result (PASS/FAIL), severity, explanation, citation
    rule_results: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
    failure_reasons: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    assessed_by_rule_engine_version: Mapped[str | None] = mapped_column(String(50), nullable=True, default="1.0.0-deterministic")
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Officer override  -  AI cannot set this
    officer_confirmed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    officer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    officer_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# -------------------------------------------------------------------
# Deficiency
# -------------------------------------------------------------------
class Deficiency(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Deficiency raised by an officer for missing/inadequate documents.
    Applicant must respond before the deadline.
    """

    __tablename__ = "deficiencies"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raised_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)
    document_type_requested: Mapped[str | None] = mapped_column(String(80), nullable=True)

    status: Mapped[DeficiencyStatus] = mapped_column(
        SAEnum(DeficiencyStatus, name="deficiency_status_enum"),
        default=DeficiencyStatus.OPEN,
        nullable=False,
    )

    response_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    applicant_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# -------------------------------------------------------------------
# SelectionResult
# -------------------------------------------------------------------
class SelectionResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Final selection decision for an application.
    Only a selection_committee or higher role can set this.
    """

    __tablename__ = "selection_results"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    decided_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    decision: Mapped[SelectionDecision] = mapped_column(
        SAEnum(SelectionDecision, name="selection_decision_enum"), nullable=False
    )
    merit_rank: Mapped[int | None] = mapped_column(Numeric(10, 0), nullable=True)
    award_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
