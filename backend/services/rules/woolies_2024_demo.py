"""Demonstration ruleset for the allocation-based overtime hierarchy.

The public-holiday values are intentional demo values, not award advice.
"""


class Woolies2024Rules:
    SHIFT_RULES = {
        "default_break_hours": 0.5,
        "minimum_paid_shift_hours": {
            "variation": "employment_type",
            "full_time": 4,
            "part_time": 4,
            "casual": 4,
        },
    }

    ORDINARY_TIME_RULES = {
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
            "full_time": 38,
            "part_time": 38,
            "casual": 38,
            "part_time_uses_contracted_hours": False,
        },
    }

    DAY_TREATMENT_RULES = {
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

    GAP_BETWEEN_SHIFTS_RULE = {"minimum_hours": 10, "loading": 1.0}
    ORDINARY_HOUR_PENALTIES = {
        "evening_hours_6pm_to_11pm": {
            "type": "time_based", "basis": "time", "start": 18, "end": 23,
            "rate": 0.25, "description": "Evening hours loading (25%)",
            "applies_to": ["day", "shift"],
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        }
    }
    TOP_UP_RULES = {
        "part_time": True,
        "full_time": True,
    }

    # Compatibility aliases for the current guided source editor. Runtime
    # calculation reads the grouped contract above; these can disappear when
    # the editor is migrated to author the grouped fields directly.
    ORDINARY_HOURS_LIMIT_DAILY = 9
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    DAY_WORKER_ORDINARY_HOURS_DAILY = 9
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2.0
    SATURDAY_OVERTIME_RATE = 1.5
    SUNDAY_OVERTIME_RATE = 2.0
    TWO_TIER_OVERTIME = True
    TWO_TIER_OVERTIME_THRESHOLD = 3
    EXTENDED_OVERTIME_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    APPLY_SPAN_OVERTIME = True
    SPAN_OVERTIME_START_HOUR = 7
    SPAN_OVERTIME_HOUR = 23
    GAP_PENALTY_HOURS = 10
    GAP_PENALTY_RATE = 1.0
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = False
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    DEFAULT_BREAK = 0.5
    WEEKEND_RULES = {
        "day": {"Saturday": {"is_overtime": False, "penalty_rate": 0.25}, "Sunday": {"is_overtime": False, "penalty_rate": 0.5}},
        "shift": {"Saturday": {"is_overtime": False, "penalty_rate": 0.5}, "Sunday": {"is_overtime": False, "penalty_rate": 0.75}},
    }
    PENALTIES = {
        "evening_hours_6pm_to_11pm": {
            "type": "time_based", "basis": "time", "start": 18, "end": 23,
            "rate": 0.25, "description": "Evening hours loading (25%)",
            "applies_to": ["day", "shift"],
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        }
    }
