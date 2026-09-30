"""
Tests for Application submission, status transitions, and deficiency response workflow.
"""

import unittest
import uuid
from datetime import datetime, timezone, date
from models.application import Application, ApplicationStatus, ApplicationStatusHistory
from models.workflow import Deficiency, DeficiencyStatus


class TestApplicationsWorkflow(unittest.TestCase):
    def test_application_status_enum(self):
        """Verify all mandatory application statuses exist."""
        statuses = [s.value for s in ApplicationStatus]
        self.assertIn("draft", statuses)
        self.assertIn("submitted", statuses)
        self.assertIn("deficiency", statuses)
        self.assertIn("resubmitted", statuses)
        self.assertIn("eligible", statuses)
        self.assertIn("selected", statuses)

    def test_deficiency_status_transitions(self):
        """Verify deficiency transitions from OPEN to RESPONDED."""
        app_id = uuid.uuid4()
        user_id = uuid.uuid4()

        deficiency = Deficiency(
            id=uuid.uuid4(),
            application_id=app_id,
            raised_by_id=user_id,
            description="Clear ST caste certificate with official seal is required.",
            document_type_requested="caste_certificate",
            status=DeficiencyStatus.OPEN,
            response_deadline=date(2026, 10, 15),
        )

        self.assertEqual(deficiency.status, DeficiencyStatus.OPEN)
        self.assertIsNone(deficiency.applicant_response)

        # Applicant responds
        deficiency.applicant_response = "Attached digital copy of Tahsildar caste certificate."
        deficiency.status = DeficiencyStatus.RESPONDED
        deficiency.resolved_at = datetime.now(timezone.utc)

        self.assertEqual(deficiency.status, DeficiencyStatus.RESPONDED)
        self.assertIsNotNone(deficiency.applicant_response)
        self.assertIsNotNone(deficiency.resolved_at)