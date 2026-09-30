"""
Document, DocumentExtractedFields, DocumentVerificationResult models.

Uploaded applicant documents:
- File content stored via StorageService (local filesystem or S3)
- DB record stores the storage key, not the file content
- Access via signed URL (15-min TTL) through /api/v1/files/access-url/{doc_id}
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum, Boolean

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentStatus(str, PyEnum):
    UPLOADED = "uploaded"
    SCANNING = "scanning"           # ClamAV in progress
    SCAN_FAILED = "scan_failed"     # Malware detected
    PROCESSING = "processing"       # OCR/AI pipeline running
    PROCESSED = "processed"         # AI pipeline complete
    VERIFIED = "verified"           # Officer verified
    REJECTED = "rejected"
    SUPERSEDED = "superseded"       # Replaced by a newer upload


class MalwareScanStatus(str, PyEnum):
    PENDING = "pending"
    CLEAN = "clean"
    INFECTED = "infected"
    UNAVAILABLE = "unavailable"     # ClamAV not configured  -  NOT bypassed silently
    FAILED = "failed"


class DocumentType(str, PyEnum):
    """Common document types across MoTA schemes."""
    CASTE_CERTIFICATE = "caste_certificate"
    INCOME_CERTIFICATE = "income_certificate"
    MARKSHEET = "marksheet"
    ADMISSION_LETTER = "admission_letter"
    INSTITUTION_ID = "institution_id"
    BANK_PASSBOOK = "bank_passbook"
    PHOTOGRAPH = "photograph"
    AADHAAR_CARD = "aadhaar_card"        # Only uploaded for verification; hash stored in users table
    DISABILITY_CERTIFICATE = "disability_certificate"
    PVTG_CERTIFICATE = "pvtg_certificate"
    DOMICILE_CERTIFICATE = "domicile_certificate"
    FEE_RECEIPT = "fee_receipt"
    RESEARCH_PROPOSAL = "research_proposal"  # NFS
    SUPERVISOR_LETTER = "supervisor_letter"   # NFS
    PASSPORT = "passport"                      # NOS
    VISA_DOCUMENT = "visa_document"            # NOS
    OTHER = "other"


#  -  - - Document  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Uploaded document record.

    storage_key: identifier within the storage provider (path in local mode, S3 key in cloud).
    The actual file bytes are NEVER stored in the database.
    """

    __tablename__ = "documents"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    document_type: Mapped[DocumentType] = mapped_column(
        SAEnum(DocumentType, name="document_type_enum"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)

    # File metadata
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content_hash_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus, name="document_status_enum"),
        default=DocumentStatus.UPLOADED,
        nullable=False,
    )

    # Malware scanning
    malware_scan_status: Mapped[MalwareScanStatus] = mapped_column(
        SAEnum(MalwareScanStatus, name="malware_scan_status_enum"),
        default=MalwareScanStatus.PENDING,
        nullable=False,
    )
    malware_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    extracted_fields: Mapped[list["DocumentExtractedFields"]] = relationship(
        "DocumentExtractedFields", back_populates="document"
    )
    verification_results: Mapped[list["DocumentVerificationResult"]] = relationship(
        "DocumentVerificationResult", back_populates="document"
    )

    def __repr__(self) -> str:
        return f"<Document {self.document_type} status={self.status}>"


#  -  - - DocumentExtractedFields  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class DocumentExtractedFields(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    AI/OCR extracted structured fields from a document.

    Results are cached  -  same document is never reprocessed.
    Check this table before calling any AI API.
    """

    __tablename__ = "document_extracted_fields"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    extracted_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI provider metadata (for audit and reproducibility)
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)   # "gemini", "mock"
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="extracted_fields")


#  -  - - DocumentVerificationResult  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class DocumentVerificationResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    AI verification findings and officer decision for a document.
    """

    __tablename__ = "document_verification_results"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # AI findings
    is_readable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_complete: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_authentic: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # AI flag only; officer decides
    quality_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    anomaly_flags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    ai_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Officer decision (human authority  -  AI CANNOT set this)
    officer_decision: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "accepted" | "rejected"
    officer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="verification_results")
