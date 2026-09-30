"""
Phase 9: Notifications, Case Management & Operational Scrutiny Workflow Test Suite.

Verified behaviors:
  1. Notification service provider abstractions (InApp, Email, SMS, Mock).
  2. Duplicate notification suppression within deduplication window.
  3. Notification API endpoints: unread count, mark-read, IDOR protection.
  4. Work queue RBAC: applicant blocked (403), officer permitted.
  5. Case assignment: applicant blocked (403), officer succeeds with audit records.
  6. Case notes: applicant blocked (403), officer can add internal notes.
  7. Deficiency lifecycle: raised by officer creates {Deficiency, Notification, AuditLog, CaseTimelineEvent}.
  8. Deficiency resolution by authorized officer.
  9. Timeline service: internal events excluded for applicants.
 10. Timeline IDOR: applicant cannot view another applicant's timeline.
 11. TimelineEventType enum completeness check.
"""

import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_at_least_32_chars_long_12345")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "bGV2ZWxfb25lX2VuY3J5cHRpb25fa2V5XzMyYnl0ZXM=")

from database import get_db
from main import app
from models.application import Application, ApplicationStatus, ApplicationStatusHistory
from models.case import (
    CaseAssignment,
    CaseNote,
    CaseTimelineEvent,
    TimelineEventType,
)
from models.system import AuditLog, Notification, NotificationChannel, NotificationStatus
from models.user import Role, User
from models.workflow import Deficiency, DeficiencyStatus
from routers.cases import _require_officer
from security.rbac import get_current_user
from services.notification_service import (
    DeliveryResult,
    EmailNotificationProvider,
    InAppNotificationProvider,
    MockEmailProvider,
    MockSMSProvider,
    NotificationCategory,
    NotificationService,
    SMSNotificationProvider,
)
from services.timeline_service import CaseTimelineService


def _make_app_obj(app_id, applicant_id, status=ApplicationStatus.SUBMITTED):
    """Helper: construct minimal Application without DB."""
    return Application(
        id=app_id,
        applicant_id=applicant_id,
        scheme_version_id=uuid.uuid4(),
        reference_number=f"REF-{str(app_id)[:8]}",
        status=status,
        submitted_at=datetime.now(timezone.utc),
        assigned_officer_id=None,
        updated_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        internal_notes=None,
        is_demo=False,
    )


