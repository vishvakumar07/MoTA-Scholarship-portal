"""AI package exports and factory."""

from __future__ import annotations

from ai.base import AIService
from ai.mock import MockAIService
from ai.ocr import OCRService, get_ocr_service
from config import settings


def get_ai_service() -> AIService:
    """
    Factory returning the active AI service implementation.
    If GOOGLE_AI_API_KEY is not configured, automatically degrades to MockAIService.
    """
    if settings.GOOGLE_AI_API_KEY:
        try:
            from ai.gemini import GeminiAIService
            return GeminiAIService(api_key=settings.GOOGLE_AI_API_KEY)
        except ImportError:
            return MockAIService()
    return MockAIService()


__all__ = ["AIService", "MockAIService", "get_ai_service", "OCRService", "get_ocr_service"]
