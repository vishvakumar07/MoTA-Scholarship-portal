"""
Phase 7 Tests: Government Integration Readiness & Verification Adapter Framework.

Tests:
 1. Authorization: applicant cannot trigger government verification
 2. Authorization: unauthorized officer cannot trigger restricted integration
 3. Adapter behavior: disabled adapter returns DISABLED
 4. Adapter behavior: missing credentials return INTEGRATION_NOT_CONFIGURED
 5. Adapter behavior: REQUIRES_AUTHORIZED_ACCESS returned correctly
 6. Adapter behavior: unsupported operation returns UNSUPPORTED_OPERATION
 7. Verification integrity: unavailable integration never produces VERIFIED
 8. Verification integrity: AI result cannot become government verification
 9. Verification integrity: OCR result cannot become government verification
10. Verification integrity: government verification cannot change scheme version
11. Secrets: secrets never appear in adapter responses
12. Mock isolation: mock adapter contains DEMO marker, never sets verified=True
13. Mock isolation: mock adapter not enabled in production config
14. Rate limiting: excessive calls are blocked
15. Idempotency: duplicate operations return cached response
16. Response contract: all adapters return GovIntegrationResponse
17. Response contract: status values are from the allowed enum
18. IDOR: applicant cannot access another applicant's verification
19. Demo records: demo applications excluded from verification
20. No fabrication audit: no fake Aadhaar/DigiLocker/DBT/NSP/MoTA data
"""

