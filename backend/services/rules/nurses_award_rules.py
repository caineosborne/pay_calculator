"""
Rule engine for Nurses Award pay calculations.
This module contains business rules and constants used in Nurses Award pay calculations.
"""

class NursesAwardRules:
    """
    Business rules for Nurses & Midwives Award (QLD) 2015 pay calculations.
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
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2.0  # After 3 hours of overtime
    SUNDAY_OVERTIME_RATE = 2.0
    PUBLIC_HOLIDAY_OVERTIME_RATE = 2.5
    SATURDAY_OVERTIME_RATE = 1.5  # Overtime on Saturday (needed for rule engine)

    # Penalty Rates for Ordinary Hours
    SATURDAY_PENALTY_RATE = 0.50  # Time + 50%
    SUNDAY_PENALTY_RATE = 0.75    # Time + 75%
    NIGHT_SHIFT_PENALTY = 0.20    # Time + 20%
    
    # Span overtime settings
    APPLY_SPAN_OVERTIME = False
    SPAN_OVERTIME_HOUR = None

    # Overtime threshold by shift length
    OVERTIME_TIERS = {
        'standard': {
            'first_n_hours': 3,
            'first_rate': 1.5,
            'subsequent_rate': 2.0
        }
    }

    # Weekend rules - organized by worker type and day
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

    # Night shift hours (penalty applies)
    PENALTIES = {
        'night_hours': {
            'type': 'time_based',
            'start': 18,   # 6pm
            'end': 6,      # 6am
            'rate': 0.20,
            'description': 'Night Shift Loading (20%)',
            'applies_to': ['shift', 'day']
        }
    }

    HOURS_PEN_RULES = {}

    # Broken shift allowance
    BROKEN_SHIFT_ALLOWANCE = 2.90

    # Two-tier overtime applies
    TWO_TIER_OVERTIME = True
    TWO_TIER_OVERTIME_THRESHOLD = 3  # First 3 hours at 1.5x, then 2.0x
    
    # Added for consistency with other rule classes
    DEFAULT_OVERTIME_RATE = None  # Not used when TWO_TIER_OVERTIME is True
