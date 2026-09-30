"""
Application router --- /api/v1/applications/*

POST /api/v1/applications/start            --- Start a draft application
GET  /api/v1/applications                  --- List my applications
GET  /api/v1/applications/{id}             --- Get application detail + form
PUT  /api/v1/applications/{id}/save        --- Autosave draft answers
POST /api/v1/applications/{id}/submit      --- Submit application
GET  /api/v1/applications/{id}/timeline    --- Get workflow timeline

POST /api/v1/applications/eligibility-check --- Eligibility pre-check (before applying)
"""

from __future__ import annotations

import hashlib
import uuid as _uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.application import Application, ApplicationAnswer, ApplicationStatus, ApplicationStatusHistory
from models.scheme import SchemeVersion, SchemeFormField, Scheme, SchemeDocument
from models.document import Document, DocumentStatus
from models.system import AuditLog, Notification, NotificationChannel, NotificationStatus
from models.workflow import Deficiency, DeficiencyStatus
from schemas.application import (
    ApplicationDetailOut,
    ApplicationListItem,
    ApplicationListResponse,
    ApplicationSaveRequest,
    ApplicationStartRequest,
    ApplicationStartResponse,
    ApplicationSubmitRequest,
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    ApplicationAnswerOut,
    FormFieldOut,
    StatusHistoryItem,
    DeficiencyResponseRequest,
)
from security.rbac import get_current_user
from models.user import User
from services.rule_engine import RuleEngineService

router = APIRouter(prefix="/applications", tags=["Applications"])


def _generate_reference(scheme_code: str) -> str:
    """Generate a human-readable reference number."""
    import random, string
    now = datetime.now(timezone.utc)
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"MOTA/{scheme_code}/{now.year}/{suffix}"


def _application_to_detail(app: Application, db: Session) -> ApplicationDetailOut:
    answers = []
    for a in (app.answers or []):
        answers.append(ApplicationAnswerOut(
            field_key=a.field_key,
            answer_value=a.answer_value,
            form_field_id=str(a.form_field_id),
        ))

    history = []
    for h in sorted(app.status_history or [], key=lambda x: x.changed_at):
        history.append(StatusHistoryItem(
            from_status=h.from_status,
            to_status=h.to_status,
            changed_at=h.changed_at,
            change_reason=h.change_reason,
            system_note=h.system_note,
        ))

    return ApplicationDetailOut(
        id=str(app.id),
        reference_number=app.reference_number,
        status=app.status.value,
        scheme_version_id=str(app.scheme_version_id),
        submitted_at=app.submitted_at,
        answers=answers,
        status_history=history,
    )


@router.post(
    "/eligibility-check",
    response_model=EligibilityCheckResponse,
    summary="Run eligibility pre-check for a scheme (before applying)",
)
def eligibility_pre_check(
    body: EligibilityCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Evaluates the applicant''s answers against the scheme''s rules.

    Result is preliminary only --- NOT a final determination.
    Final eligibility is always determined by authorised MoTA officers.
    """
    version = db.query(SchemeVersion).filter(
        SchemeVersion.id == body.scheme_version_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Scheme version not found.")

    rules = version.rules
    rule_engine = RuleEngineService()
    results = rule_engine.evaluate_rules(rules, body.answers)

    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    pending = sum(1 for r in results if r.status not in ("PASS", "FAIL"))

    hard_fails = [r for r in results if r.status == "FAIL" and r.severity == "HARD_STOP"]
    if hard_fails:
        overall = "likely_ineligible"
    elif failed > 0:
        overall = "requires_verification"
    else:
        overall = "likely_eligible"

    return EligibilityCheckResponse(
        overall=overall,
        passed_count=passed,
        failed_count=failed,
        pending_count=pending,
        rule_results=[r.to_dict() for r in results],
    )


@router.post(
    "/start",
    response_model=ApplicationStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new draft application for a scheme",
)
def start_application(
    body: ApplicationStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a DRAFT application for the given scheme version.
    Only one DRAFT per applicant per scheme version is allowed.
    """
    version = db.query(SchemeVersion).filter(
        SchemeVersion.id == body.scheme_version_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Scheme version not found.")
    if not version.is_accepting_applications:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This scheme version is not currently accepting applications.",
        )

    # Prevent duplicate DRAFT
    existing_draft = db.query(Application).filter(
        Application.applicant_id == current_user.id,
        Application.scheme_version_id == version.id,
        Application.status == ApplicationStatus.DRAFT,
    ).first()
    if existing_draft:
        return ApplicationStartResponse(
            application_id=str(existing_draft.id),
            reference_number=existing_draft.reference_number,
            status=existing_draft.status.value,
            scheme_version_id=str(existing_draft.scheme_version_id),
        )

    app = Application(
        applicant_id=current_user.id,
        scheme_version_id=version.id,
        status=ApplicationStatus.DRAFT,
    )
    db.add(app)
    db.flush()

    # Initial status history entry
    hist = ApplicationStatusHistory(
        application_id=app.id,
        from_status=None,
        to_status=ApplicationStatus.DRAFT.value,
        system_note="Application draft started by applicant.",
    )
    db.add(hist)
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role="applicant",
        action="APPLICATION_DRAFT_CREATED",
        resource_type="application",
        resource_id=app.id,
        details={"scheme_version_id": str(version.id)},
    ))
    db.commit()
    db.refresh(app)

    return ApplicationStartResponse(
        application_id=str(app.id),
        reference_number=app.reference_number,
        status=app.status.value,
        scheme_version_id=str(app.scheme_version_id),
    )


