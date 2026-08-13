"""Acceptance tests for the canonical allocation demo ruleset."""

import unittest

from models.request_models import PayRequest
from services.pay_calculator import PayCalculator


DEMO = "woolies_2024_demo"


def calculate(*shifts, worker_type="day", employment_type="full_time", public_holidays=()):
    return PayCalculator(PayRequest(
        hourly_rate=20,
        award=DEMO,
        worker_type=worker_type,
        employment_type=employment_type,
        public_holidays=list(public_holidays),
        shifts=list(shifts),
    )).calculate_pay()


class OvertimeAllocationDemoTests(unittest.TestCase):
    def test_span_break_is_deducted_from_ordinary_before_overtime(self):
        request = PayRequest(
            hourly_rate=20, award=DEMO,
            worker_type="day", employment_type="full_time", shifts=[
                {"day": "Monday", "start": 14, "end": 20, "break_duration": .5}
            ],
        )
        calculator = PayCalculator(request)
        calculator.rules.config["shift"]["minimum_paid_shift_hours"] = {}
        calculator.rules.config["ordinary_time"]["span_overtime"]["day"]["default"]["end"] = 18
        self.assertEqual(calculator.calculate_pay().overtime_hours, 2)

        calculator = PayCalculator(PayRequest(
            hourly_rate=20, award=DEMO,
            worker_type="day", employment_type="full_time", shifts=[
                {"day": "Monday", "start": 18, "end": 22, "break_duration": .5}
            ],
        ))
        calculator.rules.config["shift"]["minimum_paid_shift_hours"] = {}
        calculator.rules.config["ordinary_time"]["span_overtime"]["day"]["default"]["end"] = 18
        self.assertEqual(calculator.calculate_pay().overtime_hours, 3.5)

    def test_first_long_day_in_each_week_uses_eleven_hour_limit(self):
        result = calculate(
            {"week": 1, "day": "Monday", "start": 8, "end": 18, "break_duration": 0},
            {"week": 1, "day": "Tuesday", "start": 8, "end": 20, "break_duration": 0},
        )
        self.assertEqual(result.ordinary_hours, 19)
        self.assertEqual(result.overtime_hours, 3)

    def test_daily_and_minimum_shift_rules_can_vary_by_employment_type(self):
        calculator = PayCalculator(PayRequest(
            hourly_rate=20, award=DEMO, worker_type="day",
            employment_type="part_time", shifts=[
                {"day": "Monday", "start": 9, "end": 16, "break_duration": 0},
            ],
        ))
        calculator.rules.config["ordinary_time"]["daily"]["part_time"] = 6
        calculator.rules.config["ordinary_time"]["long_day"]["uses_per_week"] = 0
        result = calculator.calculate_pay()
        self.assertEqual(result.ordinary_hours, 6)
        self.assertEqual(result.overtime_hours, 1)

    def test_minimum_shift_and_manual_overtime(self):
        result = calculate({"day": "Monday", "start": 9, "end": 10, "break_duration": 0, "manual_overtime": True})
        self.assertEqual(result.total_hours, 4)
        self.assertEqual(result.overtime_hours, 4)
        self.assertEqual(result.overtime_pay, 130)  # first 3 hours at 1.5x, then 2x

    def test_manual_overtime_uses_sunday_rate(self):
        result = calculate(
            {"day": "Sunday", "start": 9, "end": 13, "break_duration": 0, "manual_overtime": True},
        )
        self.assertEqual(result.overtime_hours, 4)
        self.assertEqual(result.overtime_pay, 160)  # 4 hours at Sunday 2x

    def test_manual_overtime_uses_public_holiday_rate(self):
        result = calculate(
            {"day": "Monday", "start": 9, "end": 13, "break_duration": 0, "manual_overtime": True},
            public_holidays=[{"week": 1, "day": "Monday"}],
        )
        self.assertEqual(result.overtime_hours, 4)
        self.assertEqual(result.overtime_pay, 200)  # 4 hours at public holiday 2.5x

    def test_shiftworker_weekday_loading_is_time_based_for_all_hours(self):
        result = calculate(
            {"day": "Monday", "start": 9, "end": 17, "break_duration": 0},
            worker_type="shift",
        )
        self.assertEqual(result.ordinary_hours, 8)
        self.assertEqual(result.hourly_penalty_pay, 48)  # 8 hours at 30% loading

    def test_two_tier_overtime_applies_to_configured_saturday(self):
        calculator = PayCalculator(PayRequest(
            hourly_rate=20, award=DEMO, worker_type="day",
            employment_type="full_time", shifts=[
                {"day": "Saturday", "start": 9, "end": 15, "break_duration": 0},
            ],
        ))
        calculator.rules.config["day_treatment"]["Saturday"]["day"][
            "base_classification"
        ] = "overtime"
        result = calculator.calculate_pay()
        self.assertEqual(result.overtime_hours, 6)
        self.assertEqual(result.overtime_pay, 210)  # 3 hours at 1.5x, then 3 at 2x

    def test_manual_ordinary_bypasses_overtime_but_keeps_weekend_penalty(self):
        result = calculate(
            {"day": "Sunday", "start": 9, "end": 13, "break_duration": 0, "manual_ordinary": True},
        )
        self.assertEqual(result.ordinary_hours, 4)
        self.assertEqual(result.overtime_hours, 0)
        self.assertEqual(result.penalty_pay, 40)
        self.assertIn("Manual Ordinary", result.daily_breakdown["Week 1 - Sunday"]["applied_rules"])

    def test_casual_sunday_daily_overtime_uses_sunday_rate(self):
        result = calculate(
            {"day": "Sunday", "start": 7, "end": 21, "break_duration": 1},
            worker_type="shift", employment_type="casual",
        )
        self.assertEqual(result.ordinary_hours, 11)
        self.assertEqual(result.overtime_hours, 2)
        self.assertEqual(result.overtime_pay, 90)  # 2 hours at Sunday casual 2.25x ($20 base)

    def test_public_holiday_profiles_replace_normal_penalties(self):
        result = calculate(
            {"day": "Monday", "start": 9, "end": 13, "break_duration": 0},
            public_holidays=[{"week": 1, "day": "Monday"}],
        )
        self.assertEqual(result.ordinary_hours, 4)
        self.assertEqual(result.penalty_pay, 100)

    def test_public_holiday_can_apply_to_one_segment_of_a_split_day(self):
        result = calculate(
            {"day": "Monday", "start": 9, "end": 13, "break_duration": 0, "public_holiday": True},
            {"day": "Monday", "start": 13, "end": 17, "break_duration": 0, "public_holiday": False},
        )
        self.assertEqual(result.ordinary_hours, 8)
        self.assertEqual(result.overtime_hours, 0)
        self.assertEqual(result.hourly_penalty_pay, 100)

        result = calculate(
            {"day": "Monday", "start": 9, "end": 13, "break_duration": 0},
            worker_type="shift",
            public_holidays=[{"week": 1, "day": "Monday"}],
        )
        self.assertEqual(result.ordinary_hours, 4)
        self.assertEqual(result.penalty_pay, 100)

    def test_period_overtime_removes_sunday_ordinary_loading(self):
        calculator = PayCalculator(PayRequest(
            hourly_rate=20, award=DEMO,
            worker_type="day", employment_type="full_time", shifts=[
                {"day": "Sunday", "start": 9, "end": 13, "break_duration": 0},
            ],
        ))
        calculator.rules.config["ordinary_time"]["period"] = {
            "variation": "default", "default": 0,
        }
        result = calculator.calculate_pay()
        self.assertEqual(result.overtime_hours, 4)
        self.assertEqual(result.penalty_pay, 0)

    def test_weekly_period_limit_does_not_average_hours_across_weeks(self):
        calculator = PayCalculator(PayRequest(
            hourly_rate=20, award=DEMO, worker_type="day", employment_type="full_time",
            shifts=[
                {"week": 1, "day": "Monday", "start": 8, "end": 18, "break_duration": 0},
                {"week": 2, "day": "Monday", "start": 8, "end": 14, "break_duration": 0},
            ],
        ))
        calculator.rules.config["ordinary_time"]["period"] = {
            "variation": "default", "default": 8, "basis": "weekly",
        }
        result = calculator.calculate_pay()
        self.assertEqual(result.overtime_hours, 2)

    def test_pay_period_limit_and_max_work_days_convert_later_days_to_overtime(self):
        calculator = PayCalculator(PayRequest(
            hourly_rate=20, award=DEMO, worker_type="day", employment_type="full_time",
            shifts=[
                {"week": 1, "day": day, "start": 9, "end": 13, "break_duration": 0}
                for day in ("Monday", "Tuesday", "Wednesday")
            ],
        ))
        calculator.rules.config["ordinary_time"]["period"] = {
            "variation": "default", "default": 12, "basis": "pay_period", "max_work_days": 2,
        }
        result = calculator.calculate_pay()
        self.assertEqual(result.overtime_hours, 4)
        self.assertIn("Maximum day overtime", result.daily_breakdown["Week 1 - Wednesday"]["applied_rules"])

    def test_demo_period_overtime_varies_by_employment_type(self):
        shifts = [
            {"week": 1, "day": day, "start": 8, "end": 16, "break_duration": 0}
            for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
        ]
        self.assertEqual(calculate(*shifts, employment_type="full_time").overtime_hours, 0)
        self.assertEqual(calculate(*shifts, employment_type="part_time").overtime_hours, 2)
        self.assertEqual(calculate(*shifts, employment_type="casual").overtime_hours, 2)

    def test_demo_has_ten_day_fortnight_cap(self):
        shifts = [
            {"week": week, "day": day, "start": 9, "end": 13, "break_duration": 0}
            for week, days in ((1, ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")),
                               (2, ("Monday", "Tuesday", "Wednesday", "Thursday")))
            for day in days
        ]
        result = calculate(*shifts)
        self.assertEqual(result.overtime_hours, 4)
        self.assertIn("Maximum day overtime", result.daily_breakdown["Week 2 - Thursday"]["applied_rules"])

    def test_casual_values_are_explicit_for_ordinary_penalty_and_overtime(self):
        ordinary = calculate(
            {"day": "Monday", "start": 9, "end": 13, "break_duration": 0},
            employment_type="casual",
        )
        self.assertEqual(ordinary.ordinary_pay, 100)  # 4 hours at 1.25x

        penalty = calculate(
            {"day": "Saturday", "start": 9, "end": 13, "break_duration": 0},
            worker_type="shift", employment_type="casual",
        )
        self.assertEqual(penalty.ordinary_pay, 80)
        self.assertEqual(penalty.penalty_pay, 60)  # 4 hours at the 0.75 loading

        overtime = calculate(
            {"day": "Monday", "start": 9, "end": 13, "break_duration": 0, "manual_overtime": True},
            employment_type="casual",
        )
        self.assertEqual(overtime.overtime_pay, 150)  # 3 hours at 1.75x, then 1 at 2.25x


if __name__ == "__main__":
    unittest.main()
