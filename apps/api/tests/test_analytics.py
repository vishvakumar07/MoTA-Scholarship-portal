"""
Phase 6 Tests: Administrative Intelligence, Dashboards & Analytics.

Tests:
1. Authorization & RBAC: Applicants blocked (403), Officers/Admins allowed.
2. Core KPI Aggregation Accuracy: Application volumes, status distribution, demo isolation.
3. Scheme Version Locking in Analytics: Historical applications locked to original version.
4. Document Intelligence Separation: AI processing states vs Authoritative Officer decisions.
5. Deterministic Rule Engine Eligibility Metrics: Strictly from rule engine, never AI.
6. Operational Scrutiny Workload: Factual operational view without artificial scoring/rankings.
7. Processing Timelines: Empirical calculation from timestamps; empty states when absent.
8. Safe CSV Export & PII Minimization: No Aadhaar or bank numbers in exports.
9. Data Source Transparency: Clear declaration of local DB source vs disconnected government systems.
"""

import os
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_at_least_32_chars_long_12345")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "bGV2ZWxfb25lX2VuY3J5cHRpb25fa2V5XzMyYnl0ZXM=")

import unittest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from models.user import User, Role
from models.application import Application, ApplicationStatus, ApplicationStatusHistory
from models.document import (
    Document,
    DocumentStatus,
    DocumentType,
    MalwareScanStatus,
    DocumentExtractedFields,
    DocumentVerificationResult,
)
from models.scheme import Scheme, SchemeVersion, SchemeType, SchemeStatus, SchemeVersionStatus
from models.workflow import EligibilityResult, EligibilityDecision, Deficiency, DeficiencyStatus
from services.analytics_service import AnalyticsService
from routers.analytics import _require_authorized_staff


