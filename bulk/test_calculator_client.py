import unittest

from calculator_client import create_requests, parse_csv


class BulkCalculatorClientTests(unittest.TestCase):
    def test_groups_monday_cycle_into_a_single_fortnight(self):
        shifts = parse_csv(
            b"employee,shift_date,start_time,end_time\nAlex,2026-07-06,09:00,17:00\nAlex,2026-07-19,09:00,17:00\n"
        )
        jobs = create_requests(shifts, {
            "pay_cycle_start_day": "Monday", "hourly_rate": 30, "award": "hospitality",
            "worker_type": "shift", "employment_type": "full_time",
        })
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["period_start"].isoformat(), "2026-07-06")
        self.assertEqual(jobs[0]["payload"]["shifts"][1]["week"], 2)

    def test_non_monday_cycle_moves_pre_cycle_days_into_week_two(self):
        shifts = parse_csv(b"shift_date,start_time,end_time\n2026-07-08,09:00,17:00\n2026-07-13,09:00,17:00\n")
        jobs = create_requests(shifts, {
            "pay_cycle_start_day": "Wednesday", "hourly_rate": 30, "award": "hospitality",
            "worker_type": "shift", "employment_type": "full_time",
        })
        payload_shifts = jobs[0]["payload"]["shifts"]
        self.assertEqual([item["week"] for item in payload_shifts], [1, 2])
        self.assertEqual([item["day"] for item in payload_shifts], ["Wednesday", "Monday"])


if __name__ == "__main__":
    unittest.main()
