"""
Government integration stubs.

All government integrations return REQUIRES_AUTHORIZED_ACCESS by default.

NO fake government API responses are generated.
The UI clearly communicates integration status.

Live adapters will be implemented when:
- Authorized API credentials are provided
- API specifications are available
- Integration is explicitly requested
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    REQUIRES_AUTHORIZED_ACCESS = "requires_authorized_access"
    CONFIGURATION_REQUIRED = "configuration_required"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"


@dataclass
class IntegrationResult:
    status: IntegrationStatus
    message: str
    data: dict | None = None
    verified: bool | None = None  # None = not verified (not False = failed)


#  -  - - Aadhaar Adapter  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class AadhaarAdapter:
    """
    Aadhaar verification via UIDAI API.
    Stub: returns REQUIRES_AUTHORIZED_ACCESS.
    """

    def verify(self, aadhaar_hash: str, dob: str, name: str) -> IntegrationResult:
        return IntegrationResult(
            status=IntegrationStatus.REQUIRES_AUTHORIZED_ACCESS,
            message=(
                "Aadhaar verification requires authorized UIDAI API access. "
                "Contact MoTA IT division for integration credentials. "
                "This feature is not available in the SIH prototype."
            ),
            verified=None,
        )


#  -  - - DigiLocker Adapter  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class DigiLockerAdapter:
    """
    DigiLocker document fetch.
    Stub: returns REQUIRES_AUTHORIZED_ACCESS.
    """

    def fetch_document(self, user_token: str, document_type: str) -> IntegrationResult:
        return IntegrationResult(
            status=IntegrationStatus.REQUIRES_AUTHORIZED_ACCESS,
            message=(
                "DigiLocker integration requires authorized API credentials. "
                "This feature is not available in the SIH prototype."
            ),
        )


#  -  - - DBT Adapter  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class DBTAdapter:
    """
    DBT portal integration for disbursement status.
    Stub: returns REQUIRES_AUTHORIZED_ACCESS.
    """

    def get_disbursement_status(self, application_id: str, scheme_code: str) -> IntegrationResult:
        return IntegrationResult(
            status=IntegrationStatus.REQUIRES_AUTHORIZED_ACCESS,
            message=(
                "DBT Portal integration requires authorized API access. "
                "Live disbursement data is not available in the SIH prototype. "
                "Visit https://dbttribal.gov.in/ for official disbursement records."
            ),
        )


#  -  - - NSP Adapter  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class NSPAdapter:
    """
    National Scholarship Portal integration.
    Stub: returns REQUIRES_AUTHORIZED_ACCESS.
    """

    def get_application_status(self, nsp_application_id: str) -> IntegrationResult:
        return IntegrationResult(
            status=IntegrationStatus.REQUIRES_AUTHORIZED_ACCESS,
            message=(
                "NSP integration requires authorized API access. "
                "Visit https://scholarships.gov.in for official NSP portal."
            ),
        )


#  -  - - MoTA Dashboard Adapter  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class MoTADashboardAdapter:
    """
    MoTA Dashboard API for official statistics.
    Stub: returns REQUIRES_AUTHORIZED_ACCESS.

    Note: Published statistics from dashboard.tribal.gov.in are shown
    in the UI from the seed data (with source attribution). Live/real-time
    figures require API integration.
    """

    def get_scheme_statistics(self, scheme_code: str) -> IntegrationResult:
        return IntegrationResult(
            status=IntegrationStatus.REQUIRES_AUTHORIZED_ACCESS,
            message=(
                "MoTA Dashboard API integration requires authorized access. "
                "Published official statistics are available at https://dashboard.tribal.gov.in"
            ),
        )


#  -  - - Service Bundle  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class GovernmentIntegrationService:
    """
    Bundle of all government integration adapters.
    All are stubs unless explicitly configured with authorized credentials.
    """

    def __init__(self):
        self.aadhaar = AadhaarAdapter()
        self.digilocker = DigiLockerAdapter()
        self.dbt = DBTAdapter()
        self.nsp = NSPAdapter()
        self.mota_dashboard = MoTADashboardAdapter()

    @property
    def integration_status_summary(self) -> dict:
        return {
            "aadhaar": "stub  -  requires UIDAI authorization",
            "digilocker": "stub  -  requires authorized credentials",
            "dbt": "stub  -  requires DBT portal authorization",
            "nsp": "stub  -  requires NSP API authorization",
            "mota_dashboard": "stub  -  requires MoTA Dashboard API authorization",
        }


government_integration_service = GovernmentIntegrationService()
