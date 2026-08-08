"""Project editable rule classes into a guided questionnaire and patch them back."""

from __future__ import annotations

import ast
import copy
import io
import pprint
import re
import tokenize
from typing import Any

from services.award_registry import load_awards


MANAGED_ATTRIBUTES = {
    "SHIFT_RULES",
    "ORDINARY_TIME_RULES",
    "DAY_TREATMENT_RULES",
    "PAY_RATES",
    "GAP_BETWEEN_SHIFTS_RULE",
    "ORDINARY_HOUR_PENALTIES",
    "TOP_UP_RULES",
}

WEEKEND_FIELDS = {
    ("day", "Saturday"): (
        "weekend_treatment.day_saturday_treatment",
        "weekend_treatment.day_saturday_penalty_loading",
    ),
    ("day", "Sunday"): (
        "weekend_treatment.day_sunday_treatment",
        "weekend_treatment.day_sunday_penalty_loading",
    ),
    ("shift", "Saturday"): (
        "weekend_treatment.shift_saturday_treatment",
        "weekend_treatment.shift_saturday_penalty_loading",
    ),
    ("shift", "Sunday"): (
        "weekend_treatment.shift_sunday_treatment",
        "weekend_treatment.shift_sunday_penalty_loading",
    ),
}

SECTION_FIELDS = {
    "overtime": [
        "daily_overtime_configuration",
        "weekly_overtime_configuration",
        "standard_overtime_rate",
        "two_tier_overtime",
        "extended_overtime_rate",
        "two_tier_overtime_threshold",
        "extended_overtime_days",
        "saturday_overtime_rate",
        "sunday_overtime_rate",
    ],
    "span_overtime": ["applies", "before_cutoff_hour", "cutoff_hour"],
    "weekend_treatment": [
        "day_saturday_treatment",
        "day_saturday_penalty_loading",
        "day_sunday_treatment",
        "day_sunday_penalty_loading",
        "shift_saturday_treatment",
        "shift_saturday_penalty_loading",
        "shift_sunday_treatment",
        "shift_sunday_penalty_loading",
    ],
    "gap_between_shifts": ["applies", "minimum_hours", "penalty_rate"],
    "weekday_penalties": ["shift_based_penalties", "time_based_penalties"],
    "employment_defaults": [
        "default_break",
        "part_time_top_up_entitlement",
        "full_time_top_up_entitlement",
    ],
}

def _issue(field_path: str, message: str, severity: str = "warning") -> dict:
    return {
        "severity": severity,
        "field_path": field_path,
        "message": message,
    }


def _record(
    answer: Any,
    attribute: str | None = None,
    status: str = "derived",
    message: str | None = None,
) -> dict:
    return {
        "answer": answer,
        "status": status,
        "source_ruleset_keys": [],
        "source_rule_ids": [],
        "clause_references": [],
        "reasoning_summary": message
        or (
            f"Loaded from Python attribute {attribute}."
            if attribute
            else "Derived from the selected Python rule class."
        ),
        "special_case_notes": [],
    }


def _class_assignments(
    award_key: str, source: str
) -> tuple[ast.ClassDef | None, dict[str, tuple[ast.AST, ast.AST]], list[dict]]:
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return (
            None,
            {},
            [
                _issue(
                    "_class",
                    f"Invalid Python syntax at line {error.lineno}: {error.msg}",
                    "error",
                )
            ],
        )
    award = next(
        (item for item in load_awards() if item["key"] == award_key),
        None,
    )
    if award is None:
        raise ValueError(f"Unknown award: {award_key}")
    class_name = award["class_name"]
    class_node = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == class_name
        ),
        None,
    )
    if class_node is None:
        return (
            None,
            {},
            [_issue("_class", f"Expected a top-level class named {class_name}.", "error")],
        )

    assignments: dict[str, tuple[ast.AST, ast.AST]] = {}
    for statement in class_node.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            if isinstance(target, ast.Name):
                assignments[target.id] = (statement, statement.value)
        elif isinstance(statement, ast.AnnAssign) and isinstance(
            statement.target, ast.Name
        ):
            assignments[statement.target.id] = (statement, statement.value)
    return class_node, assignments, []


