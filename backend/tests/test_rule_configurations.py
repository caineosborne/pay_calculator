"""Focused tests for filesystem-backed custom rule configurations."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from models.request_models import PayRequest
from services.pay_calculator import PayCalculator
from services.rule_configurations import (
    CUSTOM_RULES_ENV,
    RuleConfigurationError,
    create_custom_rule,
    get_rule_configuration,
    load_custom_rule_class,
    list_rule_configurations,
    update_custom_rule,
    validate_rule_source,
)


class RuleConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.previous_custom_directory = os.environ.get(CUSTOM_RULES_ENV)
        os.environ[CUSTOM_RULES_ENV] = self.temporary_directory.name
        self.builtin = get_rule_configuration("builtin:hospitality")

    def tearDown(self):
        if self.previous_custom_directory is None:
            os.environ.pop(CUSTOM_RULES_ENV, None)
        else:
            os.environ[CUSTOM_RULES_ENV] = self.previous_custom_directory
        self.temporary_directory.cleanup()

    def test_create_and_update_custom_rule_never_changes_builtin(self):
        original_builtin_source = self.builtin["source"]
        custom = create_custom_rule(
            "hospitality", "Local Test", original_builtin_source
        )

        self.assertEqual(custom["id"], "custom:hospitality:local-test")
        self.assertEqual(custom["kind"], "custom")
        self.assertIn(
            custom["id"],
            {
                configuration["id"]
                for configuration in list_rule_configurations()
            },
        )

        updated_source = original_builtin_source.replace(
            "ORDINARY_HOURS_LIMIT_DAILY = 10",
            "ORDINARY_HOURS_LIMIT_DAILY = 4",
            1,
        )
        update_custom_rule(custom["id"], updated_source)

        self.assertEqual(
            get_rule_configuration("builtin:hospitality")["source"],
            original_builtin_source,
        )
        custom_path = (
            Path(self.temporary_directory.name)
            / "hospitality__local-test.py"
        )
        self.assertTrue(custom_path.is_file())
        self.assertIn(
            "ORDINARY_HOURS_LIMIT_DAILY = 4",
            custom_path.read_text(encoding="utf-8"),
        )

    def test_validation_rejects_missing_required_attributes(self):
        with self.assertRaisesRegex(
            RuleConfigurationError, "missing required attributes"
        ):
            validate_rule_source(
                "hospitality", "class HospitalityRules:\n    pass\n"
            )

    def test_custom_configuration_is_used_for_calculation(self):
        custom_source = self.builtin["source"].replace(
            "ORDINARY_HOURS_LIMIT_DAILY = 10",
            "ORDINARY_HOURS_LIMIT_DAILY = 4",
            1,
        )
        custom = create_custom_rule(
            "hospitality", "Four Hour Day", custom_source
        )
        request_data = {
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

        builtin_result = PayCalculator(
            PayRequest(**request_data)
        ).calculate_pay()
        custom_result = PayCalculator(
            PayRequest(
                **request_data,
                rule_configuration=custom["id"],
            )
        ).calculate_pay()

        self.assertEqual(builtin_result.overtime_hours, 0)
        self.assertEqual(custom_result.overtime_hours, 4)
        self.assertGreater(custom_result.total_pay, builtin_result.total_pay)

    def test_calculators_keep_their_rule_configurations_isolated(self):
        custom_source = self.builtin["source"].replace(
            "ORDINARY_HOURS_LIMIT_DAILY = 10",
            "ORDINARY_HOURS_LIMIT_DAILY = 4",
            1,
        )
        custom = create_custom_rule(
            "hospitality", "Isolated Four Hour Day", custom_source
        )
        hospitality_request = PayRequest(
            hourly_rate=20,
            worker_type="shift",
            award="hospitality",
            employment_type="casual",
            rule_configuration=custom["id"],
            shifts=[
                {
                    "day": "Monday",
                    "start": 9,
                    "end": 17,
                    "break_duration": 0,
                }
            ],
        )
        custom_calculator = PayCalculator(hospitality_request)

        # Constructing another award calculator must not replace this one's rules.
        PayCalculator(
            PayRequest(
                hourly_rate=20,
                worker_type="shift",
                award="aged_care",
                employment_type="casual",
                shifts=[],
            )
        )

        result = custom_calculator.calculate_pay()
        self.assertEqual(result.overtime_hours, 4)

    def test_aged_care_day_work_before_morning_span_cutoff_is_overtime(self):
        result = PayCalculator(
            PayRequest(
                hourly_rate=20,
                worker_type="day",
                award="aged_care",
                employment_type="full_time",
                shifts=[
                    {
                        "day": "Monday",
                        "start": 5,
                        "end": 6,
                        "break_duration": 0,
                    }
                ],
            )
        ).calculate_pay()

        self.assertEqual(result.overtime_hours, 1)
        self.assertEqual(result.overtime_pay, 30)

    def test_two_tier_overtime_splits_standard_and_higher_rates(self):
        result = PayCalculator(
            PayRequest(
                hourly_rate=20,
                worker_type="day",
                award="aged_care",
                employment_type="full_time",
                shifts=[
                    {
                        "day": "Monday",
                        "start": 16,
                        "end": 21,
                        "break_duration": 0,
                    }
                ],
            )
        ).calculate_pay()

        self.assertEqual(result.overtime_hours, 3)
        self.assertEqual(result.overtime_pay, 100)

    def test_overtime_hours_do_not_create_a_contracted_hours_top_up(self):
        shifts = [
            {
                "week": week,
                "day": day,
                "start": 12,
                "end": 21,
                "break_duration": 0.5,
            }
            for week in (1, 2)
            for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
        ]
        result = PayCalculator(
            PayRequest(
                hourly_rate=20,
                worker_type="day",
                award="aged_care",
                employment_type="full_time",
                contracted_hours=38,
                shifts=shifts,
            )
        ).calculate_pay()

        self.assertGreater(result.overtime_hours, 0)
        self.assertGreater(result.total_hours, 76)
        self.assertEqual(result.topup_hours, 0)

    def test_time_based_penalty_reports_only_overlapping_loaded_hours(self):
        aged_care_source = get_rule_configuration("builtin:aged_care")[
            "source"
        ].replace(
            "    PENALTIES = {\n",
            "    PENALTIES = {\n"
            "        'afternoon_loading': {\n"
            "            'type': 'time_based',\n"
            "            'basis': 'time',\n"
            "            'start': 14,\n"
            "            'end': 16,\n"
            "            'rate': 0.1,\n"
            "            'description': 'Afternoon loading',\n"
            "            'applies_to': ['day', 'shift'],\n"
            "        },\n",
            1,
        )
        custom = create_custom_rule(
            "aged_care", "Afternoon Loading", aged_care_source
        )
        result = PayCalculator(
            PayRequest(
                hourly_rate=20,
                worker_type="day",
                award="aged_care",
                employment_type="full_time",
                rule_configuration=custom["id"],
                shifts=[
                    {
                        "day": "Monday",
                        "start": 12,
                        "end": 20,
                        "break_duration": 0,
                    }
                ],
            )
        ).calculate_pay()

        self.assertEqual(result.time_based_penalty_hours, 2)
        self.assertEqual(result.hourly_penalty_pay, 4)

    def test_custom_rule_classes_are_cached_until_the_file_changes(self):
        custom = create_custom_rule(
            "hospitality", "Cached Rule", self.builtin["source"]
        )
        first = load_custom_rule_class(custom["id"], "hospitality")
        second = load_custom_rule_class(custom["id"], "hospitality")
        self.assertIs(first, second)

        updated_source = self.builtin["source"].replace(
            "ORDINARY_HOURS_LIMIT_DAILY = 10",
            "ORDINARY_HOURS_LIMIT_DAILY = 4",
            1,
        )
        update_custom_rule(custom["id"], updated_source)
        updated = load_custom_rule_class(custom["id"], "hospitality")

        self.assertIsNot(updated, first)
        self.assertEqual(updated.ORDINARY_HOURS_LIMIT_DAILY, 4)


if __name__ == "__main__":
    unittest.main()
