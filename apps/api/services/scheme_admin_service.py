"""
Scheme Administration Service.

Handles scheme lifecycle, draft creation, version publishing, and version immutability.
Once a scheme version is published, it CANNOT be modified.
Any edit request to a published version spawns a new DRAFT version.
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.scheme import (
    Scheme,
    SchemeDocument,
    SchemeFormField,
    SchemeNotificationTemplate,
    SchemeRule,
    SchemeSelectionCriteria,
    SchemeStatus,
    SchemeVersion,
    SchemeVersionStatus,
    SchemeWorkflow,
)


class SchemeAdminService:
    @classmethod
    def create_scheme(
        cls,
        db: Session,
        code: str,
        name: str,
        short_name: str,
        scheme_type: str,
        description: str | None = None,
        official_url: str | None = None,
        portal_url: str | None = None,
    ) -> Scheme:
        scheme = Scheme(
            code=code.upper(),
            name=name,
            short_name=short_name,
            scheme_type=scheme_type,
            status=SchemeStatus.ACTIVE,
            description=description,
            official_url=official_url,
            portal_url=portal_url,
        )
        db.add(scheme)
        db.flush()
        return scheme

    @classmethod
    def create_draft_version(
        cls,
        db: Session,
        scheme_id: uuid.UUID,
        version_number: str,
        academic_year: str | None = None,
        effective_from: date | None = None,
        source_document_title: str | None = None,
        source_document_url: str | None = None,
        copy_from_version_id: uuid.UUID | None = None,
    ) -> SchemeVersion:
        version = SchemeVersion(
            scheme_id=scheme_id,
            version_number=version_number,
            academic_year=academic_year,
            version_status=SchemeVersionStatus.DRAFT,
            effective_from=effective_from or date.today(),
            is_published=False,
            is_accepting_applications=False,
            source_document_title=source_document_title,
            source_document_url=source_document_url,
            source_retrieved_date=date.today(),
        )
        db.add(version)
        db.flush()

        # If copying from a published or existing version
        if copy_from_version_id:
            old_version = db.query(SchemeVersion).filter(SchemeVersion.id == copy_from_version_id).first()
            if old_version:
                cls._copy_version_contents(db, old_version, version)

        return version

    @classmethod
    def publish_version(cls, db: Session, version_id: uuid.UUID) -> SchemeVersion:
        version = db.query(SchemeVersion).filter(SchemeVersion.id == version_id).first()
        if not version:
            raise ValueError("Scheme version not found.")

        version.is_published = True
        version.is_accepting_applications = True
        version.version_status = SchemeVersionStatus.PUBLISHED
        db.flush()
        return version

    @classmethod
    def ensure_draft(cls, db: Session, version: SchemeVersion) -> SchemeVersion:
        """
        Enforces Rule Version Immutability.
        If version is published, creates a new draft version instead of editing published version.
        """
        if version.is_published or version.version_status == SchemeVersionStatus.PUBLISHED:
            # Generate next version number e.g. "1.0" -> "1.1" or "2.0"
            v_parts = version.version_number.split(".")
            try:
                next_minor = int(v_parts[-1]) + 1
                new_vnum = f"{'.'.join(v_parts[:-1])}.{next_minor}"
            except ValueError:
                new_vnum = f"{version.version_number}.1"

            new_draft = cls.create_draft_version(
                db=db,
                scheme_id=version.scheme_id,
                version_number=new_vnum,
                academic_year=version.academic_year,
                effective_from=date.today(),
                source_document_title=version.source_document_title,
                source_document_url=version.source_document_url,
                copy_from_version_id=version.id,
            )
            return new_draft
        return version

    @classmethod
    def _copy_version_contents(cls, db: Session, source_v: SchemeVersion, target_v: SchemeVersion):
        for r in source_v.rules:
            if not getattr(r, "is_deleted", False):
                new_r = SchemeRule(
                    version_id=target_v.id,
                    rule_type=r.rule_type,
                    rule_key=r.rule_key,
                    rule_value=r.rule_value,
                    field=r.field,
                    operator=r.operator,
                    expected_value=r.expected_value,
                    unit=r.unit,
                    severity=r.severity,
                    explanation=r.explanation,
                    display_label=r.display_label,
                    description=r.description,
                    is_mandatory=r.is_mandatory,
                    source_url=r.source_url,
                    source_document_title=r.source_document_title,
                    source_document_id=r.source_document_id,
                    source_section=r.source_section,
                    source_page_number=r.source_page_number,
                    source_type=r.source_type,
                    source_publication_date=r.source_publication_date,
                    source_retrieved_date=r.source_retrieved_date,
                    is_official_source_confirmed=r.is_official_source_confirmed,
                )
                db.add(new_r)

        for f in source_v.form_fields:
            if not getattr(f, "is_deleted", False):
                new_f = SchemeFormField(
                    version_id=target_v.id,
                    field_key=f.field_key,
                    field_name=f.field_name,
                    field_label=f.field_label,
                    field_type=f.field_type,
                    is_required=f.is_required,
                    display_order=f.display_order,
                    section=f.section,
                    validation_rules=f.validation_rules,
                    options=f.options,
                    conditional_logic=f.conditional_logic,
                    help_text=f.help_text,
                    source=f.source,
                )
                db.add(new_f)

        for d in source_v.documents:
            if not getattr(d, "is_deleted", False):
                new_d = SchemeDocument(
                    version_id=target_v.id,
                    document_type_code=d.document_type_code,
                    document_display_name=d.document_display_name,
                    description=d.description,
                    is_mandatory=d.is_mandatory,
                    accepted_formats=d.accepted_formats,
                    max_size_mb=d.max_size_mb,
                    display_order=d.display_order,
                    source_url=d.source_url,
                    source_retrieved_date=d.source_retrieved_date,
                )
                db.add(new_d)

        for w in source_v.workflows:
            if not getattr(w, "is_deleted", False):
                new_w = SchemeWorkflow(
                    version_id=target_v.id,
                    from_state=w.from_state,
                    to_state=w.to_state,
                    transition_type=w.transition_type,
                    required_role=w.required_role,
                    conditions=w.conditions,
                    description=w.description,
                )
                db.add(new_w)

        db.flush()
