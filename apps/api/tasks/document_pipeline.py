"""
Document Processing Pipeline - Celery Tasks.

Pipeline stages (triggered on-demand, never automatically):
  1. Malware Scan      -> MalwareScanStatus: PENDING -> CLEAN | INFECTED | UNAVAILABLE | FAILED
  2. Classification    -> AI suggestion for document type (NEVER authoritative)
  3. OCR               -> Raw text extraction
  4. Field Extraction  -> Structured fields from OCR text (AI SUGGESTION)
  5. Quality Analysis  -> Readability and completeness check (AI SUGGESTION)
  6. Consistency Check -> Cross-document anomaly detection (AI SUGGESTION)

AI_PRINCIPLE:
  - All AI/OCR results are clearly labeled as AI SUGGESTIONS.
  - Officers review and make the final determination.
  - AI CANNOT set officer_decision or final application status.
"""

from __future__ import annotations

import io
import logging
import time
import uuid
from typing import Any

from celery_app import celery_app
from config import settings

log = logging.getLogger("mota_pipeline")


# ---------------------------------------------------------------------------
# Helper: get a DB session inside a Celery task
# ---------------------------------------------------------------------------

def _get_db():
    from database import SessionLocal
    return SessionLocal()


def _get_document(db, document_id: str):
    from models.document import Document
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ValueError(f"Document {document_id} not found")
    return doc


def _get_file_bytes(storage_key: str) -> bytes:
    """Retrieve file bytes synchronously from storage."""
    import asyncio
    from storage.local import get_storage_service
    storage = get_storage_service()

    async def _read():
        stream = await storage.download(storage_key)
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        return b"".join(chunks)

    return asyncio.run(_read())


