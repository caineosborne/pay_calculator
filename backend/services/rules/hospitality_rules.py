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
    DAY_WORKER_ORDINARY_HOURS_DAILY = 8 # Standard 7.6 hour day
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38
    
    # Part time overtime rules
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = True  # If True, part-time employees get overtime after contracted hours
    
    # Contracted hours top-up rules
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True  # If True, part-time employees get top-up to contracted hours
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True  # If True, full-time employees get top-up to contracted hours
    
    # Rate multipliers
    STANDARD_OVERTIME_RATE = 1.5
    SUNDAY_OVERTIME_RATE = 2.0
    SATURDAY_OVERTIME_RATE = 1.5
    SATURDAY_PENALTY_RATE = 0.25
    SUNDAY_PENALTY_RATE = 0.50
    
    # No overtime for day workers after 6pm, using hourly penalties instead
    APPLY_SPAN_OVERTIME = False
    SPAN_OVERTIME_HOUR = 18  # 6pm in 24-hour format - keeping for reference but not applied
    
    # Hourly penalties based on time of day - applies to all worker types (weekdays only, not on weekends)
    HOURS_PEN_RULES = {
        'evening': {'start': 19, 'end': 24, 'rate': 0.20},  # 7pm to midnight - 20% penalty
        'night': {'start': 0, 'end': 7, 'rate': 0.50},  # Midnight to 7am - 50% penalty
    }
    
    # Weekend rules by worker type
    WEEKEND_RULES = {
        'day': {
            'Saturday': {'is_overtime': True, 'rate': 1.5},  # All hours are overtime
            'Sunday': {'is_overtime': True, 'rate': 2.0}     # All hours are overtime
        },
        'shift': {
            'Saturday': {'penalty_rate': 0.25},  # Penalty rate for non-overtime hours
            'Sunday': {'penalty_rate': 0.50}     # Penalty rate for non-overtime hours
        }
    }