def _literal(
    assignments: dict[str, tuple[ast.AST, ast.AST]],
    attribute: str,
    path: str,
    issues: list[dict],
) -> tuple[Any, str]:
    assignment = assignments.get(attribute)
    if assignment is None:
        issues.append(_issue(path, f"Python attribute {attribute} is missing."))
        return None, "not_found"
    try:
        return ast.literal_eval(assignment[1]), "derived"
    except (ValueError, TypeError):
        issues.append(
            _issue(
                path,
                f"Python attribute {attribute} is not a literal value and cannot "
                "be represented by the Review Helper.",
            )
        )
        return None, "not_found"


def project_rule_source(
    award_key: str, source: str, imported_context: dict | None = None
) -> dict:
    """Build the guided questionnaire from canonical grouped rule dictionaries."""
    class_node, assignments, issues = _class_assignments(award_key, source)
    questionnaire = {
        section: {field: _record(None, status="not_found") for field in fields}
        for section, fields in SECTION_FIELDS.items()
    }
    if class_node is None:
        return {
            "questionnaire": questionnaire,
            "structural_issues": issues,
            "advanced_attributes": [],
        }
    groups = {}
    for attribute in MANAGED_ATTRIBUTES:
        value, _ = _literal(assignments, attribute, attribute, issues)
        groups[attribute] = value if isinstance(value, dict) else {}

    shift_rules = groups["SHIFT_RULES"]
    ordinary = groups["ORDINARY_TIME_RULES"]
    treatments = groups["DAY_TREATMENT_RULES"]
    overtime = groups["PAY_RATES"].get("overtime", {})
    gap = groups["GAP_BETWEEN_SHIFTS_RULE"]
    penalties = groups["ORDINARY_HOUR_PENALTIES"]
    top_up = groups["TOP_UP_RULES"]

    daily = ordinary.get("daily", {})
    period = ordinary.get("period", {})
    questionnaire["overtime"]["daily_overtime_configuration"] = _record(
        daily, "ORDINARY_TIME_RULES", "derived"
    )
    questionnaire["overtime"]["weekly_overtime_configuration"] = _record(
        period, "ORDINARY_TIME_RULES", "derived"
    )

    tier = overtime.get("two_tier", {})
    overtime_answers = {
        "part_time_contracted_hours_overtime": period.get(
            "part_time_uses_contracted_hours", False
        ),
        "standard_overtime_rate": overtime.get("weekday", {}).get("multiplier"),
        "two_tier_overtime": tier.get("enabled", False),
        "extended_overtime_rate": overtime.get("extended", {}).get("multiplier"),
        "two_tier_overtime_threshold": tier.get("threshold", 0),
        "extended_overtime_days": tier.get("days", []),
        "saturday_overtime_rate": overtime.get("saturday", {}).get("multiplier"),
        "sunday_overtime_rate": overtime.get("sunday", {}).get("multiplier"),
    }
    for field, value in overtime_answers.items():
        questionnaire["overtime"][field] = _record(
            value, "PAY_RATES", "derived"
        )

    span = ordinary.get("span_overtime", {}).get("day", {}).get("default", {})
    span_answers = {
        "applies": bool(span.get("enabled", False)),
        "before_cutoff_hour": span.get("start"),
        "cutoff_hour": span.get("end"),
    }
    for field, value in span_answers.items():
        questionnaire["span_overtime"][field] = _record(
            value, "ORDINARY_TIME_RULES", "derived"
        )

    for (worker, day), (treatment_path, loading_path) in WEEKEND_FIELDS.items():
        treatment_section, treatment_field = treatment_path.split(".", 1)
        loading_section, loading_field = loading_path.split(".", 1)
        rule = treatments.get(day, {}).get(worker)
        treatment = None
        loading = None
        if isinstance(rule, dict):
            if rule.get("base_classification") == "overtime":
                treatment = "overtime"
            else:
                loading = rule.get("ordinary_loading", 0)
                treatment = (
                    "penalty"
                    if loading not in (None, 0, 0.0)
                    else "not_applicable"
                )
        if rule is None:
            issues.append(
                _issue(
                    treatment_path,
                    f"DAY_TREATMENT_RULES has no {worker} worker {day} entry.",
                )
            )
        questionnaire[treatment_section][treatment_field] = _record(
            treatment, "DAY_TREATMENT_RULES", "derived" if rule else "not_found"
        )
        questionnaire[loading_section][loading_field] = _record(
            loading, "DAY_TREATMENT_RULES", "derived" if rule else "not_found"
        )

    gap_hours = gap.get("minimum_hours", 0)
    gap_rate = gap.get("loading", 0)
    questionnaire["gap_between_shifts"] = {
        "applies": _record(
            bool(gap_hours), "GAP_BETWEEN_SHIFTS_RULE", "derived"
        ),
        "minimum_hours": _record(gap_hours, "GAP_BETWEEN_SHIFTS_RULE", "derived"),
        "penalty_rate": _record(gap_rate, "GAP_BETWEEN_SHIFTS_RULE", "derived"),
    }

    shift_rows: list[dict] = []
    time_rows: list[dict] = []
    if isinstance(penalties, dict):
        for code_name, penalty in penalties.items():
            if not isinstance(penalty, dict):
                row = {
                    "code_name": code_name,
                    "type": "",
                    "basis": "",
                    "start_hour": None,
                    "end_hour": None,
                    "rate": None,
                    "description": "",
                    "applies_to": [],
                    "extra": {"raw_value": penalty},
                }
            else:
                managed_keys = {
                    "type",
                    "basis",
                    "start",
                    "end",
                    "finish_start",
                    "finish_end",
                    "rate",
                    "description",
                    "applies_to",
                }
                row = {
                    "code_name": code_name,
                    "type": penalty.get("type", ""),
                    "basis": (
                        penalty.get("basis", penalty.get("match_on", "start"))
                        if penalty.get("type") == "shift_based"
                        else "time"
                    ),
                    "start_hour": penalty.get("start"),
                    "end_hour": penalty.get("end"),
                    "rate": penalty.get("rate"),
                    "description": penalty.get("description", ""),
                    "applies_to": penalty.get("applies_to", []),
                    # Preserve keys the guided editor does not own.
                    "extra": {
                        key: copy.deepcopy(value)
                        for key, value in penalty.items()
                        if key not in managed_keys
                    },
                }
                if row["basis"] == "start_and_end":
                    row["finish_start_hour"] = penalty.get("finish_start")
                    row["finish_end_hour"] = penalty.get("finish_end")
            if row["type"] == "shift_based":
                shift_rows.append(row)
            elif row["type"] == "time_based":
                time_rows.append(row)
            else:
                issues.append(
                    _issue(
                        f"weekday_penalties.{code_name}",
                        f"Penalty '{code_name}' has an unsupported or missing type.",
                    )
                )
    elif penalties is not None:
        issues.append(
            _issue(
                "weekday_penalties",
                "ORDINARY_HOUR_PENALTIES must be a dictionary.",
            )
        )
    questionnaire["weekday_penalties"] = {
        "shift_based_penalties": _record(
            shift_rows, "ORDINARY_HOUR_PENALTIES", "derived"
        ),
        "time_based_penalties": _record(
            time_rows, "ORDINARY_HOUR_PENALTIES", "derived"
        ),
    }

    employment_answers = {
        "default_break": shift_rules.get("default_break_hours", 0.5),
        "part_time_top_up_entitlement": top_up.get("part_time", False),
        "full_time_top_up_entitlement": top_up.get("full_time", False),
    }
    for field, value in employment_answers.items():
        questionnaire["employment_defaults"][field] = _record(
            value,
            "SHIFT_RULES" if field == "default_break" else "TOP_UP_RULES",
            "derived",
        )

    _merge_imported_context(questionnaire, imported_context)
    issues.extend(validate_questionnaire(questionnaire))
    advanced_attributes = sorted(
        attribute for attribute in assignments if attribute not in MANAGED_ATTRIBUTES
    )
    return {
        "questionnaire": questionnaire,
        "structural_issues": _deduplicate_issues(issues),
        "advanced_attributes": advanced_attributes,
    }