class TestPhase9CasesAndNotifications(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

        self.applicant_id = uuid.uuid4()
        self.other_applicant_id = uuid.uuid4()
        self.officer_id = uuid.uuid4()

        self.applicant_role = Role(id=uuid.uuid4(), code="applicant", name="applicant")
        self.officer_role = Role(id=uuid.uuid4(), code="scrutiny_officer", name="scrutiny_officer")

        self.applicant_user = User(
            id=self.applicant_id,
            email="applicant@example.com",
            full_name="Jaipal Singh Munda",
            is_active=True,
        )
        self.applicant_user.roles = [self.applicant_role]

        self.officer_user = User(
            id=self.officer_id,
            email="officer@mota.gov.in",
            full_name="Scrutiny Officer",
            is_active=True,
        )
        self.officer_user.roles = [self.officer_role]

        self.app_id = uuid.uuid4()
        self.test_application = _make_app_obj(self.app_id, self.applicant_id)

    def tearDown(self):
        app.dependency_overrides.clear()

    # -----------------------------------------------------------------------
    # 1. Notification Service Provider Abstractions
    # -----------------------------------------------------------------------
    def test_inapp_provider_creates_notification_record(self):
        """InAppNotificationProvider persists Notification to DB."""
        mock_db = MagicMock()
        provider = InAppNotificationProvider(mock_db)

        result = provider.send(
            recipient_id=self.applicant_id,
            recipient_contact=None,
            title="Application Submitted",
            body="Your NFST application has been received.",
        )
        self.assertEqual(result.channel, NotificationChannel.IN_APP)
        self.assertEqual(result.status, NotificationStatus.SENT)
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    def test_email_provider_reports_skipped_when_not_configured(self):
        """EmailNotificationProvider returns SKIPPED with not-configured detail."""
        provider = EmailNotificationProvider()
        result = provider.send(self.applicant_id, "test@example.com", "Title", "Body")
        self.assertEqual(result.channel, NotificationChannel.EMAIL)
        self.assertEqual(result.status, NotificationStatus.SKIPPED)
        self.assertIn("not configured", result.detail.lower())

    def test_sms_provider_reports_skipped_when_not_configured(self):
        """SMSNotificationProvider returns SKIPPED with not-configured detail."""
        provider = SMSNotificationProvider()
        result = provider.send(self.applicant_id, "+919999999999", "Title", "Body")
        self.assertEqual(result.channel, NotificationChannel.SMS)
        self.assertEqual(result.status, NotificationStatus.SKIPPED)
        self.assertIn("not configured", result.detail.lower())

    def test_mock_email_provider_marked_demo(self):
        """MockEmailProvider explicitly stamps DEMO / TEST marker."""
        provider = MockEmailProvider()
        result = provider.send(self.applicant_id, "test@example.com", "Title", "Body")
        self.assertIn(MockEmailProvider.DEMO_MARKER, result.detail)

    def test_mock_sms_provider_marked_demo(self):
        """MockSMSProvider explicitly stamps DEMO / TEST marker."""
        provider = MockSMSProvider()
        result = provider.send(self.applicant_id, "+919999999999", "Title", "Body")
        self.assertIn(MockSMSProvider.DEMO_MARKER, result.detail)

    def test_notification_service_suppresses_duplicate_within_window(self):
        """NotificationService returns SKIPPED for duplicate within 10-minute window."""
        mock_db = MagicMock()
        existing_notif = Notification(
            id=uuid.uuid4(),
            recipient_id=self.applicant_id,
            title="Application Submitted",
            body="",
            status=NotificationStatus.SENT,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=2),
            sent_at=datetime.now(timezone.utc) - timedelta(minutes=2),
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_notif

        results = NotificationService.send_notification(
            db=mock_db,
            recipient_id=self.applicant_id,
            title="Application Submitted",
            body="",
            related_entity_id=self.app_id,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, NotificationStatus.SKIPPED)
        self.assertIn("Duplicate", results[0].detail)
        mock_db.add.assert_not_called()

    # -----------------------------------------------------------------------
    # 2. Notification API Endpoints
    # -----------------------------------------------------------------------
    def test_unread_count_endpoint(self):
        """Applicant can get unread notification count."""
        app.dependency_overrides[get_current_user] = lambda: self.applicant_user
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        app.dependency_overrides[get_db] = lambda: mock_db

        res = self.client.get("/api/v1/notifications/unread-count")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["unread_count"], 5)

    def test_mark_read_idor_protection(self):
        """Cannot mark another user's notification as read (404)."""
        app.dependency_overrides[get_current_user] = lambda: self.applicant_user
        notif_id = uuid.uuid4()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        app.dependency_overrides[get_db] = lambda: mock_db

        res = self.client.post(f"/api/v1/notifications/{notif_id}/read")
        self.assertEqual(res.status_code, 404)

    # -----------------------------------------------------------------------
    # 3. Work Queue RBAC
    # -----------------------------------------------------------------------
    def test_applicant_blocked_from_work_queue(self):
        """Applicant gets 403 on work queue."""
        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [("applicant",)]
        app.dependency_overrides[get_current_user] = lambda: self.applicant_user
        app.dependency_overrides[get_db] = lambda: mock_db

        res = self.client.get("/api/v1/admin/work-queue")
        self.assertEqual(res.status_code, 403)

    def test_officer_permitted_on_work_queue(self):
        """Officer can access work queue, receives items+total."""
        # Directly override the _require_officer dependency
        app.dependency_overrides[_require_officer] = lambda: self.officer_user

        mock_db = MagicMock()
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.join.return_value = mock_q
        mock_q.outerjoin.return_value = mock_q
        mock_q.options.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.count.return_value = 0
        mock_q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_q.scalar.return_value = 0
        app.dependency_overrides[get_db] = lambda: mock_db

        res = self.client.get("/api/v1/admin/work-queue")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("items", data)
        self.assertIn("total", data)

    # -----------------------------------------------------------------------
    # 4. Case Assignment RBAC
    # -----------------------------------------------------------------------
    def test_applicant_blocked_from_assignment(self):
        """Applicant gets 403 on case assignment."""
        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [("applicant",)]
        app.dependency_overrides[get_current_user] = lambda: self.applicant_user
        app.dependency_overrides[get_db] = lambda: mock_db

        res = self.client.post(
            f"/api/v1/admin/applications/{self.app_id}/assign",
            json={"assigned_to": str(self.officer_id), "priority": "HIGH"},
        )
        self.assertEqual(res.status_code, 403)

    def test_officer_assigns_case_with_audit(self):
        """Officer assignment creates CaseAssignment + AuditLog."""
        app.dependency_overrides[_require_officer] = lambda: self.officer_user

        mock_db = MagicMock()

        def side_effect(model):
            m = MagicMock()
            if model == Application:
                m.filter.return_value.first.return_value = self.test_application
            elif model == User:
                m.filter.return_value.first.return_value = self.officer_user
            elif model == CaseAssignment:
                m.filter.return_value.first.return_value = None
            else:
                m.filter.return_value.first.return_value = None
            return m

        mock_db.query.side_effect = side_effect
        app.dependency_overrides[get_db] = lambda: mock_db

        res = self.client.post(
            f"/api/v1/admin/applications/{self.app_id}/assign",
            json={"assigned_to_id": str(self.officer_id), "priority": "high", "notes": "Urgent."},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertEqual(res.json()["assigned_to"], self.officer_user.full_name)
        self.assertEqual(res.json()["priority"].lower(), "high")
        added_types = [type(a[0][0]) for a in mock_db.add.call_args_list]
        self.assertIn(CaseAssignment, added_types)
        self.assertIn(AuditLog, added_types)

    # -----------------------------------------------------------------------
    # 5. Case Notes RBAC
    # -----------------------------------------------------------------------
    def test_applicant_blocked_from_notes(self):
        """Applicant gets 403 on case notes endpoint."""
        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [("applicant",)]
        app.dependency_overrides[get_current_user] = lambda: self.applicant_user
        app.dependency_overrides[get_db] = lambda: mock_db

        res = self.client.post(
            f"/api/v1/admin/applications/{self.app_id}/notes",
            json={"note": "Unauthorized"},
        )
        self.assertEqual(res.status_code, 403)

    def test_officer_can_add_case_note(self):
        """Officer adds internal case note."""
        app.dependency_overrides[_require_officer] = lambda: self.officer_user

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = self.test_application
        app.dependency_overrides[get_db] = lambda: mock_db

        res = self.client.post(
            f"/api/v1/admin/applications/{self.app_id}/notes",
            json={"note": "Income certificate verified.", "is_internal": True},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertIn("note_id", res.json())
        self.assertEqual(res.json()["message"], "Internal case note recorded successfully.")

    # -----------------------------------------------------------------------
    # 6. Deficiency Lifecycle
    # -----------------------------------------------------------------------
    def test_raise_deficiency_creates_all_records(self):
        """Raising deficiency creates Deficiency, Notification, AuditLog, CaseTimelineEvent."""
        app.dependency_overrides[_require_officer] = lambda: self.officer_user
        mock_db = MagicMock()
        def side_effect(model):
            m = MagicMock()
            if model == Application:
                m.filter.return_value.first.return_value = self.test_application
            elif model == Notification:
                m.filter.return_value.first.return_value = None
            else:
                m.filter.return_value.first.return_value = None
            return m
        mock_db.query.side_effect = side_effect
        app.dependency_overrides[get_db] = lambda: mock_db

        res = self.client.post(
            f"/api/v1/admin/applications/{self.app_id}/deficiency",
            json={
                "deficiency_type": "DOCUMENT_BLURRY",
                "description": "Caste certificate scan is illegible.",
                "required_action": "Upload clear PDF of ST certificate.",
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"].lower(), "open")
        added_types = [type(a[0][0]) for a in mock_db.add.call_args_list]
        self.assertIn(Deficiency, added_types)
        self.assertIn(Notification, added_types)
        self.assertIn(AuditLog, added_types)
        self.assertIn(CaseTimelineEvent, added_types)

    def test_resolve_deficiency_by_officer(self):
        """Officer resolves an open deficiency."""
        app.dependency_overrides[_require_officer] = lambda: self.officer_user

        def_id = uuid.uuid4()
        test_def = Deficiency(
            id=def_id,
            application_id=self.app_id,
            document_type_requested="caste_certificate",
            description="Re-upload needed.",
            status=DeficiencyStatus.OPEN,
            created_at=datetime.now(timezone.utc),
        )
        mock_db = MagicMock()

        def side_effect(model):
            m = MagicMock()
            if model == Deficiency:
                m.filter.return_value.first.return_value = test_def
            elif model == Application:
                m.filter.return_value.first.return_value = self.test_application
            else:
                m.filter.return_value.first.return_value = None
            return m

        mock_db.query.side_effect = side_effect
        app.dependency_overrides[get_db] = lambda: mock_db

        res = self.client.post(
            f"/api/v1/admin/deficiencies/{def_id}/resolve",
            json={"resolution_notes": "Clear ST certificate verified."},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "closed")

    # -----------------------------------------------------------------------
    # 7. Timeline Service Privacy
    # -----------------------------------------------------------------------
    def test_timeline_hides_internal_events_from_applicants(self):
        """Internal timeline events not visible to applicants."""
        mock_db = MagicMock()

        ev_pub = CaseTimelineEvent(
            id=uuid.uuid4(),
            application_id=self.app_id,
            event_type=TimelineEventType.APPLICATION_SUBMITTED.value,
            title="Application Submitted",
            description="Submitted.",
            actor_type="applicant",
            is_internal=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=2),
        )
        ev_int = CaseTimelineEvent(
            id=uuid.uuid4(),
            application_id=self.app_id,
            event_type=TimelineEventType.CASE_NOTE_ADDED.value,
            title="Internal Note",
            description="Officer internal note.",
            actor_type="officer",
            is_internal=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

        def q_side(model):
            m = MagicMock()
            if model == CaseTimelineEvent:
                m_filter1 = MagicMock()
                m_filter2 = MagicMock()
                m.filter.return_value = m_filter1
                m_filter1.filter.return_value = m_filter2
                m_filter1.all.return_value = [ev_pub, ev_int]
                m_filter2.all.return_value = [ev_pub]
            elif model == ApplicationStatusHistory:
                m.filter.return_value.all.return_value = []
            elif model == Deficiency:
                m.filter.return_value.all.return_value = []
            return m

        mock_db.query.side_effect = q_side

        timeline = CaseTimelineService.get_timeline(mock_db, self.app_id, is_staff=False)
        self.assertEqual(len(timeline), 1)
        self.assertEqual(timeline[0]["event_type"], TimelineEventType.APPLICATION_SUBMITTED.value)
        self.assertFalse(timeline[0]["is_internal"])

    def test_timeline_idor_protection(self):
        """Applicant cannot access another applicant's timeline (returns 404)."""
        app.dependency_overrides[get_current_user] = lambda: self.applicant_user
        other_app_id = uuid.uuid4()
        mock_db = MagicMock()
        # Query filters by applicant_id=current_user.id, so other user's app returns None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        app.dependency_overrides[get_db] = lambda: mock_db

        res = self.client.get(f"/api/v1/applications/{other_app_id}/timeline")
        self.assertIn(res.status_code, [403, 404])

    # -----------------------------------------------------------------------
    # 8. TimelineEventType Enum Completeness
    # -----------------------------------------------------------------------
    def test_timeline_event_type_enum_coverage(self):
        """TimelineEventType contains all required lifecycle event types."""
        values = {e.value for e in TimelineEventType}
        required = {
            "APPLICATION_SUBMITTED",
            "DEFICIENCY_RAISED",
            "DEFICIENCY_RESOLVED",
            "OFFICER_ASSIGNED",
            "CASE_NOTE_ADDED",
            "APPLICATION_STATUS_CHANGED",
        }
        missing = required - values
        self.assertEqual(missing, set(), f"Missing TimelineEventType values: {missing}")


if __name__ == "__main__":
    unittest.main()
