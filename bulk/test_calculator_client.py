import unittest

from calculator_client import BulkImportError, create_requests, parse_csv, parse_emd_csv


class BulkCalculatorClientTests(unittest.TestCase):
    def test_groups_monday_cycle_into_a_single_fortnight(self):
        shifts = parse_csv(
            b"employee,shift_date,start_time,end_time\nAlex,2026-07-06,09:00,17:00\nAlex,2026-07-19,09:00,17:00\n"
        )
        jobs = create_requests(shifts, {"Alex": {
            "pay_cycle_start_day": "Monday", "hourly_rate": 30, "award": "fast_food",
            "worker_type": "shift", "employment_type": "full_time",
        }})
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["period_start"].isoformat(), "2026-07-06")
        self.assertEqual(jobs[0]["payload"]["shifts"][1]["week"], 2)

    def test_non_monday_cycle_moves_pre_cycle_days_into_week_two(self):
        shifts = parse_csv(b"shift_date,start_time,end_time\n2026-07-08,09:00,17:00\n2026-07-13,09:00,17:00\n")
        jobs = create_requests(shifts, {"Employee": {
            "pay_cycle_start_day": "Wednesday", "hourly_rate": 30, "award": "coles_2024",
            "worker_type": "shift", "employment_type": "full_time",
        }})
        payload_shifts = jobs[0]["payload"]["shifts"]
        self.assertEqual([item["week"] for item in payload_shifts], [1, 2])
        self.assertEqual([item["day"] for item in payload_shifts], ["Wednesday", "Monday"])

    def test_uses_each_employees_own_profile(self):
        shifts = parse_csv(
            b"employee,shift_date,start_time,end_time\nAlex,2026-07-06,09:00,17:00\nJordan,2026-07-06,09:00,17:00\n"
        )
        profiles = {
            "Alex": {"pay_cycle_start_day": "Monday", "hourly_rate": 30, "award": "fast_food", "worker_type": "shift", "employment_type": "full_time"},
            "Jordan": {"pay_cycle_start_day": "Monday", "hourly_rate": 45, "award": "gria_2026", "worker_type": "day", "employment_type": "casual"},
        }
        jobs = create_requests(shifts, profiles)
        self.assertEqual(jobs[0]["payload"]["hourly_rate"], 30)
        self.assertEqual(jobs[1]["payload"]["hourly_rate"], 45)
        self.assertEqual(jobs[1]["payload"]["award"], "gria_2026")

    def test_parses_strict_emd_contract(self):
        emd = parse_emd_csv(b"employee,hourly_rate,award,worker_type,employment_type,contracted_hours,pay_cycle_start_day,pay_cycle_anchor,rule_configuration\nAlex,30,fast_food,shift,full_time,38,Monday,2026-07-06,\n")
        self.assertEqual(emd["Alex"]["hourly_rate"], 30)

    def test_rejects_reordered_emd_headers(self):
        with self.assertRaises(BulkImportError):
            parse_emd_csv(b"hourly_rate,employee\n30,Alex\n")


if __name__ == "__main__":
    unittest.main()
