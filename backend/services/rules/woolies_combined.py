"""Simplified pay-calculation rules for the Woolworths 2024 EBA."""


class WooliesCombinedRules:
    """Simplified Woolworths 2024 EBA rules configuration."""

    # Simplified ordinary-hours limits for all employment types.
    ORDINARY_HOURS_LIMIT_DAILY = 9
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    DAY_WORKER_ORDINARY_HOURS_DAILY = 9
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38

    # Overtime rates.
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2.0
    SATURDAY_OVERTIME_RATE = 1.5
    SUNDAY_OVERTIME_RATE = 2.0
    TWO_TIER_OVERTIME = True
    TWO_TIER_OVERTIME_THRESHOLD = 3
    EXTENDED_OVERTIME_DAYS = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]

    # Day-worker span: overtime applies before 7:00 am and after 11:00 pm.
    APPLY_SPAN_OVERTIME = True
    SPAN_OVERTIME_START_HOUR = 7
    SPAN_OVERTIME_HOUR = 23

    # Minimum break between shifts.
    GAP_PENALTY_HOURS = 12
    GAP_PENALTY_RATE = 1.0

    # Contracted-hours treatment.
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = True
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    DEFAULT_BREAK = 0.5

    # Applies Monday to Friday; weekend loadings are configured separately.
    PENALTIES = {
        "day_worker_evening_hours_6pm_to_11pm": {
            "type": "time_based",
            "basis": "time",
            "start": 18,
            "end": 23,
            "rate": 0.25,
            "description": "Day-worker evening-hours loading (25%)",
            "applies_to": ["day"],
            "days": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
            ],
        },
    }

    # Weekend ordinary-hour loadings. Day-worker weekend hours are not OT.
    WEEKEND_RULES = {
        "day": {
            "Saturday": {"is_overtime": False, "penalty_rate": 0.25},
            "Sunday": {"is_overtime": False, "penalty_rate": 0.50},
        },
        "shift": {
            "Saturday": {"is_overtime": False, "penalty_rate": 0.50},
            "Sunday": {"is_overtime": False, "penalty_rate": 0.75},
        },
    }
