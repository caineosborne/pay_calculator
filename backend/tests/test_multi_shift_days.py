"""Regression tests for multiple attendance periods in one workday."""

import unittest

from models.request_models import PayRequest
from services.pay_calculator import PayCalculator


def request_for(periods, worker_type="day"):
    return PayRequest(
        hourly_rate=20,
        worker_type=worker_type,
        award="hospitality",
        employment_type="casual",
        shifts=periods,
    )


class MultiShiftDayTests(unittest.TestCase):
    def test_daily_limit_combines_periods_and_keeps_one_daily_result(self):
        result = PayCalculator(request_for([
            {"day": "Monday", "start": 6, "end": 12, "break_duration": 0},
            {"day": "Monday", "start": 17, "end": 23, "break_duration": 0},
        ])).calculate_pay()

        self.assertEqual(result.ordinary_hours, 8)
        self.assertEqual(result.overtime_hours, 4)
        self.assertEqual(list(result.daily_breakdown), ["Week 1 - Monday"])

    def test_shift_penalty_uses_combined_day_but_hourly_penalty_uses_periods(self):
        calculator = PayCalculator(request_for([
            {"day": "Monday", "start": 6, "end": 10, "break_duration": 0},
            {"day": "Monday", "start": 17, "end": 20, "break_duration": 0},
        ], worker_type="shift"))
        calculator.rules.active_rules.PENALTIES = {
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

    def test_overlapping_periods_are_rejected(self):
        calculator = PayCalculator(request_for([
            {"day": "Monday", "start": 9, "end": 14, "break_duration": 0},
            {"day": "Monday", "start": 13, "end": 17, "break_duration": 0},
        ]))

        with self.assertRaisesRegex(ValueError, "Overlapping shifts"):
            calculator.calculate_pay()

