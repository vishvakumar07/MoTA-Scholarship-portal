"""
Government Integration Router — Phase 7.

Endpoints:
  GET  /api/v1/admin/integrations
      List all integration health and config status (admin only).
  GET  /api/v1/admin/integrations/{integration}
      Get status for one integration.
  POST /api/v1/admin/integrations/{integration}/health-check
      Trigger a health check for one integration.
  POST /api/v1/admin/applications/{application_id}/government-verification
      Officer triggers a government verification operation.
  GET  /api/v1/admin/applications/{application_id}/government-verification
      Get all government verification records for an application.
  GET  /api/v1/applicant/applications/{application_id}/government-verification-status
      Applicant sees high-level summary ONLY (no internal details).

SECURITY RULES:
  - Applicants cannot trigger verification operations.
  - Applicants see only high-level status (no internal errors or API details).
  - Officers require explicit role.
  - Secrets never appear in any response.
  - Demo records are isolated from official verification.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from database import get_db
from integrations.base import GovIntegrationResponse, GovIntegrationStatus, IntegrationName
from integrations.service import get_integration_service
from models.application import Application
from models.gov_verification import GovIntegrationName, GovVerificationStatus
from models.user import User
from security.rbac import get_current_user, require_roles
from services.gov_verification_service import GovVerificationService

logger = logging.getLogger("mota.routers.integrations")

router = APIRouter(tags=["Government Integrations (Phase 7)"])

ADMIN_ROLES = ["super_admin", "scheme_admin", "scrutiny_officer", "verification_officer", "selection_committee"]
OFFICER_ROLES = ["super_admin", "scheme_admin", "scrutiny_officer", "verification_officer"]

_require_admin = require_roles(ADMIN_ROLES)
_require_officer = require_roles(OFFICER_ROLES)


def _get_user_roles(user: User, db: Session) -> set[str]:
    from models.user import Role, UserRole
    rows = (
        db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    return {r[0] for r in rows}


def _require_admin_role(user: User, db: Session) -> None:
    roles = _get_user_roles(user, db)
    if not roles.intersection(set(ADMIN_ROLES)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authorised administrative officers.",
        )


def _require_officer_role(user: User, db: Session) -> None:
    roles = _get_user_roles(user, db)
    if not roles.intersection(set(OFFICER_ROLES)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authorised verification officers.",
        )


def _is_applicant_role(user: User, db: Session) -> bool:
    roles = _get_user_roles(user, db)
    return "applicant" in roles and not roles.intersection(set(ADMIN_ROLES))


# ---------------------------------------------------------------------------
# INTEGRATION HEALTH & CONFIG
# ---------------------------------------------------------------------------

@router.get(
    "/admin/integrations",
    summary="[Admin] List all government integration configurations and health",
)
async def list_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns configuration state and health for all government integrations.
    Does NOT call external APIs for disabled/unconfigured integrations.
    """
    _require_admin_role(current_user, db)

    service = get_integration_service()
    config_summary = service.get_integration_config_summary()

    return {
        "integrations": config_summary,
        "notice": (
            "Government integrations shown here are integration-ready adapters. "
            "Actual verification requires authorized government credentials, "
            "API specifications, and access approval from the respective authority."
        ),
        "adapter_framework_version": "1.0.0-phase7",
        "data_source": "local_configuration",
    }


