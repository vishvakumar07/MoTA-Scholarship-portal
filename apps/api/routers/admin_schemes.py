"""
Admin Schemes Router  -  /api/v1/admin/schemes/*

Provides admin endpoints for managing scheme configuration, draft versioning,
publishing, rules, dynamic form fields, and rule preview evaluations.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.scheme import Scheme, SchemeVersion, SchemeRule, SchemeFormField, SchemeDocument, RuleSeverity, RuleType
from services.scheme_admin_service import SchemeAdminService
from services.rule_engine import RuleEngineService
from services.form_validator import FormValidationEngine
from security.rbac import require_roles
from models.user import User

_require_scheme_admin = require_roles(["scheme_admin", "super_admin"])

router = APIRouter(prefix="/admin/schemes", tags=["Admin Schemes"])


class CreateSchemeReq(BaseModel):
    code: str
    name: str
    short_name: str
    scheme_type: str
    description: Optional[str] = None
    official_url: Optional[str] = None
    portal_url: Optional[str] = None


class CreateVersionReq(BaseModel):
    version_number: str
    academic_year: Optional[str] = None
    copy_from_version_id: Optional[str] = None
    source_document_title: Optional[str] = None
    source_document_url: Optional[str] = None


class AddRuleReq(BaseModel):
    rule_type: str
    rule_key: str
    field: str
    operator: str
    expected_value: Any
    unit: Optional[str] = None
    severity: str = "HARD_STOP"
    display_label: str
    description: Optional[str] = None
    explanation: Optional[str] = None
    source_url: Optional[str] = None
    source_document_title: Optional[str] = None
    source_section: Optional[str] = None
    source_page_number: Optional[str] = None
    is_official_source_confirmed: bool = False


class AddFormFieldReq(BaseModel):
    field_key: str
    field_label: str
    field_type: str
    is_required: bool = True
    display_order: int = 0
    section: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    options: Optional[List[Any]] = None
    conditional_logic: Optional[Dict[str, Any]] = None
    help_text: Optional[str] = None
    source: Optional[str] = None


class EvaluatePreviewReq(BaseModel):
    applicant_data: Dict[str, Any]
    application_answers: Dict[str, Any]


@router.post("", summary="Create a new master scheme")
def create_scheme(req: CreateSchemeReq, current_user: User = Depends(_require_scheme_admin), db: Session = Depends(get_db)):
    try:
        scheme = SchemeAdminService.create_scheme(
            db=db,
            code=req.code,
            name=req.name,
            short_name=req.short_name,
            scheme_type=req.scheme_type,
            description=req.description,
            official_url=req.official_url,
            portal_url=req.portal_url,
        )
        db.commit()
        return {"id": str(scheme.id), "code": scheme.code, "name": scheme.name}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{scheme_id}/versions", summary="Create a new draft version for a scheme")
def create_version(scheme_id: str, req: CreateVersionReq, current_user: User = Depends(_require_scheme_admin), db: Session = Depends(get_db)):
    try:
        copy_id = uuid.UUID(req.copy_from_version_id) if req.copy_from_version_id else None
        version = SchemeAdminService.create_draft_version(
            db=db,
            scheme_id=uuid.UUID(scheme_id),
            version_number=req.version_number,
            academic_year=req.academic_year,
            source_document_title=req.source_document_title,
            source_document_url=req.source_document_url,
            copy_from_version_id=copy_id,
        )
        db.commit()
        return {
            "version_id": str(version.id),
            "version_number": version.version_number,
            "version_status": version.version_status.value if hasattr(version.version_status, "value") else str(version.version_status),
            "is_published": version.is_published,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/versions/{version_id}/publish", summary="Publish a scheme version (makes rules immutable)")
def publish_version(version_id: str, current_user: User = Depends(_require_scheme_admin), db: Session = Depends(get_db)):
    try:
        version = SchemeAdminService.publish_version(db=db, version_id=uuid.UUID(version_id))
        db.commit()
        return {
            "version_id": str(version.id),
            "version_number": version.version_number,
            "version_status": "published",
            "is_published": True,
            "message": "Scheme version published successfully and locked as immutable.",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/versions/{version_id}/rules", summary="Add/Update an eligibility rule (spawns draft if published)")
def add_rule(version_id: str, req: AddRuleReq, current_user: User = Depends(_require_scheme_admin), db: Session = Depends(get_db)):
    version = db.query(SchemeVersion).filter(SchemeVersion.id == uuid.UUID(version_id)).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found.")

    # Enforce Rule Version Immutability  -  spawn new draft if version is published!
    target_version = SchemeAdminService.ensure_draft(db, version)

    explanation_val = req.explanation
    if not req.is_official_source_confirmed:
        explanation_val = "OFFICIAL SOURCE REQUIRED"

    rule = SchemeRule(
        version_id=target_version.id,
        rule_type=req.rule_type,
        rule_key=req.rule_key,
        rule_value={"expected_value": req.expected_value, "operator": req.operator},
        field=req.field,
        operator=req.operator,
        expected_value=req.expected_value,
        unit=req.unit,
        severity=req.severity,
        display_label=req.display_label,
        description=req.description,
        explanation=explanation_val,
        source_url=req.source_url,
        source_document_title=req.source_document_title,
        source_section=req.source_section,
        source_page_number=req.source_page_number,
        is_official_source_confirmed=req.is_official_source_confirmed,
    )
    db.add(rule)
    db.commit()

    return {
        "rule_id": str(rule.id),
        "version_id": str(target_version.id),
        "version_number": target_version.version_number,
        "rule_key": rule.rule_key,
        "is_official_source_confirmed": rule.is_official_source_confirmed,
    }


@router.post("/versions/{version_id}/form-fields", summary="Add a dynamic form field (spawns draft if published)")
def add_form_field(version_id: str, req: AddFormFieldReq, current_user: User = Depends(_require_scheme_admin), db: Session = Depends(get_db)):
    version = db.query(SchemeVersion).filter(SchemeVersion.id == uuid.UUID(version_id)).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found.")

    target_version = SchemeAdminService.ensure_draft(db, version)

    field = SchemeFormField(
        version_id=target_version.id,
        field_key=req.field_key,
        field_name=req.field_key,
        field_label=req.field_label,
        field_type=req.field_type,
        is_required=req.is_required,
        display_order=req.display_order,
        section=req.section,
        validation_rules=req.validation_rules,
        options=req.options,
        conditional_logic=req.conditional_logic,
        help_text=req.help_text,
        source=req.source,
    )
    db.add(field)
    db.commit()

    return {
        "field_id": str(field.id),
        "version_id": str(target_version.id),
        "field_key": field.field_key,
    }


@router.post("/versions/{version_id}/evaluate-preview", summary="Evaluate rules for preview/testing")
def evaluate_preview(version_id: str, req: EvaluatePreviewReq, current_user: User = Depends(_require_scheme_admin), db: Session = Depends(get_db)):
    version = db.query(SchemeVersion).filter(SchemeVersion.id == uuid.UUID(version_id)).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found.")

    payload = {**req.applicant_data, **req.application_answers}
    eval_result = RuleEngineService.evaluate_scheme_version(
        version=version,
        payload=payload,
        is_preview_mode=True,
    )
    form_validation = FormValidationEngine.validate_answers(version=version, answers=req.application_answers)

    return {
        "rule_evaluation": eval_result,
        "form_validation": form_validation,
    }
