"""
Schemes router  -  /api/v1/schemes/*

GET /api/v1/schemes               -  List all active schemes (public)
GET /api/v1/schemes/{code}        -  Get scheme detail with active version rules (public)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.scheme import Scheme, SchemeStatus, SchemeVersion
from schemas.scheme import SchemeDetail, SchemeListItem, SchemeListResponse, SchemeVersionOut

router = APIRouter(prefix="/schemes", tags=["Schemes"])


@router.get(
    "",
    response_model=SchemeListResponse,
    summary="List all MoTA scholarship and fellowship schemes",
)
def list_schemes(db: Session = Depends(get_db)):
    """
    Returns all active MoTA scholarship/fellowship schemes.

    Data is sourced from official MoTA guidelines:
    https://tribal.nic.in/ScholarshiP.aspx

    No authentication required  -  public endpoint.
    """
    schemes = (
        db.query(Scheme)
        .filter(Scheme.status == SchemeStatus.ACTIVE)
        .order_by(Scheme.display_order.asc())
        .all()
    )

    return SchemeListResponse(
        schemes=[
            SchemeListItem(
                id=str(s.id),
                code=s.code,
                name=s.name,
                short_name=s.short_name,
                scheme_type=s.scheme_type.value,
                status=s.status.value,
                official_url=s.official_url,
                portal_url=s.portal_url,
                description=s.description,
                display_order=s.display_order,
            )
            for s in schemes
        ],
        total=len(schemes),
    )


@router.get(
    "/{code}",
    response_model=SchemeDetail,
    summary="Get scheme details including eligibility rules",
)
def get_scheme(code: str, db: Session = Depends(get_db)):
    """
    Returns full scheme detail including the active version's eligibility rules,
    required documents, and form fields.

    All rules cite official source documents with URLs.
    Rules without a confirmed official source are marked OFFICIAL SOURCE REQUIRED.

    No authentication required  -  public endpoint.
    """
    scheme = (
        db.query(Scheme)
        .options(
            joinedload(Scheme.versions).joinedload(SchemeVersion.rules),
            joinedload(Scheme.versions).joinedload(SchemeVersion.documents),
        )
        .filter(Scheme.code == code.upper(), Scheme.status == SchemeStatus.ACTIVE)
        .first()
    )

    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{code}' not found or is not active.",
        )

    # Find the current active version (no effective_to = currently active)
    active_version = next(
        (v for v in scheme.versions if v.effective_to is None and v.is_published),
        None,
    )

    active_version_out = None
    if active_version:
        from schemas.scheme import SchemeDocumentOut, SchemeRuleOut
        active_version_out = SchemeVersionOut(
            id=str(active_version.id),
            version_number=active_version.version_number,
            academic_year=active_version.academic_year,
            effective_from=active_version.effective_from,
            effective_to=active_version.effective_to,
            is_published=active_version.is_published,
            is_accepting_applications=active_version.is_accepting_applications,
            source_document_url=active_version.source_document_url,
            source_document_title=active_version.source_document_title,
            source_retrieved_date=active_version.source_retrieved_date,
            rules=[
                SchemeRuleOut(
                    rule_type=r.rule_type.value,
                    rule_key=r.rule_key,
                    rule_value=r.rule_value,
                    display_label=r.display_label,
                    description=r.description,
                    is_mandatory=r.is_mandatory,
                    source_url=r.source_url,
                    source_document_title=r.source_document_title,
                    source_section=r.source_section,
                    is_official_source_confirmed=r.is_official_source_confirmed,
                )
                for r in active_version.rules
            ],
            required_documents=[
                SchemeDocumentOut(
                    document_type_code=d.document_type_code,
                    document_display_name=d.document_display_name,
                    description=d.description,
                    is_mandatory=d.is_mandatory,
                    accepted_formats=d.accepted_formats,
                    max_size_mb=d.max_size_mb,
                    display_order=d.display_order,
                )
                for d in active_version.documents
            ],
        )

    return SchemeDetail(
        id=str(scheme.id),
        code=scheme.code,
        name=scheme.name,
        short_name=scheme.short_name,
        scheme_type=scheme.scheme_type.value,
        status=scheme.status.value,
        official_url=scheme.official_url,
        portal_url=scheme.portal_url,
        description=scheme.description,
        display_order=scheme.display_order,
        active_version=active_version_out,
    )
