"""Tests for the guided ruleset questionnaire and Python round trips."""

from __future__ import annotations

import copy
import os
import tempfile
import unittest
from pathlib import Path

from models.request_models import PayRequest, Shift
from services.pay_calculator import PayCalculator
from services.rule_configurations import (
    CUSTOM_RULES_ENV,
    RuleConfigurationError,
    create_custom_rule,
    get_rule_configuration,
    list_rule_configurations,
    validate_rule_payload,
)
from services.rule_questionnaire import validate_questionnaire


class RuleQuestionnaireTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.previous_custom_directory = os.environ.get(CUSTOM_RULES_ENV)
        os.environ[CUSTOM_RULES_ENV] = self.temporary_directory.name

    def tearDown(self):
        if self.previous_custom_directory is None:
            os.environ.pop(CUSTOM_RULES_ENV, None)
        else:
            os.environ[CUSTOM_RULES_ENV] = self.previous_custom_directory
        self.temporary_directory.cleanup()

    def test_every_builtin_projects_all_questions(self):
        for item in list_rule_configurations():
            if item["kind"] != "builtin":
                continue
            with self.subTest(configuration=item["id"]):
                configuration = get_rule_configuration(item["id"])
                question_count = sum(
                    len(fields)
                    for fields in configuration["questionnaire"].values()
                )
                errors = [
                    issue
                    for issue in configuration["structural_issues"]
                    if issue["severity"] == "error"
                ]
                self.assertEqual(question_count, 33)
                self.assertEqual(errors, [])

    def test_missing_default_break_projects_and_calculates_half_hour(self):
        hospitality = get_rule_configuration("builtin:hospitality")
        default_break = hospitality["questionnaire"]["employment_defaults"][
            "default_break"
        ]
        self.assertEqual(default_break["answer"], 0.5)
        self.assertEqual(default_break["status"], "defaulted")

        calculator = PayCalculator(
            PayRequest(
                hourly_rate=20,
                worker_type="shift",
                award="hospitality",
                employment_type="casual",
                shifts=[],
            )
        )
        breakdown = calculator.calculate_daily_hours(
            Shift(day="Monday", start=9, end=17)
        )
        self.assertEqual(breakdown["break"], 0.5)
        self.assertEqual(breakdown["total"], 7.5)

    def test_round_trips_every_managed_field(self):
        configuration = get_rule_configuration("builtin:ma000018")
        questionnaire = copy.deepcopy(configuration["questionnaire"])
        answers = {
            "core_hours": {
                "day_worker_daily_limit_hours": 7,
                "shift_worker_daily_limit_hours": 9,
                "day_worker_weekly_limit_hours": 35,
                "shift_worker_weekly_limit_hours": 36,
            },
            "overtime": {
                "daily_overtime_configuration": {
                    "variation": "worker_type", "day": 7, "shift": 9
                },
                "weekly_overtime_configuration": {
                    "variation": "worker_type", "day": 35, "shift": 36
                },
                "part_time_contracted_hours_overtime": False,
                "standard_overtime_rate": 1.7,
                "two_tier_overtime": True,
                "extended_overtime_rate": 2.3,
                "two_tier_overtime_threshold": 3,
                "extended_overtime_days": ["Monday", "Sunday"],
                "saturday_overtime_rate": 1.8,
                "sunday_overtime_rate": 2.4,
            },
            "span_overtime": {
                "applies": True,
                "before_cutoff_hour": None,
                "cutoff_hour": 19.5,
            },
            "weekend_treatment": {
                "day_saturday_treatment": "overtime",
                "day_saturday_penalty_loading": None,
                "day_sunday_treatment": "penalty",
                "day_sunday_penalty_loading": 0.6,
                "shift_saturday_treatment": "not_applicable",
                "shift_saturday_penalty_loading": 0,
                "shift_sunday_treatment": "penalty",
                "shift_sunday_penalty_loading": 0.8,
            },
            "gap_between_shifts": {
                "applies": True,
                "minimum_hours": 11,
                "penalty_rate": 1.2,
            },
            "weekday_penalties": {
                "shift_based_penalties": [
                    {
                        "code_name": "late_shift",
                        "type": "shift_based",
                        "basis": "start",
                        "start_hour": 18,
                        "end_hour": 24,
                        "rate": 0.2,
                        "description": "Late shift",
                        "applies_to": ["shift"],
                        "extra": {"days": ["Monday"]},
                    }
                ],
                "time_based_penalties": [
                    {
                        "code_name": "night_hours",
                        "type": "time_based",
                        "basis": "time",
                        "start_hour": 0,
                        "end_hour": 6,
                        "rate": 0.3,
                        "description": "Night hours",
                        "applies_to": ["day", "shift"],
                        "extra": {},
                    }
                ],
            },
            "employment_defaults": {
                "default_break": 0.75,
                "part_time_top_up_entitlement": False,
                "full_time_top_up_entitlement": True,
            },
        }
        for section, fields in answers.items():
            for field, answer in fields.items():
                questionnaire[section][field]["answer"] = answer

        validated = validate_rule_payload(
            "ma000018", configuration["source"], questionnaire
        )
        projected = validated["questionnaire"]
        for section, fields in answers.items():
            for field, expected in fields.items():
                self.assertEqual(
                    projected[section][field]["answer"],
                    expected,
                    f"{section}.{field}",
                )

    def test_guided_save_preserves_hidden_attributes_comments_and_builtin(self):
        builtin = get_rule_configuration("builtin:hospitality")
        original = builtin["source"]
        source = original.replace(
            "class HospitalityRules:",
            "class HospitalityRules:\n"
            "    # review helper must preserve this comment\n"
            "    HIDDEN_ADVANCED_SETTING = {'keep': True}",
            1,
        )
        questionnaire = copy.deepcopy(builtin["questionnaire"])
        questionnaire["core_hours"]["shift_worker_daily_limit_hours"][
            "answer"
        ] = 9
        custom = create_custom_rule(
            "hospitality",
            "Guided Preserve",
            source,
            questionnaire,
        )

        self.assertIn(
            "# review helper must preserve this comment", custom["source"]
        )
        self.assertIn("# Standard 7.6 hour day", custom["source"])
        self.assertIn("HIDDEN_ADVANCED_SETTING = {'keep': True}", custom["source"])
        self.assertEqual(
            get_rule_configuration("builtin:hospitality")["source"], original
        )

    def test_guided_save_changes_selected_custom_calculation(self):
        builtin = get_rule_configuration("builtin:hospitality")
        questionnaire = copy.deepcopy(builtin["questionnaire"])
        questionnaire["overtime"]["daily_overtime_configuration"]["answer"] = {
            "variation": "default",
            "default": 4,
        }
        custom = create_custom_rule(
            "hospitality", "Guided Four Hour Day", builtin["source"], questionnaire
        )
        request = {
            "hourly_rate": 20,
            "worker_type": "shift",
            "award": "hospitality",
            "employment_type": "casual",
            "shifts": [
                {
                    "day": "Monday",
                    "start": 9,
                    "end": 17,
                    "break_duration": 0,
                }
            ],
        }
        result = PayCalculator(
            PayRequest(**request, rule_configuration=custom["id"])
        ).calculate_pay()
        self.assertEqual(result.overtime_hours, 4)

    def test_start_and_end_penalty_requires_both_windows(self):
        builtin = get_rule_configuration("builtin:hospitality")
        questionnaire = copy.deepcopy(builtin["questionnaire"])
        questionnaire["weekday_penalties"]["shift_based_penalties"]["answer"] = [
            {
                "code_name": "afternoon_shift",
                "type": "shift_based",
                "basis": "start_and_end",
                "start_hour": 10,
                "end_hour": 13,
                "finish_start_hour": 18,
                "finish_end_hour": 24,
                "rate": 0.125,
                "description": "Afternoon shift loading",
                "applies_to": ["shift"],
                "extra": {},
            }
        ]
        custom = create_custom_rule(
            "hospitality", "Start And End Penalty", builtin["source"], questionnaire
        )

        def calculate_penalty(end):
            return PayCalculator(
                PayRequest(
                    hourly_rate=20,
                    worker_type="shift",
                    award="hospitality",
                    employment_type="casual",
                    shifts=[
                        Shift(
                            day="Monday",
                            start=11,
                            end=end,
                            break_duration=0,
                        )
                    ],
                    rule_configuration=custom["id"],
                )
            ).calculate_pay().penalty_pay

        self.assertGreater(calculate_penalty(19), 0)
        self.assertEqual(calculate_penalty(17), 0)

    def test_raw_validation_refreshes_questionnaire(self):
        builtin = get_rule_configuration("builtin:hospitality")
        source = builtin["source"].replace(
            "ORDINARY_HOURS_LIMIT_DAILY = 10",
            "ORDINARY_HOURS_LIMIT_DAILY = 6",
            1,
        )
        validated = validate_rule_payload("hospitality", source)
        self.assertEqual(
            validated["questionnaire"]["core_hours"][
                "shift_worker_daily_limit_hours"
            ]["answer"],
            6,
        )

    def test_award_extractor_evidence_is_optional_and_does_not_control_values(self):
        builtin = get_rule_configuration("builtin:hospitality")
        imported = {
            "questionnaire_answers": {
                "core_hours": {
                    "day_worker_daily_limit_hours": {
                        "answer": 999,
                        "status": "needs_review",
                        "source_ruleset_keys": ["overtime_creation"],
                        "source_rule_ids": ["rule-1"],
                        "clause_references": ["22.1(c)"],
                        "reasoning_summary": "Imported evidence.",
                        "special_case_notes": "Check the night-shift exception.",
                    }
                }
            }
        }
        with_evidence = create_custom_rule(
            "hospitality",
            "Extractor Evidence",
            builtin["source"],
            imported,
        )
        record = with_evidence["questionnaire"]["core_hours"][
            "day_worker_daily_limit_hours"
        ]
        self.assertEqual(record["answer"], 8)
        self.assertEqual(record["clause_references"], ["22.1(c)"])
        self.assertEqual(record["status"], "needs_review")
        self.assertTrue(
            Path(self.temporary_directory.name)
            .joinpath("hospitality__extractor-evidence.questionnaire.json")
            .is_file()
        )

        without_evidence = create_custom_rule(
            "hospitality", "Extractor Python Only", builtin["source"]
        )
        self.assertIsNone(without_evidence["imported_evidence"])

    def test_structural_validation_blocks_incomplete_rows(self):
        questionnaire = copy.deepcopy(
            get_rule_configuration("builtin:hospitality")["questionnaire"]
        )
        questionnaire["weekday_penalties"]["shift_based_penalties"]["answer"] = [
            {
                "code_name": "duplicate",
                "type": "shift_based",
                "basis": "invalid",
                "start_hour": None,
                "end_hour": 25,
                "rate": -1,
                "description": "",
                "applies_to": [],
                "extra": {},
            },
            {
                "code_name": "duplicate",
                "type": "shift_based",
                "basis": "start",
                "start_hour": 1,
                "end_hour": 2,
                "rate": 0.1,
                "description": "Duplicate",
                "applies_to": ["shift"],
                "extra": {},
            },
        ]
        errors = [
            issue
            for issue in validate_questionnaire(questionnaire)
            if issue["severity"] == "error"
        ]
        self.assertGreaterEqual(len(errors), 6)
        with self.assertRaises(RuleConfigurationError):
            validate_rule_payload(
                "hospitality",
                get_rule_configuration("builtin:hospitality")["source"],
                questionnaire,
            )
        validation_result = validate_rule_payload(
            "hospitality",
            get_rule_configuration("builtin:hospitality")["source"],
            questionnaire,
            allow_invalid_questionnaire=True,
        )
        self.assertFalse(validation_result["valid"])
        self.assertGreaterEqual(
            len(validation_result["structural_issues"]), 6
        )


if __name__ == "__main__":
    unittest.main()
