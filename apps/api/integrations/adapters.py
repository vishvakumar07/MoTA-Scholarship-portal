"""
Government Integration Adapters — Phase 7.

Concrete stub adapters for each government integration.
All return truthful NOT_CONFIGURED / REQUIRES_AUTHORIZED_ACCESS status
when credentials are absent.

NO FABRICATED:
  - Aadhaar records or verification results
  - DigiLocker documents
  - NSP applications
  - DBT transactions
  - MoTA beneficiary records
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from config import get_settings
from integrations.base import (
    ADAPTER_VERSION,
    GovernmentIntegrationAdapter,
    GovIntegrationResponse,
    GovIntegrationStatus,
    IntegrationName,
)

logger = logging.getLogger("mota.integrations.adapters")


# ---------------------------------------------------------------------------
# UIDAI / Aadhaar Adapter
# ---------------------------------------------------------------------------
class UIDaiAdapter(GovernmentIntegrationAdapter):
    """
    Aadhaar identity verification via UIDAI API.

    STUB: Returns INTEGRATION_NOT_CONFIGURED until authorized
    UIDAI API credentials and specifications are provided.

    SECURITY:
      - Full Aadhaar numbers are NEVER stored.
      - Only SHA-256 hash of Aadhaar may be used where legally required.
      - No fake UIDAI responses are ever generated.
    """

    integration_name = IntegrationName.UIDAI

    def __init__(self):
        settings = get_settings()
        self._mode = settings.AADHAAR_INTEGRATION  # "stub" or "live"

    async def health_check(self, request: dict[str, Any] | None = None) -> GovIntegrationResponse:
        if self._mode == "stub":
            return self._disabled("health_check")
        return self._not_configured("health_check")

    async def verify_identity(self, request: dict[str, Any]) -> GovIntegrationResponse:
        """
        Aadhaar-based identity verification.

        When authorized credentials are available, implement UIDAI e-KYC here.
        Until then, returns INTEGRATION_NOT_CONFIGURED.

        PROHIBITED: Do not generate fake Aadhaar verification results.
        """
        if self._mode != "live":
            return self._disabled("verify_identity")

        # Placeholder for authorized live implementation.
        # Requires: AADHAAR_API_URL, AADHAAR_CLIENT_ID, AADHAAR_CLIENT_SECRET
        return self._not_configured("verify_identity")


# ---------------------------------------------------------------------------
# DigiLocker Adapter
# ---------------------------------------------------------------------------
class DigiLockerAdapter(GovernmentIntegrationAdapter):
    """
    DigiLocker document retrieval and verification via official API.

    STUB: Returns REQUIRES_AUTHORIZED_ACCESS until OAuth credentials
    and API specifications are provided by DigiLocker authorities.

    PROHIBITED: No fake DigiLocker documents or authorization codes.
    """

    integration_name = IntegrationName.DIGILOCKER

    def __init__(self):
        settings = get_settings()
        self._mode = settings.DIGILOCKER_INTEGRATION

    async def health_check(self, request: dict[str, Any] | None = None) -> GovIntegrationResponse:
        if self._mode == "stub":
            return self._requires_authorized_access("health_check")
        return self._not_configured("health_check")

    async def initiate_authorization(self, request: dict[str, Any]) -> GovIntegrationResponse:
        """
        Begin DigiLocker OAuth2 authorization flow.
        Requires DIGILOCKER_CLIENT_ID and DIGILOCKER_CLIENT_SECRET.
        """
        if self._mode != "live":
            return self._requires_authorized_access("initiate_authorization")
        return self._not_configured("initiate_authorization")

    async def get_document(self, request: dict[str, Any]) -> GovIntegrationResponse:
        """
        Fetch a document from a user's DigiLocker vault.
        Requires an authorized user access token obtained via OAuth.
        """
        if self._mode != "live":
            return self._requires_authorized_access("get_document")
        return self._not_configured("get_document")

    async def verify_document(self, request: dict[str, Any]) -> GovIntegrationResponse:
        """
        Verify a document's authenticity via DigiLocker.
        The 'verified' field MUST NOT be set True without confirmed API response.
        """
        if self._mode != "live":
            return self._requires_authorized_access("verify_document")
        return self._not_configured("verify_document")


# ---------------------------------------------------------------------------
# National Scholarship Portal (NSP) Adapter
# ---------------------------------------------------------------------------
class NSPAdapter(GovernmentIntegrationAdapter):
    """
    National Scholarship Portal interoperability.

    STUB: Returns INTEGRATION_NOT_CONFIGURED until an NSP API
    specification and authorized access are available.

    PROHIBITED: Do not invent an NSP API or fabricate NSP application records.
    """

    integration_name = IntegrationName.NSP

    def __init__(self):
        settings = get_settings()
        self._mode = settings.NSP_INTEGRATION

    async def health_check(self, request: dict[str, Any] | None = None) -> GovIntegrationResponse:
        if self._mode == "stub":
            return self._disabled("health_check")
        return self._not_configured("health_check")

    async def get_status(self, request: dict[str, Any]) -> GovIntegrationResponse:
        """
        Check application status on NSP.
        Requires authorized NSP API access and a valid NSP application ID.
        """
        if self._mode != "live":
            return self._not_configured("get_status")
        # Placeholder for authorized live implementation.
        return self._not_configured("get_status")

    async def verify_document(self, request: dict[str, Any]) -> GovIntegrationResponse:
        """Check if an NSP external record exists for the given reference."""
        if self._mode != "live":
            return self._not_configured("verify_document")
        return self._not_configured("verify_document")


# ---------------------------------------------------------------------------
# DBT / Tribal DBT Adapter
# ---------------------------------------------------------------------------
class DBTAdapter(GovernmentIntegrationAdapter):
    """
    DBT Portal integration for disbursement status interoperability.

    STUB: Returns INTEGRATION_NOT_CONFIGURED.

    PROHIBITED:
      - Do NOT initiate payments.
      - Do NOT fabricate transaction reference numbers or bank confirmations.
      - Do NOT simulate DBT transactions.
    """

    integration_name = IntegrationName.DBT

    def __init__(self):
        settings = get_settings()
        self._mode = settings.DBT_INTEGRATION

    async def health_check(self, request: dict[str, Any] | None = None) -> GovIntegrationResponse:
        if self._mode == "stub":
            return self._disabled("health_check")
        return self._not_configured("health_check")

    async def check_beneficiary(self, request: dict[str, Any]) -> GovIntegrationResponse:
        """
        Check if an applicant is registered as a beneficiary on DBT.
        Requires authorized DBT portal credentials.
        """
        if self._mode != "live":
            return self._not_configured("check_beneficiary")
        return self._not_configured("check_beneficiary")

    async def get_status(self, request: dict[str, Any]) -> GovIntegrationResponse:
        """
        Check disbursement/payment status for a reference on DBT.
        No fake payment data is ever generated.
        """
        if self._mode != "live":
            return self._not_configured("get_status")
        return self._not_configured("get_status")


# ---------------------------------------------------------------------------
# MoTA Dashboard / Ministry System Adapter
# ---------------------------------------------------------------------------
class MoTAAdapter(GovernmentIntegrationAdapter):
    """
    MoTA Dashboard / Ministry system synchronization adapter.

    STUB: Returns INTEGRATION_NOT_CONFIGURED until official
    MoTA API endpoints and credentials are provided.

    PROHIBITED:
      - Do not invent MoTA endpoint URLs or schemas.
      - Local analytics are NOT official MoTA statistics.
    """

    integration_name = IntegrationName.MOTA

    def __init__(self):
        settings = get_settings()
        self._mode = settings.MOTA_DASHBOARD_INTEGRATION

    async def health_check(self, request: dict[str, Any] | None = None) -> GovIntegrationResponse:
        if self._mode == "stub":
            return self._disabled("health_check")
        return self._not_configured("health_check")

    async def submit_record(self, request: dict[str, Any]) -> GovIntegrationResponse:
        """
        Submit an application record to the MoTA Ministry system.
        Requires officially provided API endpoint and credentials.
        """
        if self._mode != "live":
            return self._not_configured("submit_record")
        return self._not_configured("submit_record")

    async def get_status(self, request: dict[str, Any]) -> GovIntegrationResponse:
        """Sync status with MoTA Ministry system."""
        if self._mode != "live":
            return self._not_configured("get_status")
        return self._not_configured("get_status")


# ---------------------------------------------------------------------------
# Mock Adapter (TESTING ONLY)
# ---------------------------------------------------------------------------
class MockGovernmentIntegrationAdapter(GovernmentIntegrationAdapter):
    """
    Mock adapter for automated testing ONLY.

    MUST NEVER be used in production configuration.
    All results contain 'DEMO / TEST -- NOT GOVERNMENT DATA'.
    Uses clearly invalid test identifiers -- no realistic fake data.
    """

    integration_name = IntegrationName.MOCK
    DEMO_MARKER = "DEMO / TEST -- NOT GOVERNMENT DATA"

    def __init__(self, configured: bool = True):
        self._configured = configured

    async def health_check(self, request: dict[str, Any] | None = None) -> GovIntegrationResponse:
        return GovIntegrationResponse(
            integration=self.integration_name,
            operation="health_check",
            status=GovIntegrationStatus.SUCCESS,
            verified=None,
            message=f"Mock adapter is healthy. {self.DEMO_MARKER}",
            metadata={"is_mock": True, "demo_marker": self.DEMO_MARKER},
        )

    async def verify_identity(self, request: dict[str, Any]) -> GovIntegrationResponse:
        if not self._configured:
            return self._not_configured("verify_identity")
        return GovIntegrationResponse(
            integration=self.integration_name,
            operation="verify_identity",
            status=GovIntegrationStatus.SUCCESS,
            verified=None,  # Mock does NOT set verified=True -- only real API can
            message=f"Mock identity check executed. {self.DEMO_MARKER}",
            external_reference="TEST-REF-000",
            metadata={"is_mock": True, "demo_marker": self.DEMO_MARKER},
        )

    async def verify_document(self, request: dict[str, Any]) -> GovIntegrationResponse:
        if not self._configured:
            return self._not_configured("verify_document")
        return GovIntegrationResponse(
            integration=self.integration_name,
            operation="verify_document",
            status=GovIntegrationStatus.SUCCESS,
            verified=None,  # Mock does NOT set verified=True
            message=f"Mock document check executed. {self.DEMO_MARKER}",
            external_reference="TEST-DOC-000",
            metadata={"is_mock": True, "demo_marker": self.DEMO_MARKER},
        )

    async def get_document(self, request: dict[str, Any]) -> GovIntegrationResponse:
        return GovIntegrationResponse(
            integration=self.integration_name,
            operation="get_document",
            status=GovIntegrationStatus.SUCCESS,
            verified=None,
            message=f"Mock document retrieval executed. {self.DEMO_MARKER}",
            metadata={"is_mock": True, "demo_marker": self.DEMO_MARKER},
        )

    async def get_status(self, request: dict[str, Any]) -> GovIntegrationResponse:
        return GovIntegrationResponse(
            integration=self.integration_name,
            operation="get_status",
            status=GovIntegrationStatus.SUCCESS,
            verified=None,
            message=f"Mock status check executed. {self.DEMO_MARKER}",
            metadata={"is_mock": True, "demo_marker": self.DEMO_MARKER},
        )

    async def check_beneficiary(self, request: dict[str, Any]) -> GovIntegrationResponse:
        return GovIntegrationResponse(
            integration=self.integration_name,
            operation="check_beneficiary",
            status=GovIntegrationStatus.SUCCESS,
            verified=None,
            message=f"Mock beneficiary check executed. {self.DEMO_MARKER}",
            metadata={"is_mock": True, "demo_marker": self.DEMO_MARKER},
        )

    async def submit_record(self, request: dict[str, Any]) -> GovIntegrationResponse:
        return GovIntegrationResponse(
            integration=self.integration_name,
            operation="submit_record",
            status=GovIntegrationStatus.SUCCESS,
            verified=None,
            message=f"Mock record submission executed. {self.DEMO_MARKER}",
            request_reference="TEST-REQ-000",
            metadata={"is_mock": True, "demo_marker": self.DEMO_MARKER},
        )
