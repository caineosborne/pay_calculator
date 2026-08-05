"""Acceptance tests for the canonical allocation demo ruleset."""

import unittest

from models.request_models import PayRequest
from services.pay_calculator import PayCalculator


DEMO = "custom:woolies_2024:allocation-demo"


def calculate(*shifts, worker_type="day", public_holidays=()):
    return PayCalculator(PayRequest(
        hourly_rate=20,
        award="woolies_2024",
        rule_configuration=DEMO,
        worker_type=worker_type,
        employment_type="full_time",
        public_holidays=list(public_holidays),
        shifts=list(shifts),
    )).calculate_pay()


class OvertimeAllocationDemoTests(unittest.TestCase):
    def test_span_break_is_deducted_from_ordinary_before_overtime(self):
        request = PayRequest(
            hourly_rate=20, award="woolies_2024", rule_configuration=DEMO,
            worker_type="day", employment_type="full_time", shifts=[
                {"day": "Monday", "start": 14, "end": 20, "break_duration": .5}
            ],
        )
        calculator = PayCalculator(request)
        calculator.rules.config["attendance"]["minimum_paid_shift_hours"] = {}
        calculator.rules.config["ordinary_time"]["windows"]["day"]["default"]["end"] = 18
        self.assertEqual(calculator.calculate_pay().overtime_hours, 2)

        calculator = PayCalculator(PayRequest(
            hourly_rate=20, award="woolies_2024", rule_configuration=DEMO,
            worker_type="day", employment_type="full_time", shifts=[
                {"day": "Monday", "start": 18, "end": 22, "break_duration": .5}
            ],
        ))
        calculator.rules.config["attendance"]["minimum_paid_shift_hours"] = {}
        calculator.rules.config["ordinary_time"]["windows"]["day"]["default"]["end"] = 18
        self.assertEqual(calculator.calculate_pay().overtime_hours, 3.5)

    def test_first_long_day_in_each_week_uses_eleven_hour_limit(self):
        result = calculate(
            {"week": 1, "day": "Monday", "start": 8, "end": 18, "break_duration": 0},
            {"week": 1, "day": "Tuesday", "start": 8, "end": 20, "break_duration": 0},
        )
        self.assertEqual(result.ordinary_hours, 19)
        self.assertEqual(result.overtime_hours, 3)

    def test_minimum_shift_and_manual_overtime(self):
        result = calculate({"day": "Monday", "start": 9, "end": 10, "break_duration": 0, "manual_overtime": True})
        self.assertEqual(result.total_hours, 4)
        self.assertEqual(result.overtime_hours, 4)

    def test_public_holiday_profiles_replace_normal_penalties(self):
        result = calculate(
            {"day": "Monday", "start": 9, "end": 13, "break_duration": 0},
            public_holidays=[{"week": 1, "day": "Monday"}],
        )
        self.assertEqual(result.overtime_hours, 4)
        self.assertEqual(result.overtime_pay, 200)

        result = calculate(
            {"day": "Monday", "start": 9, "end": 13, "break_duration": 0},
            worker_type="shift",
            public_holidays=[{"week": 1, "day": "Monday"}],
        )
        self.assertEqual(result.ordinary_hours, 4)
        self.assertEqual(result.penalty_pay, 120)

    def test_period_overtime_removes_sunday_ordinary_loading(self):
        calculator = PayCalculator(PayRequest(
            hourly_rate=20, award="woolies_2024", rule_configuration=DEMO,
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


if __name__ == "__main__":
    unittest.main()