def _merge_imported_context(questionnaire: dict, imported_context: dict | None) -> None:
    """Copy evidence metadata without replacing Python-derived answers."""
    if not isinstance(imported_context, dict):
        return
    sections = imported_context.get("questionnaire_answers", imported_context)
    if not isinstance(sections, dict):
        return
    for section, fields in questionnaire.items():
        for field, record in fields.items():
            imported_path = f"{section}.{field}"
            imported_section_name, imported_field_name = imported_path.split(
                ".", 1
            )
            imported_section = sections.get(imported_section_name)
            imported_record = (
                imported_section.get(imported_field_name)
                if isinstance(imported_section, dict)
                else None
            )
            if not isinstance(record, dict) or not isinstance(imported_record, dict):
                continue
            for key in (
                "status",
                "source_ruleset_keys",
                "source_rule_ids",
                "clause_references",
                "reasoning_summary",
                "special_case_notes",
            ):
                if key in imported_record:
                    value = copy.deepcopy(imported_record[key])
                    if key in {
                        "source_ruleset_keys",
                        "source_rule_ids",
                        "clause_references",
                        "special_case_notes",
                    }:
                        if value is None:
                            value = []
                        elif not isinstance(value, list):
                            value = [value]
                    record[key] = value


def _answer(questionnaire: dict, path: str) -> Any:
    section, field = path.split(".", 1)
    value = questionnaire.get(section, {}).get(field)
    return value.get("answer") if isinstance(value, dict) else value


