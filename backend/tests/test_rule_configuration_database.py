"""PostgreSQL persistence tests for custom ruleset overrides."""

from __future__ import annotations

import copy
import os
import uuid
import unittest

from services.rule_configuration_store import DatabaseUnavailable
from services.rule_configuration_store import delete_configuration, get_configuration
from services.rule_configurations import (
    create_custom_rule,
    delete_custom_rule,
    get_rule_configuration,
    load_custom_rule_class,
    rename_custom_rule,
    RuleConfigurationNotFound,
)
from models.request_models import PayRequest
from services.pay_calculator import PayCalculator


def _database_is_available() -> bool:
    try:
        from services.rule_configuration_store import initialize_store

        initialize_store()
        return True
    except DatabaseUnavailable:
        return False


@unittest.skipUnless(_database_is_available(), "PostgreSQL is not running")
class RuleConfigurationDatabaseTests(unittest.TestCase):
    def test_database_stores_only_the_changed_rule_values(self):
        builtin = get_rule_configuration("builtin:fast_food")
        questionnaire = copy.deepcopy(builtin["questionnaire"])
        questionnaire["overtime"]["daily_overtime_configuration"]["answer"] = {
            "variation": "default",
            "default": 7,
        }
        name = f"Database patch {uuid.uuid4().hex[:8]}"
        custom = create_custom_rule(
            "fast_food", name, builtin["source"], questionnaire
        )

        identifier = uuid.UUID(custom["id"].removeprefix("custom:"))
        try:
            stored = get_configuration(identifier)
            self.assertEqual(
                stored["rules_json"],
                {"ORDINARY_TIME_RULES": {"daily": {"variation": "default", "default": 7}}},
            )
            loaded_class = load_custom_rule_class(custom["id"], "fast_food")
            self.assertEqual(loaded_class.ORDINARY_TIME_RULES["daily"]["default"], 7)
            self.assertEqual(loaded_class.PAY_RATES["overtime"]["weekday"]["multiplier"], 1.5)

            reloaded = get_rule_configuration(custom["id"])
            self.assertEqual(
                reloaded["questionnaire"]["overtime"]["daily_overtime_configuration"]["answer"]["default"],
                7,
            )
        finally:
            delete_configuration(identifier)

    def test_saved_override_affects_calculation_and_can_be_renamed_or_deleted(self):
        builtin = get_rule_configuration("builtin:fast_food")
        questionnaire = copy.deepcopy(builtin["questionnaire"])
        questionnaire["overtime"]["daily_overtime_configuration"]["answer"] = {
            "variation": "default",
            "default": 9,
        }
        custom = create_custom_rule(
            "fast_food", f"Nine hour OT {uuid.uuid4().hex[:8]}", builtin["source"], questionnaire
        )
        try:
            result = PayCalculator(
                PayRequest(
                    hourly_rate=20,
                    worker_type="day",
                    award="fast_food",
                    employment_type="full_time",
                    rule_configuration=custom["id"],
                    shifts=[{
                        "day": "Monday",
                        "start": 9,
                        "end": 19.75,
                        "break_duration": 0.5,
                    }],
                )
            ).calculate_pay()
            self.assertEqual(result.overtime_hours, 1.25)

            renamed = rename_custom_rule(custom["id"], "Nine Hour Daily Overtime")
            self.assertEqual(renamed["name"], "Nine Hour Daily Overtime")
            delete_custom_rule(custom["id"])
            with self.assertRaises(RuleConfigurationNotFound):
                get_rule_configuration(custom["id"])
        finally:
            delete_configuration(uuid.UUID(custom["id"].removeprefix("custom:")))

    def test_long_day_rule_is_editable_and_persisted_as_an_override(self):
        builtin = get_rule_configuration("builtin:gria_2026")
        questionnaire = copy.deepcopy(builtin["questionnaire"])
        self.assertTrue(questionnaire["long_day"]["enabled"]["answer"])
        self.assertEqual(
            questionnaire["long_day"]["ordinary_limit_hours"]["answer"], 11
        )
        questionnaire["long_day"]["ordinary_limit_hours"]["answer"] = 10
        custom = create_custom_rule(
            "gria_2026", f"Ten hour long day {uuid.uuid4().hex[:8]}",
            builtin["source"], questionnaire,
        )
        try:
            loaded_class = load_custom_rule_class(custom["id"], "gria_2026")
            self.assertEqual(
                loaded_class.ORDINARY_TIME_RULES["long_day"]["ordinary_limit_hours"],
                10,
            )
            stored = get_configuration(uuid.UUID(custom["id"].removeprefix("custom:")))
            self.assertEqual(
                stored["rules_json"]["ORDINARY_TIME_RULES"]["long_day"],
                {"ordinary_limit_hours": 10},
            )
        finally:
            delete_configuration(uuid.UUID(custom["id"].removeprefix("custom:")))
