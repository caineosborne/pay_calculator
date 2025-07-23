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
    DEFAULT_BREAK = 0.5

    # Time rules for day workers
    DAY_WORKER_ORDINARY_HOURS_DAILY = 8 # Standard 7.6 hour day
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38
    
    # Rate multipliers
    STANDARD_OVERTIME_RATE = 1.5
    SUNDAY_OVERTIME_RATE = 2.0
    SATURDAY_OVERTIME_RATE = 1.5
    SATURDAY_PENALTY_RATE = 0.25
    SUNDAY_PENALTY_RATE = 0.50
    SPAN_OVERTIME_HOUR = 18  # 6pm in 24-hour format
    
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