def _numeric(
    questionnaire: dict,
    path: str,
    issues: list[dict],
    *,
    positive: bool = False,
    minimum: float | None = None,
    maximum: float | None = None,
) -> None:
    value = _answer(questionnaire, path)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        issues.append(_issue(path, "A numeric value is required.", "error"))
        return
    if positive and value <= 0:
        issues.append(_issue(path, "The value must be greater than zero.", "error"))
    if minimum is not None and value < minimum:
        issues.append(_issue(path, f"The value must be at least {minimum}.", "error"))
    if maximum is not None and value > maximum:
        issues.append(_issue(path, f"The value must not exceed {maximum}.", "error"))


def _boolean(questionnaire: dict, path: str, issues: list[dict]) -> None:
    if not isinstance(_answer(questionnaire, path), bool):
        issues.append(_issue(path, "Choose Yes or No.", "error"))


def _validate_overtime_configuration(questionnaire: dict, path: str, issues: list[dict]) -> None:
    value = _answer(questionnaire, path)
    if not isinstance(value, dict):
        issues.append(_issue(path, "Choose how this overtime limit varies.", "error"))
        return
    variation = value.get("variation")
    fields = {
        "default": ("default",),
        "worker_type": ("day", "shift"),
        "employment_type": ("full_time", "part_time", "casual"),
    }.get(variation)
    if fields is None:
        issues.append(_issue(path + ".variation", "Choose one variation method.", "error"))
        return
    for field in fields:
        number = value.get(field)
        if isinstance(number, bool) or not isinstance(number, (int, float)) or number <= 0:
            issues.append(_issue(path + f".{field}", "Enter a limit greater than zero.", "error"))

    if path == "overtime.weekly_overtime_configuration":
        basis = value.get("basis", "weekly")
        valid_bases = {"weekly", "pay_period"}
        if isinstance(basis, dict):
            if variation != "employment_type" or any(
                basis.get(employment_type) not in valid_bases
                for employment_type in ("full_time", "part_time", "casual")
            ):
                issues.append(_issue(path + ".basis", "Set weekly or pay-period overtime for each employment type.", "error"))
        elif basis not in valid_bases:
            issues.append(_issue(path + ".basis", "Choose weekly or pay-period overtime.", "error"))
        max_work_days = value.get("max_work_days")
        if max_work_days is not None and (
            isinstance(max_work_days, bool)
            or not isinstance(max_work_days, int)
            or max_work_days < 1
        ):
            issues.append(_issue(path + ".max_work_days", "Enter a whole number of at least 1, or leave it blank.", "error"))


