"""
Deterministic Eligibility Rule Engine Service.

Evaluates scheme rules strictly deterministically (NO LLM / AI involved).
Full explainability and source traceability per rule.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

from models.scheme import SchemeRule, SchemeVersion, SchemeVersionStatus, RuleSeverity
from models.workflow import EligibilityDecision


class RuleEvaluationResult:
    def __init__(
        self,
        rule_id: str,
        rule_key: str,
        field: str,
        operator: str,
        expected_value: Any,
        actual_value: Any,
        status: str,  # "PASS" | "FAIL" | "OFFICIAL_SOURCE_REQUIRED"
        severity: str,  # "HARD_STOP" | "WARNING" | "INFO"
        explanation: str,
        display_label: str,
        source_citation: Dict[str, Any],
        evaluated_at: str,
    ):
        self.rule_id = rule_id
        self.rule_key = rule_key
        self.field = field
        self.operator = operator
        self.expected_value = expected_value
        self.actual_value = actual_value
        self.status = status
        self.severity = severity
        self.explanation = explanation
        self.display_label = display_label
        self.source_citation = source_citation
        self.evaluated_at = evaluated_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_key": self.rule_key,
            "field": self.field,
            "operator": self.operator,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "status": self.status,
            "severity": self.severity,
            "explanation": self.explanation,
            "display_label": self.display_label,
            "source_citation": self.source_citation,
            "evaluated_at": self.evaluated_at,
        }


class RuleEngineService:
    """
    Deterministic rule engine for evaluating scheme eligibility.
    """

    @staticmethod
    def get_field_value(data: Dict[str, Any], field_path: str) -> Any:
        """
        Extracts nested field values from data dict using dot notation.
        e.g. 'applicant.income' -> data['applicant']['income'] or data.get('applicant.income')
        """
        if field_path in data:
            return data[field_path]
        
        parts = field_path.split(".")
        curr = data
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                return None
        return curr

    @classmethod
    def evaluate_rule(cls, rule: SchemeRule, payload: Dict[str, Any]) -> RuleEvaluationResult:
        now_str = datetime.utcnow().isoformat()
        citation = {
            "source_url": rule.source_url,
            "source_document_title": rule.source_document_title,
            "source_section": rule.source_section,
            "source_page_number": rule.source_page_number,
            "source_type": rule.source_type,
            "is_official_source_confirmed": rule.is_official_source_confirmed,
        }

        # Check official source confirmation
        if not rule.is_official_source_confirmed or rule.explanation == "OFFICIAL SOURCE REQUIRED":
            return RuleEvaluationResult(
                rule_id=str(rule.id),
                rule_key=rule.rule_key,
                field=rule.field,
                operator=rule.operator,
                expected_value=rule.expected_value,
                actual_value=cls.get_field_value(payload, rule.field),
                status="OFFICIAL_SOURCE_REQUIRED",
                severity=rule.severity.value if hasattr(rule.severity, "value") else str(rule.severity),
                explanation="OFFICIAL SOURCE REQUIRED: Rule parameter unverified against official MoTA source.",
                display_label=rule.display_label,
                source_citation=citation,
                evaluated_at=now_str,
            )

        actual_val = cls.get_field_value(payload, rule.field)
        expected_val = rule.expected_value
        op = (rule.operator or "eq").lower()

        is_pass = False

        if actual_val is None:
            explanation = f"Missing value for field '{rule.field}'. Expected: {op} {expected_val}."
            return RuleEvaluationResult(
                rule_id=str(rule.id),
                rule_key=rule.rule_key,
                field=rule.field,
                operator=op,
                expected_value=expected_val,
                actual_value=None,
                status="FAIL",
                severity=rule.severity.value if hasattr(rule.severity, "value") else str(rule.severity),
                explanation=explanation,
                display_label=rule.display_label,
                source_citation=citation,
                evaluated_at=now_str,
            )

        try:
            if op == "lte":
                is_pass = float(actual_val) <= float(expected_val)
            elif op == "gte":
                is_pass = float(actual_val) >= float(expected_val)
            elif op == "eq":
                is_pass = str(actual_val).strip().lower() == str(expected_val).strip().lower()
            elif op == "ne":
                is_pass = str(actual_val).strip().lower() != str(expected_val).strip().lower()
            elif op == "in":
                if isinstance(expected_val, list):
                    is_pass = str(actual_val) in [str(x) for x in expected_val]
                else:
                    is_pass = str(actual_val) in str(expected_val).split(",")
            elif op == "contains":
                is_pass = str(expected_val).lower() in str(actual_val).lower()
            elif op == "regex":
                is_pass = bool(re.search(str(expected_val), str(actual_val)))
            elif op == "between":
                if isinstance(expected_val, list) and len(expected_val) == 2:
                    is_pass = float(expected_val[0]) <= float(actual_val) <= float(expected_val[1])
                else:
                    is_pass = False
            else:
                is_pass = str(actual_val) == str(expected_val)
        except (ValueError, TypeError):
            is_pass = False

        status_str = "PASS" if is_pass else "FAIL"
        if is_pass:
            explanation = rule.explanation or f"Field '{rule.field}' satisfied requirement ({actual_val} {op} {expected_val})."
        else:
            explanation = rule.explanation or f"Field '{rule.field}' failed requirement ({actual_val} does not satisfy {op} {expected_val})."

        return RuleEvaluationResult(
            rule_id=str(rule.id),
            rule_key=rule.rule_key,
            field=rule.field,
            operator=op,
            expected_value=expected_val,
            actual_value=actual_val,
            status=status_str,
            severity=rule.severity.value if hasattr(rule.severity, "value") else str(rule.severity),
            explanation=explanation,
            display_label=rule.display_label,
            source_citation=citation,
            evaluated_at=now_str,
        )

    @classmethod
    def evaluate_scheme_version(
        cls,
        version: SchemeVersion,
        payload: Dict[str, Any],
        is_preview_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluates all rules for a scheme version against applicant/application payload.
        Enforces PUBLISHED version status unless preview_mode is explicitly requested.
        """
        is_published = (
            version.is_published
            or (hasattr(version, "version_status") and version.version_status == SchemeVersionStatus.PUBLISHED)
        )

        if not is_published and not is_preview_mode:
            raise ValueError("Rule engine cannot evaluate an unpublished/draft scheme version for an official application.")

        rule_results: List[Dict[str, Any]] = []
        failure_reasons: List[str] = []
        has_hard_stop = False
        has_official_source_required = False

        for rule in version.rules:
            if hasattr(rule, "is_deleted") and rule.is_deleted:
                continue

            res = cls.evaluate_rule(rule, payload)
            res_dict = res.to_dict()
            rule_results.append(res_dict)

            if res.status == "FAIL":
                failure_reasons.append(f"Rule [{rule.rule_key}] failed: {res.explanation}")
                if res.severity == "HARD_STOP":
                    has_hard_stop = True
            elif res.status == "OFFICIAL_SOURCE_REQUIRED":
                has_official_source_required = True

        if has_hard_stop:
            decision = EligibilityDecision.INELIGIBLE
        elif len(failure_reasons) > 0:
            decision = EligibilityDecision.PENDING_REVIEW
        else:
            decision = EligibilityDecision.ELIGIBLE

        evaluation_tag = "DRAFT / PREVIEW ONLY" if not is_published else "OFFICIAL EVALUATION"

        return {
            "scheme_version_id": str(version.id),
            "version_number": version.version_number,
            "version_status": getattr(version, "version_status", "published"),
            "evaluation_tag": evaluation_tag,
            "decision": decision.value if hasattr(decision, "value") else str(decision),
            "is_eligible": decision == EligibilityDecision.ELIGIBLE,
            "rule_results": rule_results,
            "failure_reasons": failure_reasons,
            "has_official_source_required": has_official_source_required,
            "assessed_at": datetime.utcnow().isoformat(),
            "rule_engine_version": "1.0.0-deterministic",
        }
