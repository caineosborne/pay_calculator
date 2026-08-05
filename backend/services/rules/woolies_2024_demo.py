"""Demonstration ruleset for the allocation-based overtime hierarchy.

The public-holiday values are intentional demo values, not award advice.
"""


class Woolies2024Rules:
    CANONICAL_RULESET = True

    SHIFT_RULES = {
        "default_break_hours": 0.5,
        "minimum_paid_shift_hours": {
            "variation": "employment_type",
            "full_time": 4,
            "part_time": 2,
            "casual": 2,
        },
    }

    ORDINARY_TIME_RULES = {
        # Additional loading for ordinary hours that do not receive another
        # ordinary-hours loading.  This is deliberately a loading, not a
        # total multiplier: 1.00 base + 0.25 casual loading = 1.25x.
        "ordinary_rates": {"casual_loading": 0.25},
        "span_overtime": {
            "day": {
                "default": {"start": 7, "end": 23, "enabled": True},
                "Sunday": {"start": 9, "end": 23, "enabled": True},
            }
        },
        "daily": {
            "variation": "employment_type",
            "full_time": 9,
            "part_time": 9,
            "casual": 9,
        },
        "long_day": {"uses_per_week": 1, "ordinary_limit_hours": 11},
        "period": {
            "variation": "employment_type",
            "full_time": 76,
            "part_time": 38,
            "casual": 38,
            "basis": {
                "full_time": "pay_period",
                "part_time": "weekly",
                "casual": "weekly",
            },
            "max_work_days": 10,
            "max_work_days_basis": "pay_period",
            "part_time_uses_contracted_hours": False,
        },
    }

    DAY_TREATMENT_RULES = {
        "Saturday": {
            "day": {"base_classification": "overtime", "ordinary_loading": 0.25, "casual_rate": 0.40, "overtime_rate_key": "saturday"},
            "shift": {"base_classification": "ordinary", "ordinary_loading": 0.50, "casual_rate": 0.65, "overtime_rate_key": "saturday"},
        },
        "Sunday": {
            "day": {"base_classification": "ordinary", "ordinary_loading": 0.50, "casual_rate": 0.65, "overtime_rate_key": "sunday"},
            "shift": {"base_classification": "ordinary", "ordinary_loading": 0.75, "casual_rate": 0.90, "overtime_rate_key": "sunday"},
        },
        "public_holiday": {
            "day": {"base_classification": "overtime", "ordinary_loading": 0, "overtime_rate_key": "public_holiday"},
            "shift": {"base_classification": "ordinary", "ordinary_loading": 1.5, "casual_rate": 1.5, "overtime_rate_key": "public_holiday"},
        },
    }

    PAY_RATES = {
        "overtime": {
            "weekday": {"multiplier": 1.5, "casual": 1.875},
            "manual": {"multiplier": 1.5, "casual": 1.875},
            "saturday": {"multiplier": 1.5, "casual": 1.875},
            "sunday": {"multiplier": 2, "casual": 2.25},
            "public_holiday": {"multiplier": 2.5, "casual": 3.5},
            "extended": {"multiplier": 2.0, "casual": 2.25},
            "two_tier": {"enabled": True, "threshold": 3, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]},
        }
    }

    GAP_BETWEEN_SHIFTS_RULE = {"minimum_hours": 10, "loading": 1.0, "casual_rate": 1.0}
    ORDINARY_HOUR_PENALTIES = {
        "evening_hours_6pm_to_11pm": {
            "type": "time_based", "basis": "time", "start": 18, "end": 23,
            "rate": 0.25, "casual_rate": 0.40,
            "description": "Evening hours loading (25%)",
            "applies_to": ["day", "shift"],
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        }
    }
    TOP_UP_RULES = {
        "part_time": False,
        "full_time": False,
    }
