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
    get_rule_configuration,
    load_custom_rule_class,
)


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