def _add_audit(db, actor_id, action: str, resource_type: str, resource_id, details: dict):
    from models.system import AuditLog
    entry = AuditLog(
        actor_id=actor_id,
        actor_role="system",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(entry)


# ---------------------------------------------------------------------------
# Stage 1: Malware Scan
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="tasks.document_pipeline.scan_malware",
    max_retries=2,
    default_retry_delay=30,
)
def scan_malware(self, document_id: str) -> dict[str, Any]:
    """
    Stage 1: Malware scan via ClamAV.

    Sets malware_scan_status to:
      CLEAN       - No threats detected
      INFECTED    - Threat detected; document quarantined
      UNAVAILABLE - ClamAV not configured (explicit, not a silent pass)
      FAILED      - Scan error (not CLEAN; requires manual review)
    """
    from models.document import Document, DocumentStatus, MalwareScanStatus
    from datetime import datetime, timezone

    db = _get_db()
    try:
        doc = _get_document(db, document_id)
        doc.malware_scan_status = MalwareScanStatus.PENDING
        db.commit()

        scan_result_status = MalwareScanStatus.UNAVAILABLE
        scan_details: dict[str, Any] = {}

        try:
            import clamd
            clam = clamd.ClamdNetworkSocket(
                host=settings.CLAMAV_HOST,
                port=settings.CLAMAV_PORT,
                timeout=30,
            )
            file_bytes = _get_file_bytes(doc.storage_key)
            result = clam.instream(io.BytesIO(file_bytes))
            status_str, virus_name = result.get("stream", ("ERROR", ""))

            if status_str == "OK":
                scan_result_status = MalwareScanStatus.CLEAN
                scan_details = {"result": "clean"}
            elif status_str == "FOUND":
                scan_result_status = MalwareScanStatus.INFECTED
                scan_details = {"threat": virus_name}
                log.warning(f"MALWARE DETECTED in document {document_id}: {virus_name}")
            else:
                scan_result_status = MalwareScanStatus.FAILED
                scan_details = {"error": f"Unexpected ClamAV response: {status_str}"}

        except ImportError:
            scan_result_status = MalwareScanStatus.UNAVAILABLE
            scan_details = {"note": "clamd package not installed"}
        except Exception as e:
            if "Connection refused" in str(e) or "timed out" in str(e):
                scan_result_status = MalwareScanStatus.UNAVAILABLE
                scan_details = {"note": f"ClamAV not reachable: {e}"}
            else:
                scan_result_status = MalwareScanStatus.FAILED
                scan_details = {"error": str(e)}
                log.error(f"Malware scan error for {document_id}: {e}")

        doc.malware_scan_status = scan_result_status
        doc.malware_scanned_at = datetime.now(timezone.utc)

        # Quarantine if infected
        if scan_result_status == MalwareScanStatus.INFECTED:
            doc.status = DocumentStatus.SCAN_FAILED
        elif scan_result_status == MalwareScanStatus.CLEAN:
            if doc.status == DocumentStatus.UPLOADED:
                doc.status = DocumentStatus.PROCESSING

        _add_audit(db, None, "MALWARE_SCAN_COMPLETE", "document", doc.id, {
            "scan_status": scan_result_status.value,
            **scan_details,
        })
        db.commit()

        log.info(f"Malware scan for {document_id}: {scan_result_status.value}")
        return {
            "document_id": document_id,
            "scan_status": scan_result_status.value,
            **scan_details,
        }
    except Exception as exc:
        log.error(f"scan_malware task failed for {document_id}: {exc}")
        try:
            self.retry(exc=exc)
        except Exception:
            pass
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Stage 2-5: Full AI Processing Pipeline (triggered after scan)
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="tasks.document_pipeline.process_document",
    max_retries=1,
    default_retry_delay=60,
)
def process_document(self, document_id: str) -> dict[str, Any]:
    """
    Stages 2-5: AI-assisted document processing.

    Stage 2: Document Classification (AI SUGGESTION)
    Stage 3: OCR — raw text extraction
    Stage 4: Field Extraction (AI SUGGESTION)
    Stage 5: Quality Analysis (AI SUGGESTION)

    ALL AI results are:
    - Stored with provider label (MOCK, GOOGLE_GEMINI, GOOGLE_VISION, UNAVAILABLE)
    - Marked with confidence scores
    - Never presented as government verification
    - Subject to officer review
    """
    from models.document import (
        Document, DocumentStatus, DocumentExtractedFields, DocumentVerificationResult
    )
    from datetime import datetime, timezone

    db = _get_db()
    try:
        doc = _get_document(db, document_id)

        # Guard: only process documents that passed scan or are in UPLOADED state
        from models.document import MalwareScanStatus
        if doc.malware_scan_status == MalwareScanStatus.INFECTED:
            log.warning(f"Refusing to process infected document {document_id}")
            return {"document_id": document_id, "skipped": "infected"}

        if doc.status == DocumentStatus.PROCESSED:
            log.info(f"Document {document_id} already processed; skipping.")
            return {"document_id": document_id, "skipped": "already_processed"}

        doc.status = DocumentStatus.PROCESSING
        db.commit()

        file_bytes = _get_file_bytes(doc.storage_key)
        mime_type = doc.mime_type or "image/jpeg"

        # -- Stage 2: Classification (AI SUGGESTION) --
        from ai import get_ai_service
        ai_service = get_ai_service()

        t_start = time.monotonic()
        classification = ai_service.classify_document(file_bytes, doc.original_filename)
        classification_ms = int((time.monotonic() - t_start) * 1000)

        # -- Stage 3: OCR --
        from ai.ocr import get_ocr_service
        ocr_service = get_ocr_service()

        t_start = time.monotonic()
        ocr_result = ocr_service.extract_text(file_bytes, mime_type)
        ocr_ms = int((time.monotonic() - t_start) * 1000)
        raw_text = ocr_result.get("raw_text") or ""

        # -- Stage 4: Field Extraction (AI SUGGESTION) --
        doc_type_str = doc.document_type.value
        field_schema = _get_field_schema(doc_type_str)

        t_start = time.monotonic()
        extraction = ai_service.extract_fields(raw_text, doc_type_str, field_schema)
        extraction_ms = int((time.monotonic() - t_start) * 1000)

        # -- Stage 5: Quality Analysis (AI SUGGESTION) --
        t_start = time.monotonic()
        quality = ai_service.check_quality(file_bytes, doc_type_str)
        quality_ms = int((time.monotonic() - t_start) * 1000)

        total_ms = classification_ms + ocr_ms + extraction_ms + quality_ms

        # -- Persist: DocumentExtractedFields --
        extracted_fields_record = DocumentExtractedFields(
            document_id=doc.id,
            extracted_data=extraction.get("extracted_fields", {}),
            confidence_scores={
                "classification": classification.get("confidence"),
                "ocr": ocr_result.get("confidence"),
                "extraction": extraction.get("confidence"),
            },
            raw_text=raw_text if raw_text else None,
            ai_provider=ai_service.__class__.__name__,
            model_name="gemini-1.5-flash" if not classification.get("is_mock") else "MOCK",
            model_version="phase5",
            processing_time_ms=total_ms,
        )
        db.add(extracted_fields_record)

        # -- Persist: DocumentVerificationResult (AI findings only; officer_decision=None) --
        verification_record = DocumentVerificationResult(
            document_id=doc.id,
            is_readable=quality.get("is_readable"),
            is_complete=quality.get("is_complete"),
            is_authentic=None,          # AI CANNOT determine authenticity
            quality_score=quality.get("quality_score"),
            anomaly_flags=[],           # Populated by consistency check (Stage 6)
            ai_notes=(
                f"[AI SUGGESTION - NOT VERIFIED] "
                f"Classification: {classification.get('document_type', 'UNKNOWN')} "
                f"(confidence: {classification.get('confidence', 0):.0%}). "
                f"OCR: {'available' if ocr_result.get('is_available') else 'unavailable'}. "
                f"Quality: {quality.get('quality_score', 'N/A')}. "
                f"Provider: {classification.get('provider', 'MOCK')}. "
                f"Manual officer review required."
            ),
            officer_decision=None,      # HUMAN sets this; AI cannot
            officer_notes=None,
            verified_at=None,
        )
        db.add(verification_record)

        # -- Update document status --
        doc.status = DocumentStatus.PROCESSED
        db.commit()

        _add_audit(db, None, "DOCUMENT_AI_PROCESSED", "document", doc.id, {
            "ai_provider": classification.get("provider"),
            "is_mock": classification.get("is_mock", True),
            "ocr_available": ocr_result.get("is_available"),
            "quality_score": quality.get("quality_score"),
            "processing_time_ms": total_ms,
            "note": "AI SUGGESTION - requires officer review",
        })
        db.commit()

        log.info(f"Document {document_id} processed. Provider={classification.get('provider')}, "
                 f"mock={classification.get('is_mock')}, time={total_ms}ms")

        return {
            "document_id": document_id,
            "status": "processed",
            "ai_provider": classification.get("provider"),
            "is_mock": classification.get("is_mock", True),
            "quality_score": quality.get("quality_score"),
            "note": "AI SUGGESTION — requires officer review before any administrative decision",
        }
    except Exception as exc:
        log.error(f"process_document task failed for {document_id}: {exc}")
        db.rollback()
        try:
            db2 = _get_db()
            doc2 = db2.query(__import__("models.document", fromlist=["Document"]).Document).filter_by(id=document_id).first()
            if doc2:
                doc2.status = __import__("models.document", fromlist=["DocumentStatus"]).DocumentStatus.UPLOADED
                db2.commit()
            db2.close()
        except Exception:
            pass
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Stage 6: Cross-Document Consistency Check
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="tasks.document_pipeline.check_consistency",
    max_retries=1,
    default_retry_delay=30,
)
def check_consistency(self, application_id: str) -> dict[str, Any]:
    """
    Stage 6: Cross-document consistency analysis (AI SUGGESTION).

    Checks for anomalies across all processed documents for one application.
    Results are stored as anomaly_flags on each DocumentVerificationResult.
    Officers review and make the final determination.
    """
    from models.application import Application
    from models.document import Document, DocumentStatus, DocumentExtractedFields, DocumentVerificationResult
    from models.applicant import ApplicantProfile

    db = _get_db()
    try:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found")

        # Gather all processed documents and their extracted fields
        processed_docs = (
            db.query(Document)
            .filter(
                Document.application_id == application_id,
                Document.status == DocumentStatus.PROCESSED,
            )
            .all()
        )

        if not processed_docs:
            return {"application_id": application_id, "skipped": "no_processed_documents"}

        all_extracted: dict[str, dict] = {}
        for doc in processed_docs:
            fields_record = (
                db.query(DocumentExtractedFields)
                .filter(DocumentExtractedFields.document_id == doc.id)
                .order_by(DocumentExtractedFields.created_at.desc())
                .first()
            )
            if fields_record:
                all_extracted[doc.document_type.value] = fields_record.extracted_data

        # Build application context for AI comparison
        profile = db.query(ApplicantProfile).filter(
            ApplicantProfile.user_id == app.applicant_id
        ).first()

        application_context = {
            "application_id": str(app.id),
            "scheme_version_id": str(app.scheme_version_id),
        }
        if profile:
            application_context["declared_name"] = profile.full_name
            application_context["declared_category"] = "ST"

        from ai import get_ai_service
        ai_service = get_ai_service()
        anomaly_result = ai_service.detect_anomalies(all_extracted, application_context)

        anomalies = anomaly_result.get("anomalies", [])
        ai_provider = anomaly_result.get("provider", "MOCK")
        is_mock = anomaly_result.get("is_mock", True)

        # Update anomaly_flags on each verification record
        for doc in processed_docs:
            vr = (
                db.query(DocumentVerificationResult)
                .filter(DocumentVerificationResult.document_id == doc.id)
                .order_by(DocumentVerificationResult.created_at.desc())
                .first()
            )
            if vr:
                doc_anomalies = [a for a in anomalies]  # attach all cross-doc anomalies
                vr.anomaly_flags = doc_anomalies
                vr.ai_notes = (vr.ai_notes or "") + (
                    f" | Cross-document consistency: {len(doc_anomalies)} flags "
                    f"[AI SUGGESTION, provider={ai_provider}, mock={is_mock}]. "
                    "Officer review required."
                )

        _add_audit(db, None, "CONSISTENCY_CHECK_COMPLETE", "application", app.id, {
            "anomaly_count": len(anomalies),
            "ai_provider": ai_provider,
            "is_mock": is_mock,
            "note": "AI SUGGESTION - requires officer review",
        })
        db.commit()

        log.info(f"Consistency check for application {application_id}: "
                 f"{len(anomalies)} anomalies (mock={is_mock})")

        return {
            "application_id": application_id,
            "anomaly_count": len(anomalies),
            "ai_provider": ai_provider,
            "is_mock": is_mock,
            "note": "AI SUGGESTION — requires officer review before any administrative decision",
        }
    except Exception as exc:
        log.error(f"check_consistency task failed for {application_id}: {exc}")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Orchestrator: trigger full pipeline for one document
