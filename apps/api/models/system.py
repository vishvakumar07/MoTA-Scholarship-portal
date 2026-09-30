"""
System models: Notification, AuditLog, KnowledgeDocument, KnowledgeChunk, AIAnalysisResult.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False


class NotificationChannel(str, PyEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"


class NotificationStatus(str, PyEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"       # Channel not configured
    READ = "read"              # In-app only


#  -  - - Notification  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Multi-channel notification log.

    For SIH prototype: only IN_APP channel is active.
    EMAIL and SMS channels are stubs (status=SKIPPED if not configured).
    """

    __tablename__ = "notifications"

    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    channel: Mapped[NotificationChannel] = mapped_column(
        SAEnum(NotificationChannel, name="notification_channel_enum"), nullable=False
    )
    status: Mapped[NotificationStatus] = mapped_column(
        SAEnum(NotificationStatus, name="notification_status_enum"),
        default=NotificationStatus.PENDING,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Related entity (for deep-linking)
    related_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


#  -  - - AuditLog  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class AuditLog(Base, UUIDPrimaryKeyMixin):
    """
    Immutable, append-only system audit log.

    Records every significant action.
    A DB trigger prevents UPDATE and DELETE on this table.
    PII is scrubbed before logging.
    """

    __tablename__ = "audit_logs"

    # Who
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    actor_role: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # What
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    # Details
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


#  -  - - KnowledgeDocument  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class KnowledgeDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Official MoTA documents ingested for RAG.

    Only specific, official documents are ingested  -  not whole government websites.
    Source URL and metadata required for every document.
    """

    __tablename__ = "knowledge_documents"

    # Source (required for every document)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # guideline, faq, amendment, reference
    publication_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    retrieved_date: Mapped[str] = mapped_column(String(20), nullable=False)
    related_scheme_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Processing
    is_ingested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Chunks
    chunks: Mapped[list["KnowledgeChunk"]] = relationship("KnowledgeChunk", back_populates="document")


#  -  - - KnowledgeChunk  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class KnowledgeChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Chunked text from a KnowledgeDocument with vector embedding.

    pgvector stores the embedding for semantic similarity search.
    Embedding dimension: 1536 (text-embedding-004 / text-embedding-ada-002 compatible).
    """

    __tablename__ = "knowledge_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Vector embedding (pgvector)  -  nullable until ingestion pipeline runs
    # Dimension 768 for text-embedding-gecko or 1536 for ada-002 / Gemini text-embedding-004
    if PGVECTOR_AVAILABLE:
        embedding = mapped_column(Vector(768), nullable=True)

    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    document: Mapped["KnowledgeDocument"] = relationship("KnowledgeDocument", back_populates="chunks")


#  -  - - AIAnalysisResult  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class AIAnalysisResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Cached AI model output for a document or application.

    IMPORTANT: Check this table BEFORE calling any AI API.
    Same document is NEVER reprocessed unless explicitly requested.
    """

    __tablename__ = "ai_analysis_results"

    # Target entity
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True
    )

    analysis_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    # Examples: "ocr", "classify", "extract_fields", "quality_check", "cross_verify", "anomaly_detect"

    # Result
    result_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

    # Provider metadata (audit trail)
    ai_provider: Mapped[str] = mapped_column(String(50), nullable=False)  # "gemini", "mock"
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Content hash  -  used to detect if source file changed (triggers reprocessing)
    input_content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    is_mock_result: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
