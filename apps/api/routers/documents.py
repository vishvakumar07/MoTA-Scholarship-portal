"""
Document upload router - /api/v1/documents/*

POST /api/v1/documents/upload            - Upload a document for an application
GET  /api/v1/documents/{application_id}  - List documents for an application
POST /api/v1/documents/{doc_id}/resubmit - Resubmit a superseded/rejected document
"""

from __future__ import annotations

import hashlib
import uuid as _uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from database import get_db
from models.application import Application, ApplicationStatus
from models.document import Document, DocumentStatus, DocumentType, MalwareScanStatus
from schemas.application import DocumentOut, DocumentListResponse
from models.system import AuditLog
from fastapi.responses import StreamingResponse
import urllib.parse
from security.rbac import get_current_user
from models.user import User
from storage.local import get_storage_service

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB default


def _doc_to_out(doc: Document) -> DocumentOut:
    return DocumentOut(
        id=str(doc.id),
        document_type=doc.document_type.value,
        original_filename=doc.original_filename,
        file_size_bytes=doc.file_size_bytes,
        mime_type=doc.mime_type,
        status=doc.status.value,
        malware_scan_status=doc.malware_scan_status.value,
        uploaded_at=doc.uploaded_at,
    )


@router.post(
    "/upload",
    summary="Upload a document for an application",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    application_id: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a document (PDF, JPG, PNG) for a specific application.

    - Documents must be under 10 MB (configurable per scheme).
    - Accepted formats: PDF, JPG, JPEG, PNG.
    - Files are stored securely; never served as public static assets.
    - Old rejected/superseded versions are retained in the audit trail.
    """
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.applicant_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    if app.status not in (
        ApplicationStatus.DRAFT,
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.DEFICIENCY,
        ApplicationStatus.RESUBMITTED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot upload documents for application in status: {app.status.value}",
        )

    # Validate document type
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid document type: {document_type}",
        )

    # Validate MIME type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}. Allowed: PDF, JPG, PNG.",
        )

    # Path traversal and null byte prevention in filename
    raw_filename = file.filename or "upload"
    if "\x00" in raw_filename or ".." in raw_filename or "/" in raw_filename or "\\" in raw_filename:
        # Check if strictly a path traversal attempt
        if "\x00" in raw_filename or ".." in raw_filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename: path traversal sequences or null bytes detected.",
            )
    safe_filename = Path(raw_filename).name

    # Read file
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum allowed: 10 MB.",
        )

    # Magic Bytes / File Signature Verification (Phase 8 Hardening)
    MAGIC_SIGNATURES = {
        "application/pdf": [b"%PDF-"],
        "image/jpeg": [b"\xff\xd8\xff"],
        "image/jpg": [b"\xff\xd8\xff"],
        "image/png": [b"\x89PNG\r\n\x1a\n"],
    }
    expected_signatures = MAGIC_SIGNATURES.get(content_type, [])
    if expected_signatures:
        if not any(file_bytes.startswith(sig) for sig in expected_signatures):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="File content does not match the declared MIME type signature.",
            )

    # SHA-256 content hash for deduplication
    content_hash = hashlib.sha256(file_bytes).hexdigest()

    # Mark previous versions of the same type as SUPERSEDED (if resubmitting)
    previous = db.query(Document).filter(
        Document.application_id == app.id,
        Document.document_type == doc_type,
        Document.status.in_([DocumentStatus.UPLOADED, DocumentStatus.PROCESSED, DocumentStatus.VERIFIED]),
    ).all()
    for prev in previous:
        prev.status = DocumentStatus.SUPERSEDED

    # Build storage key
    ext = ALLOWED_MIME_TYPES.get(content_type, "bin")
    storage_key = f"{app.id}/{doc_type.value}/{_uuid.uuid4()}.{ext}"

    # Upload to storage
    import io
    storage = get_storage_service()
    await storage.upload(io.BytesIO(file_bytes), storage_key, content_type)

    # Create Document record
    doc = Document(
        application_id=app.id,
        uploaded_by_id=current_user.id,
        document_type=doc_type,
        original_filename=safe_filename,
        storage_key=storage_key,
        file_size_bytes=len(file_bytes),
        mime_type=content_type,
        content_hash_sha256=content_hash,
        status=DocumentStatus.UPLOADED,
        malware_scan_status=MalwareScanStatus.UNAVAILABLE,  # ClamAV not configured in prototype
    )
    db.add(doc)
    # Record AuditLog
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role="applicant",
        action="DOCUMENT_UPLOADED",
        resource_type="document",
        resource_id=doc.id,
        details={
            "application_id": str(app.id),
            "document_type": doc_type.value,
            "filename": doc.original_filename,
            "file_size_bytes": doc.file_size_bytes,
        },
    ))
    db.commit()
    db.refresh(doc)

    return {
        "uploaded": True,
        "document_id": str(doc.id),
        "document_type": doc_type.value,
        "status": doc.status.value,
        "malware_scan_status": doc.malware_scan_status.value,
        "malware_scan_note": "Malware scanning requires ClamAV configuration. Not available in prototype.",
        "original_filename": doc.original_filename,
        "file_size_bytes": doc.file_size_bytes,
    }


@router.get(
    "/{application_id}",
    response_model=DocumentListResponse,
    summary="List all documents uploaded for an application",
)
def list_documents(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.applicant_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    docs = (
        db.query(Document)
        .filter(Document.application_id == app.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    return DocumentListResponse(
        documents=[_doc_to_out(d) for d in docs],
        total=len(docs),
    )



@router.get(
    "/{document_id}/download",
    summary="Download or stream an uploaded document with strict access control",
)
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    app = db.query(Application).filter(Application.id == doc.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Associated application not found.")

    # Strict IDOR Access Control: Only the owning applicant or authorized officials may access
    is_owner = app.applicant_id == current_user.id
    user_roles = [r.name for r in getattr(current_user, "roles", [])]
    is_staff = any(r in ["super_admin", "scheme_admin", "scrutiny_officer", "verification_officer"] for r in user_roles)
    if not is_owner and not is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You are not authorized to access this document.",
        )

    storage = get_storage_service()
    try:
        stream = await storage.download(doc.storage_key)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found in storage: {str(e)}")

    filename_encoded = urllib.parse.quote(doc.original_filename)
    return StreamingResponse(
        stream,
        media_type=doc.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{filename_encoded}",
            "X-Content-Type-Options": "nosniff",
        },
    )
