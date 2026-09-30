"""
Government Integration Service — Phase 7.

The central service facade that:
  1. Instantiates and manages all government integration adapters.
  2. Enforces rate limiting on integration calls.
  3. Provides idempotency handling for stateful operations.
  4. Routes operations to the correct adapter.
  5. Coordinates audit logging.

SECURITY:
  - Never logs secrets, tokens, or Aadhaar numbers.
  - All government calls must be explicitly triggered by authorized officers.
  - Rate limiting prevents repeated/loop-based calls.
"""

from __future__ import annotations

from config import get_settings

import asyncio
import hashlib
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from integrations.adapters import (
    DBTAdapter,
    DigiLockerAdapter,
    MockGovernmentIntegrationAdapter,
    MoTAAdapter,
    NSPAdapter,
    UIDaiAdapter,
)
from integrations.base import (
    ADAPTER_VERSION,
    GovIntegrationResponse,
    GovIntegrationStatus,
    IntegrationName,
)

logger = logging.getLogger("mota.integrations.service")

# ---------------------------------------------------------------------------
# Rate Limiting: simple in-memory token bucket per (actor_id, integration)
# ---------------------------------------------------------------------------
_RATE_LIMIT_WINDOW_SECONDS = 60
_RATE_LIMIT_MAX_CALLS = 5  # Max calls per actor per integration per minute

_rate_limit_store: dict[str, list[float]] = {}


def _check_rate_limit(actor_id: str, integration: str) -> bool:
    """Returns True if call is allowed, False if rate-limited."""
    key = f"{actor_id}:{integration}"
    now = time.monotonic()
    window_start = now - _RATE_LIMIT_WINDOW_SECONDS

    calls = _rate_limit_store.get(key, [])
    calls = [t for t in calls if t > window_start]

    if len(calls) >= _RATE_LIMIT_MAX_CALLS:
        return False

    calls.append(now)
    _rate_limit_store[key] = calls
    return True


# ---------------------------------------------------------------------------
# Idempotency Store (in-memory; production should use Redis/DB)
# ---------------------------------------------------------------------------
_idempotency_store: dict[str, dict[str, Any]] = {}


def _make_idempotency_key(actor_id: str, integration: str, operation: str, request: dict) -> str:
    """Derive a stable idempotency key from request parameters."""
    stable = f"{actor_id}:{integration}:{operation}:{sorted(request.items())}"
    return hashlib.sha256(stable.encode()).hexdigest()


def _get_cached_response(key: str) -> GovIntegrationResponse | None:
    """Return a cached idempotent response if available and fresh (60s)."""
    entry = _idempotency_store.get(key)
    if entry and (time.monotonic() - entry["stored_at"] < 60):
        return entry["response"]
    return None


def _cache_response(key: str, response: GovIntegrationResponse) -> None:
    _idempotency_store[key] = {"response": response, "stored_at": time.monotonic()}