@router.get(
    "",
    response_model=ApplicationListResponse,
    summary="List all applications for the current applicant",
)
def list_applications(
    status: Any = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_roles = [r.name for r in getattr(current_user, "roles", [])]
    is_staff = any(r in ["super_admin", "scheme_admin", "scrutiny_officer", "verification_officer"] for r in user_roles)

    query = db.query(Application)
    if not is_staff:
        # Strict applicant scoping: only own applications
        query = query.filter(Application.applicant_id == current_user.id)
    elif status:
        query = query.filter(Application.status == status)

    total = query.count()
    apps = query.order_by(Application.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for a in apps:
        scheme_code = None
        scheme_name = None
        if a.scheme_version_id:
            version = db.query(SchemeVersion).filter(
                SchemeVersion.id == a.scheme_version_id
            ).first()
            if version:
                scheme = db.query(Scheme).filter(Scheme.id == version.scheme_id).first()
                if scheme:
                    scheme_code = scheme.code
                    scheme_name = scheme.name

        items.append(ApplicationListItem(
            id=str(a.id),
            reference_number=a.reference_number,
            status=a.status.value,
            submitted_at=a.submitted_at,
            scheme_code=scheme_code,
            scheme_name=scheme_name,
            scheme_version_id=str(a.scheme_version_id),
        ))

    return ApplicationListResponse(applications=items, total=total)


@router.get(
    "/{application_id}",
    summary="Get application detail including form fields and answers",
)
def get_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the application, its answers, status history, and the form definition."""
    app = (
        db.query(Application)
        .options(joinedload(Application.answers), joinedload(Application.status_history))
        .filter(Application.id == application_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    user_roles = [r.name for r in getattr(current_user, "roles", [])]
    is_staff = any(r in ["super_admin", "scheme_admin", "scrutiny_officer", "verification_officer"] for r in user_roles)
    is_owner = app.applicant_id == current_user.id
    if not is_owner and not is_staff:
        # IDOR protection: applicant cannot view another applicant's application
        raise HTTPException(status_code=404, detail="Application not found.")
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Load form fields for this scheme version
    form_fields = (
        db.query(SchemeFormField)
        .filter(
            SchemeFormField.version_id == app.scheme_version_id,
            SchemeFormField.is_deleted == False,
        )
        .order_by(SchemeFormField.display_order)
        .all()
    )

    # Build answer map
    answer_map = {a.field_key: a.answer_value for a in app.answers}

    # Load deficiencies
    deficiencies = (
        db.query(Deficiency)
        .filter(
            Deficiency.application_id == app.id,
            Deficiency.status == DeficiencyStatus.OPEN,
        )
        .all()
    )

    scheme_docs = (
        db.query(SchemeDocument)
        .filter(
            SchemeDocument.version_id == app.scheme_version_id,
            SchemeDocument.is_deleted == False,
        )
        .order_by(SchemeDocument.display_order)
        .all()
    )

    detail = _application_to_detail(app, db)

    return {
        "application": detail.model_dump(),
        "required_documents": [
            {
                "id": str(sd.id),
                "document_type_code": sd.document_type_code,
                "document_display_name": sd.document_display_name,
                "description": sd.description,
                "is_mandatory": sd.is_mandatory,
                "accepted_formats": sd.accepted_formats,
                "max_size_mb": sd.max_size_mb,
            }
            for sd in scheme_docs
        ],
        "form_fields": [
            FormFieldOut(
                id=str(f.id),
                field_key=f.field_key,
                field_label=f.field_label,
                field_type=f.field_type,
                is_required=f.is_required,
                section=f.section,
                display_order=f.display_order,
                options=f.options,
                validation_rules=f.validation_rules,
                help_text=f.help_text,
                conditional_logic=f.conditional_logic,
            ).model_dump()
            for f in form_fields
        ],
        "open_deficiencies": [
            {
                "id": str(d.id),
                "deficiency_type": d.deficiency_type.value if hasattr(d.deficiency_type, "value") else d.deficiency_type,
                "description": d.description,
                "affected_document_type": d.document_type_requested,
                "officer_comment": None,  # officer_comment not exposed to applicants by default
                "response_deadline": d.response_deadline.isoformat() if d.response_deadline else None,
                "status": d.status.value,
            }
            for d in deficiencies
        ],
    }


@router.put(
    "/{application_id}/save",
    summary="Autosave draft answers",
)
def save_draft(
    application_id: str,
    body: ApplicationSaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Autosave form answers for a DRAFT application.
    Upserts answers --- existing answers for the same field_key are replaced.
    """
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.applicant_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    if app.status != ApplicationStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit application in status: {app.status.value}",
        )

    # Load form field IDs for validation
    form_fields = db.query(SchemeFormField).filter(
        SchemeFormField.version_id == app.scheme_version_id,
        SchemeFormField.is_deleted == False,
    ).all()
    field_map = {f.field_key: f for f in form_fields}

    for ans_in in body.answers:
        if ans_in.field_key not in field_map:
            continue  # Skip unknown fields silently

        existing = db.query(ApplicationAnswer).filter(
            ApplicationAnswer.application_id == app.id,
            ApplicationAnswer.field_key == ans_in.field_key,
        ).first()

        if existing:
            existing.answer_value = ans_in.answer_value if isinstance(ans_in.answer_value, (dict, list)) else {"value": ans_in.answer_value}
        else:
            db.add(ApplicationAnswer(
                application_id=app.id,
                form_field_id=field_map[ans_in.field_key].id,
                field_key=ans_in.field_key,
                answer_value=ans_in.answer_value if isinstance(ans_in.answer_value, (dict, list)) else {"value": ans_in.answer_value},
            ))

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role="applicant",
        action="APPLICATION_DRAFT_SAVED",
        resource_type="application",
        resource_id=app.id,
        details={"answers_count": len(body.answers)},
    ))
    db.commit()
    return {"saved": True, "application_id": application_id}


