"""Pydantic v2 schemas for Scheme endpoints."""

from __future__ import annotations

from datetime import date
from pydantic import BaseModel, ConfigDict, HttpUrl


class SchemeRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_type: str
    rule_key: str
    rule_value: dict
    display_label: str
    description: str | None = None
    is_mandatory: bool
    source_url: str | None = None
    source_document_title: str | None = None
    source_section: str | None = None
    is_official_source_confirmed: bool


class SchemeDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_type_code: str
    document_display_name: str
    description: str | None = None
    is_mandatory: bool
    accepted_formats: list | None = None
    max_size_mb: int | None = None
    display_order: int


class SchemeVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version_number: str
    academic_year: str | None = None
    effective_from: date
    effective_to: date | None = None
    is_published: bool
    is_accepting_applications: bool
    source_document_url: str | None = None
    source_document_title: str | None = None
    source_retrieved_date: date | None = None
    rules: list[SchemeRuleOut] = []
    required_documents: list[SchemeDocumentOut] = []


class SchemeListItem(BaseModel):
    """Lightweight scheme list item for catalogue view."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    short_name: str
    scheme_type: str
    status: str
    official_url: str | None = None
    portal_url: str | None = None
    description: str | None = None
    display_order: int


class SchemeDetail(SchemeListItem):
    """Full scheme detail including active version's rules."""
    active_version: SchemeVersionOut | None = None


class SchemeListResponse(BaseModel):
    schemes: list[SchemeListItem]
    total: int
    source_note: str = (
        "Scheme information sourced from the Ministry of Tribal Affairs, "
        "Government of India. Source: https://tribal.nic.in/ScholarshiP.aspx"
    )
