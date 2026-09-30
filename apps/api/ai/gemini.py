"""
Google Gemini AI Service implementation.

Activated ONLY when GOOGLE_AI_API_KEY is configured in the environment.
Implements the AIService abstract interface.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ai.base import AIService

logger = logging.getLogger("mota_gemini")


class GeminiAIService(AIService):
    """
    Real Gemini implementation for OCR refinement, document classification,
    and official MoTA scheme RAG Q&A.
    """

    PROVIDER_NAME = "GOOGLE_GEMINI"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel("gemini-1.5-flash")
            logger.info("Google Gemini AI client successfully initialized.")
        except ImportError:
            logger.warning("google-generativeai package not installed. Gemini AI unavailable.")
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            self._client = None

    @property
    def is_available(self) -> bool:
        return self._client is not None

    @property
    def status_message(self) -> str:
        if self.is_available:
            return "Active (Google Gemini 1.5 Flash)"
        return "Configured but initialization failed or package missing"

    def classify_document(self, image_bytes: bytes, filename: str) -> dict[str, Any]:
        if not self.is_available:
            return {
                "provider": self.PROVIDER_NAME,
                "is_mock": False,
                "confidence": 0.0,
                "document_type": "UNKNOWN",
                "note": "Gemini client not initialized",
            }
        try:
            prompt = (
                "You are an AI document verification officer for the Ministry of Tribal Affairs (MoTA). "
                "Classify this document into one of: CASTE_CERTIFICATE, INCOME_CERTIFICATE, "
                "DOMICILE_CERTIFICATE, MARKS_CARD, ADMISSION_LETTER, BANK_PASSBOOK, OTHER. "
                "Respond in JSON format: {\"document_type\": \"...\", \"confidence\": 0.0-1.0, \"explanation\": \"...\"}"
            )
            response = self._client.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_bytes},
            ])
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            data = json.loads(text)
            data["provider"] = self.PROVIDER_NAME
            data["is_mock"] = False
            return data
        except Exception as e:
            logger.error(f"Gemini classify_document error: {e}")
            return {
                "provider": self.PROVIDER_NAME,
                "is_mock": False,
                "confidence": 0.0,
                "document_type": "UNKNOWN",
                "error": str(e),
            }

    def extract_fields(self, text: str, document_type: str, schema: dict[str, Any]) -> dict[str, Any]:
        if not self.is_available:
            return {"provider": self.PROVIDER_NAME, "is_mock": False, "extracted_fields": {}}
        try:
            prompt = (
                f"Extract the following fields from this {document_type} document text according to the schema:\n"
                f"Schema: {json.dumps(schema)}\n"
                f"Text:\n{text}\n"
                "Return a JSON object matching the requested schema."
            )
            response = self._client.generate_content(prompt)
            raw = response.text.strip()
            if raw.startswith("```json"):
                raw = raw[7:-3].strip()
            fields = json.loads(raw)
            return {
                "provider": self.PROVIDER_NAME,
                "is_mock": False,
                "extracted_fields": fields,
            }
        except Exception as e:
            logger.error(f"Gemini extract_fields error: {e}")
            return {"provider": self.PROVIDER_NAME, "is_mock": False, "extracted_fields": {}, "error": str(e)}

    def check_quality(self, image_bytes: bytes, document_type: str) -> dict[str, Any]:
        if not self.is_available:
            return {"provider": self.PROVIDER_NAME, "is_mock": False, "confidence": 0.0}
        try:
            prompt = (
                f"Assess the quality of this uploaded {document_type} image for government scholarship verification. "
                "Check for blurriness, completeness, glare, and legibility. "
                "Return JSON: {\"is_readable\": bool, \"is_complete\": bool, \"quality_score\": float (0.0-1.0), \"issues\": []}"
            )
            response = self._client.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_bytes},
            ])
            raw = response.text.strip()
            if raw.startswith("```json"):
                raw = raw[7:-3].strip()
            res = json.loads(raw)
            res["provider"] = self.PROVIDER_NAME
            res["is_mock"] = False
            return res
        except Exception as e:
            logger.error(f"Gemini check_quality error: {e}")
            return {"provider": self.PROVIDER_NAME, "is_mock": False, "confidence": 0.0, "error": str(e)}

    def detect_anomalies(self, extracted_fields: dict[str, Any], application_context: dict[str, Any]) -> dict[str, Any]:
        if not self.is_available:
            return {"provider": self.PROVIDER_NAME, "is_mock": False, "anomalies": []}
        try:
            prompt = (
                "Cross-check the extracted document fields against applicant profile data. "
                "Flag discrepancies in Name, DOB, Category (ST), or Family Income. "
                f"Extracted: {json.dumps(extracted_fields)}\n"
                f"Application context: {json.dumps(application_context)}\n"
                "Return JSON: {\"anomalies\": [{\"field\": str, \"severity\": \"low\"|\"medium\"|\"high\", \"description\": str}]}"
            )
            response = self._client.generate_content(prompt)
            raw = response.text.strip()
            if raw.startswith("```json"):
                raw = raw[7:-3].strip()
            res = json.loads(raw)
            res["provider"] = self.PROVIDER_NAME
            res["is_mock"] = False
            return res
        except Exception as e:
            logger.error(f"Gemini detect_anomalies error: {e}")
            return {"provider": self.PROVIDER_NAME, "is_mock": False, "anomalies": [], "error": str(e)}

    def generate_rag_response(self, query: str, context_chunks: list[str]) -> dict[str, Any]:
        if not self.is_available:
            return {"provider": self.PROVIDER_NAME, "is_mock": False, "answer": None}
        try:
            context_text = "\n---\n".join(context_chunks)
            prompt = (
                "You are an AI assistant for the Ministry of Tribal Affairs (MoTA) Scholarship Portal. "
                "Answer the user's question accurately using ONLY the provided official guideline excerpts. "
                "If the answer cannot be determined from the excerpts, state clearly that official guidance should be consulted. "
                f"Excerpts:\n{context_text}\n\n"
                f"User Question: {query}\n"
            )
            response = self._client.generate_content(prompt)
            return {
                "provider": self.PROVIDER_NAME,
                "is_mock": False,
                "answer": response.text.strip(),
                "source_chunks_count": len(context_chunks),
            }
        except Exception as e:
            logger.error(f"Gemini generate_rag_response error: {e}")
            return {"provider": self.PROVIDER_NAME, "is_mock": False, "answer": None, "error": str(e)}
