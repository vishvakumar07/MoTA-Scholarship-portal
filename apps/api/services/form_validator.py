"""
Dynamic Schema-Driven Form Validation Engine.

Validates application form answers against SchemeFormField definitions,
types, constraints, validation rules, enum options, and conditional logic.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from models.scheme import SchemeFormField, SchemeVersion


class FormValidationError:
    def __init__(self, field_key: str, field_label: str, message: str, error_type: str):
        self.field_key = field_key
        self.field_label = field_label
        self.message = message
        self.error_type = error_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_key": self.field_key,
            "field_label": self.field_label,
            "message": self.message,
            "error_type": self.error_type,
        }


class FormValidationEngine:
    """
    Validates dynamic form answers against a SchemeVersion's form field definitions.
    """

    @classmethod
    def evaluate_condition(cls, condition: Dict[str, Any], answers: Dict[str, Any]) -> bool:
        """
        Evaluates conditional visibility logic.
        e.g. { "depends_on": "category", "operator": "eq", "value": "ST" }
        """
        if not condition or not isinstance(condition, dict):
            return True

        depends_on = condition.get("depends_on")
        if not depends_on:
            return True

        actual = answers.get(depends_on)
        op = (condition.get("operator") or "eq").lower()
        expected = condition.get("value")

        if actual is None:
            return False

        if op == "eq":
            return str(actual).strip().lower() == str(expected).strip().lower()
        elif op == "ne":
            return str(actual).strip().lower() != str(expected).strip().lower()
        elif op == "in":
            if isinstance(expected, list):
                return str(actual) in [str(x) for x in expected]
            return str(actual) in str(expected).split(",")
        return True

    @classmethod
    def validate_field(cls, field: SchemeFormField, answers: Dict[str, Any]) -> List[FormValidationError]:
        errors: List[FormValidationError] = []
        key = field.field_key
        label = field.field_label or field.field_key
        val = answers.get(key)

        # Check conditional logic  -  if field is hidden by condition, skip validation
        if field.conditional_logic:
            is_visible = cls.evaluate_condition(field.conditional_logic, answers)
            if not is_visible:
                return []

        # Required validation
        if field.is_required and (val is None or str(val).strip() == ""):
            errors.append(
                FormValidationError(
                    field_key=key,
                    field_label=label,
                    message=f"Field '{label}' is required.",
                    error_type="REQUIRED_FIELD_MISSING",
                )
            )
            return errors

        if val is None or str(val).strip() == "":
            return []

        ftype = (field.field_type or "text").lower()

        # Type validations
        if ftype == "number":
            try:
                num_val = float(val)
                # Validation rules: min/max numeric range
                if field.validation_rules:
                    v_min = field.validation_rules.get("min")
                    v_max = field.validation_rules.get("max")
                    if v_min is not None and num_val < float(v_min):
                        errors.append(
                            FormValidationError(
                                field_key=key,
                                field_label=label,
                                message=f"Field '{label}' must be at least {v_min}.",
                                error_type="NUMERIC_MIN_VIOLATION",
                            )
                        )
                    if v_max is not None and num_val > float(v_max):
                        errors.append(
                            FormValidationError(
                                field_key=key,
                                field_label=label,
                                message=f"Field '{label}' cannot exceed {v_max}.",
                                error_type="NUMERIC_MAX_VIOLATION",
                            )
                        )
            except (ValueError, TypeError):
                errors.append(
                    FormValidationError(
                        field_key=key,
                        field_label=label,
                        message=f"Field '{label}' must be a valid number.",
                        error_type="INVALID_NUMBER_FORMAT",
                    )
                )

        elif ftype == "boolean":
            if not isinstance(val, bool) and str(val).lower() not in ("true", "false", "1", "0"):
                errors.append(
                    FormValidationError(
                        field_key=key,
                        field_label=label,
                        message=f"Field '{label}' must be a boolean (true/false).",
                        error_type="INVALID_BOOLEAN_FORMAT",
                    )
                )

        elif ftype == "date":
            # Check ISO date format YYYY-MM-DD
            try:
                dt = datetime.strptime(str(val), "%Y-%m-%d")
                if field.validation_rules:
                    min_date = field.validation_rules.get("min_date")
                    max_date = field.validation_rules.get("max_date")
                    if min_date:
                        min_dt = datetime.strptime(min_date, "%Y-%m-%d")
                        if dt < min_dt:
                            errors.append(
                                FormValidationError(
                                    field_key=key,
                                    field_label=label,
                                    message=f"Field '{label}' must be on or after {min_date}.",
                                    error_type="DATE_MIN_VIOLATION",
                                )
                            )
                    if max_date:
                        max_dt = datetime.strptime(max_date, "%Y-%m-%d")
                        if dt > max_dt:
                            errors.append(
                                FormValidationError(
                                    field_key=key,
                                    field_label=label,
                                    message=f"Field '{label}' must be on or before {max_date}.",
                                    error_type="DATE_MAX_VIOLATION",
                                )
                            )
            except ValueError:
                errors.append(
                    FormValidationError(
                        field_key=key,
                        field_label=label,
                        message=f"Field '{label}' must be a valid date in YYYY-MM-DD format.",
                        error_type="INVALID_DATE_FORMAT",
                    )
                )

        elif ftype in ("select", "radio"):
            if field.options:
                valid_options = []
                for opt in field.options:
                    if isinstance(opt, dict):
                        valid_options.append(str(opt.get("value")))
                    else:
                        valid_options.append(str(opt))
                
                if str(val) not in valid_options:
                    errors.append(
                        FormValidationError(
                            field_key=key,
                            field_label=label,
                            message=f"Field '{label}' selected option '{val}' is invalid. Allowed options: {valid_options}.",
                            error_type="INVALID_OPTION_SELECTED",
                        )
                    )

        elif ftype == "email":
            email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if not re.match(email_pattern, str(val)):
                errors.append(
                    FormValidationError(
                        field_key=key,
                        field_label=label,
                        message=f"Field '{label}' must be a valid email address.",
                        error_type="INVALID_EMAIL_FORMAT",
                    )
                )

        elif ftype == "phone":
            phone_pattern = r"^\+?\d{10,15}$"
            if not re.match(phone_pattern, str(val).replace("-", "").replace(" ", "")):
                errors.append(
                    FormValidationError(
                        field_key=key,
                        field_label=label,
                        message=f"Field '{label}' must be a valid phone number (10-15 digits).",
                        error_type="INVALID_PHONE_FORMAT",
                    )
                )

        # Regex validation if specified in validation_rules
        if field.validation_rules and "regex" in field.validation_rules:
            pattern = field.validation_rules["regex"]
            if not re.search(pattern, str(val)):
                msg = field.validation_rules.get("regex_message", f"Field '{label}' value does not match expected format.")
                errors.append(
                    FormValidationError(
                        field_key=key,
                        field_label=label,
                        message=msg,
                        error_type="REGEX_PATTERN_MISMATCH",
                    )
                )

        return errors

    @classmethod
    def validate_answers(cls, version: SchemeVersion, answers: Dict[str, Any]) -> Dict[str, Any]:
        all_errors: List[FormValidationError] = []

        for field in version.form_fields:
            if hasattr(field, "is_deleted") and field.is_deleted:
                continue
            errs = cls.validate_field(field, answers)
            all_errors.extend(errs)

        is_valid = len(all_errors) == 0
        return {
            "is_valid": is_valid,
            "error_count": len(all_errors),
            "errors": [e.to_dict() for e in all_errors],
            "scheme_version_id": str(version.id),
        }
