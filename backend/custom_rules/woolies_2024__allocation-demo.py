"""Demonstration ruleset for the allocation-based overtime hierarchy.

The public-holiday values are intentional demo values, not award advice.
"""


class Woolies2024Rules:
    ATTENDANCE_RULES = {
        "default_break_hours": 0.5,
        "minimum_paid_shift_hours": {"day": 4, "shift": 4},
    }

    ORDINARY_TIME_RULES = {
        "windows": {
            "day": {
                "default": {"start": 7, "end": 23, "enabled": True},
                "Sunday": {"start": 9, "end": 23, "enabled": True},
            }
        },
        "daily": {"variation": "worker_type", "day": 9, "shift": 9},
        "long_day": {"uses_per_week": 1, "ordinary_limit_hours": 11},
        "period": {"variation": "worker_type", "day": 38, "shift": 38},
    }

    DAY_RULES = {
        "Saturday": {
            "day": {"base_classification": "ordinary", "ordinary_loading": 0.25, "overtime_rate_key": "saturday"},
            "shift": {"base_classification": "ordinary", "ordinary_loading": 0.50, "overtime_rate_key": "saturday"},
        },
        "Sunday": {
            "day": {"base_classification": "ordinary", "ordinary_loading": 0.50, "overtime_rate_key": "sunday"},
            "shift": {"base_classification": "ordinary", "ordinary_loading": 0.75, "overtime_rate_key": "sunday"},
        },
        "public_holiday": {
            "day": {"base_classification": "overtime", "ordinary_loading": 0, "overtime_rate_key": "public_holiday"},
            "shift": {"base_classification": "ordinary", "ordinary_loading": 1.5, "overtime_rate_key": "public_holiday"},
        },
    }

    PAY_RATES = {
        "overtime": {
            "weekday": {"multiplier": 1.5},
            "manual": {"multiplier": 1.5},
            "saturday": {"multiplier": 1.5},
            "sunday": {"multiplier": 2.0},
            "public_holiday": {"multiplier": 2.5},
            "extended": {"multiplier": 2.0},
            "two_tier": {"enabled": True, "threshold": 3, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]},
        }
    }

    BBS_RULE = {"minimum_hours": 10, "loading": 1.0}
    PENALTIES = {
        "evening_hours_6pm_to_11pm": {
            "type": "time_based", "basis": "time", "start": 18, "end": 23,
            "rate": 0.25, "description": "Evening hours loading (25%)",
            "applies_to": ["day", "shift"],
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        }
    }
    TOP_UP_RULES = {
        "use_contracted_hours_for_pt_overtime": False,
        "part_time": True,
        "full_time": True,
    }
