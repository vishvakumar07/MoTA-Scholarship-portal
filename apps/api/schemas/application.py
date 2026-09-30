"""
Pydantic v2 schemas for Application endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class ApplicationAnswerIn(BaseModel):
    field_key: str
    answer_value: Any = None


class ApplicationStartRequest(BaseModel):
    scheme_version_id: str


class ApplicationStartResponse(BaseModel):
    application_id: str
    reference_number: Optional[str] = None
    status: str
    scheme_version_id: str


class ApplicationSaveRequest(BaseModel):
    answers: list[ApplicationAnswerIn]


class ApplicationSubmitRequest(BaseModel):
    answers: list[ApplicationAnswerIn]
    declaration_accepted: bool = False


class ApplicationAnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    field_key: str
    answer_value: Any = None
    form_field_id: str


class FormFieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    field_key: str
    field_label: str
    field_type: str
    is_required: bool
    section: Optional[str] = None
    display_order: int
    options: Optional[list] = None
    validation_rules: Optional[dict] = None
    help_text: Optional[str] = None
    conditional_logic: Optional[dict] = None


class StatusHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    from_status: Optional[str] = None
    to_status: str
    changed_at: datetime
    change_reason: Optional[str] = None
    system_note: Optional[str] = None


class ApplicationDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    reference_number: Optional[str] = None
    status: str
    scheme_version_id: str
    submitted_at: Optional[datetime] = None
    answers: list[ApplicationAnswerOut] = []
    status_history: list[StatusHistoryItem] = []


class ApplicationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    reference_number: Optional[str] = None
    status: str
    submitted_at: Optional[datetime] = None
    scheme_code: Optional[str] = None
    scheme_name: Optional[str] = None
    scheme_version_id: str


class ApplicationListResponse(BaseModel):
    applications: list[ApplicationListItem]
    total: int


# -- Eligibility Pre-check -----------------------------------------------------
class EligibilityCheckRequest(BaseModel):
    scheme_version_id: str
    answers: dict[str, Any]


class EligibilityCheckResponse(BaseModel):
    overall: str            # "likely_eligible" | "likely_ineligible" | "requires_verification"
    passed_count: int
    failed_count: int
    pending_count: int
    rule_results: list[dict]
    disclaimer: str = (
        "This is a preliminary automated assessment only. "
        "Final eligibility determination is made by authorised MoTA officers "
        "after document verification. This result does not constitute a guarantee "
        "of scholarship sanction."
    )


# -- Document schemas ----------------------------------------------------------
class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    document_type: str
    original_filename: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    status: str
    malware_scan_status: str
    uploaded_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentOut]
    total: int


# -- Deficiency schemas ---------------------------------------------------------
class DeficiencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    deficiency_type: str
    description: str
    affected_document_type: Optional[str] = None
    officer_comment: Optional[str] = None
    response_deadline: Optional[datetime] = None
    status: str
    created_at: datetime


class DeficiencyResponseRequest(BaseModel):
    deficiency_id: str
    response_note: str


# -- Notification schemas -------------------------------------------------------
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    channel: str
    status: str
    title: str
    body: str
    action_url: Optional[str] = None
    related_entity_type: Optional[str] = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    notifications: list[NotificationOut]
    total: int
    unread_count: int
