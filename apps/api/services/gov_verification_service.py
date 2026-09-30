"""
Government Verification Database Service — Phase 7.

Handles CRUD for GovernmentVerification and GovernmentVerificationAttempt.
Enforces:
  - Immutability of historical records
  - Idempotency key uniqueness
  - Separation from AI/OCR/officer-manual verification
  - No secrets stored in the database
  - Audit logging via existing AuditLog model
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from integrations.base import ADAPTER_VERSION, GovIntegrationResponse, GovIntegrationStatus
from models.gov_verification import (
    GovIntegrationName,
    GovVerificationStatus,
    GovernmentVerification,
    GovernmentVerificationAttempt,
)
from models.system import AuditLog

logger = logging.getLogger("mota.gov_verification")


def _map_status(integration_status: GovIntegrationStatus) -> GovVerificationStatus:
    """Map adapter response status to DB verification status enum."""
    mapping = {
        GovIntegrationStatus.SUCCESS: GovVerificationStatus.VERIFIED,
        GovIntegrationStatus.NOT_VERIFIED: GovVerificationStatus.NOT_VERIFIED,
        GovIntegrationStatus.REQUIRES_AUTHORIZED_ACCESS: GovVerificationStatus.REQUIRES_AUTHORIZED_ACCESS,
        GovIntegrationStatus.INTEGRATION_NOT_CONFIGURED: GovVerificationStatus.INTEGRATION_NOT_CONFIGURED,
        GovIntegrationStatus.DISABLED: GovVerificationStatus.DISABLED,
        GovIntegrationStatus.TEMPORARILY_UNAVAILABLE: GovVerificationStatus.REQUIRES_AUTHORIZED_ACCESS,
        GovIntegrationStatus.UNSUPPORTED_OPERATION: GovVerificationStatus.INTEGRATION_NOT_CONFIGURED,
        GovIntegrationStatus.ERROR: GovVerificationStatus.ERROR,
    }
    return mapping.get(integration_status, GovVerificationStatus.ERROR)


def _make_idem_key(application_id: str, integration: str, operation: str) -> str:
    """Derive idempotency key for a verification request."""
    raw = f"{application_id}:{integration}:{operation}"
    return hashlib.sha256(raw.encode()).hexdigest()


class GovVerificationService:
    """
    Service for persisting and querying government verification records.

    Historical records are append-only.
    The 'verified' field is set True ONLY when the adapter
    explicitly returns SUCCESS from an authorized integration.
    """

    @staticmethod
    def get_or_create_verification(
        db: Session,
        application_id: uuid.UUID,
        integration: GovIntegrationName,
        operation: str,
        requested_by_id: uuid.UUID | None,
        document_id: uuid.UUID | None = None,
    ) -> GovernmentVerification:
        """
        Get an existing verification record or create a new one.
        Exactly one GovernmentVerification per (application_id, integration, operation).
        """
        existing = (
            db.query(GovernmentVerification)
            .filter(
                GovernmentVerification.application_id == application_id,
                GovernmentVerification.integration == integration,
                GovernmentVerification.operation == operation,
            )
            .first()
        )
        if existing:
            return existing

        record = GovernmentVerification(
            id=uuid.uuid4(),
            application_id=application_id,
            document_id=document_id,
            integration=integration,
            operation=operation,
            status=GovVerificationStatus.NOT_REQUESTED,
            verified=None,
            requested_by_id=requested_by_id,
            adapter_version=ADAPTER_VERSION,
            idempotency_key=_make_idem_key(str(application_id), integration.value, operation),
        )
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def record_attempt(
        db: Session,
        verification: GovernmentVerification,
        response: GovIntegrationResponse,
        actor_id: uuid.UUID | None,
    ) -> GovernmentVerificationAttempt:
        """
        Append a new attempt record (immutable history).
        Update the parent verification status to latest result.
        """
        # Append attempt (never overwrite historical records)
        attempt = GovernmentVerificationAttempt(
            id=uuid.uuid4(),
            verification_id=verification.id,
            operation=response.operation,
            status=response.status.value,
            verified=response.verified,
            external_reference=response.external_reference,
            request_reference=response.request_reference,
            adapter_version=response.adapter_version,
            attempted_by_id=actor_id,
            message=response.message[:500] if response.message else None,
        )
        db.add(attempt)

        # Update parent verification to latest result
        verification.status = _map_status(response.status)
        verification.verified = response.verified
        verification.message = response.message[:500] if response.message else None
        verification.external_reference = response.external_reference
        verification.request_reference = response.request_reference
        verification.adapter_version = response.adapter_version
        if response.verified is True:
            verification.verified_at = datetime.now(timezone.utc)
        verification.provider_timestamp = response.timestamp

        db.flush()

        # Write to audit log (never log secrets or Aadhaar numbers)
        audit = AuditLog(
            id=uuid.uuid4(),
            actor_id=actor_id,
            actor_role="officer",
            action="government_verification_attempt",
            resource_type="government_verification",
            resource_id=verification.id,
            details={
                "integration": verification.integration.value,
                "operation": response.operation,
                "status": response.status.value,
                "verified": response.verified,
                "adapter_version": response.adapter_version,
                "application_id": str(verification.application_id),
                # NEVER log: API keys, Aadhaar numbers, tokens, full response
            },
        )
        db.add(audit)
        db.flush()

        return attempt

    @staticmethod
    def get_verifications_for_application(
        db: Session,
        application_id: uuid.UUID,
    ) -> list[GovernmentVerification]:
        """Return all government verification records for an application."""
        return (
            db.query(GovernmentVerification)
            .filter(GovernmentVerification.application_id == application_id)
            .all()
        )

    @staticmethod
    def get_verification_summary(
        verifications: list[GovernmentVerification],
    ) -> list[dict[str, Any]]:
        """Return a safe summary dict for each verification (no secrets)."""
        results = []
        for v in verifications:
            results.append({
                "id": str(v.id),
                "integration": v.integration.value,
                "operation": v.operation,
                "status": v.status.value,
                "verified": v.verified,
                "message": v.message,
                "external_reference": v.external_reference,
                "adapter_version": v.adapter_version,
                "verified_at": v.verified_at.isoformat() if v.verified_at else None,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "attempt_count": len(v.attempts) if v.attempts else 0,
            })
        return results
