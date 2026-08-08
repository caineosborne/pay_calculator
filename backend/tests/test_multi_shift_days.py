"""Regression tests for multiple attendance periods in one workday."""

import unittest

from models.request_models import PayRequest
from services.pay_calculator import PayCalculator


def request_for(periods, worker_type="day"):
    return PayRequest(
        hourly_rate=20,
        worker_type=worker_type,
        award="fast_food",
        employment_type="casual",
        shifts=periods,
    )


class MultiShiftDayTests(unittest.TestCase):
    def test_overnight_shift_uses_next_calendar_days_weekend_loading(self):
        result = PayCalculator(PayRequest(
            hourly_rate=20,
            worker_type="shift",
            award="fast_food",
            employment_type="full_time",
            shifts=[{"day": "Friday", "start": 22, "end": 3, "break_duration": 0}],
        )).calculate_pay()

        friday = result.daily_breakdown["Week 1 - Friday"]
        saturday_penalty = next(
            penalty for penalty in friday["hourly_penalties"]
            if penalty["description"] == "Saturday Penalty (25%)"
        )
        self.assertEqual(saturday_penalty["hours"], 3)
        self.assertEqual(saturday_penalty["rate"], 0.25)

    def test_gap_penalty_suppresses_all_other_penalties(self):
        result = PayCalculator(PayRequest(
            hourly_rate=20,
            worker_type="shift",
            award="woolies_2024_demo",
            employment_type="full_time",
            shifts=[
                {"day": "Friday", "start": 22, "end": 3, "break_duration": 0},
                {"day": "Saturday", "start": 10, "end": 18, "break_duration": 0},
            ],
        )).calculate_pay()

        saturday = result.daily_breakdown["Week 1 - Saturday"]
        self.assertEqual(saturday["gap_penalty"], 8)
        self.assertEqual(saturday["penalty"], 0)
        self.assertEqual(saturday["shift_penalty"], 0)
        self.assertEqual(saturday["hourly_penalties"], [])
        self.assertEqual(saturday["applied_rules"], ["Gap Penalty (100%)"])

    def test_daily_limit_combines_periods_and_keeps_one_daily_result(self):
        result = PayCalculator(request_for([
            {"day": "Monday", "start": 6, "end": 12, "break_duration": 0},
            {"day": "Monday", "start": 17, "end": 23, "break_duration": 0},
        ])).calculate_pay()

        self.assertEqual(result.ordinary_hours, 11)
        self.assertEqual(result.overtime_hours, 1)
        self.assertEqual(list(result.daily_breakdown), ["Week 1 - Monday"])
        self.assertEqual(result.daily_breakdown["Week 1 - Monday"]["pay"], result.total_pay)

    def test_shift_penalty_uses_combined_day_but_hourly_penalty_uses_periods(self):
        calculator = PayCalculator(request_for([
            {"day": "Monday", "start": 6, "end": 10, "break_duration": 0},
            {"day": "Monday", "start": 17, "end": 20, "break_duration": 0},
        ], worker_type="shift"))
        calculator.rules.config["penalties"] = {
            "afternoon_shift": {
                "type": "shift_based",
                "basis": "start_and_end",
                "start": 0,
                "end": 24,
                "finish_start": 18,
                "finish_end": 24,
                "rate": 0.1,
                "description": "Afternoon shift",
                "applies_to": ["shift"],
            },
            "evening_hours": {
                "type": "time_based",
                "start": 19,
                "end": 24,
                "rate": 0.2,
                "description": "Evening hours",
                "applies_to": ["shift"],
            },
        }

        result = calculator.calculate_pay()
        self.assertEqual(result.ordinary_hours, 7)
        # All seven ordinary hours receive the combined-day shift loading,
        # but only the actual 19:00-20:00 hour receives the hourly loading.
        self.assertEqual(result.penalty_pay, 18)

    def test_overnight_shift_matches_each_time_based_penalty_window(self):
        calculator = PayCalculator(PayRequest(
            hourly_rate=20,
            worker_type="shift",
            award="fast_food",
            employment_type="full_time",
            shifts=[{"day": "Monday", "start": 22, "end": 3, "break_duration": 0}],
        ))
        calculator.rules.config["penalties"] = {
            "evening": {
                "type": "time_based", "start": 19, "end": 23,
                "rate": 0.1, "description": "Evening", "applies_to": ["shift"],
            },
            "late": {
                "type": "time_based", "start": 23, "end": 24,
                "rate": 0.2, "description": "Late", "applies_to": ["shift"],
            },
            "night": {
                "type": "time_based", "start": 0, "end": 6,
                "rate": 0.3, "description": "Night", "applies_to": ["shift"],
            },
        }

        result = calculator.calculate_pay()
        penalties = result.daily_breakdown["Week 1 - Monday"]["hourly_penalties"]

        self.assertEqual(
            [(item["description"], item["hours"]) for item in penalties],
            [("Evening", 1), ("Late", 1), ("Night", 3)],
        )

    def test_overnight_calendar_day_treatments_do_not_follow_shift_start_day(self):
        def calculate(day):
            return PayCalculator(PayRequest(
                hourly_rate=20,
                worker_type="shift",
                award="fast_food",
                employment_type="full_time",
                shifts=[{"day": day, "start": 22, "end": 3, "break_duration": 0}],
            )).calculate_pay().daily_breakdown[f"Week 1 - {day}"]

        friday = calculate("Friday")
        saturday = calculate("Saturday")
        sunday = calculate("Sunday")

        self.assertEqual(friday["pay"], 119)
        self.assertCountEqual(
            friday["applied_rules"],
            ["Monday-Friday 10pm to midnight loading", "Saturday Penalty (25%)"],
        )
        self.assertEqual(saturday["pay"], 125)
        self.assertCountEqual(
            saturday["applied_rules"],
            ["Saturday Penalty (25%)", "Sunday Penalty (25%)"],
        )
        self.assertEqual(sunday["pay"], 119)
        self.assertCountEqual(
            sunday["applied_rules"],
            ["Sunday Penalty (25%)", "Monday-Friday midnight to 6am loading"],
        )

    def test_lunch_segments_do_not_each_trigger_minimum_engagement(self):
        result = PayCalculator(PayRequest(
            hourly_rate=20,
            worker_type="shift",
            award="fast_food",
            employment_type="part_time",
            shifts=[
                {
                    "day": "Monday", "start": 9, "end": 16,
                    "break_duration": 0, "minimum_engagement_exempt": True,
                },
                {
                    "day": "Monday", "start": 16.5, "end": 17,
                    "break_duration": 0, "minimum_engagement_exempt": True,
                },
            ],
        )).calculate_pay()

        monday = result.daily_breakdown["Week 1 - Monday"]
        self.assertEqual(monday["total"], 7.5)
        self.assertNotIn("Minimum paid shift (3 hours)", monday["applied_rules"])

    def test_manual_lunch_keeps_calendar_day_loadings_for_each_worked_period(self):
        def calculate(day):
            return PayCalculator(PayRequest(
                hourly_rate=20,
                worker_type="shift",
                award="fast_food",
                employment_type="full_time",
                shifts=[
                    {
                        "day": day, "start": 22, "end": 23,
                        "break_duration": 0, "minimum_engagement_exempt": True,
                    },
                    {
                        "day": day, "start": 23.5, "end": 3,
                        "break_duration": 0, "minimum_engagement_exempt": True,
                    },
                ],
            )).calculate_pay().daily_breakdown[f"Week 1 - {day}"]

        friday = calculate("Friday")
        saturday = calculate("Saturday")
        sunday = calculate("Sunday")

        self.assertEqual(friday["pay"], 108)
        self.assertCountEqual(
            friday["applied_rules"],
            ["Monday-Friday 10pm to midnight loading", "Saturday Penalty (25%)"],
        )
        self.assertEqual(saturday["pay"], 112.5)
        self.assertCountEqual(
            saturday["applied_rules"],
            ["Saturday Penalty (25%)", "Sunday Penalty (25%)"],
        )
        self.assertEqual(sunday["pay"], 106.5)
        self.assertCountEqual(
            sunday["applied_rules"],
            ["Sunday Penalty (25%)", "Monday-Friday midnight to 6am loading"],
        )

    def test_same_day_weekend_periods_keep_one_weekend_loading(self):
        result = PayCalculator(PayRequest(
            hourly_rate=20,
            worker_type="shift",
            award="fast_food",
            employment_type="full_time",
            shifts=[
                {"day": "Saturday", "start": 9, "end": 12, "break_duration": 0},
                {"day": "Saturday", "start": 13, "end": 17, "break_duration": 0},
            ],
        )).calculate_pay()

        saturday = result.daily_breakdown["Week 1 - Saturday"]
        self.assertEqual(saturday["pay"], 175)
        self.assertEqual(saturday["applied_rules"], ["Saturday Penalty (25%)"])

    def test_overlapping_periods_are_rejected(self):
        calculator = PayCalculator(request_for([
            {"day": "Monday", "start": 9, "end": 14, "break_duration": 0},
            {"day": "Monday", "start": 13, "end": 17, "break_duration": 0},
        ]))

        with self.assertRaisesRegex(ValueError, "Overlapping shifts"):
            calculator.calculate_pay()
