"""
Government integrations package — Phase 7.

Exports both legacy stubs (backward compat) and Phase 7 framework.
"""

# Phase 7: Full adapter framework
from integrations.base import (
    ADAPTER_VERSION,
    GovIntegrationStatus,
    GovIntegrationResponse,
    IntegrationName,
    GovernmentIntegrationAdapter,
)
from integrations.adapters import (
    UIDaiAdapter,
    DigiLockerAdapter,
    NSPAdapter,
    DBTAdapter,
    MoTAAdapter,
    MockGovernmentIntegrationAdapter,
)
from integrations.service import GovernmentIntegrationService, get_integration_service

# Legacy stubs (kept for backward compatibility with existing tests)
from integrations.stubs import (
    IntegrationStatus,
    IntegrationResult,
    AadhaarAdapter,
    DigiLockerAdapter as DigiLockerAdapterLegacy,
    DBTAdapter as DBTAdapterLegacy,
    NSPAdapter as NSPAdapterLegacy,
    MoTADashboardAdapter,
    GovernmentIntegrationService as GovernmentIntegrationServiceLegacy,
    government_integration_service,
)

__all__ = [
    # Phase 7
    "ADAPTER_VERSION",
    "GovIntegrationStatus",
    "GovIntegrationResponse",
    "IntegrationName",
    "GovernmentIntegrationAdapter",
    "UIDaiAdapter",
    "NSPAdapter",
    "DBTAdapter",
    "MoTAAdapter",
    "MockGovernmentIntegrationAdapter",
    "GovernmentIntegrationService",
    "get_integration_service",
    # Legacy
    "IntegrationStatus",
    "IntegrationResult",
    "AadhaarAdapter",
    "MoTADashboardAdapter",
    "GovernmentIntegrationServiceLegacy",
    "government_integration_service",
]