# ---------------------------------------------------------------------------

@celery_app.task(name="tasks.document_pipeline.trigger_pipeline")
def trigger_pipeline(document_id: str) -> dict[str, Any]:
    """
    Orchestrate the full document processing pipeline for one document.
    Triggered manually by an officer or by the upload endpoint (if configured).

    COST CONTROL: Never called automatically on a schedule.
    """
    log.info(f"Triggering processing pipeline for document {document_id}")

    # Run stages sequentially via chaining
    from celery import chain
    pipeline = chain(
        scan_malware.s(document_id),
        _maybe_process.s(document_id),
    )
    pipeline.apply_async()

    return {"document_id": document_id, "pipeline": "started"}


@celery_app.task(name="tasks.document_pipeline._maybe_process")
def _maybe_process(scan_result: dict, document_id: str) -> dict[str, Any]:
    """Bridge task: only call process_document if scan passed."""
    scan_status = scan_result.get("scan_status", "unavailable")
    if scan_status == "infected":
        log.warning(f"Pipeline halted for {document_id}: infected document.")
        return {"document_id": document_id, "halted": "infected"}
    # Proceed to AI processing regardless of UNAVAILABLE/FAILED scan
    # (unavailable scan = ClamAV not configured; document not blocked, flagged for officer)
    process_document.apply_async(args=[document_id])
    return {"document_id": document_id, "next_stage": "process_document"}


