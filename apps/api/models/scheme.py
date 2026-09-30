"""
Scheme, SchemeVersion, SchemeRule, SchemeDocument,
SchemeFormField, SchemeWorkflow, SchemeSelectionCriteria, SchemeNotificationTemplate models.

Design principles:
  - Every scheme version is immutable once published
  - Applications are locked to the scheme_version at submission time
  - Rules are stored with source metadata (URL, document, section, page)
  - Deterministic eligibility rule evaluation with full citation traceability
  - No eligibility rules are invented  -  unverified rules marked OFFICIAL SOURCE REQUIRED
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SchemeType(str, PyEnum):
    """Official MoTA scheme classification."""
    CENTRALLY_SPONSORED = "centrally_sponsored"   # CSS: shared Central+State funding
    CENTRAL_SECTOR = "central_sector"              # 100% Central Government funded


class SchemeStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class SchemeVersionStatus(str, PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class RuleType(str, PyEnum):
    """Types of eligibility/selection rules."""
    INCOME_CEILING = "income_ceiling"
    CLASS_LEVEL = "class_level"
    COURSE_LEVEL = "course_level"
    INSTITUTE_LIST = "institute_list"
    SEAT_COUNT = "seat_count"
    SCHOLARSHIP_AMOUNT = "scholarship_amount"
    PRIORITY_PREFERENCE = "priority_preference"
    RESIDENCY = "residency"
    CASTE_CATEGORY = "caste_category"
    AGE_LIMIT = "age_limit"
    DOCUMENT_REQUIREMENT = "document_requirement"
    CUSTOM = "custom"


class RuleSeverity(str, PyEnum):
    HARD_STOP = "HARD_STOP"
    WARNING = "WARNING"
    INFO = "INFO"


class WorkflowTransitionType(str, PyEnum):
    AUTOMATIC = "automatic"    # Triggered by system event
    MANUAL = "manual"          # Requires officer action


# -------------------------------------------------------------------
# Scheme Master
# -------------------------------------------------------------------
class Scheme(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Master scheme record.
    Actual rules are in SchemeVersion (versioned).
    """

    __tablename__ = "schemes"

    # Official identifiers
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    short_name: Mapped[str] = mapped_column(String(80), nullable=False)
    scheme_type: Mapped[SchemeType] = mapped_column(
        SAEnum(SchemeType, name="scheme_type_enum"), nullable=False
    )
    status: Mapped[SchemeStatus] = mapped_column(
        SAEnum(SchemeStatus, name="scheme_status_enum"), default=SchemeStatus.ACTIVE, nullable=False
    )

    # Soft deletion
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Official source
    official_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    portal_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ministry: Mapped[str] = mapped_column(String(200), default="Ministry of Tribal Affairs", nullable=False)

    # Description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sort order for display
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    versions: Mapped[list["SchemeVersion"]] = relationship("SchemeVersion", back_populates="scheme", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Scheme {self.code}>"


# -------------------------------------------------------------------
# SchemeVersion
# -------------------------------------------------------------------
class SchemeVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A specific version of a scheme's rules.

    Immutable once published. Applications are locked to a version at submission.
    When MoTA publishes new guidelines, a new SchemeVersion is created.
    """

    __tablename__ = "scheme_versions"

    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[str] = mapped_column(String(20), nullable=False)
    academic_year: Mapped[str | None] = mapped_column(String(10), nullable=True)  # e.g. "2024-25"

    version_status: Mapped[SchemeVersionStatus] = mapped_column(
        SAEnum(SchemeVersionStatus, name="scheme_version_status_enum"),
        default=SchemeVersionStatus.DRAFT,
        nullable=False,
        index=True,
    )

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)  # NULL = currently active

    # Application Window
    application_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    application_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_accepting_applications: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Soft deletion
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Source references for this version
    source_document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_document_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    source_retrieved_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Version metadata (JSON: change summary, notes)
    version_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("scheme_id", "version_number", name="uq_scheme_version"),
    )

    # Relationships
    scheme: Mapped["Scheme"] = relationship("Scheme", back_populates="versions")
    rules: Mapped[list["SchemeRule"]] = relationship("SchemeRule", back_populates="version", cascade="all, delete-orphan")
    documents: Mapped[list["SchemeDocument"]] = relationship("SchemeDocument", back_populates="version", cascade="all, delete-orphan")
    form_fields: Mapped[list["SchemeFormField"]] = relationship("SchemeFormField", back_populates="version", cascade="all, delete-orphan")
    workflows: Mapped[list["SchemeWorkflow"]] = relationship("SchemeWorkflow", back_populates="version", cascade="all, delete-orphan")
    selection_criteria: Mapped[list["SchemeSelectionCriteria"]] = relationship("SchemeSelectionCriteria", back_populates="version", cascade="all, delete-orphan")
    notification_templates: Mapped[list["SchemeNotificationTemplate"]] = relationship("SchemeNotificationTemplate", back_populates="version", cascade="all, delete-orphan")


# -------------------------------------------------------------------
# SchemeRule
# -------------------------------------------------------------------
class SchemeRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A single eligibility or selection rule for a scheme version.

    MANDATORY: Every rule must cite an official source.
    Rules without an official source are marked with:
      is_official_source_confirmed = False
      explanation / expected_value = "OFFICIAL SOURCE REQUIRED"
    """

    __tablename__ = "scheme_rules"

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheme_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    rule_type: Mapped[RuleType] = mapped_column(
        SAEnum(RuleType, name="rule_type_enum"), nullable=False
    )
    rule_key: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_value: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Deterministic Rule Engine fields
    field: Mapped[str] = mapped_column(String(120), nullable=False, default="applicant.general")
    operator: Mapped[str] = mapped_column(String(30), nullable=False, default="eq")  # lte, gte, eq, ne, in, contains, regex
    expected_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)  # INR, %, Years
    severity: Mapped[RuleSeverity] = mapped_column(
        SAEnum(RuleSeverity, name="rule_severity_enum"), default=RuleSeverity.HARD_STOP, nullable=False
    )
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    display_label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Source traceability  -  REQUIRED for every rule
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_document_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True
    )
    source_section: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_page_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # guideline, faq, amendment, notice
    source_publication_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_retrieved_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_official_source_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Effective dates
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Soft deletion
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Version metadata
    version: Mapped["SchemeVersion"] = relationship("SchemeVersion", back_populates="rules")

    @property
    def rule_id(self) -> uuid.UUID:
        return self.id

    @property
    def scheme_version_id(self) -> uuid.UUID:
        return self.version_id

    def __repr__(self) -> str:
        return f"<SchemeRule {self.rule_key}={self.field} {self.operator} {self.expected_value}>"


