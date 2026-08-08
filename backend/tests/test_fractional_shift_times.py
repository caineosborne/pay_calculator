import unittest

from models.request_models import PayRequest, Shift
from services.pay_calculator import PayCalculator


class FractionalShiftTimeTests(unittest.TestCase):
    def test_quarter_hour_times_are_preserved_in_calculations(self):
        request = PayRequest(
            hourly_rate=20,
            award="fast_food",
            worker_type="shift",
            employment_type="full_time",
            shifts=[Shift(day="Monday", start=9.25, end=17.75, break_duration=0.5)],
        )

        result = PayCalculator(request).calculate_pay()

        self.assertEqual(result.total_hours, 8)
        self.assertEqual(result.ordinary_hours, 8)
        self.assertEqual(result.total_pay, 160)


if __name__ == "__main__":
    unittest.main()
