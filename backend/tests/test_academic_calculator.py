"""Coverage for the generic academic activity calculator and QUT ruleset."""

import unittest
from datetime import date

from models.academic_models import AcademicPayRequest
from services.academic_calculator import AcademicPayCalculator, public_academic_ruleset


def request(*items, courses=None, lookback_items=None, start="2026-08-17"):
    return AcademicPayRequest.model_validate({
        "scheme": "qut_sessional",
        "period_start": start,
        "courses": courses or [
            {"id": "law", "code": "LLB101", "eligibility": "standard"}
        ],
        "work_items": list(items),
        "lookback_items": lookback_items or [],
    })


def tutorial(item_id, day, topic="Week 3", **updates):
    item = {
        "id": item_id,
        "kind": "activity",
        "date": day,
        "occasion_id": item_id,
        "course_id": "law",
        "topic": topic,
        "activity": "tutorial",
        "delivered_quantity": 1,
        "actual_associated_hours": 2,
    }
    item.update(updates)
    return item


class AcademicCalculatorTests(unittest.TestCase):
    def test_public_ruleset_exposes_both_payment_bases(self):
        rules = public_academic_ruleset("qut_sessional")
        self.assertEqual(rules["activities"]["tutorial"]["payment_basis"], "composite_unit")
        self.assertEqual(rules["activities"]["marking"]["payment_basis"], "direct_hour")
        self.assertEqual(rules["rate_schedules"][0]["effective_from"], "2025-12-13")

    def test_normal_then_repeat_tutorial(self):
        result = AcademicPayCalculator(request(
            tutorial("first", "2026-08-18"),
            tutorial("second", "2026-08-20", actual_associated_hours=1),
        )).calculate()
        self.assertEqual(result.line_items[0].rate_code, "CATRE")
        self.assertEqual(result.line_items[0].pay, 165.64)
        self.assertEqual(result.line_items[1].rate_code, "CATRF")
        self.assertEqual(result.line_items[1].repeat_match_id, "first")
        self.assertEqual(result.total_pay, 275.96)

    def test_tutorial_rate_multiplies_by_delivered_hours(self):
        result = AcademicPayCalculator(request(
            tutorial("long", "2026-08-18", delivered_quantity=5, actual_associated_hours=10),
        )).calculate()
        self.assertEqual(result.line_items[0].quantity, 5)
        self.assertEqual(result.line_items[0].incorporated_hours, 10)
        self.assertEqual(result.total_pay, 828.20)

    def test_repeat_exactly_seven_days_and_not_after(self):
        exact = AcademicPayCalculator(request(
            tutorial("first", "2026-08-17"),
            tutorial("second", "2026-08-24"),
        )).calculate()
        self.assertEqual(exact.line_items[1].final_classification, "repeat")

        outside = AcademicPayCalculator(request(
            tutorial("first", "2026-08-17"),
            tutorial("second", "2026-08-25"),
        )).calculate()
        self.assertEqual(outside.line_items[1].final_classification, "original")

    def test_different_topic_is_original(self):
        result = AcademicPayCalculator(request(
            tutorial("first", "2026-08-18", "Week 3"),
            tutorial("second", "2026-08-20", "Week 4"),
        )).calculate()
        self.assertEqual(result.line_items[1].final_classification, "original")

    def test_lookback_classifies_first_visible_item_as_repeat(self):
        result = AcademicPayCalculator(request(
            tutorial("visible", "2026-08-18", actual_associated_hours=1),
            lookback_items=[tutorial("prior", "2026-08-14")],
        )).calculate()
        self.assertEqual(result.line_items[0].repeat_match_id, "prior")
        self.assertEqual(result.line_items[0].rate_code, "CATRF")

    def test_phd_and_coordinator_use_higher_tutorial_rate(self):
        for eligibility in ("relevant_phd", "full_coordinator"):
            with self.subTest(eligibility=eligibility):
                result = AcademicPayCalculator(request(
                    tutorial("item", "2026-08-18"),
                    courses=[{"id": "law", "code": "LLB101", "eligibility": eligibility}],
                )).calculate()
                self.assertEqual(result.line_items[0].rate_code, "CATRG")
                self.assertEqual(result.total_pay, 198.27)

    def test_all_lecture_variants_and_repeat_rate(self):
        expected = {
            "basic": ("CALRA", 232.33),
            "developed": ("CALRB", 310.20),
            "specialised": ("CALRC", 387.97),
        }
        for variant, (rate_code, pay) in expected.items():
            with self.subTest(variant=variant):
                item = tutorial(
                    f"lecture-{variant}",
                    "2026-08-18",
                    topic=f"Topic {variant}",
                    activity="lecture",
                    variant=variant,
                )
                result = AcademicPayCalculator(request(item)).calculate()
                self.assertEqual(result.line_items[0].rate_code, rate_code)
                self.assertEqual(result.total_pay, pay)

        repeat = AcademicPayCalculator(request(
            tutorial("lecture-first", "2026-08-18", activity="lecture", variant="specialised"),
            tutorial("lecture-repeat", "2026-08-20", activity="lecture", variant="developed"),
        )).calculate()
        self.assertEqual(repeat.line_items[1].rate_code, "CALRD")

    def test_clinical_and_music_eligibility_variants(self):
        cases = [
            ("clinical_health", "normal_preparation", "standard", "CACNK"),
            ("clinical_health", "little_preparation", "standard", "CACNL"),
            ("clinical_health", "normal_preparation", "relevant_phd", "CACNM"),
            ("clinical_health", "little_preparation", "full_coordinator", "CACNN"),
            ("music_accompanying", "normal", "standard", "CAMAI"),
            ("music_accompanying", "normal", "relevant_phd", "CAMAJ"),
        ]
        for activity, variant, eligibility, rate_code in cases:
            with self.subTest(activity=activity, variant=variant, eligibility=eligibility):
                item = tutorial(
                    "item", "2026-08-18", activity=activity, variant=variant, topic=None
                )
                result = AcademicPayCalculator(request(
                    item,
                    courses=[{"id": "law", "code": "LLB101", "eligibility": eligibility}],
                )).calculate()
                self.assertEqual(result.line_items[0].rate_code, rate_code)

    def test_marking_and_other_required_activity_rates(self):
        cases = [
            ("marking", "standard", "standard", "CAMGP"),
            ("marking", "standard", "relevant_phd", "CAMGQ"),
            ("marking", "higher_level", "standard", "CAMGO"),
            ("other_academic_activity", "workshop", "standard", "CAAAR"),
            ("other_academic_activity", "meeting", "full_coordinator", "CAAAS"),
        ]
        for activity, variant, eligibility, rate_code in cases:
            with self.subTest(activity=activity, variant=variant, eligibility=eligibility):
                item = {
                    "id": "direct",
                    "kind": "direct_hours",
                    "date": "2026-08-19",
                    "occasion_id": "direct",
                    "course_id": "law",
                    "activity": activity,
                    "variant": variant,
                    "actual_hours": 2,
                    "required_or_approved": True,
                }
                result = AcademicPayCalculator(request(
                    item,
                    courses=[{"id": "law", "code": "LLB101", "eligibility": eligibility}],
                )).calculate()
                self.assertEqual(result.line_items[0].rate_code, rate_code)

    def test_same_topic_in_different_course_is_not_repeat(self):
        result = AcademicPayCalculator(request(
            tutorial("law-item", "2026-08-18"),
            tutorial("business-item", "2026-08-20", course_id="business"),
            courses=[
                {"id": "law", "code": "LLB101", "eligibility": "standard"},
                {"id": "business", "code": "BSB101", "eligibility": "standard"},
            ],
        )).calculate()
        self.assertEqual(result.line_items[1].final_classification, "original")

    def test_dates_before_first_rate_schedule_are_rejected(self):
        old_request = request(
            tutorial("old", "2025-12-12"),
            start="2025-12-08",
        )
        with self.assertRaisesRegex(ValueError, "No academic rate schedule"):
            AcademicPayCalculator(old_request).calculate()

    def test_direct_marking_and_associated_hours_warning(self):
        marking = {
            "id": "marking",
            "kind": "direct_hours",
            "date": "2026-08-19",
            "occasion_id": "marking",
            "course_id": "law",
            "activity": "marking",
            "variant": "standard",
            "actual_hours": 3.5,
            "required_or_approved": True,
        }
        result = AcademicPayCalculator(request(
            tutorial("tutorial", "2026-08-18", actual_associated_hours=3),
            marking,
        )).calculate()
        self.assertEqual(result.direct_hours_pay, 192.89)
        self.assertEqual(result.line_items[0].associated_hours_variance, 1)
        self.assertTrue(result.review_warnings)

    def test_minimum_engagement_groups_same_occasion_without_times(self):
        first = {
            "id": "meeting",
            "kind": "direct_hours",
            "date": "2026-08-19",
            "occasion_id": "campus-a",
            "activity": "other_academic_activity",
            "variant": "meeting",
            "actual_hours": 0.75,
            "required_or_approved": True,
        }
        second = {**first, "id": "consult", "variant": "consultation", "actual_hours": 0.5}
        result = AcademicPayCalculator(request(first, second)).calculate()
        self.assertEqual(len(result.occasions), 1)
        self.assertEqual(result.occasions[0].credited_hours, 1.25)
        self.assertEqual(result.occasions[0].shortfall_hours, 0.75)

    def test_weekend_does_not_change_rate(self):
        result = AcademicPayCalculator(request(
            tutorial("weekday", "2026-08-18", topic="Weekday"),
            tutorial("weekend", "2026-08-22", topic="Weekend"),
        )).calculate()
        self.assertEqual(result.line_items[0].rate, result.line_items[1].rate)

    def test_override_requires_reason_and_is_auditable(self):
        result = AcademicPayCalculator(request(
            tutorial(
                "item", "2026-08-18",
                classification_override="repeat",
                override_reason="Earlier delivery is held in university records.",
                actual_associated_hours=1,
            ),
        )).calculate()
        self.assertEqual(result.line_items[0].automatic_classification, "original")
        self.assertEqual(result.line_items[0].final_classification, "repeat")
        self.assertIn("User override", result.line_items[0].classification_reason)


if __name__ == "__main__":
    unittest.main()
