"""
AIService abstract interface.

Business logic MUST only interact with AIService (the abstract class).
Never import concrete GeminiAIService or MockAIService directly in routers/services.

Factory get_ai_service() provides the active implementation based on environment configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIService(ABC):
    """Abstract interface for AI/ML capabilities."""

    @abstractmethod
    def classify_document(self, image_bytes: bytes, filename: str) -> dict[str, Any]:
        """Classify document type (e.g. Caste Certificate, Income Certificate, Marks Card)."""
        ...

    @abstractmethod
    def extract_fields(self, text: str, document_type: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Extract structured fields from OCR text based on document schema."""
        ...

    @abstractmethod
    def check_quality(self, image_bytes: bytes, document_type: str) -> dict[str, Any]:
        """Assess document image quality, completeness, and legibility."""
        ...

    @abstractmethod
    def detect_anomalies(self, extracted_fields: dict[str, Any], application_context: dict[str, Any]) -> dict[str, Any]:
        """Check for anomalies or contradictions across documents and applicant claims."""
        ...

    @abstractmethod
    def generate_rag_response(self, query: str, context_chunks: list[str]) -> dict[str, Any]:
        """Generate response to applicant queries grounded in official scheme guidelines."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Indicates whether real AI capabilities are currently configured and operational."""
        ...

    @property
    @abstractmethod
    def status_message(self) -> str:
        """Human-readable status of AI capabilities for transparency in UI."""
        ...
