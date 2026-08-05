"""Ensure every registered built-in supplies a complete canonical projection."""

import unittest

from services.rule_schema import canonical_rules
from services.rules.rule_factory import BUILTIN_RULES


class CanonicalRulesetCoverageTests(unittest.TestCase):
    def test_every_builtin_contains_every_canonical_group(self):
        for award, rule_class in BUILTIN_RULES.items():
            with self.subTest(award=award):
                config = canonical_rules(rule_class)
                self.assertIn("default_break_hours", config["shift"])
                self.assertIn("span_overtime", config["ordinary_time"])
                self.assertIn("daily", config["ordinary_time"])
                self.assertIn("period", config["ordinary_time"])
                self.assertIn("part_time_uses_contracted_hours", config["ordinary_time"]["period"])
                self.assertIn("weekday", config["pay_rates"]["overtime"])
                for day in ("Saturday", "Sunday"):
                    for worker in ("day", "shift"):
                        self.assertIn("base_classification", config["day_treatment"][day][worker])
                        self.assertIn("overtime_rate_key", config["day_treatment"][day][worker])
                self.assertIsInstance(config["gap_between_shifts"], dict)
                self.assertIsInstance(config["penalties"], dict)
                self.assertIn("part_time", config["top_up"])
                self.assertIn("full_time", config["top_up"])