@router.post(
    "/{application_id}/submit",
    summary="Submit a draft application",
)
def submit_application(
    application_id: str,
    body: ApplicationSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Validates and submits the application.
    - Required fields must have answers
    - Status changes from DRAFT to SUBMITTED
    - Generates a reference number
    - Records a status history entry
    """
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.applicant_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    if app.status != ApplicationStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application is already in status: {app.status.value}",
        )

    # Enforce mandatory statutory applicant declaration
    if not body.declaration_accepted:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mandatory statutory applicant declaration must be accepted prior to submission.",
        )

    # Save final answers
    form_fields = db.query(SchemeFormField).filter(
        SchemeFormField.version_id == app.scheme_version_id,
        SchemeFormField.is_deleted == False,
    ).all()
    field_map = {f.field_key: f for f in form_fields}

    for ans_in in body.answers:
        if ans_in.field_key not in field_map:
            continue
        existing = db.query(ApplicationAnswer).filter(
            ApplicationAnswer.application_id == app.id,
            ApplicationAnswer.field_key == ans_in.field_key,
        ).first()
        val = ans_in.answer_value if isinstance(ans_in.answer_value, (dict, list)) else {"value": ans_in.answer_value}
        if existing:
            existing.answer_value = val
        else:
            db.add(ApplicationAnswer(
                application_id=app.id,
                form_field_id=field_map[ans_in.field_key].id,
                field_key=ans_in.field_key,
                answer_value=val,
            ))

    db.flush()

    # Validate required fields
    answer_keys = {
        a.field_key for a in db.query(ApplicationAnswer).filter(
            ApplicationAnswer.application_id == app.id
        ).all()
        if a.answer_value and a.answer_value != {"value": None} and a.answer_value != {"value": ""}
    }
    missing = [f.field_label for f in form_fields if f.is_required and f.field_key not in answer_keys]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Required fields missing: {missing}",
        )

    # Get scheme code for reference number
    version = db.query(SchemeVersion).filter(SchemeVersion.id == app.scheme_version_id).first()
    scheme = db.query(Scheme).filter(Scheme.id == version.scheme_id).first() if version else None
    scheme_code = scheme.code if scheme else "MOTA"

    # Transition to SUBMITTED
    prev_status = app.status.value
    app.status = ApplicationStatus.SUBMITTED
    app.submitted_at = datetime.now(timezone.utc)
    app.reference_number = _generate_reference(scheme_code)

    # Enforce server-side required documents check from scheme version
    mandatory_docs = db.query(SchemeDocument).filter(
        SchemeDocument.version_id == app.scheme_version_id,
        SchemeDocument.is_mandatory == True,
        SchemeDocument.is_deleted == False,
    ).all()
    if mandatory_docs:
        uploaded_types = {
            doc.document_type.value for doc in db.query(Document).filter(
                Document.application_id == app.id,
                Document.status.in_([DocumentStatus.UPLOADED, DocumentStatus.PROCESSED, DocumentStatus.VERIFIED]),
            ).all()
        }
        missing_docs = [sd.document_display_name for sd in mandatory_docs if sd.document_type_code not in uploaded_types]
        if missing_docs:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Mandatory documents missing: {missing_docs}",
            )

    hist = ApplicationStatusHistory(
        application_id=app.id,
        from_status=prev_status,
        to_status=ApplicationStatus.SUBMITTED.value,
        system_note="Application submitted by applicant. Pending document processing.",
    )
    db.add(hist)

    # Immutable Audit Log
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role="applicant",
        action="APPLICATION_SUBMITTED",
        resource_type="application",
        resource_id=app.id,
        details={"reference_number": app.reference_number, "scheme_version_id": str(app.scheme_version_id)},
    ))

    # Official Notification
    db.add(Notification(
        recipient_id=current_user.id,
        channel=NotificationChannel.IN_APP,
        status=NotificationStatus.SENT,
        title=f"Application Submitted - Ref: {app.reference_number}",
        body=f"Your scholarship application ({app.reference_number}) has been successfully submitted and forwarded to verification officers for scrutiny.",
        action_url=f"/applications/{app.id}",
        related_entity_type="application",
        related_entity_id=app.id,
        sent_at=datetime.now(timezone.utc),
    ))

    db.commit()
    db.refresh(app)

    return {
        "submitted": True,
        "reference_number": app.reference_number,
        "status": app.status.value,
        "submitted_at": app.submitted_at.isoformat(),
    }


@router.get(
    "/{application_id}/timeline",
    summary="Get application workflow timeline",
)
def get_timeline(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the ordered status history for the application as a visual timeline.
    Only includes stages that have been reached.
    """
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.applicant_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    history = (
        db.query(ApplicationStatusHistory)
        .filter(ApplicationStatusHistory.application_id == app.id)
        .order_by(ApplicationStatusHistory.changed_at.asc())
        .all()
    )

    # Status display metadata
    STATUS_META = {
        "draft": {"label": "Draft", "icon": "edit", "description": "Application being prepared"},
        "submitted": {"label": "Submitted", "icon": "send", "description": "Application received"},
        "document_processing": {"label": "Document Processing", "icon": "file-scan", "description": "Documents being processed"},
        "document_verification": {"label": "Document Verification", "icon": "file-check", "description": "Documents under officer review"},
        "deficiency": {"label": "Deficiency Raised", "icon": "alert-triangle", "description": "Action required from applicant"},
        "resubmitted": {"label": "Documents Resubmitted", "icon": "refresh-cw", "description": "Corrected documents submitted"},
        "eligibility_review": {"label": "Eligibility Review", "icon": "clipboard-check", "description": "Eligibility being assessed"},
        "eligible": {"label": "Eligible", "icon": "check-circle", "description": "Declared eligible"},
        "ineligible": {"label": "Ineligible", "icon": "x-circle", "description": "Declared ineligible"},
        "scrutiny": {"label": "Scrutiny", "icon": "search", "description": "Under detailed scrutiny"},
        "shortlisted": {"label": "Shortlisted", "icon": "list", "description": "Shortlisted for selection"},
        "selection_review": {"label": "Selection Review", "icon": "users", "description": "Selection committee review"},
        "selected": {"label": "Selected", "icon": "award", "description": "Selected for scholarship"},
        "not_selected": {"label": "Not Selected", "icon": "minus-circle", "description": "Not selected this cycle"},
        "post_selection": {"label": "Post-Selection", "icon": "clipboard", "description": "Post-selection processing"},
        "completed": {"label": "Completed", "icon": "check-circle-2", "description": "Scholarship disbursed"},
        "withdrawn": {"label": "Withdrawn", "icon": "log-out", "description": "Application withdrawn"},
    }

    timeline = []
    for h in history:
        meta = STATUS_META.get(h.to_status, {"label": h.to_status, "icon": "circle", "description": ""})
        timeline.append({
            "status": h.to_status,
            "label": meta["label"],
            "icon": meta["icon"],
            "description": meta["description"],
            "reached_at": h.changed_at.isoformat(),
            "change_reason": h.change_reason,
            "system_note": h.system_note,
            "is_current": h.to_status == app.status.value,
        })

    return {
        "application_id": application_id,
        "reference_number": app.reference_number,
        "current_status": app.status.value,
        "timeline": timeline,
    }



@router.post(
    "/{application_id}/deficiencies/{deficiency_id}/respond",
    summary="Respond to an open deficiency",
)
def respond_to_deficiency(
    application_id: str,
    deficiency_id: str,
    body: DeficiencyResponseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Applicant responds to an open deficiency with an explanation/clarification note.
    If all open deficiencies for this application are responded to,
    the application status automatically transitions from DEFICIENCY to RESUBMITTED.
    """
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.applicant_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    deficiency = db.query(Deficiency).filter(
        Deficiency.id == deficiency_id,
        Deficiency.application_id == app.id,
    ).first()
    if not deficiency:
        raise HTTPException(status_code=404, detail="Deficiency not found.")

    if deficiency.status != DeficiencyStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Deficiency is already in status: {deficiency.status.value}",
        )

    if not body.response_note or not body.response_note.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A clarification or response note is required.",
        )

    # If an officer requested a specific document, verify that a replacement was uploaded
    if deficiency.document_type_requested:
        has_replacement = (
            db.query(Document)
            .filter(
                Document.application_id == app.id,
                Document.document_type == deficiency.document_type_requested,
                Document.uploaded_at >= deficiency.created_at,
                Document.status.in_([DocumentStatus.UPLOADED, DocumentStatus.PROCESSED, DocumentStatus.VERIFIED]),
            )
            .first()
        )
        if not has_replacement:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Please upload the requested replacement document ({deficiency.document_type_requested}) before submitting this deficiency response.",
            )

    deficiency.applicant_response = body.response_note
    deficiency.status = DeficiencyStatus.RESPONDED
    deficiency.resolved_at = datetime.now(timezone.utc)

    # Audit log
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role="applicant",
        action="DEFICIENCY_RESPONDED",
        resource_type="deficiency",
        resource_id=deficiency.id,
        details={"application_id": str(app.id), "response_note": body.response_note[:200]},
    ))

    # Official in-app notification
    db.add(Notification(
        recipient_id=current_user.id,
        channel=NotificationChannel.IN_APP,
        status=NotificationStatus.SENT,
        title=f"Deficiency Response Received - Ref: {app.reference_number}",
        body=f"Your response to the deficiency notice for application {app.reference_number} has been recorded and submitted for re-scrutiny.",
        action_url=f"/applications/{app.id}",
        related_entity_type="application",
        related_entity_id=app.id,
        sent_at=datetime.now(timezone.utc),
    ))

    # Check remaining open deficiencies
    remaining_open = (
        db.query(Deficiency)
        .filter(
            Deficiency.application_id == app.id,
            Deficiency.status == DeficiencyStatus.OPEN,
            Deficiency.id != deficiency.id,
        )
        .count()
    )

    prev_status = app.status.value
    if remaining_open == 0 and app.status == ApplicationStatus.DEFICIENCY:
        app.status = ApplicationStatus.RESUBMITTED
        hist = ApplicationStatusHistory(
            application_id=app.id,
            from_status=prev_status,
            to_status=ApplicationStatus.RESUBMITTED.value,
            change_reason="Applicant responded to deficiency notification.",
            system_note="All open deficiencies addressed. Application moved to resubmitted verification queue.",
        )
        db.add(hist)

    db.commit()
    db.refresh(deficiency)
    return {
        "success": True,
        "deficiency_id": str(deficiency.id),
        "status": deficiency.status.value,
        "application_status": app.status.value,
        "message": "Deficiency response submitted successfully.",
    }