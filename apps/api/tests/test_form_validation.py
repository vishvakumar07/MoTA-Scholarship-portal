"""
Tests for Dynamic Form Validation Engine.
"""

import unittest
import uuid
from models.scheme import SchemeVersion, SchemeFormField
from services.form_validator import FormValidationEngine


class TestFormValidation(unittest.TestCase):
    def setUp(self):
        self.version = SchemeVersion(
            id=uuid.uuid4(),
            scheme_id=uuid.uuid4(),
            version_number="1.0",
            form_fields=[],
        )

        self.field_income = SchemeFormField(
            id=uuid.uuid4(),
            version_id=self.version.id,
            field_key="annual_family_income",
            field_label="Annual Family Income",
            field_type="number",
            is_required=True,
            validation_rules={"min": 0, "max": 250000},
        )

        self.field_email = SchemeFormField(
            id=uuid.uuid4(),
            version_id=self.version.id,
            field_key="applicant_email",
            field_label="Email Address",
            field_type="email",
            is_required=True,
        )

        self.field_class = SchemeFormField(
            id=uuid.uuid4(),
            version_id=self.version.id,
            field_key="current_class",
            field_label="Current Class",
            field_type="select",
            is_required=True,
            options=[{"label": "Class IX", "value": "Class IX"}, {"label": "Class X", "value": "Class X"}],
        )

        self.field_conditional = SchemeFormField(
            id=uuid.uuid4(),
            version_id=self.version.id,
            field_key="disability_percentage",
            field_label="Disability Percentage",
            field_type="number",
            is_required=True,
            conditional_logic={"depends_on": "is_pwd", "operator": "eq", "value": "true"},
            validation_rules={"min": 40, "max": 100},
        )

        self.version.form_fields = [
            self.field_income,
            self.field_email,
            self.field_class,
            self.field_conditional,
        ]

    def test_valid_form_submission(self):
        answers = {
            "annual_family_income": 180000,
            "applicant_email": "student@example.gov.in",
            "current_class": "Class IX",
            "is_pwd": "false",
        }
        res = FormValidationEngine.validate_answers(self.version, answers)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["error_count"], 0)

    def test_missing_required_field(self):
        answers = {
            "annual_family_income": 180000,
            "applicant_email": "student@example.gov.in",
        }
        res = FormValidationEngine.validate_answers(self.version, answers)
        self.assertFalse(res["is_valid"])
        err_keys = [e["field_key"] for e in res["errors"]]
        self.assertIn("current_class", err_keys)

    def test_numeric_max_exceeded(self):
        answers = {
            "annual_family_income": 300000,
            "applicant_email": "student@example.gov.in",
            "current_class": "Class IX",
        }
        res = FormValidationEngine.validate_answers(self.version, answers)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["errors"][0]["error_type"], "NUMERIC_MAX_VIOLATION")

    def test_invalid_option_selected(self):
        answers = {
            "annual_family_income": 180000,
            "applicant_email": "student@example.gov.in",
            "current_class": "Class XII",
        }
        res = FormValidationEngine.validate_answers(self.version, answers)
        self.assertFalse(res["is_valid"])
        err_types = [e["error_type"] for e in res["errors"]]
        self.assertIn("INVALID_OPTION_SELECTED", err_types)

    def test_conditional_logic_triggered(self):
        # is_pwd = true requires disability_percentage
        answers_missing_pwd = {
            "annual_family_income": 180000,
            "applicant_email": "student@example.gov.in",
            "current_class": "Class IX",
            "is_pwd": "true",
        }
        res = FormValidationEngine.validate_answers(self.version, answers_missing_pwd)
        self.assertFalse(res["is_valid"])
        err_keys = [e["field_key"] for e in res["errors"]]
        self.assertIn("disability_percentage", err_keys)


if __name__ == "__main__":
    unittest.main()
