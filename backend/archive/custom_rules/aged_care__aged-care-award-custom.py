"""
Rule engine for Aged Care award pay calculations.

This module contains business rules and constants used in Aged Care award pay calculations.
"""

class AgedCareRules:
    """
    Business rules for Aged Care award pay calculations.
    """

    # Time rules for shift workers
    ORDINARY_HOURS_LIMIT_DAILY = 10  # Increased to 12 hours per day
    ORDINARY_HOURS_LIMIT_WEEKLY = 38  # Increased to 40 hours per week
    # DEFAULT_BREAK = 1

    # Time rules for day workers
    DAY_WORKER_ORDINARY_HOURS_DAILY = 8
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38  # Increased to 40 hours per week

    # Part time overtime rules
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = False  # If True, part-time employees get overtime after contracted hours

    # Contracted hours top-up rules
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = False  # If True, part-time employees get top-up to contracted hours
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True  # If True, full-time employees get top-up to contracted hours

    # Rate multipliers
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2  # Used for extended overtime (keeping consistent with structure)
    SUNDAY_OVERTIME_RATE = 2.5  # Increased to 2.5x for weekends
    SATURDAY_OVERTIME_RATE = 2.5  # Increased to 2.5x for weekends
    EXTENDED_OVERTIME_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    SATURDAY_PENALTY_RATE = 0.25
    SUNDAY_PENALTY_RATE = 0.50

    # Span overtime settings
    APPLY_SPAN_OVERTIME = True  # Using span overtime for Aged Care
    SPAN_OVERTIME_HOUR = 18  # 6pm in 24-hour format    SPAN_OVERTIME_START_HOUR = 6

    # Gap penalty rule - specific to Aged Care award
    GAP_PENALTY_HOURS = 10  # Minimum hours required between shifts to avoid gap penalty
    GAP_PENALTY_RATE = 1  # 100% penalty rate when shifts are too close together

    # Unified penalties structure
    # Type can be "shift_based" (applies to entire shift based on start time) or "time_based" (applies to specific hours)
    # 10am
    # 1pm
    # 10% penalty
    # Only applies to shift workers
    # 1pm
    # 4pm
    # 12.5% penalty
    # Only applies to shift workers
    # 4pm
    # Midnight
    # 15% penalty
    # Only applies to shift workers
    PENALTIES = {'time_based_loading_1': {'type': 'time_based',
                              'basis': 'time',
                              'start': 14,
                              'end': 16,
                              'rate': 0.1,
                              'description': 'time_based_loading_1',
                              'applies_to': ['day', 'shift']}}


    # Hourly penalties based on time of day (not used in Aged Care)
    HOURS_PEN_RULES = {}

    # Weekend rules by worker type
    # All hours are overtime at 2.5x
    # All hours are overtime at 2.5x
    # Penalty rate for non-overtime hours
    # Penalty rate for non-overtime hours
    WEEKEND_RULES = {'day': {'Saturday': {'is_overtime': True, 'rate': 1.5},
             'Sunday': {'is_overtime': True, 'rate': 2}},
     'shift': {'Saturday': {'penalty_rate': 0.25, 'is_overtime': False},
               'Sunday': {'penalty_rate': 0.5, 'is_overtime': False}}}

    # Two-tier overtime structure (not used in Aged Care)
    TWO_TIER_OVERTIME = True
    TWO_TIER_OVERTIME_THRESHOLD = 2  # Not applicable
    DEFAULT_BREAK = 0.5
    DAILY_OVERTIME_CONFIGURATION = {'variation': 'default', 'default': 10}
    WEEKLY_OVERTIME_CONFIGURATION = {'variation': 'default', 'default': 38}

    SPAN_OVERTIME_START_HOUR = 6
