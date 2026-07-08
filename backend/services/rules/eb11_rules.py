"""
Rule engine for Queensland Health EB11 pay calculations.
This module contains business rules and constants used in EB11 public hospital pay calculations.
"""

class EB11Rules:
    """
    Business rules for Queensland Health EB11 pay calculations.
    """

    # Time rules
    ORDINARY_HOURS_LIMIT_DAILY = 10
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    
    # Day worker time rules
    DAY_WORKER_ORDINARY_HOURS_DAILY = 8
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38

    # Part-time overtime rules
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = True
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True

    # Rate multipliers
    STANDARD_OVERTIME_RATE = 2.0  # EB11 pays all overtime at double time
    EXTENDED_OVERTIME_RATE = 2.0  # Not used but needed for compatibility
    SUNDAY_OVERTIME_RATE = 2.0
    SATURDAY_OVERTIME_RATE = 2.0
    EXTENDED_OVERTIME_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    # Span overtime settings
    APPLY_SPAN_OVERTIME = False
    SPAN_OVERTIME_HOUR = None
    
    # Continuous/Back-to-back shift rule
    BACK_TO_BACK_OVERTIME_RATE = 2.0  # All overtime paid at double time

    # Public holiday
    PUBLIC_HOLIDAY_RATE = 2.5
    CHRISTMAS_SPECIAL_RATE = 3.0  # May apply in specific cases

    # Weekend Penalties - organized by worker type and day
    # Using two-tier structure with worker type as primary key
    WEEKEND_RULES = {
        'shift': {
            'Saturday': {'penalty_rate': 0.50, 'max_hours': 10, 'excess_rate': 2.0},
            'Sunday': {'penalty_rate': 0.75, 'max_hours': 10, 'excess_rate': 2.0},
        },
        'day': {
            'Saturday': {'penalty_rate': 0.50, 'max_hours': 10, 'excess_rate': 2.0},
            'Sunday': {'penalty_rate': 0.75, 'max_hours': 10, 'excess_rate': 2.0},
        }
    }

    # Night shift penalties
    PENALTIES = {
        'night_hours': {
            'type': 'time_based',
            'start': 18,
            'end': 6,
            'rate': 0.20,
            'description': 'Night Shift Loading (20%)',
            'applies_to': ['shift', 'day']
        }
    }

    HOURS_PEN_RULES = {}

    BROKEN_SHIFT_ALLOWANCE = 2.90

    # Simplified overtime - no tier
    TWO_TIER_OVERTIME = False
    DEFAULT_OVERTIME_RATE = 2.0  # Default overtime rate used when TWO_TIER_OVERTIME is False