def validate_questionnaire(questionnaire: dict) -> list[dict]:
    """Return executable-structure errors for questionnaire values."""
    issues: list[dict] = []
    for path in (
        "overtime.standard_overtime_rate",
        "overtime.saturday_overtime_rate",
        "overtime.sunday_overtime_rate",
    ):
        _numeric(questionnaire, path, issues, positive=True)

    _validate_overtime_configuration(
        questionnaire, "overtime.daily_overtime_configuration", issues
    )
    _validate_overtime_configuration(
        questionnaire, "overtime.weekly_overtime_configuration", issues
    )

    _boolean(questionnaire, "overtime.two_tier_overtime", issues)
    if _answer(questionnaire, "overtime.two_tier_overtime") is True:
        _numeric(
            questionnaire,
            "overtime.extended_overtime_rate",
            issues,
            positive=True,
        )
        _numeric(
            questionnaire,
            "overtime.two_tier_overtime_threshold",
            issues,
            minimum=0,
        )
        days = _answer(questionnaire, "overtime.extended_overtime_days")
        valid_days = {
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        }
        if (
            not isinstance(days, list)
            or not days
            or any(day not in valid_days for day in days)
        ):
            issues.append(
                _issue(
                    "overtime.extended_overtime_days",
                    "Select at least one valid extended-overtime day.",
                    "error",
                )
            )

    _boolean(questionnaire, "span_overtime.applies", issues)
    if _answer(questionnaire, "span_overtime.applies") is True:
        _numeric(
            questionnaire,
            "span_overtime.cutoff_hour",
            issues,
            minimum=0,
            maximum=24,
        )
        before_cutoff = _answer(questionnaire, "span_overtime.before_cutoff_hour")
        if before_cutoff is not None:
            _numeric(
                questionnaire,
                "span_overtime.before_cutoff_hour",
                issues,
                minimum=0,
                maximum=24,
            )

    for treatment_path, loading_path in WEEKEND_FIELDS.values():
        treatment = _answer(questionnaire, treatment_path)
        if treatment not in {"overtime", "penalty", "not_applicable"}:
            issues.append(
                _issue(
                    treatment_path,
                    "Choose Overtime, Penalty loading, or Not applicable.",
                    "error",
                )
            )
        if treatment == "penalty":
            _numeric(questionnaire, loading_path, issues, minimum=0)

    _boolean(questionnaire, "gap_between_shifts.applies", issues)
    if _answer(questionnaire, "gap_between_shifts.applies") is True:
        _numeric(
            questionnaire,
            "gap_between_shifts.minimum_hours",
            issues,
            positive=True,
        )
        _numeric(
            questionnaire,
            "gap_between_shifts.penalty_rate",
            issues,
            minimum=0,
        )

    seen_codes: set[str] = set()
    for field, expected_type in (
        ("shift_based_penalties", "shift_based"),
        ("time_based_penalties", "time_based"),
    ):
        rows = _answer(questionnaire, f"weekday_penalties.{field}")
        if not isinstance(rows, list):
            issues.append(
                _issue(
                    f"weekday_penalties.{field}",
                    "Penalty rows must be a list.",
                    "error",
                )
            )
            continue
        for index, row in enumerate(rows):
            path = f"weekday_penalties.{field}.{index}"
            if not isinstance(row, dict):
                issues.append(_issue(path, "Penalty row is malformed.", "error"))
                continue
            code = row.get("code_name")
            if not isinstance(code, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", code):
                issues.append(
                    _issue(path + ".code_name", "Enter a valid unique code name.", "error")
                )
            elif code in seen_codes:
                issues.append(
                    _issue(path + ".code_name", "Penalty code names must be unique.", "error")
                )
            else:
                seen_codes.add(code)
            if row.get("type") != expected_type:
                issues.append(
                    _issue(path + ".type", f"Type must be {expected_type}.", "error")
                )
            allowed_bases = (
                {"start", "end", "duration", "start_and_end"}
                if expected_type == "shift_based"
                else {"time"}
            )
            if row.get("basis") not in allowed_bases:
                issues.append(
                    _issue(path + ".basis", "Choose a valid penalty condition.", "error")
                )
            for key in ("start_hour", "end_hour"):
                value = row.get(key)
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or value < 0
                    or value > 24
                ):
                    issues.append(
                        _issue(path + f".{key}", "Enter a time from 0 to 24.", "error")
                    )
            if row.get("basis") == "start_and_end":
                for key in ("finish_start_hour", "finish_end_hour"):
                    value = row.get(key)
                    if (
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or value < 0
                        or value > 24
                    ):
                        issues.append(
                            _issue(path + f".{key}", "Enter a time from 0 to 24.", "error")
                        )
            rate = row.get("rate")
            if isinstance(rate, bool) or not isinstance(rate, (int, float)) or rate < 0:
                issues.append(
                    _issue(path + ".rate", "Enter a non-negative numeric rate.", "error")
                )
            if not isinstance(row.get("description"), str) or not row["description"].strip():
                issues.append(
                    _issue(path + ".description", "Description is required.", "error")
                )
            applicability = row.get("applies_to")
            if (
                not isinstance(applicability, list)
                or not applicability
                or any(worker not in {"day", "shift"} for worker in applicability)
            ):
                issues.append(
                    _issue(
                        path + ".applies_to",
                        "Select day workers, shift workers, or both.",
                        "error",
                    )
                )

    _numeric(
        questionnaire,
        "employment_defaults.default_break",
        issues,
        minimum=0,
        maximum=24,
    )
    for path in (
        "overtime.part_time_contracted_hours_overtime",
        "employment_defaults.part_time_top_up_entitlement",
        "employment_defaults.full_time_top_up_entitlement",
    ):
        _boolean(questionnaire, path, issues)
    return _deduplicate_issues(issues)