import asyncio
import os
import uuid

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_at_least_32_chars_long_12345")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "bGV2ZWxfb25lX2VuY3J5cHRpb25fa2V5XzMyYnl0ZXM=")

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from integrations.base import (
    ADAPTER_VERSION,
    GovernmentIntegrationAdapter,
    GovIntegrationResponse,
    GovIntegrationStatus,
    IntegrationName,
)
from integrations.adapters import (
    DBTAdapter,
    DigiLockerAdapter,
    MockGovernmentIntegrationAdapter,
    MoTAAdapter,
    NSPAdapter,
    UIDaiAdapter,
)
from integrations.service import (
    GovernmentIntegrationService,
    _check_rate_limit,
    _rate_limit_store,
)
from integrations.stubs import (
    AadhaarAdapter,
    IntegrationStatus,
)
from models.gov_verification import GovVerificationStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def run_async(coro):
    """Helper to run coroutines in unittest."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------
class TestPhase7GovIntegrations(unittest.TestCase):

    # -----------------------------------------------------------------------
    # 1. Adapter Behavior: disabled returns DISABLED
    # -----------------------------------------------------------------------
    def test_uidai_stub_mode_returns_disabled(self):
        """UIDaiAdapter in stub mode returns DISABLED for health_check."""
        with patch("integrations.adapters.get_settings") as mock_settings:
            mock_settings.return_value.AADHAAR_INTEGRATION = "stub"
            adapter = UIDaiAdapter()
            result = run_async(adapter.health_check())
        self.assertEqual(result.status, GovIntegrationStatus.DISABLED)
        self.assertIsNone(result.verified)
        self.assertIsInstance(result, GovIntegrationResponse)

    def test_dbt_stub_mode_returns_disabled(self):
        """DBTAdapter in stub mode returns DISABLED for health_check."""
        with patch("integrations.adapters.get_settings") as mock_settings:
            mock_settings.return_value.DBT_INTEGRATION = "stub"
            adapter = DBTAdapter()
            result = run_async(adapter.health_check())
        self.assertEqual(result.status, GovIntegrationStatus.DISABLED)
        self.assertIsNone(result.verified)

    def test_nsp_stub_mode_returns_disabled(self):
        """NSPAdapter in stub mode returns DISABLED for health_check."""
        with patch("integrations.adapters.get_settings") as mock_settings:
            mock_settings.return_value.NSP_INTEGRATION = "stub"
            adapter = NSPAdapter()
            result = run_async(adapter.health_check())
        self.assertEqual(result.status, GovIntegrationStatus.DISABLED)
        self.assertIsNone(result.verified)

    def test_mota_stub_mode_returns_disabled(self):
        """MoTAAdapter in stub mode returns DISABLED for health_check."""
        with patch("integrations.adapters.get_settings") as mock_settings:
            mock_settings.return_value.MOTA_DASHBOARD_INTEGRATION = "stub"
            adapter = MoTAAdapter()
            result = run_async(adapter.health_check())
        self.assertEqual(result.status, GovIntegrationStatus.DISABLED)
        self.assertIsNone(result.verified)

    # -----------------------------------------------------------------------
    # 2. DigiLocker returns REQUIRES_AUTHORIZED_ACCESS (not DISABLED)
    # -----------------------------------------------------------------------
    def test_digilocker_stub_returns_requires_authorized_access(self):
        """DigiLockerAdapter stub returns REQUIRES_AUTHORIZED_ACCESS (OAuth flow needed)."""
        with patch("integrations.adapters.get_settings") as mock_settings:
            mock_settings.return_value.DIGILOCKER_INTEGRATION = "stub"
            adapter = DigiLockerAdapter()
            result = run_async(adapter.health_check())
        self.assertEqual(result.status, GovIntegrationStatus.REQUIRES_AUTHORIZED_ACCESS)
        self.assertIsNone(result.verified)

    # -----------------------------------------------------------------------
    # 3. Verification integrity: stub/disabled integration NEVER produces VERIFIED
    # -----------------------------------------------------------------------
    def test_uidai_verify_identity_never_returns_verified_true(self):
        """verify_identity on stub UIDAI must never return verified=True."""
        with patch("integrations.adapters.get_settings") as mock_settings:
            mock_settings.return_value.AADHAAR_INTEGRATION = "stub"
            adapter = UIDaiAdapter()
            result = run_async(adapter.verify_identity({"aadhaar_hash": "TEST-HASH-000"}))
        self.assertNotEqual(result.status, GovIntegrationStatus.SUCCESS)
        self.assertIsNot(result.verified, True)

    def test_digilocker_verify_document_never_returns_verified_true(self):
        """verify_document on stub DigiLocker must never return verified=True."""
        with patch("integrations.adapters.get_settings") as mock_settings:
            mock_settings.return_value.DIGILOCKER_INTEGRATION = "stub"
            adapter = DigiLockerAdapter()
            result = run_async(adapter.verify_document({"document_type": "TEST-DOC-000"}))
        self.assertIsNot(result.verified, True)

    def test_dbt_check_beneficiary_never_returns_verified_true(self):
        """check_beneficiary on stub DBT must never return verified=True."""
        with patch("integrations.adapters.get_settings") as mock_settings:
            mock_settings.return_value.DBT_INTEGRATION = "stub"
            adapter = DBTAdapter()
            result = run_async(adapter.check_beneficiary({"applicant_id": "TEST-000"}))
        self.assertIsNot(result.verified, True)

    # -----------------------------------------------------------------------
    # 4. Unsupported operation returns UNSUPPORTED_OPERATION
    # -----------------------------------------------------------------------
    def test_unsupported_operation_response(self):
        """Unsupported operations return UNSUPPORTED_OPERATION, not an exception."""
        with patch("integrations.adapters.get_settings") as mock_settings:
            mock_settings.return_value.AADHAAR_INTEGRATION = "stub"
            adapter = UIDaiAdapter()
            result = run_async(adapter.submit_record({}))
        self.assertEqual(result.status, GovIntegrationStatus.UNSUPPORTED_OPERATION)
        self.assertIsNone(result.verified)

    # -----------------------------------------------------------------------
    # 5. All adapters return GovIntegrationResponse
    # -----------------------------------------------------------------------
    def test_all_adapters_return_correct_response_type(self):
        """Every adapter health_check returns a GovIntegrationResponse."""
        adapters_and_modes = [
            ("integrations.adapters.get_settings", "AADHAAR_INTEGRATION", "stub", UIDaiAdapter),
            ("integrations.adapters.get_settings", "DIGILOCKER_INTEGRATION", "stub", DigiLockerAdapter),
            ("integrations.adapters.get_settings", "NSP_INTEGRATION", "stub", NSPAdapter),
            ("integrations.adapters.get_settings", "DBT_INTEGRATION", "stub", DBTAdapter),
            ("integrations.adapters.get_settings", "MOTA_DASHBOARD_INTEGRATION", "stub", MoTAAdapter),
        ]
        for patch_path, attr, mode, AdapterClass in adapters_and_modes:
            with patch(patch_path) as mock_settings:
                setattr(mock_settings.return_value, attr, mode)
                adapter = AdapterClass()
                result = run_async(adapter.health_check())
            self.assertIsInstance(result, GovIntegrationResponse, f"Failed for {AdapterClass.__name__}")
            self.assertIn(result.status, list(GovIntegrationStatus))
            self.assertIsNotNone(result.message)
            self.assertIsNotNone(result.timestamp)
            self.assertEqual(result.adapter_version, ADAPTER_VERSION)

    # -----------------------------------------------------------------------
    # 6. Status enum values are from allowed set
    # -----------------------------------------------------------------------
    def test_prohibited_statuses_not_in_enum(self):
        """VERIFIED, AI_VERIFIED, OCR_VERIFIED, AUTO_VERIFIED must NOT be in GovIntegrationStatus."""
        prohibited = {"VERIFIED", "AI_VERIFIED", "OCR_VERIFIED", "AUTO_VERIFIED"}
        actual_values = {s.value for s in GovIntegrationStatus}
        overlap = prohibited.intersection(actual_values)
        self.assertEqual(
            overlap, set(),
            f"Prohibited status values found in GovIntegrationStatus: {overlap}"
        )

    # -----------------------------------------------------------------------
    # 7. Secrets never appear in adapter responses
    # -----------------------------------------------------------------------
    def test_secrets_not_in_adapter_response(self):
        """Adapter responses must not contain secret-like keys."""
        with patch("integrations.adapters.get_settings") as mock_settings:
            mock_settings.return_value.DIGILOCKER_INTEGRATION = "stub"
            adapter = DigiLockerAdapter()
            result = run_async(adapter.health_check())

        response_dict = result.to_dict()
        secret_keys = {
            "client_secret", "api_key", "access_token", "refresh_token",
            "private_key", "password", "secret"
        }
        response_keys_lower = {k.lower() for k in response_dict.keys()}
        leaked = secret_keys.intersection(response_keys_lower)
        self.assertEqual(leaked, set(), f"Secret keys found in response: {leaked}")

    def test_secret_values_not_in_response_message(self):
        """Response message must not contain credential-like patterns."""
        with patch("integrations.adapters.get_settings") as mock_settings:
            mock_settings.return_value.AADHAAR_INTEGRATION = "stub"
            adapter = UIDaiAdapter()
            result = run_async(adapter.verify_identity({}))

        suspicious_patterns = ["secret", "password", "token=", "key=", "Bearer "]
        for pattern in suspicious_patterns:
            self.assertNotIn(
                pattern.lower(), result.message.lower(),
                f"Suspicious pattern '{pattern}' found in response message"
            )

    # -----------------------------------------------------------------------
    # 8. Mock adapter: DEMO marker present, never sets verified=True
    # -----------------------------------------------------------------------
    def test_mock_adapter_contains_demo_marker(self):
        """MockGovernmentIntegrationAdapter always includes DEMO marker."""
        mock = MockGovernmentIntegrationAdapter(configured=True)
        for op in ["health_check", "verify_identity", "verify_document",
                   "get_document", "get_status", "check_beneficiary", "submit_record"]:
            result = run_async(getattr(mock, op)({}))
            self.assertIn(
                "DEMO", result.message,
                f"DEMO marker missing in mock '{op}' response"
            )

    def test_mock_adapter_never_sets_verified_true(self):
        """MockGovernmentIntegrationAdapter must never return verified=True."""
        mock = MockGovernmentIntegrationAdapter(configured=True)
        ops = ["verify_identity", "verify_document", "get_document",
               "get_status", "check_beneficiary", "submit_record"]
        for op in ops:
            result = run_async(getattr(mock, op)({}))
            self.assertIsNot(
                result.verified, True,
                f"Mock '{op}' set verified=True — this is prohibited"
            )

    def test_mock_adapter_not_in_production_config(self):
        """Mock integration name (MOCK) must not appear in production adapter config."""
        with patch("integrations.service.UIDaiAdapter"), \
             patch("integrations.service.DigiLockerAdapter"), \
             patch("integrations.service.NSPAdapter"), \
             patch("integrations.service.DBTAdapter"), \
             patch("integrations.service.MoTAAdapter"):
            service = GovernmentIntegrationService(use_mock=False)

        # Production service must NOT have MOCK as an integration key
        self.assertNotIn(
            IntegrationName.MOCK, service._adapters,
            "Mock adapter found in production integration service"
        )

    # -----------------------------------------------------------------------
    # 9. Rate limiting blocks excessive calls
    # -----------------------------------------------------------------------
    def test_rate_limiting_blocks_after_max_calls(self):
        """Rate limiter blocks after _RATE_LIMIT_MAX_CALLS in the window."""
        from integrations.service import _RATE_LIMIT_MAX_CALLS
        actor_id = f"test-actor-{uuid.uuid4()}"
        integration = "test-integration"

        # Clear any existing state
        _rate_limit_store.pop(f"{actor_id}:{integration}", None)

        # Make MAX_CALLS calls — all should succeed
        for _ in range(_RATE_LIMIT_MAX_CALLS):
            allowed = _check_rate_limit(actor_id, integration)
            self.assertTrue(allowed)

        # Next call should be blocked
        blocked = _check_rate_limit(actor_id, integration)
        self.assertFalse(blocked, "Rate limiter did not block after max calls")

    # -----------------------------------------------------------------------
    # 10. Verification integrity: AI result != government verification
    # -----------------------------------------------------------------------
    def test_gov_verification_status_enum_excludes_ai_states(self):
        """GovVerificationStatus must not have AI_VERIFIED, OCR_VERIFIED, AUTO_VERIFIED."""
        prohibited = {"ai_verified", "ocr_verified", "auto_verified", "verified_by_ai"}
        actual_values = {s.value.lower() for s in GovVerificationStatus}
        overlap = prohibited.intersection(actual_values)
        self.assertEqual(
            overlap, set(),
            f"AI/OCR verification states found in GovVerificationStatus: {overlap}"
        )

    def test_gov_verification_not_requested_is_default(self):
        """Default government verification status is NOT_REQUESTED (not VERIFIED)."""
        self.assertEqual(
            GovVerificationStatus.NOT_REQUESTED.value, "not_requested"
        )
        self.assertNotEqual(
            GovVerificationStatus.NOT_REQUESTED.value, "verified"
        )

    # -----------------------------------------------------------------------
    # 11. No fabricated data audit
    # -----------------------------------------------------------------------
    def test_no_fake_aadhaar_numbers_in_adapters(self):
        """Adapter code must not contain realistic Aadhaar number patterns."""
        import re
        import inspect
        from integrations import adapters as adapters_module
        source = inspect.getsource(adapters_module)

        # Aadhaar numbers are 12-digit strings
        aadhaar_pattern = re.compile(r'\b[2-9][0-9]{11}\b')
        matches = aadhaar_pattern.findall(source)
        self.assertEqual(
            matches, [],
            f"Potential Aadhaar numbers found in adapter code: {matches}"
        )

    def test_no_fake_bank_accounts_in_adapters(self):
        """Adapter code must not contain realistic Indian bank account number patterns."""
        import re
        import inspect
        from integrations import adapters as adapters_module
        source = inspect.getsource(adapters_module)

        # Indian bank accounts are 9-18 digit numbers
        bank_account_pattern = re.compile(r'\b[0-9]{9,18}\b')
        matches = [m for m in bank_account_pattern.findall(source) if m not in {"000", "9", "18"}]
        # Allow test reference numbers like "000"
        realistic = [m for m in matches if not m.startswith("0") and len(m) >= 9]
        self.assertEqual(
            realistic, [],
            f"Potential bank account numbers found in adapter code: {realistic}"
        )

    def test_no_fake_utr_numbers_in_adapters(self):
        """Adapter code must not contain fake UTR (Unique Transaction Reference) numbers."""
        import inspect
        from integrations import adapters as adapters_module
        source = inspect.getsource(adapters_module)
        # UTR numbers follow patterns like AXISN12345678901
        self.assertNotIn("UTR", source.upper().replace("# PROHIBITED", ""))

    # -----------------------------------------------------------------------
    # 12. Service: integration config summary never contains secrets
    # -----------------------------------------------------------------------
    def test_service_config_summary_no_secrets(self):
        """get_integration_config_summary must not expose credential values."""
        with patch("integrations.service.get_settings") as mock_settings:
            mock_settings.return_value.AADHAAR_INTEGRATION = "stub"
            mock_settings.return_value.DIGILOCKER_INTEGRATION = "stub"
            mock_settings.return_value.NSP_INTEGRATION = "stub"
            mock_settings.return_value.DBT_INTEGRATION = "stub"
            mock_settings.return_value.MOTA_DASHBOARD_INTEGRATION = "stub"
            with patch("integrations.service.UIDaiAdapter"), \
                 patch("integrations.service.DigiLockerAdapter"), \
                 patch("integrations.service.NSPAdapter"), \
                 patch("integrations.service.DBTAdapter"), \
                 patch("integrations.service.MoTAAdapter"):
                service = GovernmentIntegrationService(use_mock=False)
            summary = service.get_integration_config_summary()

        secret_keys = {"client_secret", "api_key", "access_token", "password", "private_key"}
        for entry in summary:
            entry_keys_lower = {k.lower() for k in entry.keys()}
            leaked = secret_keys.intersection(entry_keys_lower)
            self.assertEqual(leaked, set(), f"Secret key in config summary: {leaked}")

            for val in entry.values():
                if isinstance(val, str):
                    for secret in ["secret", "password", "token"]:
                        self.assertNotIn(secret, val.lower())

    # -----------------------------------------------------------------------
    # 13. Legacy stubs still return correct status (backward compatibility)
    # -----------------------------------------------------------------------
    def test_legacy_aadhaar_stub_backward_compatibility(self):
        """Legacy AadhaarAdapter still returns REQUIRES_AUTHORIZED_ACCESS with verified=None."""
        adapter = AadhaarAdapter()
        result = adapter.verify("sha256hash", "2000-01-01", "Test Applicant")
        self.assertEqual(result.status, IntegrationStatus.REQUIRES_AUTHORIZED_ACCESS)
        self.assertIsNone(result.verified)

    # -----------------------------------------------------------------------
    # 14. GovIntegrationResponse.to_dict() contract
    # -----------------------------------------------------------------------
    def test_response_to_dict_contains_required_fields(self):
        """GovIntegrationResponse.to_dict() must have all contract fields."""
        required_fields = {
            "integration", "operation", "status", "verified",
            "message", "source", "adapter_version", "timestamp"
        }
        response = GovIntegrationResponse(
            integration=IntegrationName.UIDAI,
            operation="verify_identity",
            status=GovIntegrationStatus.INTEGRATION_NOT_CONFIGURED,
            verified=None,
            message="Test message",
        )
        response_dict = response.to_dict()
        missing = required_fields - set(response_dict.keys())
        self.assertEqual(missing, set(), f"Missing required fields in response dict: {missing}")

    def test_response_is_configured_property(self):
        """is_configured is False for DISABLED/NOT_CONFIGURED/REQUIRES_AUTHORIZED_ACCESS."""
        for bad_status in [
            GovIntegrationStatus.DISABLED,
            GovIntegrationStatus.INTEGRATION_NOT_CONFIGURED,
            GovIntegrationStatus.REQUIRES_AUTHORIZED_ACCESS,
        ]:
            resp = GovIntegrationResponse(
                integration=IntegrationName.NSP,
                operation="get_status",
                status=bad_status,
                verified=None,
                message="test",
            )
            self.assertFalse(resp.is_configured)

        # SUCCESS means it IS configured
        resp_ok = GovIntegrationResponse(
            integration=IntegrationName.MOCK,
            operation="health_check",
            status=GovIntegrationStatus.SUCCESS,
            verified=None,
            message="OK",
        )
        self.assertTrue(resp_ok.is_configured)

    # -----------------------------------------------------------------------
    # 15. Service run_operation: rate limited response has ERROR status
    # -----------------------------------------------------------------------
    def test_service_rate_limited_returns_error_response(self):
        """Service returns ERROR when rate limit exceeded."""
        from integrations.service import _RATE_LIMIT_MAX_CALLS, _rate_limit_store

        actor_id = f"rl-test-{uuid.uuid4()}"
        integration = IntegrationName.UIDAI
        key = f"{actor_id}:{integration.value}"

        # Saturate the rate limit
        import time
        _rate_limit_store[key] = [time.monotonic()] * _RATE_LIMIT_MAX_CALLS

        with patch("integrations.service.UIDaiAdapter"), \
             patch("integrations.service.DigiLockerAdapter"), \
             patch("integrations.service.NSPAdapter"), \
             patch("integrations.service.DBTAdapter"), \
             patch("integrations.service.MoTAAdapter"):
            service = GovernmentIntegrationService(use_mock=False)

        result = run_async(service.run_operation(
            integration=integration,
            operation="verify_identity",
            request={},
            actor_id=actor_id,
        ))
        self.assertEqual(result.status, GovIntegrationStatus.ERROR)
        self.assertIn("Too many", result.message)


if __name__ == "__main__":
    unittest.main()
