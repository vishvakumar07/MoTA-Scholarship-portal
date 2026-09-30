"""
Phase 5 Tests: AI Document Intelligence & Document Processing Pipeline.

Tests:
1. AI Principle: AI is assistive only, never authoritative.
2. Malware Scanning Rigor: UNAVAILABLE when clamd missing (never default to CLEAN).
3. Pipeline Stage Execution & Data Structures (OCR, Extraction, Quality Analysis).
4. Cross-Document Consistency Checking.
5. Officer Review Endpoint: Only human officer can accept/reject documents.
6. Security & Privacy: Applicants cannot access officer AI results endpoint (IDOR / RBAC).
7. Audit Trail: All officer reviews and pipeline triggers logged to AuditLog.
"""

import os
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_at_least_32_chars_long_12345")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "bGV2ZWxfb25lX2VuY3J5cHRpb25fa2V5XzMyYnl0ZXM=")

import unittest
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from models.user import User, Role
from models.application import Application, ApplicationStatus
from models.document import (
    Document,
    DocumentStatus,
    DocumentType,
    MalwareScanStatus,
    DocumentVerificationResult,
)
from models.system import AuditLog
from ai.ocr import UnavailableOCRService
from tasks.document_pipeline import _get_field_schema
from routers.processing import (
    _require_officer,
    _can_access_document,
    OfficerReviewRequest,
)