class TestPhase6Analytics(unittest.TestCase):
    def setUp(self):
        self.officer_id = uuid.uuid4()
        self.applicant_id = uuid.uuid4()
        self.super_admin_id = uuid.uuid4()

        # Roles
        self.officer_role = Role(id=uuid.uuid4(), code="scrutiny_officer", name="scrutiny_officer")
        self.admin_role = Role(id=uuid.uuid4(), code="super_admin", name="super_admin")
        self.applicant_role = Role(id=uuid.uuid4(), code="applicant", name="applicant")

        # Users
        self.officer_user = User(
            id=self.officer_id,
            email="scrutiny@mota.gov.in",
            full_name="Scrutiny Officer Verma",
            password_hash="dummy_hash",
        )
        self.officer_user.roles = [self.officer_role]

        self.super_admin_user = User(
            id=self.super_admin_id,
            email="admin@mota.gov.in",
            full_name="Joint Secretary MoTA",
            password_hash="dummy_hash",
        )
        self.super_admin_user.roles = [self.admin_role]

        self.applicant_user = User(
            id=self.applicant_id,
            email="student@example.com",
            full_name="Jaipal Singh Munda",
            password_hash="dummy_hash",
        )
        self.applicant_user.roles = [self.applicant_role]

    # -------------------------------------------------------------------------
    # 1. AUTHORIZATION & RBAC
    # -------------------------------------------------------------------------
    def test_applicant_blocked_from_admin_analytics(self):
        """Applicants must be rejected with 403 Forbidden from accessing administrative analytics."""
        with self.assertRaises(HTTPException) as ctx:
            _require_authorized_staff(self.applicant_user)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Access restricted to authorised", ctx.exception.detail)

    def test_officers_and_admins_granted_access(self):
        """Scrutiny officers and Super Admins pass authorization check."""
        try:
            _require_authorized_staff(self.officer_user)
            _require_authorized_staff(self.super_admin_user)
        except HTTPException:
            self.fail("_require_authorized_staff raised HTTPException for authorized staff!")

    # -------------------------------------------------------------------------
    # 2. DATA SOURCE TRANSPARENCY & INTEGRITY
    # -------------------------------------------------------------------------
    def test_transparency_metadata_declared(self):
        """Ensure local data source and disconnected external government stubs are explicitly stated."""
        mock_db = MagicMock()
        # Mocking scalar counts to 0
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value.join.return_value.filter.return_value.with_entities.return_value.scalar.return_value = 0
        mock_db.query.return_value.join.return_value.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value.with_entities.return_value.scalar.return_value = 0
        mock_db.query.return_value.with_entities.return_value.group_by.return_value.all.return_value = []

        overview = AnalyticsService.get_dashboard_overview(mock_db, include_demo=False)
        self.assertIn("metadata", overview)
        self.assertEqual(overview["metadata"]["data_source"], "Local MoTA Scholarship Management System database")
        self.assertIn("Government integration not connected", overview["metadata"]["government_integration_status"])
        self.assertTrue(overview["metadata"]["is_demo_isolated"])

    # -------------------------------------------------------------------------
    # 3. SCHEME VERSION LOCKING IN ANALYTICS
    # -------------------------------------------------------------------------
    def test_scheme_analytics_preserves_version_locking(self):
        """Verify that applications remain mapped strictly to their locked scheme_version_id."""
        scheme_id = uuid.uuid4()
        scheme = Scheme(
            id=scheme_id,
            code="POST_MATRIC",
            name="Post Matric Scholarship for ST Students",
            short_name="Post-Matric ST",
            scheme_type=SchemeType.CENTRALLY_SPONSORED,
            status=SchemeStatus.ACTIVE,
            display_order=1,
            is_deleted=False,
        )

        v1_id = uuid.uuid4()
        v2_id = uuid.uuid4()

        v1 = SchemeVersion(
            id=v1_id,
            scheme_id=scheme_id,
            version_number="1.0",
            academic_year="2025-26",
            version_status=SchemeVersionStatus.PUBLISHED,
            is_accepting_applications=False,
            is_deleted=False,
            effective_from=datetime.now(timezone.utc).date(),
        )

        v2 = SchemeVersion(
            id=v2_id,
            scheme_id=scheme_id,
            version_number="2.0",
            academic_year="2026-27",
            version_status=SchemeVersionStatus.PUBLISHED,
            is_accepting_applications=True,
            is_deleted=False,
            effective_from=datetime.now(timezone.utc).date(),
        )

        mock_db = MagicMock()

        def query_side_effect(model, *args):
            m = MagicMock()
            if model is Scheme:
                m.filter.return_value.order_by.return_value.all.return_value = [scheme]
            elif model is SchemeVersion:
                m.filter.return_value.order_by.return_value.all.return_value = [v2, v1]
            elif model is Application:
                m.filter.return_value.count.return_value = 5
                m.filter.return_value.group_by.return_value.all.return_value = [
                    (ApplicationStatus.SUBMITTED, 3),
                    (ApplicationStatus.DEFICIENCY, 2),
                ]
            else:
                m.filter.return_value.group_by.return_value.all.return_value = [
                    (ApplicationStatus.SUBMITTED, 3),
                    (ApplicationStatus.DEFICIENCY, 2),
                ]
            return m

        mock_db.query.side_effect = query_side_effect

        results = AnalyticsService.get_scheme_analytics(mock_db, include_demo=False)
        self.assertEqual(len(results), 2)
        v_numbers = [r["version_number"] for r in results]
        self.assertIn("1.0", v_numbers)
        self.assertIn("2.0", v_numbers)
        for r in results:
            self.assertTrue(r["version_locking_verified"])

    # -------------------------------------------------------------------------
    # 4. DETERMINISTIC ELIGIBILITY VS AI SEPARATION
    # -------------------------------------------------------------------------
    def test_eligibility_metrics_rule_engine_exclusive(self):
        """Verify eligibility analytics are generated strictly from deterministic rule results."""
        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.with_entities.return_value.scalar.return_value = 10
        mock_db.query.return_value.join.return_value.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = [
            (EligibilityDecision.ELIGIBLE, 7),
            (EligibilityDecision.INELIGIBLE, 3),
        ]
        mock_db.query.return_value.join.return_value.filter.return_value.filter.return_value.with_entities.return_value.all.return_value = [
            (["Family annual income exceeds Rs. 2,50,000 threshold", "Valid ST certificate required"],),
            (["Family annual income exceeds Rs. 2,50,000 threshold"],),
        ]

        elig_analytics = AnalyticsService.get_eligibility_analytics(mock_db, include_demo=False)
        self.assertEqual(elig_analytics["total_evaluated"], 10)
        self.assertEqual(elig_analytics["decisions"]["eligible"], 7)
        self.assertEqual(elig_analytics["decisions"]["ineligible"], 3)
        self.assertIn("MoTA Deterministic Rule Engine", elig_analytics["evaluation_engine"])
        self.assertIn("strictly excluded from eligibility counts", elig_analytics["ai_separation_guarantee"])
        self.assertTrue(len(elig_analytics["common_failure_reasons"]) > 0)
        self.assertEqual(elig_analytics["common_failure_reasons"][0]["count"], 2)

    # -------------------------------------------------------------------------
    # 5. SCRUTINY WORKLOAD OPERATIONAL INTEGRITY
    # -------------------------------------------------------------------------
    def test_workload_analytics_no_artificial_scores(self):
        """Scrutiny workload metrics provide operational counts only, avoiding subjective scores/rankings."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.distinct.return_value.all.return_value = [
            self.officer_user
        ]

        workload = AnalyticsService.get_workload_analytics(mock_db)
        self.assertTrue(workload["has_assignment_data"])
        self.assertEqual(len(workload["officer_workloads"]), 1)
        off_data = workload["officer_workloads"][0]
        # Invariant: No artificial rating or performance rank
        self.assertNotIn("performance_score", off_data)
        self.assertNotIn("rank", off_data)
        self.assertNotIn("speed_grade", off_data)
        self.assertIn("Operational workload distribution only", workload["note"])

    # -------------------------------------------------------------------------
    # 6. PROCESSING TIMELINE FROM REAL TIMESTAMPS
    # -------------------------------------------------------------------------
    def test_processing_times_empty_state_when_no_timestamps(self):
        """When no transition timestamps exist, returns clear 'No data available' empty state."""
        mock_db = MagicMock()
        # Mock transitions query returning empty list
        mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = []
        # Mock deficiencies returning empty
        mock_db.query.return_value.filter.return_value.all.return_value = []

        times = AnalyticsService.get_processing_times(mock_db)
        self.assertIsNone(times["submission_to_first_review"]["average_days"])
        self.assertEqual(times["submission_to_first_review"]["status"], "No data available yet")
        self.assertIsNone(times["deficiency_resolution"]["average_days"])
        self.assertEqual(times["deficiency_resolution"]["status"], "No resolved deficiencies yet")

    # -------------------------------------------------------------------------
    # 7. PRIVACY-PRESERVING CSV EXPORT (PII MINIMIZATION)
    # -------------------------------------------------------------------------
    def test_csv_export_pii_minimization(self):
        """Exported CSVs must NEVER include Aadhaar, bank accounts, passwords, or raw certificates."""
        mock_db = MagicMock()
        # Setup dummy application
        app = Application(
            id=uuid.uuid4(),
            applicant_id=self.applicant_id,
            scheme_version_id=uuid.uuid4(),
            reference_number="MOTA/POST/2026/001",
            status=ApplicationStatus.SUBMITTED,
            submitted_at=datetime.now(timezone.utc),
        )
        mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (app, "POST_MATRIC", "1.0")
        ]

        csv_text = AnalyticsService.export_csv(mock_db, report_type="applications")
        self.assertIn("MOTA/POST/2026/001", csv_text)
        self.assertIn("POST_MATRIC", csv_text)

        # Mandatory PII Absence Check
        self.assertNotIn("aadhaar", csv_text.lower())
        self.assertNotIn("bank_account", csv_text.lower())
        self.assertNotIn("password", csv_text.lower())
        self.assertNotIn("ifsc", csv_text.lower())


if __name__ == "__main__":
    unittest.main()