# ---------------------------------------------------------------------------
# Government Integration Service
# ---------------------------------------------------------------------------
class GovernmentIntegrationService:
    """
    Central facade for all government integration adapters.

    Usage:
        service = GovernmentIntegrationService()
        result = await service.run_operation(
            integration=IntegrationName.DIGILOCKER,
            operation="verify_document",
            request={"document_type": "caste_certificate"},
            actor_id="officer-uuid",
        )
    """

    def __init__(self, use_mock: bool = False):
        if use_mock:
            # Test mode: all adapters are mock
            mock = MockGovernmentIntegrationAdapter()
            self._adapters = {
                IntegrationName.UIDAI: mock,
                IntegrationName.DIGILOCKER: mock,
                IntegrationName.NSP: mock,
                IntegrationName.DBT: mock,
                IntegrationName.MOTA: mock,
                IntegrationName.MOCK: mock,
            }
        else:
            self._adapters = {
                IntegrationName.UIDAI: UIDaiAdapter(),
                IntegrationName.DIGILOCKER: DigiLockerAdapter(),
                IntegrationName.NSP: NSPAdapter(),
                IntegrationName.DBT: DBTAdapter(),
                IntegrationName.MOTA: MoTAAdapter(),
            }

    def get_adapter(self, integration: IntegrationName):
        return self._adapters.get(integration)

    async def health_check_all(self) -> dict[str, Any]:
        """Run health_check on all adapters. NEVER calls external APIs for disabled ones."""
        results = {}
        for name, adapter in self._adapters.items():
            if name == IntegrationName.MOCK:
                continue
            try:
                resp = await adapter.health_check()
                results[name.value] = resp.to_dict()
            except Exception as exc:
                logger.error(
                    "Health check failed for %s: %s",
                    name.value,
                    type(exc).__name__,
                    exc_info=False,  # No stack trace in logs for external errors
                )
                results[name.value] = {
                    "integration": name.value,
                    "operation": "health_check",
                    "status": GovIntegrationStatus.ERROR.value,
                    "verified": None,
                    "message": f"Health check raised an unexpected error: {type(exc).__name__}",
                    "adapter_version": ADAPTER_VERSION,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        return results

    async def run_operation(
        self,
        integration: IntegrationName,
        operation: str,
        request: dict[str, Any],
        actor_id: str,
        use_idempotency: bool = True,
    ) -> GovIntegrationResponse:
        """
        Execute a single integration operation safely.

        Applies:
          - Rate limiting (per actor per integration)
          - Idempotency (prevents duplicate submissions)
          - Error containment (never leaks secrets or stack traces)
        """
        # Rate limit check
        if not _check_rate_limit(actor_id, integration.value):
            logger.warning(
                "Rate limit exceeded for actor=%s integration=%s op=%s",
                actor_id,
                integration.value,
                operation,
            )
            return GovIntegrationResponse(
                integration=integration,
                operation=operation,
                status=GovIntegrationStatus.ERROR,
                verified=None,
                message=(
                    "Too many integration requests. "
                    f"Maximum {_RATE_LIMIT_MAX_CALLS} calls per minute per integration."
                ),
            )

        # Idempotency check
        if use_idempotency:
            idempotency_key = _make_idempotency_key(actor_id, integration.value, operation, request)
            cached = _get_cached_response(idempotency_key)
            if cached is not None:
                logger.info(
                    "Returning idempotent response for actor=%s integration=%s op=%s",
                    actor_id,
                    integration.value,
                    operation,
                )
                return cached

        adapter = self._adapters.get(integration)
        if adapter is None:
            return GovIntegrationResponse(
                integration=integration,
                operation=operation,
                status=GovIntegrationStatus.INTEGRATION_NOT_CONFIGURED,
                verified=None,
                message=f"No adapter registered for integration: {integration.value}",
            )

        # Dispatch operation
        op_method = getattr(adapter, operation, None)
        if op_method is None:
            return adapter._unsupported(operation)

        try:
            response = await op_method(request)
        except asyncio.TimeoutError:
            logger.error(
                "Timeout on integration=%s op=%s actor=%s",
                integration.value,
                operation,
                actor_id,
            )
            response = GovIntegrationResponse(
                integration=integration,
                operation=operation,
                status=GovIntegrationStatus.TEMPORARILY_UNAVAILABLE,
                verified=None,
                message=f"{integration.value.upper()} integration timed out. Please retry later.",
            )
        except Exception as exc:
            # NEVER log sensitive request payloads
            logger.error(
                "Error in integration=%s op=%s actor=%s error_type=%s",
                integration.value,
                operation,
                actor_id,
                type(exc).__name__,
                exc_info=False,
            )
            response = GovIntegrationResponse(
                integration=integration,
                operation=operation,
                status=GovIntegrationStatus.ERROR,
                verified=None,
                message=(
                    f"An error occurred processing the {integration.value.upper()} request. "
                    "Please contact the system administrator."
                ),
            )

        # Cache for idempotency
        if use_idempotency and response.status not in (
            GovIntegrationStatus.ERROR,
            GovIntegrationStatus.TEMPORARILY_UNAVAILABLE,
        ):
            _cache_response(idempotency_key, response)

        return response

    def get_integration_config_summary(self) -> list[dict[str, Any]]:
        """
        Return the configuration state of all integrations.
        Used by the admin health endpoint.
        Does NOT call external APIs.
        """
        settings = get_settings()
        integrations_config = [
            {
                "integration": IntegrationName.UIDAI.value,
                "display_name": "UIDAI (Aadhaar)",
                "enabled": settings.AADHAAR_INTEGRATION == "live",
                "configured": False,  # True only when live + credentials present
                "mode": settings.AADHAAR_INTEGRATION,
                "status": (
                    "LIVE_CONFIGURED"
                    if settings.AADHAAR_INTEGRATION == "live"
                    else "NOT_CONFIGURED"
                ),
                "description": "Aadhaar identity verification via UIDAI e-KYC API",
                "requires": ["AADHAAR_API_URL", "AADHAAR_CLIENT_ID", "AADHAAR_CLIENT_SECRET"],
            },
            {
                "integration": IntegrationName.DIGILOCKER.value,
                "display_name": "DigiLocker",
                "enabled": settings.DIGILOCKER_INTEGRATION == "live",
                "configured": False,
                "mode": settings.DIGILOCKER_INTEGRATION,
                "status": (
                    "LIVE_CONFIGURED"
                    if settings.DIGILOCKER_INTEGRATION == "live"
                    else "REQUIRES_AUTHORIZED_ACCESS"
                ),
                "description": "Document retrieval and verification via DigiLocker API",
                "requires": ["DIGILOCKER_CLIENT_ID", "DIGILOCKER_CLIENT_SECRET"],
            },
            {
                "integration": IntegrationName.NSP.value,
                "display_name": "National Scholarship Portal (NSP)",
                "enabled": settings.NSP_INTEGRATION == "live",
                "configured": False,
                "mode": settings.NSP_INTEGRATION,
                "status": (
                    "LIVE_CONFIGURED"
                    if settings.NSP_INTEGRATION == "live"
                    else "NOT_CONFIGURED"
                ),
                "description": "NSP interoperability for scholarship application cross-reference",
                "requires": ["NSP_API_URL", "NSP_CLIENT_ID", "NSP_CLIENT_SECRET"],
            },
            {
                "integration": IntegrationName.DBT.value,
                "display_name": "DBT / Tribal DBT",
                "enabled": settings.DBT_INTEGRATION == "live",
                "configured": False,
                "mode": settings.DBT_INTEGRATION,
                "status": (
                    "LIVE_CONFIGURED"
                    if settings.DBT_INTEGRATION == "live"
                    else "NOT_CONFIGURED"
                ),
                "description": "DBT Portal disbursement status interoperability (read-only)",
                "requires": ["DBT_API_URL", "DBT_CLIENT_ID", "DBT_CLIENT_SECRET"],
            },
            {
                "integration": IntegrationName.MOTA.value,
                "display_name": "MoTA Dashboard / Ministry System",
                "enabled": settings.MOTA_DASHBOARD_INTEGRATION == "live",
                "configured": False,
                "mode": settings.MOTA_DASHBOARD_INTEGRATION,
                "status": (
                    "LIVE_CONFIGURED"
                    if settings.MOTA_DASHBOARD_INTEGRATION == "live"
                    else "NOT_CONFIGURED"
                ),
                "description": "MoTA Ministry system synchronization and reporting",
                "requires": ["MOTA_API_URL", "MOTA_CLIENT_ID", "MOTA_CLIENT_SECRET"],
            },
        ]
        return integrations_config


# ---------------------------------------------------------------------------
# Module-level singleton (production)
# ---------------------------------------------------------------------------
_integration_service: GovernmentIntegrationService | None = None


def get_integration_service() -> GovernmentIntegrationService:
    """Return the singleton integration service (production mode)."""
    global _integration_service
    if _integration_service is None:
        _integration_service = GovernmentIntegrationService(use_mock=False)
    return _integration_service