# ---------------------------------------------------------------------------
# Field schemas for extraction
# ---------------------------------------------------------------------------

def _get_field_schema(document_type: str) -> dict[str, Any]:
    """Return the expected extraction schema for each document type."""
    schemas = {
        "caste_certificate": {
            "applicant_name": "string",
            "caste": "string",
            "sub_tribe": "string",
            "certificate_number": "string",
            "issuing_authority": "string",
            "issue_date": "date (DD/MM/YYYY)",
            "state": "string",
            "district": "string",
        },
        "income_certificate": {
            "applicant_name": "string",
            "annual_income_inr": "number",
            "financial_year": "string",
            "certificate_number": "string",
            "issuing_authority": "string",
            "issue_date": "date (DD/MM/YYYY)",
        },
        "marksheet": {
            "student_name": "string",
            "roll_number": "string",
            "board_university": "string",
            "exam_year": "string",
            "class_standard": "string",
            "percentage_marks": "number",
            "subjects": "list of subject-marks pairs",
            "pass_status": "PASS|FAIL",
        },
        "admission_letter": {
            "student_name": "string",
            "institution_name": "string",
            "course_name": "string",
            "course_duration_years": "number",
            "academic_year": "string",
            "admission_date": "date",
        },
        "bank_passbook": {
            "account_holder_name": "string",
            "bank_name": "string",
            "branch_name": "string",
            "ifsc_code": "string",
            "account_type": "string",
        },
        "pvtg_certificate": {
            "applicant_name": "string",
            "tribe_name": "string",
            "pvtg_group": "string",
            "certificate_number": "string",
            "issuing_authority": "string",
            "issue_date": "date",
        },
    }
    return schemas.get(document_type, {"raw_content": "Extract all visible text fields as key-value pairs"})
