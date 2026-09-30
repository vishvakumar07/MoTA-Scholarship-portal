"""
Case Management & Operational Work Queue Router - Phase 9.

Endpoints:
  GET  /api/v1/admin/work-queue
  POST /api/v1/admin/applications/{application_id}/assign
  GET  /api/v1/admin/applications/{application_id}/notes
  POST /api/v1/admin/applications/{application_id}/notes
  POST /api/v1/admin/applications/{application_id}/deficiency
  POST /api/v1/admin/deficiencies/{deficiency_id}/resolve
  GET  /api/v1/admin/applications/{application_id}/timeline
  GET  /api/v1/applications/{application_id}/timeline
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.application import Application, ApplicationStatus, ApplicationStatusHistory
from models.case import CaseAssignment, CaseAssignmentStatus, CaseNote, CasePriority, TimelineEventType
from models.document import Document, DocumentStatus
from models.scheme import Scheme, SchemeVersion
from models.system import AuditLog, NotificationChannel
from models.user import Role, User, UserRole
from models.workflow import Deficiency, DeficiencyStatus
from security.rbac import get_current_user, require_roles
from services.notification_service import NotificationCategory, NotificationService
from services.timeline_service import CaseTimelineService

router = APIRouter(tags=["Case Management & Work Queue (Phase 9)"])

OFFICER_ROLES = ["super_admin", "scheme_admin", "scrutiny_officer", "verification_officer"]
_require_officer = require_roles(OFFICER_ROLES)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class AssignCaseRequest(BaseModel):
    assigned_to_id: str
    priority: str = "normal"  # "normal" | "high" | "urgent"
    notes: Optional[str] = None


class AddCaseNoteRequest(BaseModel):
    note: str
    is_internal: bool = True


class RaiseDeficiencyRequest(BaseModel):
    description: str
    document_type_requested: Optional[str] = None
    response_deadline: Optional[date] = None


class CaseNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    application_id: str
    author_id: str
    author_name: str
    note: str
    is_internal: bool
    created_at: datetime


class WorkQueueItem(BaseModel):
    id: str
    reference_number: Optional[str] = None
    applicant_name: str
    scheme_code: str
    scheme_name: str
    status: str
    priority: str
    assigned_officer_id: Optional[str] = None
    assigned_officer_name: Optional[str] = None
    pending_documents_count: int
    open_deficiencies_count: int
    submitted_at: Optional[datetime] = None
    updated_at: datetime


class WorkQueueResponse(BaseModel):
    items: list[WorkQueueItem]
    total: int


# ---------------------------------------------------------------------------
# Work Queue (Admin / Officer)
# ---------------------------------------------------------------------------
@router.get(
    "/admin/work-queue",
    response_model=WorkQueueResponse,
    summary="[Officer] Operational work queue of cases needing review",
)
def get_work_queue(
    assigned: Optional[str] = Query(None, description="'me', 'unassigned', or all"),
    priority: Optional[str] = Query(None, description="'normal', 'high', 'urgent'"),
    status: Optional[str] = Query(None, description="Filter by application status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(_require_officer),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Application)
        .filter(Application.status != ApplicationStatus.DRAFT)
    )

    if assigned == "me":
        query = query.filter(Application.assigned_officer_id == current_user.id)
    elif assigned == "unassigned":
        query = query.filter(Application.assigned_officer_id == None)

    if status:
        query = query.filter(Application.status == status)

    total = query.count()
    apps = query.order_by(Application.created_at.desc()).offset(offset).limit(limit).all()

    items: list[WorkQueueItem] = []
    for app in apps:
        # Applicant details
        applicant = db.query(User).filter(User.id == app.applicant_id).first()
        applicant_name = applicant.full_name if applicant else "Applicant"

        # Scheme details
        scheme_code = "SCHEME"
        scheme_name = "MoTA Scholarship Scheme"
        if app.scheme_version_id:
            version = db.query(SchemeVersion).filter(SchemeVersion.id == app.scheme_version_id).first()
            if version:
                scheme = db.query(Scheme).filter(Scheme.id == version.scheme_id).first()
                if scheme:
                    scheme_code = scheme.code
                    scheme_name = scheme.name

        # Assigned officer details
        assigned_name = None
        if app.assigned_officer_id:
            officer = db.query(User).filter(User.id == app.assigned_officer_id).first()
            assigned_name = officer.full_name if officer else "Assigned Officer"

        # Priority from latest assignment
        latest_assignment = (
            db.query(CaseAssignment)
            .filter(CaseAssignment.application_id == app.id)
            .order_by(CaseAssignment.assigned_at.desc())
            .first()
        )
        case_prio = latest_assignment.priority.value if latest_assignment else "normal"

        if priority and case_prio != priority:
            continue

        # Open deficiencies & pending documents
        open_defs = db.query(Deficiency).filter(
            Deficiency.application_id == app.id,
            Deficiency.status == DeficiencyStatus.OPEN,
        ).count()

        pending_docs = db.query(Document).filter(
            Document.application_id == app.id,
            Document.status.in_([DocumentStatus.UPLOADED, DocumentStatus.PROCESSING]),
        ).count()

        items.append(
            WorkQueueItem(
                id=str(app.id),
                reference_number=app.reference_number,
                applicant_name=applicant_name,
                scheme_code=scheme_code,
                scheme_name=scheme_name,
                status=app.status.value,
                priority=case_prio,
                assigned_officer_id=str(app.assigned_officer_id) if app.assigned_officer_id else None,
                assigned_officer_name=assigned_name,
                pending_documents_count=pending_docs,
                open_deficiencies_count=open_defs,
                submitted_at=app.submitted_at,
                updated_at=app.updated_at or app.created_at,
            )
        )

    return WorkQueueResponse(items=items, total=total)


# ---------------------------------------------------------------------------
# Case Assignment
# ---------------------------------------------------------------------------
@router.post(
    "/admin/applications/{application_id}/assign",
    summary="[Officer] Assign an application case to an officer",
)
def assign_case(
    application_id: str,
    body: AssignCaseRequest,
    current_user: User = Depends(_require_officer),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(Application.id == uuid.UUID(application_id)).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    target_officer = db.query(User).filter(User.id == uuid.UUID(body.assigned_to_id)).first()
    if not target_officer:
        raise HTTPException(status_code=404, detail="Target officer user not found.")

    try:
        prio = CasePriority(body.priority.lower())
    except ValueError:
        prio = CasePriority.NORMAL

    app.assigned_officer_id = target_officer.id

    assignment = CaseAssignment(
        application_id=app.id,
        assigned_to_id=target_officer.id,
        assigned_by_id=current_user.id,
        status=CaseAssignmentStatus.ASSIGNED,
        priority=prio,
        notes=body.notes,
        assigned_at=datetime.now(timezone.utc),
    )
    db.add(assignment)

    # Audit log
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role="officer",
        action="CASE_ASSIGNED",
        resource_type="application",
        resource_id=app.id,
        details={
            "assigned_to": str(target_officer.id),
            "assigned_to_name": target_officer.full_name,
            "priority": prio.value,
        },
    ))

    # Officer in-app notification
    NotificationService.send_notification(
        db=db,
        recipient_id=target_officer.id,
        title=f"Case Assigned: {app.reference_number or 'Application'}",
        body=f"Application {app.reference_number or str(app.id)[:8]} has been assigned to you with {prio.value.upper()} priority for scrutiny.",
        category=NotificationCategory.REVIEW,
        action_url=f"/admin/applications/{app.id}",
        related_entity_type="application",
        related_entity_id=app.id,
    )

    # Record timeline event
    CaseTimelineService.record_event(
        db=db,
        application_id=app.id,
        event_type=TimelineEventType.OFFICER_ASSIGNED.value,
        title="Case Assigned to Scrutiny Officer",
        description=f"Case assigned to {target_officer.full_name} ({prio.value.upper()} priority).",
        actor_type="officer",
        actor_id=current_user.id,
        is_internal=True,
    )

    db.commit()

    return {
        "success": True,
        "application_id": str(app.id),
        "assigned_to": target_officer.full_name,
        "priority": prio.value,
        "message": f"Application assigned to {target_officer.full_name}.",
    }


# ---------------------------------------------------------------------------
# Case Notes (Officer Only)
# ---------------------------------------------------------------------------
@router.get(
    "/admin/applications/{application_id}/notes",
    summary="[Officer] List internal case notes for an application",
)
def list_case_notes(
    application_id: str,
    current_user: User = Depends(_require_officer),
    db: Session = Depends(get_db),
):
    notes = (
        db.query(CaseNote)
        .filter(CaseNote.application_id == uuid.UUID(application_id))
        .order_by(CaseNote.created_at.asc())
        .all()
    )

    results = []
    for n in notes:
        author = db.query(User).filter(User.id == n.author_id).first()
        results.append({
            "id": str(n.id),
            "application_id": str(n.application_id),
            "author_id": str(n.author_id),
            "author_name": author.full_name if author else "Officer",
            "note": n.note,
            "is_internal": n.is_internal,
            "created_at": n.created_at.isoformat(),
        })

    return {"notes": results, "total": len(results)}


@router.post(
    "/admin/applications/{application_id}/notes",
    summary="[Officer] Add an internal case note",
)
def add_case_note(
    application_id: str,
    body: AddCaseNoteRequest,
    current_user: User = Depends(_require_officer),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(Application.id == uuid.UUID(application_id)).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    if not body.note or not body.note.strip():
        raise HTTPException(status_code=400, detail="Note text cannot be empty.")

    case_note = CaseNote(
        application_id=app.id,
        author_id=current_user.id,
        note=body.note.strip(),
        is_internal=body.is_internal,
        created_at=datetime.now(timezone.utc),
    )
    db.add(case_note)

    # Audit log
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role="officer",
        action="CASE_NOTE_CREATED",
        resource_type="application",
        resource_id=app.id,
        details={"note_length": len(body.note)},
    ))

    # Internal timeline record
    CaseTimelineService.record_event(
        db=db,
        application_id=app.id,
        event_type=TimelineEventType.CASE_NOTE_ADDED.value,
        title="Officer Internal Note Added",
        description=f"Internal note recorded by {current_user.full_name}.",
        actor_type="officer",
        actor_id=current_user.id,
        is_internal=True,
    )

    db.commit()

    return {
        "success": True,
        "note_id": str(case_note.id),
        "created_at": case_note.created_at.isoformat(),
        "message": "Internal case note recorded successfully.",
    }


# ---------------------------------------------------------------------------
# Officer Raises Deficiency
# ---------------------------------------------------------------------------
@router.post(
    "/admin/applications/{application_id}/deficiency",
    summary="[Officer] Raise a deficiency notice requiring applicant action",
)
def raise_deficiency(
    application_id: str,
    body: RaiseDeficiencyRequest,
    current_user: User = Depends(_require_officer),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(Application.id == uuid.UUID(application_id)).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    if not body.description or not body.description.strip():
        raise HTTPException(status_code=400, detail="Deficiency description is required.")

    deficiency = Deficiency(
        application_id=app.id,
        raised_by_id=current_user.id,
        description=body.description.strip(),
        document_type_requested=body.document_type_requested,
        status=DeficiencyStatus.OPEN,
        response_deadline=body.response_deadline,
    )
    db.add(deficiency)

    # Transition application status to DEFICIENCY
    prev_status = app.status.value
    app.status = ApplicationStatus.DEFICIENCY

    db.add(ApplicationStatusHistory(
        application_id=app.id,
        from_status=prev_status,
        to_status=ApplicationStatus.DEFICIENCY.value,
        changed_by_id=current_user.id,
        change_reason=f"Deficiency raised: {body.description[:100]}",
        system_note="Application placed in deficiency pending applicant response.",
    ))

    # Audit log
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role="officer",
        action="DEFICIENCY_RAISED",
        resource_type="deficiency",
        resource_id=deficiency.id,
        details={
            "application_id": str(app.id),
            "document_type": body.document_type_requested,
            "deadline": str(body.response_deadline) if body.response_deadline else None,
        },
    ))

    # Applicant Notification
    doc_note = f" affecting document '{body.document_type_requested}'" if body.document_type_requested else ""
    NotificationService.send_notification(
        db=db,
        recipient_id=app.applicant_id,
        title=f"Deficiency Notice: Ref {app.reference_number or str(app.id)[:8]}",
        body=f"Action required{doc_note}: {body.description.strip()}. Please respond before the deadline.",
        category=NotificationCategory.DEFICIENCY,
        action_url=f"/applications/{app.id}",
        related_entity_type="application",
        related_entity_id=app.id,
    )

    # Timeline record
    CaseTimelineService.record_event(
        db=db,
        application_id=app.id,
        event_type=TimelineEventType.DEFICIENCY_RAISED.value,
        title="Deficiency Notice Issued",
        description=f"Officer requested correction: {body.description.strip()}",
        actor_type="officer",
        actor_id=current_user.id,
        is_internal=False,
        metadata={"deficiency_id": str(deficiency.id), "document_type": body.document_type_requested},
    )

    db.commit()
    db.refresh(deficiency)

    return {
        "success": True,
        "deficiency_id": str(deficiency.id),
        "status": deficiency.status.value,
        "application_status": app.status.value,
        "message": "Deficiency notice issued and applicant notified.",
    }


# ---------------------------------------------------------------------------
# Officer Resolves Deficiency
# ---------------------------------------------------------------------------
@router.post(
    "/admin/deficiencies/{deficiency_id}/resolve",
    summary="[Officer] Mark a deficiency as resolved after verifying applicant response",
)
def resolve_deficiency(
    deficiency_id: str,
    current_user: User = Depends(_require_officer),
    db: Session = Depends(get_db),
):
    deficiency = db.query(Deficiency).filter(Deficiency.id == uuid.UUID(deficiency_id)).first()
    if not deficiency:
        raise HTTPException(status_code=404, detail="Deficiency not found.")

    app = db.query(Application).filter(Application.id == deficiency.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Associated application not found.")

    deficiency.status = DeficiencyStatus.CLOSED
    deficiency.resolved_at = datetime.now(timezone.utc)

    # Check if all deficiencies are now closed
    remaining_open = (
        db.query(Deficiency)
        .filter(
            Deficiency.application_id == app.id,
            Deficiency.status == DeficiencyStatus.OPEN,
        )
        .count()
    )

    if remaining_open == 0 and app.status in (ApplicationStatus.DEFICIENCY, ApplicationStatus.RESUBMITTED):
        prev_status = app.status.value
        app.status = ApplicationStatus.DOCUMENT_VERIFICATION
        db.add(ApplicationStatusHistory(
            application_id=app.id,
            from_status=prev_status,
            to_status=ApplicationStatus.DOCUMENT_VERIFICATION.value,
            changed_by_id=current_user.id,
            change_reason="All open deficiencies resolved by scrutiny officer.",
            system_note="Application moved back to verification stage.",
        ))

    # Audit log
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role="officer",
        action="DEFICIENCY_RESOLVED",
        resource_type="deficiency",
        resource_id=deficiency.id,
        details={"application_id": str(app.id)},
    ))

    # Applicant Notification
    NotificationService.send_notification(
        db=db,
        recipient_id=app.applicant_id,
        title=f"Deficiency Resolved: Ref {app.reference_number or str(app.id)[:8]}",
        body=f"Your submitted clarification for {app.reference_number or 'your application'} has been reviewed and accepted by the scrutiny officer.",
        category=NotificationCategory.DEFICIENCY,
        action_url=f"/applications/{app.id}",
        related_entity_type="application",
        related_entity_id=app.id,
    )

    # Timeline event
    CaseTimelineService.record_event(
        db=db,
        application_id=app.id,
        event_type=TimelineEventType.DEFICIENCY_RESOLVED.value,
        title="Deficiency Resolved",
        description="Scrutiny officer confirmed deficiency resolution.",
        actor_type="officer",
        actor_id=current_user.id,
        is_internal=False,
    )

    db.commit()

    return {
        "success": True,
        "deficiency_id": str(deficiency.id),
        "status": deficiency.status.value,
        "application_status": app.status.value,
        "message": "Deficiency resolved successfully.",
    }


# ---------------------------------------------------------------------------
# Timeline Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/admin/applications/{application_id}/timeline",
    summary="[Officer] Complete operational case timeline including internal events",
)
def get_admin_case_timeline(
    application_id: str,
    current_user: User = Depends(_require_officer),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(Application.id == uuid.UUID(application_id)).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    events = CaseTimelineService.get_timeline(db, app.id, is_staff=True)
    return {"application_id": str(app.id), "timeline": events, "total": len(events)}


@router.get(
    "/applications/{application_id}/timeline",
    summary="[Applicant/Officer] Unified applicant-safe timeline",
)
def get_applicant_case_timeline(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(Application.id == uuid.UUID(application_id)).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    user_roles = [r.name for r in getattr(current_user, "roles", [])]
    is_staff = any(r in OFFICER_ROLES for r in user_roles)
    is_owner = app.applicant_id == current_user.id

    if not is_owner and not is_staff:
        # IDOR boundary: applicant cannot view another applicant's timeline
        raise HTTPException(status_code=404, detail="Application not found.")

    events = CaseTimelineService.get_timeline(db, app.id, is_staff=is_staff)
    return {"application_id": str(app.id), "timeline": events, "total": len(events)}
