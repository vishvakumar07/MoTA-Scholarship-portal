"""
Tests for Scheme Versioning & Immutability.
"""

import unittest
import uuid
from unittest.mock import MagicMock
from models.scheme import SchemeVersion, SchemeRule, SchemeVersionStatus
from services.scheme_admin_service import SchemeAdminService


class TestSchemeVersioning(unittest.TestCase):
    def test_published_version_immutability(self):
        db_mock = MagicMock()
        pub_version = SchemeVersion(
            id=uuid.uuid4(),
            scheme_id=uuid.uuid4(),
            version_number="1.0",
            version_status=SchemeVersionStatus.PUBLISHED,
            is_published=True,
            rules=[],
            form_fields=[],
            documents=[],
            workflows=[],
        )

        target = SchemeAdminService.ensure_draft(db_mock, pub_version)
        # Verify a new draft was created instead of returning the published version
        self.assertNotEqual(target.id, pub_version.id)
        self.assertFalse(target.is_published)
        self.assertEqual(target.version_number, "1.1")


if __name__ == "__main__":
    unittest.main()
