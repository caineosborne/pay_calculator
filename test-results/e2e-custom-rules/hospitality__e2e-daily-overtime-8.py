"""
Rule engine for Hospitality award pay calculations.

This module contains business rules and constants used in Hospitality award pay calculations.
"""

class HospitalityRules:
    """
    Business rules for Hospitality award pay calculations.
    """
    
    # Time rules for shift workers
    ORDINARY_HOURS_LIMIT_DAILY = 10
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    # DEFAULT_BREAK = 0.5

    # Time rules for day workers
    DAY_WORKER_ORDINARY_HOURS_DAILY = 8  # Standard 7.6 hour day
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38
    
    # Part time overtime rules
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = True  # If True, part-time employees get overtime after contracted hours
    
    # Contracted hours top-up rules
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True  # If True, part-time employees get top-up to contracted hours
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True  # If True, full-time employees get top-up to contracted hours
    
    # Rate multipliers
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2  # Used for extended overtime (keeping consistent with structure)
    SUNDAY_OVERTIME_RATE = 2
    SATURDAY_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    SATURDAY_PENALTY_RATE = 0.25
    SUNDAY_PENALTY_RATE = 0.50
    
    # Span overtime settings
    APPLY_SPAN_OVERTIME = False  # No overtime for day workers after 6pm, using hourly penalties instead
    SPAN_OVERTIME_HOUR = 18  # 6pm in 24-hour format - keeping for reference but not applied
    
    # Gap penalty rule (not used in Hospitality)
    GAP_PENALTY_HOURS = 0  # Not applicable
    GAP_PENALTY_RATE = 0  # Not applicable
    
    # Unified penalties structure
    # Type can be "shift_based" (applies to entire shift based on start time) or "time_based" (applies to specific hours)
    PENALTIES = {'evening_hours': {'type': 'time_based',
                       'basis': 'time',
                       'start': 19,
                       'end': 24,
                       'rate': 0.2,
                       'description': 'Evening Hours Penalty (20%)',
                       'applies_to': ['shift', 'day']},
     'night_hours': {'type': 'time_based',
                     'basis': 'time',
                     'start': 0,
                     'end': 7,
                     'rate': 0.5,
                     'description': 'Night Hours Penalty (50%)',
                     'applies_to': ['shift', 'day']}}
    
    # Legacy penalty structures (commented out - using unified structure instead)
    # SHIFT_PEN_RULES = {
    #     'shift': {},  # No shift penalties in Hospitality
    #     'day': {}     # No shift penalties in Hospitality
    # }
    
    # Hourly penalties based on time of day (commented out - using unified structure instead)
    # HOURS_PEN_RULES = {
    #     'evening': {'start': 19, 'end': 24, 'rate': 0.20},  # 7pm to midnight - 20% penalty
    #     'night': {'start': 0, 'end': 7, 'rate': 0.50},  # Midnight to 7am - 50% penalty
    # }
    
    # Define empty HOURS_PEN_RULES (needed for compatibility)
    HOURS_PEN_RULES = {}
    
    # Weekend rules by worker type
    # All hours are overtime
    # All hours are overtime
    # Penalty rate for non-overtime hours
    # Penalty rate for non-overtime hours
    WEEKEND_RULES = {'day': {'Saturday': {'is_overtime': True, 'rate': 1.5},
             'Sunday': {'is_overtime': True, 'rate': 2.0}},
     'shift': {'Saturday': {'penalty_rate': 0.25, 'is_overtime': False},
               'Sunday': {'penalty_rate': 0.5, 'is_overtime': False}}}
    
    # Two-tier overtime structure (not used in Hospitality)
    TWO_TIER_OVERTIME = False
    TWO_TIER_OVERTIME_THRESHOLD = 0  # Not applicable
    DEFAULT_BREAK = 0.5
    DAILY_OVERTIME_CONFIGURATION = {'variation': 'worker_type', 'day': 8, 'shift': 10}
    WEEKLY_OVERTIME_CONFIGURATION = {'variation': 'default', 'default': 38}
    SPAN_OVERTIME_START_HOUR = None
