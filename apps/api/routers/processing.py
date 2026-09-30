"""
Document Processing Router - Phase 5.

Endpoints:
  POST /processing/trigger/{document_id}   - Officer: trigger AI pipeline
  GET  /processing/status/{document_id}    - Applicant/Officer: get processing status
  GET  /processing/results/{document_id}   - Officer: get AI extraction results
  POST /processing/review/{document_id}    - Officer: submit manual review decision
  GET  /processing/application/{app_id}    - Officer: all document statuses for an application
  POST /processing/consistency/{app_id}    - Officer: trigger cross-document consistency check

AI_PRINCIPLE:
  - AI results are clearly labeled AI SUGGESTION in all responses.
  - officer_decision is the only authoritative verification outcome.
  - Applicants can view their document status but NOT AI findings (privacy/security).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.application import Application, ApplicationStatus
from models.document import (
    Document, DocumentStatus, DocumentExtractedFields, DocumentVerificationResult
)
from models.system import AuditLog
from models.user import User
from security.rbac import get_current_user

router = APIRouter(prefix="/processing", tags=["Document Processing (Phase 5)"])


# ---------------------------------------------------------------------------
# Role helpers
# ---------------------------------------------------------------------------

def _require_officer(user: User):
    roles = [r.name for r in getattr(user, "roles", [])]
    if not any(r in ["super_admin", "scheme_admin", "scrutiny_officer", "verification_officer"] for r in roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authorised officers.",
        )


def _can_access_document(doc: Document, app: Application, user: User) -> bool:
    roles = [r.name for r in getattr(user, "roles", [])]
    is_staff = any(r in ["super_admin", "scheme_admin", "scrutiny_officer", "verification_officer"] for r in roles)
    is_owner = app.applicant_id == user.id
    return is_owner or is_staff


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TriggerPipelineResponse(BaseModel):
    document_id: str
    pipeline: str
    message: str


class DocumentStatusResponse(BaseModel):
    document_id: str
    document_type: str
    original_filename: str
    status: str
    malware_scan_status: str
    malware_scan_note: str
    uploaded_at: datetime
    ai_processing_note: str


class OfficerReviewRequest(BaseModel):
    decision: str           # "accepted" | "rejected"
    officer_notes: str | None = None


class OfficerReviewResponse(BaseModel):
    document_id: str
    officer_decision: str
    reviewed_by: str
    reviewed_at: datetime
    note: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/trigger/{document_id}",
    response_model=TriggerPipelineResponse,
    summary="[Officer] Trigger AI document processing pipeline",
)
def trigger_pipeline(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger the AI processing pipeline for a specific document.
    Officer-only. Never runs automatically.

    Pipeline: Malware Scan -> OCR -> Field Extraction -> Quality Analysis
    All AI results require officer review before any administrative action.
    """
    _require_officer(current_user)

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.status == DocumentStatus.PROCESSED:
        raise HTTPException(
            status_code=400,
            detail="Document already processed. Use /review to submit officer decision.",
        )

    if doc.status == DocumentStatus.SCAN_FAILED:
        raise HTTPException(
            status_code=400,
            detail="Document failed malware scan. Cannot process infected document.",
        )

    # Dispatch Celery task
    try:
        from tasks.document_pipeline import trigger_pipeline as _trigger
        _trigger.apply_async(args=[document_id])
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Task queue unavailable: {e}. Ensure Celery worker is running.",
        )

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role="officer",
        action="DOCUMENT_PIPELINE_TRIGGERED",
        resource_type="document",
        resource_id=doc.id,
        details={"triggered_by": str(current_user.id)},
    ))
    db.commit()

    return TriggerPipelineResponse(
        document_id=document_id,
        pipeline="started",
        message="Document processing pipeline triggered. Results will be available after processing completes.",
    )


