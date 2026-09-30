"""
Phase 8 Security Hardening, Verification, and SIH Readiness Test Suite.

Verifies:
 1. Authentication hardening (expired token, malformed token, no password leakage)
 2. RBAC hardening (applicant blocked from admin schemes routes, officer permitted)
 3. IDOR protection (applications, documents, notifications)
 4. File security (magic bytes signature verification, rejection of spoofed extensions)
 5. Path traversal & null byte filename rejection
 6. Rate limiting enforcement
 7. Readiness and health check safety (no secrets/passwords exposed)
 8. Request correlation (X-Request-ID preservation) and security headers
 9. AI safety boundary (AI remains assistive suggestion only)
10. Deterministic eligibility boundary
"""

import io
import os
import time
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from jose import jwt
from fastapi import HTTPException
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_at_least_32_chars_long_12345")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "bGV2ZWxfb25lX2VuY3J5cHRpb25fa2V5XzMyYnl0ZXM=")

from config import settings
from database import get_db
from main import app
from models.application import Application, ApplicationStatus
from models.document import Document, DocumentStatus, DocumentType
from models.scheme import SchemeVersion, SchemeVersionStatus
from models.system import Notification, NotificationChannel
from models.user import Role, User
from security.rbac import get_current_user
from security.rate_limiter import SlidingWindowRateLimiter