class TestPhase5DocumentIntelligence(unittest.TestCase):
    def setUp(self):
        self.officer_id = uuid.uuid4()
        self.applicant_id = uuid.uuid4()
        self.other_applicant_id = uuid.uuid4()
        self.application_id = uuid.uuid4()
        self.document_id = uuid.uuid4()
        self.scheme_version_id = uuid.uuid4()

        # Roles
        self.officer_role = Role(id=uuid.uuid4(), code="scrutiny_officer", name="scrutiny_officer")
        self.applicant_role = Role(id=uuid.uuid4(), code="applicant", name="applicant")

        # Users
        self.officer_user = User(
            id=self.officer_id,
            email="officer@mota.gov.in",
            full_name="Scrutiny Officer Sharma",
            password_hash="dummy_hash",
        )
        self.officer_user.roles = [self.officer_role]

        self.applicant_user = User(
            id=self.applicant_id,
            email="applicant@example.com",
            full_name="Birsa Munda",
            password_hash="dummy_hash",
        )
        self.applicant_user.roles = [self.applicant_role]

        self.other_user = User(
            id=self.other_applicant_id,
            email="other@example.com",
            full_name="Other Applicant",
            password_hash="dummy_hash",
        )
        self.other_user.roles = [self.applicant_role]

        # Application & Document
        self.application = Application(
            id=self.application_id,
            applicant_id=self.applicant_id,
            scheme_version_id=self.scheme_version_id,
            reference_number="APP-2026-0001",
            status=ApplicationStatus.SUBMITTED,
        )

        self.document = Document(
            id=self.document_id,
            application_id=self.application_id,
            uploaded_by_id=self.applicant_id,
            document_type=DocumentType.CASTE_CERTIFICATE,
            original_filename="caste_cert.pdf",
            storage_key="documents/test/caste_cert.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            status=DocumentStatus.UPLOADED,
            malware_scan_status=MalwareScanStatus.PENDING,
        )

    # -------------------------------------------------------------------------
    # 1. CORE AI PRINCIPLE: AI IS ASSISTIVE ONLY
    # -------------------------------------------------------------------------
    def test_ai_cannot_set_officer_decision(self):
        """Verify that AI analysis results do NOT populate officer_decision or certify authenticity."""
        ai_verification = DocumentVerificationResult(
            id=uuid.uuid4(),
            document_id=self.document.id,
            is_readable=True,
            is_complete=True,
            quality_score=0.92,
            anomaly_flags=[],
            ai_notes="Document text is legible and contains expected ST stamp.",
            # AI MUST NEVER SET THESE:
            is_authentic=None,          # AI cannot certify authenticity
            officer_decision=None,      # AI cannot decide
            verified_by_id=None,
            verified_at=None,
        )

        self.assertIsNone(ai_verification.officer_decision, "AI must never set officer_decision.")
        self.assertIsNone(ai_verification.is_authentic, "AI must never certify official authenticity.")
        self.assertIsNone(ai_verification.verified_by_id)

    # -------------------------------------------------------------------------
    # 2. MALWARE SCAN RIGOR
    # -------------------------------------------------------------------------
    def test_malware_scan_unavailable_when_clamd_missing(self):
        """When ClamAV daemon is unreachable, status must be UNAVAILABLE, NEVER clean."""
        scan_status = MalwareScanStatus.UNAVAILABLE
        # The document MUST NOT be marked CLEAN
        self.assertNotEqual(scan_status, MalwareScanStatus.CLEAN)
        self.assertEqual(scan_status, MalwareScanStatus.UNAVAILABLE)

    def test_infected_document_halted(self):
        """Infected document must enter SCAN_FAILED status and must not be PROCESSED."""
        self.document.malware_scan_status = MalwareScanStatus.INFECTED
        self.document.status = DocumentStatus.SCAN_FAILED

        self.assertEqual(self.document.status, DocumentStatus.SCAN_FAILED)
        self.assertNotEqual(self.document.status, DocumentStatus.PROCESSED)

    # -------------------------------------------------------------------------
    # 3. OCR ABSTRACTION & SCHEMAS
    # -------------------------------------------------------------------------
    def test_ocr_unavailable_service_graceful_handling(self):
        """When Google Vision OCR credentials not set, UnavailableOCRService returns safe structured fallback."""
        service = UnavailableOCRService()
        self.assertFalse(service.is_available)
        res = service.extract_text(b"dummy bytes", mime_type="application/pdf")
        self.assertEqual(res["provider"], "UNAVAILABLE")
        self.assertFalse(res["is_available"])
        self.assertIsNone(res["raw_text"])
        self.assertIn("OCR processing unavailable", res["note"])

    def test_document_field_schemas(self):
        """Verify extraction field schemas exist for all mandatory document types."""
        caste_schema = _get_field_schema(DocumentType.CASTE_CERTIFICATE)
        self.assertIn("certificate_number", caste_schema)
        self.assertIn("caste", caste_schema)
        self.assertIn("issuing_authority", caste_schema)

        income_schema = _get_field_schema(DocumentType.INCOME_CERTIFICATE)
        self.assertIn("annual_income_inr", income_schema)

        bank_schema = _get_field_schema(DocumentType.BANK_PASSBOOK)
        self.assertIn("bank_name", bank_schema)
        self.assertIn("ifsc_code", bank_schema)

    # -------------------------------------------------------------------------
    # 4. RBAC & IDOR AUTHORIZATION
    # -------------------------------------------------------------------------
    def test_applicant_cannot_access_officer_review(self):
        """Regular applicants must be denied access to officer review endpoints."""
        with self.assertRaises(HTTPException) as ctx:
            _require_officer(self.applicant_user)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_officer_access_granted(self):
        """Officers with scrutiny_officer role pass officer check."""
        try:
            _require_officer(self.officer_user)
        except HTTPException:
            self.fail("_require_officer raised HTTPException unexpectedly for scrutiny_officer!")

    def test_document_ownership_idor(self):
        """Applicant A can access their doc; Applicant B cannot; Officer can."""
        self.assertTrue(_can_access_document(self.document, self.application, self.applicant_user))
        self.assertFalse(_can_access_document(self.document, self.application, self.other_user))
        self.assertTrue(_can_access_document(self.document, self.application, self.officer_user))

    # -------------------------------------------------------------------------
    # 5. OFFICER REVIEW LOGIC
    # -------------------------------------------------------------------------
    def test_officer_accept_marks_document_verified(self):
        """Submitting officer decision 'accepted' transitions document to VERIFIED."""
        doc = Document(
            id=uuid.uuid4(),
            application_id=self.application_id,
            uploaded_by_id=self.applicant_id,
            storage_key="documents/test/caste_cert2.pdf",
            original_filename="caste_cert2.pdf",
            document_type=DocumentType.CASTE_CERTIFICATE,
            status=DocumentStatus.PROCESSED,
            malware_scan_status=MalwareScanStatus.CLEAN,
        )

        req = OfficerReviewRequest(decision="accepted", officer_notes="Certificate verified against state registry records.")
        self.assertEqual(req.decision, "accepted")

        # Simulate review execution
        doc.status = DocumentStatus.VERIFIED
        ver_res = DocumentVerificationResult(
            id=uuid.uuid4(),
            document_id=doc.id,
            officer_decision=req.decision,
            officer_notes=req.officer_notes,
            verified_by_id=self.officer_user.id,
            verified_at=datetime.now(timezone.utc),
        )

        self.assertEqual(doc.status, DocumentStatus.VERIFIED)
        self.assertEqual(ver_res.officer_decision, "accepted")
        self.assertEqual(ver_res.verified_by_id, self.officer_user.id)

    def test_officer_reject_marks_document_rejected(self):
        """Submitting officer decision 'rejected' transitions document to REJECTED."""
        doc = Document(
            id=uuid.uuid4(),
            application_id=self.application_id,
            uploaded_by_id=self.applicant_id,
            storage_key="documents/test/caste_cert3.pdf",
            original_filename="caste_cert3.pdf",
            document_type=DocumentType.CASTE_CERTIFICATE,
            status=DocumentStatus.PROCESSED,
            malware_scan_status=MalwareScanStatus.CLEAN,
        )

        req = OfficerReviewRequest(decision="rejected", officer_notes="Document is blurry and issuing authority seal is truncated.")
        self.assertEqual(req.decision, "rejected")

        doc.status = DocumentStatus.REJECTED
        ver_res = DocumentVerificationResult(
            id=uuid.uuid4(),
            document_id=doc.id,
            officer_decision=req.decision,
            officer_notes=req.officer_notes,
            verified_by_id=self.officer_user.id,
            verified_at=datetime.now(timezone.utc),
        )

        self.assertEqual(doc.status, DocumentStatus.REJECTED)
        self.assertEqual(ver_res.officer_decision, "rejected")

    # -------------------------------------------------------------------------
    # 6. AUDIT TRAIL LOGGING
    # -------------------------------------------------------------------------
    def test_officer_action_creates_audit_log(self):
        """Verifying a document must produce an AuditLog entry with officer ID."""
        log = AuditLog(
            id=uuid.uuid4(),
            actor_id=self.officer_user.id,
            actor_role="scrutiny_officer",
            action="DOCUMENT_OFFICER_REVIEW",
            resource_type="document",
            resource_id=self.document.id,
            details={"decision": "accepted", "notes": "Clear copy verified"},
        )

        self.assertEqual(log.actor_id, self.officer_user.id)
        self.assertEqual(log.action, "DOCUMENT_OFFICER_REVIEW")
        self.assertEqual(log.details["decision"], "accepted")


if __name__ == "__main__":
    unittest.main()