# -------------------------------------------------------------------
# SchemeDocument
# -------------------------------------------------------------------
class SchemeDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Required documents for an application under this scheme version."""

    __tablename__ = "scheme_documents"

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheme_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    document_type_code: Mapped[str] = mapped_column(String(80), nullable=False)
    document_display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    accepted_formats: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["pdf", "jpg", "png"]
    max_size_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Source
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_retrieved_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Soft deletion
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    version: Mapped["SchemeVersion"] = relationship("SchemeVersion", back_populates="documents")


# -------------------------------------------------------------------
# SchemeFormField
# -------------------------------------------------------------------
class SchemeFormField(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Dynamic application form fields for a scheme version."""

    __tablename__ = "scheme_form_fields"

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheme_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    field_label: Mapped[str] = mapped_column(String(200), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)  # text, textarea, number, date, select, radio, checkbox, boolean, file, email, phone
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    validation_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    options: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # For select/radio fields
    conditional_logic: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # { "depends_on": "caste", "operator": "eq", "value": "ST" }
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Soft deletion
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("version_id", "field_key", name="uq_form_field_version_key"),
    )

    version: Mapped["SchemeVersion"] = relationship("SchemeVersion", back_populates="form_fields")

    @property
    def label(self) -> str:
        return self.field_label

    @property
    def type(self) -> str:
        return self.field_type

    @property
    def required(self) -> bool:
        return self.is_required

    @property
    def validation(self) -> dict | None:
        return self.validation_rules

    @property
    def order(self) -> int:
        return self.display_order


# -------------------------------------------------------------------
# SchemeWorkflow
# -------------------------------------------------------------------
class SchemeWorkflow(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Configurable state machine transitions per scheme version.
    All states/transitions are data-driven  -  never hardcoded in business logic.
    """

    __tablename__ = "scheme_workflows"

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheme_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    from_state: Mapped[str] = mapped_column(String(60), nullable=False)
    to_state: Mapped[str] = mapped_column(String(60), nullable=False)
    transition_type: Mapped[WorkflowTransitionType] = mapped_column(
        SAEnum(WorkflowTransitionType, name="workflow_transition_type_enum"), nullable=False
    )
    required_role: Mapped[str | None] = mapped_column(String(60), nullable=True)
    conditions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft deletion
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("version_id", "from_state", "to_state", name="uq_workflow_transition"),
    )

    version: Mapped["SchemeVersion"] = relationship("SchemeVersion", back_populates="workflows")


# -------------------------------------------------------------------
# SchemeSelectionCriteria
# -------------------------------------------------------------------
class SchemeSelectionCriteria(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Selection methodology and criteria for a scheme version."""

    __tablename__ = "scheme_selection_criteria"

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheme_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    criteria_key: Mapped[str] = mapped_column(String(100), nullable=False)
    criteria_type: Mapped[str] = mapped_column(String(60), nullable=False)
    criteria_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    weight: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Source
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_retrieved_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_official_source_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Soft deletion
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    version: Mapped["SchemeVersion"] = relationship("SchemeVersion", back_populates="selection_criteria")


# -------------------------------------------------------------------
# SchemeNotificationTemplate
# -------------------------------------------------------------------
class SchemeNotificationTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Configurable notification templates per scheme version."""

    __tablename__ = "scheme_notification_templates"

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheme_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    event_trigger: Mapped[str] = mapped_column(String(80), nullable=False)  # APPLICATION_SUBMITTED, DEFICIENCY_RAISED, etc.
    channel: Mapped[str] = mapped_column(String(30), nullable=False, default="IN_APP")  # IN_APP, EMAIL, SMS
    subject_template: Mapped[str] = mapped_column(String(300), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Soft deletion
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    version: Mapped["SchemeVersion"] = relationship("SchemeVersion", back_populates="notification_templates")
