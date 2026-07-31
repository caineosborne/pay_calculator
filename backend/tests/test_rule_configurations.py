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


if __name__ == "__main__":
    unittest.main()