def _deduplicate_issues(issues: list[dict]) -> list[dict]:
    result = []
    seen = set()
    for issue in issues:
        key = (issue["severity"], issue["field_path"], issue["message"])
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result


def _format_assignment(attribute: str, value: Any, indent: str = "    ") -> str:
    formatted = pprint.pformat(value, width=88, sort_dicts=False)
    if "\n" in formatted:
        formatted = formatted.replace("\n", "\n" + indent)
    return f"{indent}{attribute} = {formatted}"


def patch_rule_source(award_key: str, source: str, questionnaire: dict) -> str:
    """Patch only managed class assignments while retaining all other source."""
    errors = [
        issue
        for issue in validate_questionnaire(questionnaire)
        if issue["severity"] == "error"
    ]
    if errors:
        raise ValueError(errors[0]["message"])
    class_node, assignments, parse_issues = _class_assignments(award_key, source)
    if class_node is None:
        raise ValueError(parse_issues[0]["message"])
    values = {}
    for attribute in MANAGED_ATTRIBUTES:
        try:
            values[attribute] = copy.deepcopy(
                ast.literal_eval(assignments[attribute][1])
            )
        except (KeyError, ValueError, TypeError):
            raise ValueError(
                f"{attribute} must be a literal dictionary."
            ) from None

    values["SHIFT_RULES"]["default_break_hours"] = _answer(
        questionnaire, "employment_defaults.default_break"
    )

    ordinary = values["ORDINARY_TIME_RULES"]
    ordinary["daily"] = _answer(
        questionnaire, "overtime.daily_overtime_configuration"
    )
    ordinary["period"] = _answer(
        questionnaire, "overtime.weekly_overtime_configuration"
    )
    ordinary["period"]["part_time_uses_contracted_hours"] = _answer(
        questionnaire, "overtime.part_time_contracted_hours_overtime"
    )
    if _answer(questionnaire, "span_overtime.applies"):
        span_rules = ordinary.setdefault("span_overtime", {}).setdefault("day", {})
        default_span = span_rules.setdefault("default", {})
        default_span.update(
            {
                "start": _answer(
                    questionnaire, "span_overtime.before_cutoff_hour"
                ),
                "end": _answer(questionnaire, "span_overtime.cutoff_hour"),
                "enabled": True,
            }
        )
    else:
        ordinary["span_overtime"] = {}

    overtime = values["PAY_RATES"].setdefault("overtime", {})
    for rate_key, field in (
        ("weekday", "standard_overtime_rate"),
        ("extended", "extended_overtime_rate"),
        ("saturday", "saturday_overtime_rate"),
        ("sunday", "sunday_overtime_rate"),
    ):
        overtime.setdefault(rate_key, {})["multiplier"] = _answer(
            questionnaire, f"overtime.{field}"
        )
    overtime["two_tier"] = {
        "enabled": _answer(questionnaire, "overtime.two_tier_overtime"),
        "threshold": _answer(
            questionnaire, "overtime.two_tier_overtime_threshold"
        ),
        "days": _answer(questionnaire, "overtime.extended_overtime_days"),
    }

    day_treatments = values["DAY_TREATMENT_RULES"]
    for (worker, day), (treatment_path, loading_path) in WEEKEND_FIELDS.items():
        day_rule = day_treatments.setdefault(day, {}).setdefault(worker, {})
        treatment = _answer(questionnaire, treatment_path)
        if treatment == "overtime":
            day_rule["base_classification"] = "overtime"
            day_rule["ordinary_loading"] = 0
        else:
            day_rule["base_classification"] = "ordinary"
            day_rule["ordinary_loading"] = (
                _answer(questionnaire, loading_path)
                if treatment == "penalty"
                else 0
            )

    if _answer(questionnaire, "gap_between_shifts.applies"):
        gap = values["GAP_BETWEEN_SHIFTS_RULE"]
        gap["minimum_hours"] = _answer(
            questionnaire, "gap_between_shifts.minimum_hours"
        )
        gap["loading"] = _answer(
            questionnaire, "gap_between_shifts.penalty_rate"
        )
    else:
        values["GAP_BETWEEN_SHIFTS_RULE"] = {}

    penalties = {}
    for field in ("shift_based_penalties", "time_based_penalties"):
        for row in _answer(
            questionnaire,
            f"weekday_penalties.{field}",
        ) or []:
            penalty = copy.deepcopy(row.get("extra") or {})
            penalty.update(
                {
                    "type": row["type"],
                    "basis": row["basis"],
                    "start": row["start_hour"],
                    "end": row["end_hour"],
                    "rate": row["rate"],
                    "description": row["description"],
                    "applies_to": row["applies_to"],
                }
            )
            if row["basis"] == "start_and_end":
                penalty["finish_start"] = row["finish_start_hour"]
                penalty["finish_end"] = row["finish_end_hour"]
            penalties[row["code_name"]] = penalty
    values["ORDINARY_HOUR_PENALTIES"] = penalties
    values["TOP_UP_RULES"]["part_time"] = _answer(
        questionnaire, "employment_defaults.part_time_top_up_entitlement"
    )
    values["TOP_UP_RULES"]["full_time"] = _answer(
        questionnaire, "employment_defaults.full_time_top_up_entitlement"
    )

    lines = source.splitlines(keepends=True)
    replacements: list[tuple[int, int, str]] = []
    missing: list[tuple[str, Any]] = []
    # Replace complete assignment statements by source line number. This leaves
    # class identity, hidden attributes, and code outside managed assignments intact.
    for attribute, value in values.items():
        assignment = assignments.get(attribute)
        if assignment is None:
            missing.append((attribute, value))
            continue
        statement = assignment[0]
        start = statement.lineno - 1
        end = statement.end_lineno or statement.lineno
        original = "".join(lines[start:end])
        newline = "\n" if original.endswith("\n") else ""
        indent_match = re.match(r"\s*", lines[start])
        indent = indent_match.group(0) if indent_match else "    "
        trailing_comment = ""
        if statement.end_col_offset is not None:
            last_line = lines[end - 1].rstrip("\n")
            suffix = last_line[statement.end_col_offset :]
            comment_index = suffix.find("#")
            if comment_index >= 0:
                trailing_comment = "  " + suffix[comment_index:].rstrip()
        preserved_comments = []
        # The penalty group is fully generated by the guided editor. Inline comments
        # from an older literal do not describe its current rows and used to be
        # moved above the regenerated assignment on every save.
        if attribute != "ORDINARY_HOUR_PENALTIES":
            try:
                tokens = tokenize.generate_tokens(io.StringIO(original).readline)
                for token in tokens:
                    if token.type == tokenize.COMMENT:
                        comment = token.string.rstrip()
                        if comment and comment not in trailing_comment:
                            preserved_comments.append(indent + comment + "\n")
            except tokenize.TokenError:
                preserved_comments = []
        replacements.append(
            (
                start,
                end,
                "".join(preserved_comments)
                + _format_assignment(attribute, value, indent)
                + trailing_comment
                + newline,
            )
        )

    for start, end, replacement in sorted(replacements, reverse=True):
        lines[start:end] = [replacement]

    if missing:
        insert_at = class_node.end_lineno or len(lines)
        # Account for line changes before the class end.
        delta = sum(
            replacement.count("\n") - (end - start)
            for start, end, replacement in replacements
            if start < insert_at
        )
        insert_at += delta
        block = "".join(
            _format_assignment(attribute, value) + "\n"
            for attribute, value in missing
        )
        lines.insert(insert_at, block)
    return "".join(lines)
