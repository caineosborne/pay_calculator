"""Canonical custom-rule configuration regression tests."""

from __future__ import annotations

import copy
import unittest
import uuid

from models.request_models import PayRequest
from services.pay_calculator import PayCalculator
from services.award_registry import public_awards, public_disclaimers
from services.rule_configurations import (
    RuleConfigurationError,
    create_custom_rule,
    get_rule_configuration,
    list_rule_configurations,
    validate_rule_source,
)
from services.rule_configuration_store import DatabaseUnavailable, initialize_store
from services.rule_configuration_store import delete_configuration


def _database_is_available() -> bool:
    try:
        initialize_store()
        return True
    except DatabaseUnavailable:
        return False


@unittest.skipUnless(_database_is_available(), "PostgreSQL is not running")
class RuleConfigurationTests(unittest.TestCase):
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

    def test_public_disclaimers_use_the_four_part_structure_for_every_instrument(self):
        disclaimers = public_disclaimers()

        self.assertEqual(disclaimers["generic"]["title"], "Important disclaimer")
        self.assertIn(
            "fairwork.gov.au",
            " ".join(disclaimers["generic"]["paragraphs"]),
        )
        self.assertEqual(
            disclaimers["awards"]["fast_food"]["title"],
            "Scope and assumptions",
        )
        for award in (
            "fast_food",
            "coles_2024",
            "gria_2026",
            "woolies_2024_demo",
        ):
            self.assertGreater(len(disclaimers["awards"][award]["paragraphs"]), 0)
            self.assertGreater(len(disclaimers["awards"][award]["assumptions"]), 0)
            self.assertGreater(len(disclaimers["awards"][award]["limitations"]), 0)
            exclusions = disclaimers["awards"][award].get("exclusions", [])
            exclusion_groups = disclaimers["awards"][award].get(
                "exclusion_groups", []
            )
            self.assertTrue(exclusions or exclusion_groups)
            for group in exclusion_groups:
                self.assertTrue(group["title"])
                self.assertGreater(len(group["items"]), 0)

        for award in ("coles_2024", "gria_2026", "woolies_2024_demo"):
            award_text = " ".join(
                disclaimers["awards"][award]["paragraphs"]
                + disclaimers["awards"][award]["assumptions"]
            ).lower()
            self.assertIn("shiftworker", award_text)

        for award in ("coles_2024", "gria_2026"):
            award_text = " ".join(
                disclaimers["awards"][award]["assumptions"]
            ).lower()
            self.assertIn("non-shiftwork", award_text)

        woolies_text = " ".join(
            disclaimers["awards"]["woolies_2024_demo"]["assumptions"]
        ).lower()
        self.assertIn("rostered solely for shiftwork", woolies_text)

    def test_retail_shiftworker_weekday_loading_applies_to_daytime_shifts(self):
        for award in ("coles_2024", "gria_2026"):
            with self.subTest(award=award):
                result = PayCalculator(
                    PayRequest(
                        hourly_rate=20,
                        worker_type="shift",
                        award=award,
                        employment_type="full_time",
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
                self.assertEqual(result.ordinary_hours, 8)
                self.assertEqual(result.hourly_penalty_pay, 48)

    def test_retail_overnight_shiftworker_loading_switches_at_saturday_midnight(self):
        for award in ("coles_2024", "gria_2026"):
            with self.subTest(award=award):
                result = PayCalculator(
                    PayRequest(
                        hourly_rate=20,
                        worker_type="shift",
                        award=award,
                        employment_type="full_time",
                        shifts=[
                            {
                                "day": "Friday",
                                "start": 20,
                                "end": 2,
                                "break_duration": 0,
                            }
                        ],
                    )
                ).calculate_pay()
                # Friday 20:00-midnight at +30%, Saturday midnight-02:00
                # at +50%; the calendar segments must not overlap.
                self.assertEqual(result.hourly_penalty_pay, 44)
                self.assertEqual(result.time_based_penalty_hours, 6)

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
            "fast_food",
            f"Four Hour Day {uuid.uuid4().hex[:8]}",
            builtin["source"],
            questionnaire,
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
        delete_configuration(uuid.UUID(custom["id"].removeprefix("custom:")))


if __name__ == "__main__":
    unittest.main()