@router.get(
    "/admin/integrations/{integration_name}",
    summary="[Admin] Get status for one government integration",
)
async def get_integration_detail(
    integration_name: str = Path(..., description="Integration name: uidai, digilocker, nsp, dbt, mota"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return configuration and health summary for a single integration."""
    _require_admin_role(current_user, db)

    service = get_integration_service()
    config_summary = service.get_integration_config_summary()
    detail = next((i for i in config_summary if i["integration"] == integration_name), None)

    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown integration: '{integration_name}'. "
                   "Valid values: uidai, digilocker, nsp, dbt, mota",
        )
    return {
        **detail,
        "notice": (
            "This integration is an adapter-ready stub. "
            "Authorized credentials are required for live operations."
        ),
    }


@router.post(
    "/admin/integrations/{integration_name}/health-check",
    summary="[Admin] Trigger health check for one government integration",
)
async def trigger_integration_health_check(
    integration_name: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Runs health_check() on the specified adapter.
    For disabled adapters this returns DISABLED without contacting external APIs.
    """
    _require_admin_role(current_user, db)

    try:
        integration_enum = IntegrationName(integration_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown integration: '{integration_name}'.",
        )

    service = get_integration_service()
    adapter = service.get_adapter(integration_enum)
    if adapter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No adapter registered for: {integration_name}",
        )

    response = await adapter.health_check()
    return response.to_dict()


# ---------------------------------------------------------------------------
# GOVERNMENT VERIFICATION — OFFICER
# ---------------------------------------------------------------------------

@router.post(
    "/admin/applications/{application_id}/government-verification",
    summary="[Officer] Trigger a government verification operation for an application",
)
async def trigger_government_verification(
    application_id: uuid.UUID = Path(...),
    body: dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Officer explicitly triggers a government integration operation.

    Body parameters:
      - integration: "uidai" | "digilocker" | "nsp" | "dbt" | "mota"
      - operation: "verify_identity" | "verify_document" | "get_status" | etc.
      - request: dict of operation-specific (non-secret) parameters

    SECURITY:
      - Applicants cannot call this endpoint.
      - Secrets must never be in the request body.
      - Rate limiting applied (max 5 calls/minute per officer per integration).
    """
    _require_officer_role(current_user, db)

    if body is None:
        body = {}

    integration_str = body.get("integration")
    operation = body.get("operation", "health_check")
    request_params = body.get("request", {})

    if not integration_str:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="'integration' is required. Valid values: uidai, digilocker, nsp, dbt, mota",
        )

    # Validate integration name
    try:
        integration_enum = IntegrationName(integration_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown integration: '{integration_str}'.",
        )

    # Verify application exists and officer has IDOR-safe access
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    # Demo applications should not generate official verification records
    if application.is_demo:
        return {
            "integration": integration_str,
            "operation": operation,
            "status": "DISABLED",
            "verified": None,
            "message": "Government verification is not available for demo/test applications.",
            "demo_marker": "DEMO / TEST -- NOT GOVERNMENT DATA",
        }

    # Map integration name to DB enum
    try:
        db_integration = GovIntegrationName(integration_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported integration: {integration_str}")

    # Get or create verification record
    verification = GovVerificationService.get_or_create_verification(
        db=db,
        application_id=application_id,
        integration=db_integration,
        operation=operation,
        requested_by_id=current_user.id,
    )

    # Run the integration operation
    service = get_integration_service()
    response = await service.run_operation(
        integration=integration_enum,
        operation=operation,
        request=request_params,
        actor_id=str(current_user.id),
        use_idempotency=True,
    )

    # Record the attempt in DB
    GovVerificationService.record_attempt(
        db=db,
        verification=verification,
        response=response,
        actor_id=current_user.id,
    )
    db.commit()

    logger.info(
        "Government verification triggered: integration=%s op=%s application=%s status=%s officer=%s",
        integration_str,
        operation,
        application_id,
        response.status.value,
        current_user.id,
    )

    return response.to_dict()


@router.get(
    "/admin/applications/{application_id}/government-verification",
    summary="[Officer/Admin] Get all government verification records for an application",
)
def get_government_verification_records(
    application_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns all government verification records for an application.
    Officers see full metadata. No secrets are exposed.
    """
    _require_admin_role(current_user, db)

    # Verify application exists (IDOR protection)
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")

    verifications = GovVerificationService.get_verifications_for_application(db, application_id)
    summary = GovVerificationService.get_verification_summary(verifications)

    return {
        "application_id": str(application_id),
        "reference_number": application.reference_number,
        "is_demo": application.is_demo,
        "government_verifications": summary,
        "total": len(summary),
        "notice": (
            "Government verifications shown are integration-ready adapter responses. "
            "verified=null indicates the integration has not been authorized/configured. "
            "verified=true is only set when an authorized government API confirms the result."
        ),
    }


# ---------------------------------------------------------------------------
# APPLICANT-FACING (HIGH-LEVEL ONLY)
# ---------------------------------------------------------------------------

@router.get(
    "/applicant/applications/{application_id}/government-verification-status",
    summary="[Applicant] Get high-level government verification status for own application",
)
def get_applicant_verification_status(
    application_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Applicant sees ONLY a high-level summary.
    No internal API errors, adapter details, or credentials are exposed.
    """
    # Verify applicant owns this application
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.applicant_id == current_user.id,
    ).first()

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    verifications = GovVerificationService.get_verifications_for_application(db, application_id)

    # Return only high-level, applicant-safe information
    high_level = []
    for v in verifications:
        display_status = "Integration required"
        display_message = (
            "Your application is not blocked because the government verification "
            "service is not currently connected to this prototype."
        )
        if v.status == GovVerificationStatus.VERIFIED and v.verified is True:
            display_status = "Verified"
            display_message = "Government verification completed."
        elif v.status == GovVerificationStatus.NOT_VERIFIED:
            display_status = "Not verified"
            display_message = "Government verification was run but could not confirm the record."

        high_level.append({
            "integration": v.integration.value,
            "status_display": display_status,
            "message": display_message,
        })

    if not high_level:
        high_level = [
            {
                "integration": "government_verification",
                "status_display": "Integration required",
                "message": (
                    "Your application is not blocked because the government verification "
                    "service is not currently connected to this prototype."
                ),
            }
        ]

    return {
        "application_id": str(application_id),
        "government_verification": high_level,
        "notice": (
            "Government integrations are integration-ready adapters. "
            "Your application continues to be processed by human authorized officers."
        ),
    }
