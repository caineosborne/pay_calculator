"""Ensure every live built-in supplies the canonical grouped contract."""

import unittest

from services.rule_engine import PayRules
from services.rules.rule_factory import BUILTIN_RULES


class CanonicalRulesetCoverageTests(unittest.TestCase):
    def test_only_launch_rulesets_are_registered(self):
        self.assertEqual(
            set(BUILTIN_RULES),
            {"fast_food", "coles_2024", "gria_2026", "woolies_2024_demo"},
        )

    def test_every_builtin_contains_every_canonical_group(self):
        for award in BUILTIN_RULES:
            with self.subTest(award=award):
                config = PayRules(award).config
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
