"""
MockAIService  -  used when GOOGLE_AI_API_KEY is not configured.

ALL mock results are:
- Clearly labeled with provider="MOCK"
- Marked is_mock_result=True
- Have confidence=0.0
- Include a clear note explaining AI is unavailable
- NEVER presented as real AI analysis

This ensures the application remains fully functional without AI credentials.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MockAIResult:
    provider: str = "MOCK"
    is_mock: bool = True
    confidence: float = 0.0
    note: str = (
        "AI processing unavailable. "
        "Configure GOOGLE_AI_API_KEY to enable real AI analysis. "
        "Manual review is required."
    )


class MockAIService:
    """
    MockAIService: returns clearly labeled placeholder results.

    Used when:
    - GOOGLE_AI_API_KEY is not set
    - AI_PROVIDER=mock

    NEVER call this service and present results as real AI findings.
    """

    PROVIDER_NAME = "MOCK"

    def classify_document(self, image_bytes: bytes, filename: str) -> dict:
        return {
            "provider": self.PROVIDER_NAME,
            "is_mock": True,
            "confidence": 0.0,
            "document_type": "UNKNOWN",
            "note": MockAIResult().note,
        }

    def extract_fields(self, text: str, document_type: str, schema: dict) -> dict:
        return {
            "provider": self.PROVIDER_NAME,
            "is_mock": True,
            "confidence": 0.0,
            "extracted_fields": {},
            "note": MockAIResult().note,
        }

    def check_quality(self, image_bytes: bytes, document_type: str) -> dict:
        return {
            "provider": self.PROVIDER_NAME,
            "is_mock": True,
            "confidence": 0.0,
            "is_readable": None,
            "is_complete": None,
            "quality_score": None,
            "note": MockAIResult().note,
        }

    def detect_anomalies(self, extracted_fields: dict, application_context: dict) -> dict:
        return {
            "provider": self.PROVIDER_NAME,
            "is_mock": True,
            "confidence": 0.0,
            "anomalies": [],
            "note": MockAIResult().note,
        }

    def generate_rag_response(self, query: str, context_chunks: list[str]) -> dict:
        return {
            "provider": self.PROVIDER_NAME,
            "is_mock": True,
            "answer": None,
            "source_chunks": [],
            "note": MockAIResult().note,
        }

    @property
    def is_available(self) -> bool:
        return False

    @property
    def status_message(self) -> str:
        return (
            "AI processing unavailable  -  API configuration required. "
            "Set GOOGLE_AI_API_KEY in your .env file to enable AI features."
        )


def get_ai_service():
    """Factory  -  returns the configured AI provider."""
    from config import settings
    import structlog

    log = structlog.get_logger(__name__)

    if settings.AI_PROVIDER == "gemini" and settings.GOOGLE_AI_API_KEY:
        try:
            # Gemini implementation to be added in Phase 4 (AI pipeline)
            log.info("AI provider: Gemini (API key present; full implementation in Phase 4)")
            return MockAIService()  # Placeholder until Phase 4
        except Exception as e:
            log.error("Failed to initialize GeminiAIService", error=str(e))
            return MockAIService()

    log.warning(
        "AI provider: Mock (AI features unavailable)",
        reason="GOOGLE_AI_API_KEY not configured or AI_PROVIDER=mock",
    )
    return MockAIService()
