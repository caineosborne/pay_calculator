"""Canonical custom-rule configuration regression tests."""

from __future__ import annotations

import copy
import os
import tempfile
import unittest

from models.request_models import PayRequest
from services.pay_calculator import PayCalculator
from services.award_registry import public_awards
from services.rule_configurations import (
    CUSTOM_RULES_ENV,
    RuleConfigurationError,
    create_custom_rule,
    get_rule_configuration,
    list_rule_configurations,
    validate_rule_source,
)


class RuleConfigurationTests(unittest.TestCase):
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

    def test_only_live_builtin_configurations_are_listed(self):
        builtins = {
            item["base_award"]
            for item in list_rule_configurations()
            if item["kind"] == "builtin"
        }
        self.assertEqual(
            builtins,
            {"fast_food", "coles_2024", "gria_2026", "woolies_2024_demo"},
        )

    def test_awards_expose_editable_hourly_rate_options(self):
        awards = {award["key"]: award for award in public_awards()}

        self.assertEqual(
            awards["fast_food"]["hourly_rate_options"][0]["hourly_rate"],
            27.81,
        )
        self.assertEqual(
            len(awards["gria_2026"]["hourly_rate_options"]),
            8,
        )
        self.assertEqual(
            awards["gria_2026"]["hourly_rate_options"][-1]["hourly_rate"],
            33.99,
        )
        self.assertEqual(
            awards["woolies_2024_demo"]["hourly_rate_options"][0]["hourly_rate"],
            28.26,
        )
        self.assertEqual(
            len(awards["woolies_2024_demo"]["hourly_rate_options"]),
            11,
        )
        self.assertEqual(
            awards["coles_2024"]["hourly_rate_options"][-1]["hourly_rate"],
            31.84,
        )
        self.assertEqual(
            len(awards["coles_2024"]["hourly_rate_options"]),
            6,
        )

    def test_flat_rule_class_is_rejected(self):
        with self.assertRaisesRegex(
            RuleConfigurationError, "missing required canonical attributes"
        ):
            validate_rule_source(
                "fast_food", "class FastFoodAward2026Rules:\n    pass\n"
            )

    def test_guided_editor_writes_grouped_rules_and_changes_calculation(self):
        builtin = get_rule_configuration("builtin:fast_food")
        questionnaire = copy.deepcopy(builtin["questionnaire"])
        questionnaire["overtime"]["daily_overtime_configuration"]["answer"] = {
            "variation": "default",
            "default": 4,
        }
        custom = create_custom_rule(
            "fast_food", "Four Hour Day", builtin["source"], questionnaire
        )

        self.assertIn("ORDINARY_TIME_RULES", custom["source"])
        self.assertNotIn("ORDINARY_HOURS_LIMIT_DAILY", custom["source"])

        result = PayCalculator(
            PayRequest(
                hourly_rate=20,
                worker_type="shift",
                award="fast_food",
                employment_type="full_time",
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
        ).calculate_pay()
        self.assertEqual(result.overtime_hours, 4)


if __name__ == "__main__":
    unittest.main()