@router.get(
    "/status/{document_id}",
    response_model=DocumentStatusResponse,
    summary="Get document processing status (applicant or officer)",
)
def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the current processing status of a document.
    Accessible by the document owner (applicant) or authorized officers.
    AI findings are NOT exposed here (officer-only via /results endpoint).
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    app = db.query(Application).filter(Application.id == doc.application_id).first()
    if not app or not _can_access_document(doc, app, current_user):
        raise HTTPException(status_code=403, detail="Access forbidden.")

    scan_status = doc.malware_scan_status.value

    # Honest malware scan note
    if scan_status == "unavailable":
        scan_note = "Malware scanning not configured. Manual verification required."
    elif scan_status == "infected":
        scan_note = "Document flagged by malware scan. Document has been quarantined."
    elif scan_status == "failed":
        scan_note = "Malware scan encountered an error. Manual review required."
    elif scan_status == "clean":
        scan_note = "Malware scan passed."
    else:
        scan_note = "Malware scan pending."

    # Processing note for applicants
    if doc.status == DocumentStatus.PROCESSED:
        ai_note = "Document has been processed. Awaiting officer review."
    elif doc.status == DocumentStatus.VERIFIED:
        ai_note = "Document has been reviewed and accepted by an officer."
    elif doc.status == DocumentStatus.REJECTED:
        ai_note = "Document was rejected. Please upload a corrected document."
    elif doc.status == DocumentStatus.PROCESSING:
        ai_note = "Document is currently being processed. Please check back shortly."
    elif doc.status == DocumentStatus.SCAN_FAILED:
        ai_note = "Document could not be accepted due to a security scan issue."
    else:
        ai_note = "Document uploaded. Processing has not yet been triggered."

    return DocumentStatusResponse(
        document_id=document_id,
        document_type=doc.document_type.value,
        original_filename=doc.original_filename,
        status=doc.status.value,
        malware_scan_status=scan_status,
        malware_scan_note=scan_note,
        uploaded_at=doc.uploaded_at,
        ai_processing_note=ai_note,
    )


@router.get(
    "/results/{document_id}",
    summary="[Officer] View AI extraction results for a document",
)
def get_ai_results(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns AI extraction results and quality analysis for officer review.
    Officer-only. Results are clearly labeled as AI SUGGESTIONS.

    AI findings are NEVER authoritative. Officer decision is required.
    """
    _require_officer(current_user)

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    extracted = (
        db.query(DocumentExtractedFields)
        .filter(DocumentExtractedFields.document_id == doc.id)
        .order_by(DocumentExtractedFields.created_at.desc())
        .first()
    )

    verification = (
        db.query(DocumentVerificationResult)
        .filter(DocumentVerificationResult.document_id == doc.id)
        .order_by(DocumentVerificationResult.created_at.desc())
        .first()
    )

    ai_results: dict[str, Any] = {
        "document_id": document_id,
        "document_type": doc.document_type.value,
        "status": doc.status.value,
        "ai_disclaimer": (
            "ALL results below are AI SUGGESTIONS generated by an automated system. "
            "They are NOT verified by any government authority. "
            "The authorised officer is solely responsible for verification decisions."
        ),
    }

    if extracted:
        ai_results["extraction"] = {
            "ai_provider": extracted.ai_provider,
            "model": extracted.model_name,
            "processing_time_ms": extracted.processing_time_ms,
            "extracted_fields": extracted.extracted_data,
            "confidence_scores": extracted.confidence_scores,
            "raw_text_available": extracted.raw_text is not None,
            "label": "AI SUGGESTION — requires officer verification",
        }
    else:
        ai_results["extraction"] = None

    if verification:
        ai_results["quality"] = {
            "is_readable": verification.is_readable,
            "is_complete": verification.is_complete,
            "quality_score": float(verification.quality_score) if verification.quality_score else None,
            "anomaly_flags": verification.anomaly_flags or [],
            "ai_notes": verification.ai_notes,
            "label": "AI SUGGESTION — requires officer verification",
        }
        ai_results["officer_review"] = {
            "officer_decision": verification.officer_decision,
            "officer_notes": verification.officer_notes,
            "verified_at": verification.verified_at.isoformat() if verification.verified_at else None,
            "reviewed_by_id": str(verification.verified_by_id) if verification.verified_by_id else None,
        }
    else:
        ai_results["quality"] = None
        ai_results["officer_review"] = None

    return ai_results


@router.post(
    "/review/{document_id}",
    response_model=OfficerReviewResponse,
    summary="[Officer] Submit manual review decision for a document",
)
def submit_officer_review(
    document_id: str,
    body: OfficerReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Officer submits their manual verification decision for a document.

    This is the ONLY way a document can be marked Verified or Rejected.
    AI CANNOT set officer_decision. This endpoint is officer-only.

    decision: "accepted" | "rejected"
    """
    _require_officer(current_user)

    if body.decision not in ("accepted", "rejected"):
        raise HTTPException(
            status_code=422,
            detail="decision must be 'accepted' or 'rejected'.",
        )

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.status not in (DocumentStatus.PROCESSED, DocumentStatus.VERIFIED, DocumentStatus.REJECTED):
        raise HTTPException(
            status_code=400,
            detail=f"Document is in status '{doc.status.value}'. It must be processed before review.",
        )

    # Update document status
    doc.status = DocumentStatus.VERIFIED if body.decision == "accepted" else DocumentStatus.REJECTED

    # Update or create verification result
    verification = (
        db.query(DocumentVerificationResult)
        .filter(DocumentVerificationResult.document_id == doc.id)
        .order_by(DocumentVerificationResult.created_at.desc())
        .first()
    )

    now = datetime.now(timezone.utc)

    if verification:
        verification.officer_decision = body.decision
        verification.officer_notes = body.officer_notes
        verification.verified_by_id = current_user.id
        verification.verified_at = now
    else:
        # Create a manual-only verification record (no AI data)
        db.add(DocumentVerificationResult(
            document_id=doc.id,
            verified_by_id=current_user.id,
            officer_decision=body.decision,
            officer_notes=body.officer_notes,
            verified_at=now,
            ai_notes="Manual review only (no AI processing performed).",
        ))

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role="officer",
        action="DOCUMENT_OFFICER_REVIEW",
        resource_type="document",
        resource_id=doc.id,
        details={
            "decision": body.decision,
            "notes": body.officer_notes,
        },
    ))
    db.commit()

    return OfficerReviewResponse(
        document_id=document_id,
        officer_decision=body.decision,
        reviewed_by=str(current_user.id),
        reviewed_at=now,
        note="Officer decision recorded. This is the authoritative verification outcome.",
    )


