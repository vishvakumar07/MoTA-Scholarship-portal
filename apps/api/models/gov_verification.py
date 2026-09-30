"""
GovernmentVerification and GovernmentVerificationAttempt models — Phase 7.

Stores provenance records for government integration operations.

SECURITY RULES:
  - Credentials are NEVER stored in these tables.
  - Full government API response payloads are NOT stored.
  - Only minimal normalized result + reference IDs are retained.
  - government_verification_status is separate from:
      * AI classification
      * OCR results
      * officer manual verification
      * application eligibility
  - Historical records are immutable (append-only logic enforced at service layer).
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


class GovVerificationStatus(str, PyEnum):
    """
    Explicit government verification states.

    PROHIBITED STATES (must never appear in this column):
      AI_VERIFIED, OCR_VERIFIED, AUTO_VERIFIED
    """
    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    VERIFIED = "verified"                        # Only set by confirmed authorized API response
    NOT_VERIFIED = "not_verified"
    REQUIRES_AUTHORIZED_ACCESS = "requires_authorized_access"
    INTEGRATION_NOT_CONFIGURED = "integration_not_configured"
    DISABLED = "disabled"
    ERROR = "error"


class GovIntegrationName(str, PyEnum):
    UIDAI = "uidai"
    DIGILOCKER = "digilocker"
    NSP = "nsp"
    DBT = "dbt"
    MOTA = "mota"


# ---------------------------------------------------------------------------
# GovernmentVerification
# ---------------------------------------------------------------------------
class GovernmentVerification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Government verification record for a single application.

    One record per (application_id, integration). Each subsequent
    attempt creates a GovernmentVerificationAttempt linked here.
    Historical records are retained -- not overwritten.

    NEVER STORE:
      - Aadhaar numbers
      - Bank account numbers
      - API keys / secrets / tokens
      - Full government API response payloads
    """

    __tablename__ = "government_verifications"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    integration: Mapped[GovIntegrationName] = mapped_column(
        SAEnum(GovIntegrationName, name="gov_integration_name_enum"),
        nullable=False,
    )
    operation: Mapped[str] = mapped_column(String(80), nullable=False)

    status: Mapped[GovVerificationStatus] = mapped_column(
        SAEnum(GovVerificationStatus, name="gov_verification_status_enum"),
        default=GovVerificationStatus.NOT_REQUESTED,
        nullable=False,
        index=True,
    )

    # True only if an authorized government API explicitly confirmed verification.
    # NULL = not attempted. False = integration ran but did not verify.
    verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Provenance -- minimal identifiers only
    external_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    request_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    adapter_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Who triggered the verification
    requested_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_timestamp: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Message from the adapter (safe -- no secrets)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Idempotency key -- prevents accidental duplicate submissions
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)

    # Attempt history
    attempts: Mapped[list["GovernmentVerificationAttempt"]] = relationship(
        "GovernmentVerificationAttempt",
        back_populates="verification",
        order_by="GovernmentVerificationAttempt.attempted_at",
    )

    def __repr__(self) -> str:
        return (
            f"<GovernmentVerification {self.integration.value} "
            f"application={self.application_id} status={self.status.value}>"
        )


# ---------------------------------------------------------------------------
# GovernmentVerificationAttempt
# ---------------------------------------------------------------------------
class GovernmentVerificationAttempt(Base, UUIDPrimaryKeyMixin):
    """
    Immutable record of each attempt to run a government integration.

    Retains the result status and reference metadata of every attempt.
    Historical records must not be updated -- only new attempts appended.

    NEVER STORE:
      - API keys / secrets / tokens
      - Aadhaar numbers
      - Bank account numbers
      - Full government API response payloads
    """

    __tablename__ = "government_verification_attempts"

    verification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("government_verifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    operation: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False)
    verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    external_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    request_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    adapter_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    attempted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    verification: Mapped["GovernmentVerification"] = relationship(
        "GovernmentVerification",
        back_populates="attempts",
    )
