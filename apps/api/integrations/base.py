"""
Government Integration Adapter Framework — Phase 7.

Abstract base class and shared response contract for all government
integration adapters.

GOVERNANCE PRINCIPLE:
  AI is NEVER the final authority. Government integrations are
  integration-ready adapters only. No real API calls are made unless
  authorized credentials are explicitly configured AND the adapter
  is set to 'live' mode.

RESPONSE STATUSES:
  SUCCESS                    - Authorized integration returned a result.
  NOT_VERIFIED               - Integration ran but could not verify.
  REQUIRES_AUTHORIZED_ACCESS - Integration not enabled/configured.
  INTEGRATION_NOT_CONFIGURED - Credentials/config missing.
  TEMPORARILY_UNAVAILABLE    - Configured but unreachable right now.
  UNSUPPORTED_OPERATION      - Adapter does not implement this operation.
  DISABLED                   - Integration explicitly disabled in config.
  ERROR                      - Unexpected failure in adapter.

DO NOT USE:
  VERIFIED       - Never fabricate a verification result.
  AI_VERIFIED    - AI cannot produce a government verification.
  OCR_VERIFIED   - OCR cannot produce a government verification.
  AUTO_VERIFIED  - Automation cannot produce a government verification.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger("mota.integrations")

# ---------------------------------------------------------------------------
# Adapter Version
# ---------------------------------------------------------------------------
ADAPTER_VERSION = "1.0.0-phase7"


# ---------------------------------------------------------------------------
# Canonical Integration Status Enum
# ---------------------------------------------------------------------------
class GovIntegrationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    NOT_VERIFIED = "NOT_VERIFIED"
    REQUIRES_AUTHORIZED_ACCESS = "REQUIRES_AUTHORIZED_ACCESS"
    INTEGRATION_NOT_CONFIGURED = "INTEGRATION_NOT_CONFIGURED"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"
    DISABLED = "DISABLED"
    ERROR = "ERROR"
    # PROHIBITED: VERIFIED, AI_VERIFIED, OCR_VERIFIED, AUTO_VERIFIED


# ---------------------------------------------------------------------------
# Canonical Integration Names
# ---------------------------------------------------------------------------
class IntegrationName(str, Enum):
    UIDAI = "uidai"
    DIGILOCKER = "digilocker"
    NSP = "nsp"
    DBT = "dbt"
    MOTA = "mota"
    MOCK = "mock"  # Test adapter ONLY -- never in production


# ---------------------------------------------------------------------------
# Standard Integration Response
# ---------------------------------------------------------------------------
@dataclass
class GovIntegrationResponse:
    """
    Normalized response from any government integration adapter.

    All adapters MUST return this structure.
    'verified' MUST remain None unless an authorized government API
    explicitly confirmed a positive verification.
    """

    integration: IntegrationName
    operation: str
    status: GovIntegrationStatus
    verified: "bool | None"
    message: str
    source: str = "government_integration_adapter"
    adapter_version: str = ADAPTER_VERSION
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    external_reference: "str | None" = None
    request_reference: "str | None" = None
    metadata: "dict[str, Any] | None" = None

    def to_dict(self) -> "dict[str, Any]":
        return {
            "integration": self.integration.value,
            "operation": self.operation,
            "status": self.status.value,
            "verified": self.verified,
            "message": self.message,
            "source": self.source,
            "adapter_version": self.adapter_version,
            "timestamp": self.timestamp,
            "external_reference": self.external_reference,
            "request_reference": self.request_reference,
            "metadata": self.metadata,
        }

    @property
    def is_configured(self) -> bool:
        return self.status not in (
            GovIntegrationStatus.DISABLED,
            GovIntegrationStatus.INTEGRATION_NOT_CONFIGURED,
            GovIntegrationStatus.REQUIRES_AUTHORIZED_ACCESS,
        )


# ---------------------------------------------------------------------------
# Abstract Adapter Base
# ---------------------------------------------------------------------------
class GovernmentIntegrationAdapter(ABC):
    """
    Abstract base for all government integration adapters.

    Unsupported operations return UNSUPPORTED_OPERATION -- never raise.
    """

    integration_name: IntegrationName

    def _unsupported(self, operation: str) -> GovIntegrationResponse:
        return GovIntegrationResponse(
            integration=self.integration_name,
            operation=operation,
            status=GovIntegrationStatus.UNSUPPORTED_OPERATION,
            verified=None,
            message=(
                f"The '{operation}' operation is not supported by the "
                f"{self.integration_name.value.upper()} adapter."
            ),
        )

    def _not_configured(self, operation: str) -> GovIntegrationResponse:
        return GovIntegrationResponse(
            integration=self.integration_name,
            operation=operation,
            status=GovIntegrationStatus.INTEGRATION_NOT_CONFIGURED,
            verified=None,
            message=(
                f"{self.integration_name.value.upper()} integration is not configured. "
                "Authorized credentials and API specifications are required."
            ),
        )

    def _disabled(self, operation: str) -> GovIntegrationResponse:
        return GovIntegrationResponse(
            integration=self.integration_name,
            operation=operation,
            status=GovIntegrationStatus.DISABLED,
            verified=None,
            message=(
                f"{self.integration_name.value.upper()} integration is disabled. "
                "Enable it in environment configuration with authorized credentials."
            ),
        )

    def _requires_authorized_access(self, operation: str) -> GovIntegrationResponse:
        return GovIntegrationResponse(
            integration=self.integration_name,
            operation=operation,
            status=GovIntegrationStatus.REQUIRES_AUTHORIZED_ACCESS,
            verified=None,
            message=(
                f"{self.integration_name.value.upper()} integration requires authorized "
                "government API access. Contact MoTA IT division for integration credentials."
            ),
        )

    @abstractmethod
    async def health_check(self) -> GovIntegrationResponse:
        """Return current health/availability of this integration."""

    async def verify_identity(self, request: "dict[str, Any]") -> GovIntegrationResponse:
        return self._unsupported("verify_identity")

    async def verify_document(self, request: "dict[str, Any]") -> GovIntegrationResponse:
        return self._unsupported("verify_document")

    async def get_document(self, request: "dict[str, Any]") -> GovIntegrationResponse:
        return self._unsupported("get_document")

    async def get_status(self, request: "dict[str, Any]") -> GovIntegrationResponse:
        return self._unsupported("get_status")

    async def check_beneficiary(self, request: "dict[str, Any]") -> GovIntegrationResponse:
        return self._unsupported("check_beneficiary")

    async def submit_record(self, request: "dict[str, Any]") -> GovIntegrationResponse:
        return self._unsupported("submit_record")

    async def initiate_authorization(self, request: "dict[str, Any]") -> GovIntegrationResponse:
        return self._unsupported("initiate_authorization")