@router.get(
    "/application/{application_id}",
    summary="[Officer] Get all document processing statuses for an application",
)
def get_application_processing_status(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Returns processing status summary for all documents in an application. Officer-only."""
    _require_officer(current_user)

    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    docs = db.query(Document).filter(Document.application_id == application_id).all()

    summaries = []
    for doc in docs:
        vr = (
            db.query(DocumentVerificationResult)
            .filter(DocumentVerificationResult.document_id == doc.id)
            .order_by(DocumentVerificationResult.created_at.desc())
            .first()
        )
        summaries.append({
            "document_id": str(doc.id),
            "document_type": doc.document_type.value,
            "filename": doc.original_filename,
            "status": doc.status.value,
            "malware_scan_status": doc.malware_scan_status.value,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "ai_quality_score": float(vr.quality_score) if vr and vr.quality_score else None,
            "anomaly_count": len(vr.anomaly_flags or []) if vr else 0,
            "officer_decision": vr.officer_decision if vr else None,
            "requires_review": doc.status == DocumentStatus.PROCESSED and (not vr or not vr.officer_decision),
        })

    return {
        "application_id": application_id,
        "application_status": app.status.value,
        "documents": summaries,
        "total": len(summaries),
        "pending_review": sum(1 for s in summaries if s["requires_review"]),
        "ai_disclaimer": "AI quality scores and anomaly flags are SUGGESTIONS. Officer decisions are authoritative.",
    }


@router.post(
    "/consistency/{application_id}",
    summary="[Officer] Trigger cross-document consistency analysis",
)
def trigger_consistency_check(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Trigger cross-document consistency analysis for an application.
    Officer-only. Results are AI SUGGESTIONS stored as anomaly_flags.
    """
    _require_officer(current_user)

    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    try:
        from tasks.document_pipeline import check_consistency
        check_consistency.apply_async(args=[application_id])
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Task queue unavailable: {e}. Ensure Celery worker is running.",
        )

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role="officer",
        action="CONSISTENCY_CHECK_TRIGGERED",
        resource_type="application",
        resource_id=app.id,
        details={"triggered_by": str(current_user.id)},
    ))
    db.commit()

    return {
        "application_id": application_id,
        "task": "started",
        "message": "Cross-document consistency analysis triggered. Results are AI SUGGESTIONS requiring officer review.",
    }
