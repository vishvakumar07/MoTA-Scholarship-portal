"""
Tests for Deterministic Rule Engine Service.
"""

import unittest
import uuid
from datetime import date
from models.scheme import SchemeVersion, SchemeRule, RuleSeverity, RuleType, SchemeVersionStatus
from services.rule_engine import RuleEngineService


class TestRuleEngine(unittest.TestCase):
    def setUp(self):
        self.version = SchemeVersion(
            id=uuid.uuid4(),
            scheme_id=uuid.uuid4(),
            version_number="1.0",
            version_status=SchemeVersionStatus.PUBLISHED,
            is_published=True,
            effective_from=date(2024, 4, 1),
            rules=[],
        )

        self.rule_income = SchemeRule(
            id=uuid.uuid4(),
            version_id=self.version.id,
            rule_type=RuleType.INCOME_CEILING,
            rule_key="income_limit",
            field="applicant.annual_family_income",
            operator="lte",
            expected_value=250000,
            unit="INR",
            severity=RuleSeverity.HARD_STOP,
            display_label="Annual Family Income Ceiling",
            explanation="Family income must be <= Rs. 2,50,000",
            source_url="https://tribal.nic.in/ScholarshiP.aspx",
            source_document_title="MoTA Guidelines",
            source_page_number="3",
            source_section="Section 4.1",
            is_official_source_confirmed=True,
        )

        self.rule_caste = SchemeRule(
            id=uuid.uuid4(),
            version_id=self.version.id,
            rule_type=RuleType.CASTE_CATEGORY,
            rule_key="caste_requirement",
            field="applicant.caste_category",
            operator="eq",
            expected_value="ST",
            severity=RuleSeverity.HARD_STOP,
            display_label="ST Category Requirement",
            explanation="Must belong to ST community",
            source_url="https://tribal.nic.in/ScholarshiP.aspx",
            source_document_title="MoTA Guidelines",
            source_page_number="2",
            is_official_source_confirmed=True,
        )

        self.rule_unconfirmed = SchemeRule(
            id=uuid.uuid4(),
            version_id=self.version.id,
            rule_type=RuleType.CUSTOM,
            rule_key="unverified_rule",
            field="applicant.attendance",
            operator="gte",
            expected_value=75,
            severity=RuleSeverity.WARNING,
            display_label="Attendance Percentage",
            explanation="OFFICIAL SOURCE REQUIRED",
            is_official_source_confirmed=False,
        )

        self.version.rules = [self.rule_income, self.rule_caste, self.rule_unconfirmed]

    def test_rule_pass(self):
        payload = {
            "applicant": {
                "annual_family_income": 180000,
                "caste_category": "ST",
                "attendance": 80,
            }
        }
        res = RuleEngineService.evaluate_rule(self.rule_income, payload)
        self.assertEqual(res.status, "PASS")
        self.assertEqual(res.actual_value, 180000)

    def test_rule_fail_boundary(self):
        payload = {
            "applicant": {
                "annual_family_income": 250001,
                "caste_category": "ST",
            }
        }
        res = RuleEngineService.evaluate_rule(self.rule_income, payload)
        self.assertEqual(res.status, "FAIL")
        self.assertEqual(res.severity, "HARD_STOP")

    def test_missing_value(self):
        payload = {"applicant": {}}
        res = RuleEngineService.evaluate_rule(self.rule_income, payload)
        self.assertEqual(res.status, "FAIL")
        self.assertIn("Missing value", res.explanation)

    def test_official_source_required(self):
        payload = {"applicant": {"attendance": 80}}
        res = RuleEngineService.evaluate_rule(self.rule_unconfirmed, payload)
        self.assertEqual(res.status, "OFFICIAL_SOURCE_REQUIRED")

    def test_version_evaluation(self):
        payload = {
            "applicant": {
                "annual_family_income": 200000,
                "caste_category": "ST",
            }
        }
        eval_res = RuleEngineService.evaluate_scheme_version(self.version, payload)
        self.assertTrue(eval_res["is_eligible"])
        self.assertEqual(len(eval_res["rule_results"]), 3)
        self.assertTrue(eval_res["has_official_source_required"])

    def test_draft_version_raises_without_preview_flag(self):
        draft_version = SchemeVersion(
            id=uuid.uuid4(),
            scheme_id=uuid.uuid4(),
            version_number="1.1-draft",
            version_status=SchemeVersionStatus.DRAFT,
            is_published=False,
            effective_from=date(2024, 4, 1),
            rules=[],
        )
        payload = {}
        with self.assertRaises(ValueError):
            RuleEngineService.evaluate_scheme_version(draft_version, payload, is_preview_mode=False)


if __name__ == "__main__":
    unittest.main()
