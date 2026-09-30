"""
OCR Service abstraction.

Business logic MUST only interact with OCRService (abstract class).
Never import GoogleVisionOCRService or UnavailableOCRService directly in routers/services.

Factory get_ocr_service() selects the active implementation based on environment config.

AI_PRINCIPLE: OCR results are NEVER authoritative. They are AI SUGGESTIONS
that require officer review and manual verification.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class OCRService(ABC):
    """Abstract interface for OCR capabilities."""

    @abstractmethod
    def extract_text(self, file_bytes: bytes, mime_type: str) -> dict[str, Any]:
        """
        Extract raw text from a document image or PDF.

        Returns dict with keys:
            provider, is_available, raw_text, pages, confidence, note (optional)
        """
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """True when real OCR credentials are configured and operational."""
        ...

    @property
    @abstractmethod
    def status_message(self) -> str:
        """Human-readable status for transparency in UI."""
        ...


class UnavailableOCRService(OCRService):
    """
    UnavailableOCRService - used when OCR_PROVIDER=unavailable or credentials are absent.

    ALL results:
    - provider = "UNAVAILABLE"
    - is_available = False
    - raw_text = None
    - include a clear note explaining OCR is unavailable
    - NEVER presented as real OCR output
    """

    PROVIDER_NAME = "UNAVAILABLE"

    def extract_text(self, file_bytes: bytes, mime_type: str) -> dict[str, Any]:
        return {
            "provider": self.PROVIDER_NAME,
            "is_available": False,
            "raw_text": None,
            "pages": [],
            "confidence": None,
            "note": (
                "OCR processing unavailable. "
                "Configure GOOGLE_CLOUD_VISION_API_KEY and set OCR_PROVIDER=google_vision "
                "to enable OCR. Manual document review is required."
            ),
        }

    @property
    def is_available(self) -> bool:
        return False

    @property
    def status_message(self) -> str:
        return (
            "OCR unavailable - API configuration required. "
            "Set GOOGLE_CLOUD_VISION_API_KEY in your .env file to enable OCR features."
        )


class GoogleVisionOCRService(OCRService):
    """
    Google Cloud Vision OCR implementation.
    Activated ONLY when GOOGLE_CLOUD_VISION_API_KEY is configured.
    """

    PROVIDER_NAME = "GOOGLE_VISION"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
        self._init_client()

    def _init_client(self):
        import logging
        log = logging.getLogger("mota_ocr")
        try:
            from google.cloud import vision
            from google.oauth2 import api_key as goog_api_key
            credentials = goog_api_key.Credentials(self.api_key)
            self._client = vision.ImageAnnotatorClient(credentials=credentials)
            log.info("Google Cloud Vision OCR client initialized.")
        except ImportError:
            log.warning("google-cloud-vision package not installed. OCR unavailable.")
            self._client = None
        except Exception as e:
            log.error(f"Failed to initialize Google Vision OCR: {e}")
            self._client = None

    @property
    def is_available(self) -> bool:
        return self._client is not None

    @property
    def status_message(self) -> str:
        if self.is_available:
            return "Active (Google Cloud Vision OCR)"
        return "Configured but initialization failed or package missing"

    def extract_text(self, file_bytes: bytes, mime_type: str) -> dict[str, Any]:
        import logging
        log = logging.getLogger("mota_ocr")

        if not self.is_available:
            return {
                "provider": self.PROVIDER_NAME,
                "is_available": False,
                "raw_text": None,
                "pages": [],
                "confidence": None,
                "note": "Google Vision client not initialized",
            }
        try:
            from google.cloud import vision
            image = vision.Image(content=file_bytes[:5 * 1024 * 1024])
            response = self._client.document_text_detection(image=image)

            if response.error.message:
                log.error(f"Google Vision API error: {response.error.message}")
                return {
                    "provider": self.PROVIDER_NAME,
                    "is_available": True,
                    "raw_text": None,
                    "pages": [],
                    "confidence": None,
                    "error": response.error.message,
                }

            full_text = response.full_text_annotation.text if response.full_text_annotation else ""

            pages_data = []
            for i, page in enumerate(response.full_text_annotation.pages):
                page_words = []
                for block in page.blocks:
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            page_words.append("".join([s.text for s in word.symbols]))
                pages_data.append({
                    "page": i + 1,
                    "text": " ".join(page_words),
                    "confidence": page.confidence if hasattr(page, "confidence") else None,
                })

            confs = [p["confidence"] for p in pages_data if p["confidence"] is not None]
            overall_confidence = sum(confs) / len(confs) if confs else None

            return {
                "provider": self.PROVIDER_NAME,
                "is_available": True,
                "raw_text": full_text,
                "pages": pages_data,
                "confidence": overall_confidence,
            }
        except Exception as e:
            log.error(f"Google Vision extract_text error: {e}")
            return {
                "provider": self.PROVIDER_NAME,
                "is_available": True,
                "raw_text": None,
                "pages": [],
                "confidence": None,
                "error": str(e),
            }


def get_ocr_service() -> OCRService:
    """Factory - returns the configured OCR provider."""
    import logging
    from config import settings
    log = logging.getLogger("mota_ocr")

    if settings.OCR_PROVIDER == "google_vision" and settings.GOOGLE_CLOUD_VISION_API_KEY:
        log.info("OCR provider: Google Cloud Vision")
        return GoogleVisionOCRService(settings.GOOGLE_CLOUD_VISION_API_KEY)

    log.warning("OCR provider: Unavailable (OCR features disabled)")
    return UnavailableOCRService()