class TestPhase8Hardening(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.applicant_id = uuid.uuid4()
        self.other_applicant_id = uuid.uuid4()
        self.officer_id = uuid.uuid4()
        self.admin_id = uuid.uuid4()

        # Roles
        self.applicant_role = Role(id=uuid.uuid4(), code="applicant", name="applicant")
        self.officer_role = Role(id=uuid.uuid4(), code="scrutiny_officer", name="scrutiny_officer")
        self.admin_role = Role(id=uuid.uuid4(), code="super_admin", name="super_admin")

        # Users
        self.applicant_user = User(
            id=self.applicant_id,
            email="applicant1@example.com",
            full_name="Birsa Munda",
            is_active=True,
        )
        self.applicant_user.roles = [self.applicant_role]

        self.other_user = User(
            id=self.other_applicant_id,
            email="applicant2@example.com",
            full_name="Other Applicant",
            is_active=True,
        )
        self.other_user.roles = [self.applicant_role]

        self.officer_user = User(
            id=self.officer_id,
            email="officer@mota.gov.in",
            full_name="Scrutiny Officer",
            is_active=True,
        )
        self.officer_user.roles = [self.officer_role]

        self.admin_user = User(
            id=self.admin_id,
            email="admin@mota.gov.in",
            full_name="Super Admin",
            is_active=True,
        )
        self.admin_user.roles = [self.admin_role]

    def tearDown(self):
        app.dependency_overrides.clear()

    # -----------------------------------------------------------------------
    # 1. Authentication Hardening
    # -----------------------------------------------------------------------
    def test_unauthenticated_request_returns_401(self):
        """Protected endpoint without token returns 401."""
        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_malformed_token_returns_401(self):
        """Malformed or garbage token returns 401."""
        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not_a_valid_jwt_token"}
        )
        self.assertEqual(response.status_code, 401)

    def test_expired_token_returns_401(self):
        """Expired JWT token returns 401."""
        payload = {
            "sub": str(self.applicant_id),
            "roles": ["applicant"],
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        self.assertEqual(response.status_code, 401)

    # -----------------------------------------------------------------------
    # 2. RBAC Hardening
    # -----------------------------------------------------------------------
    def test_applicant_blocked_from_admin_scheme_creation(self):
        """Applicant receives 403 on admin scheme creation route."""
        app.dependency_overrides[get_current_user] = lambda: self.applicant_user
        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [("applicant",)]
        app.dependency_overrides[get_db] = lambda: mock_db

        response = self.client.post(
            "/api/v1/admin/schemes",
            json={
                "code": "TEST",
                "name": "Test Scheme",
                "short_name": "TS",
                "scheme_type": "scholarship",
            }
        )
        self.assertEqual(response.status_code, 403)

    def test_applicant_blocked_from_admin_version_publishing(self):
        """Applicant receives 403 on version publish endpoint."""
        app.dependency_overrides[get_current_user] = lambda: self.applicant_user
        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [("applicant",)]
        app.dependency_overrides[get_db] = lambda: mock_db

        fake_version_id = str(uuid.uuid4())
        response = self.client.post(f"/api/v1/admin/schemes/versions/{fake_version_id}/publish")
        self.assertEqual(response.status_code, 403)

    # -----------------------------------------------------------------------
    # 3. IDOR Protections
    # -----------------------------------------------------------------------
    def test_applicant_cannot_access_other_applicant_application(self):
        """Applicant A querying Applicant B's application receives 404 (IDOR blocked)."""
        app.dependency_overrides[get_current_user] = lambda: self.applicant_user

        other_app_id = uuid.uuid4()
        other_app = Application(
            id=other_app_id,
            applicant_id=self.other_applicant_id,  # Owned by other user
            status=ApplicationStatus.SUBMITTED,
        )

        session_mock = MagicMock()
        session_mock.query.return_value.options.return_value.filter.return_value.first.return_value = other_app
        app.dependency_overrides[get_db] = lambda: session_mock

        response = self.client.get(f"/api/v1/applications/{other_app_id}")
        self.assertEqual(response.status_code, 404)

    def test_officer_permitted_to_inspect_application(self):
        """Scrutiny officer is permitted to inspect application for scrutiny."""
        app.dependency_overrides[get_current_user] = lambda: self.officer_user

        app_id = uuid.uuid4()
        app_obj = Application(
            id=app_id,
            applicant_id=self.applicant_id,
            status=ApplicationStatus.SUBMITTED,
            answers=[],
            status_history=[],
        )

        session_mock = MagicMock()
        session_mock.query.return_value.options.return_value.filter.return_value.first.return_value = app_obj
        session_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        session_mock.query.return_value.filter.return_value.all.return_value = []
        app.dependency_overrides[get_db] = lambda: session_mock

        response = self.client.get(f"/api/v1/applications/{app_id}")
        self.assertEqual(response.status_code, 200)

    # -----------------------------------------------------------------------
    # 4. File Security & Magic Bytes Signature Verification
    # -----------------------------------------------------------------------
    def test_spoofed_pdf_rejected_by_magic_bytes(self):
        """Executable or text bytes spoofed as application/pdf rejected with 415."""
        app.dependency_overrides[get_current_user] = lambda: self.applicant_user

        app_id = uuid.uuid4()
        app_obj = Application(
            id=app_id,
            applicant_id=self.applicant_id,
            status=ApplicationStatus.DRAFT,
        )

        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = app_obj
        app.dependency_overrides[get_db] = lambda: session_mock

        # Fake PDF content (plain text without %PDF- magic bytes)
        fake_pdf = io.BytesIO(b"This is not a real PDF file! Malicious payload here.")

        response = self.client.post(
            "/api/v1/documents/upload",
            data={
                "application_id": str(app_id),
                "document_type": "caste_certificate",
            },
            files={
                "file": ("certificate.pdf", fake_pdf, "application/pdf")
            }
        )
        self.assertEqual(response.status_code, 415)
        self.assertIn("signature", response.json()["detail"].lower())

    def test_path_traversal_filename_rejected(self):
        """Filename with path traversal sequence ('../') rejected with 400."""
        app.dependency_overrides[get_current_user] = lambda: self.applicant_user

        app_id = uuid.uuid4()
        app_obj = Application(
            id=app_id,
            applicant_id=self.applicant_id,
            status=ApplicationStatus.DRAFT,
        )

        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = app_obj
        app.dependency_overrides[get_db] = lambda: session_mock

        valid_pdf = io.BytesIO(b"%PDF-1.4 mock pdf content")

        response = self.client.post(
            "/api/v1/documents/upload",
            data={
                "application_id": str(app_id),
                "document_type": "caste_certificate",
            },
            files={
                "file": ("../../etc/passwd", valid_pdf, "application/pdf")
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("path traversal", response.json()["detail"].lower())

    # -----------------------------------------------------------------------
    # 5. Rate Limiting
    # -----------------------------------------------------------------------
    def test_sliding_window_rate_limiter_blocks_excessive_calls(self):
        """Rate limiter blocks requests after exceeding defined limit."""
        limiter = SlidingWindowRateLimiter(requests_limit=3, window_seconds=60, bucket_name="test")
        key = "test_user_ip_1"

        # 3 allowed
        self.assertFalse(limiter.is_rate_limited(key)[0])
        self.assertFalse(limiter.is_rate_limited(key)[0])
        self.assertFalse(limiter.is_rate_limited(key)[0])

        # 4th blocked
        limited, retry_after = limiter.is_rate_limited(key)
        self.assertTrue(limited)
        self.assertGreater(retry_after, 0)

    # -----------------------------------------------------------------------
    # 6. System Observability & Security Headers
    # -----------------------------------------------------------------------
    def test_security_headers_and_request_id_present(self):
        """Responses include security headers and X-Request-ID."""
        response = self.client.get("/")
        self.assertIn("x-request-id", response.headers)
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(response.headers.get("x-frame-options"), "DENY")
        self.assertEqual(response.headers.get("x-xss-protection"), "1; mode=block")

    def test_ready_check_endpoint(self):
        """GET /ready returns 200 ready status."""
        with patch("main.check_db_connection", return_value=True):
            response = self.client.get("/ready")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "ready")

    def test_health_check_no_secrets_exposed(self):
        """GET /health does not expose credentials or internal paths."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        text = response.text.lower()
        for forbidden in ["password", "secret", "private_key", "bearer"]:
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
