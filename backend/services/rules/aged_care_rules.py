"""
Rule engine for Aged Care award pay calculations.

This module contains business rules and constants used in Aged Care award pay calculations.
"""

class AgedCareRules:
    """
    Business rules for Aged Care award pay calculations.
    """
    
    # Time rules for shift workers
    ORDINARY_HOURS_LIMIT_DAILY = 12  # Increased to 12 hours per day
    ORDINARY_HOURS_LIMIT_WEEKLY = 40  # Increased to 40 hours per week
    DEFAULT_BREAK = 0.5

    # Time rules for day workers
    DAY_WORKER_ORDINARY_HOURS_DAILY = 8 
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 40  # Increased to 40 hours per week
    
    # Rate multipliers
    STANDARD_OVERTIME_RATE = 1.5
    SUNDAY_OVERTIME_RATE = 2.5  # Increased to 2.5x for weekends
    SATURDAY_OVERTIME_RATE = 2.5  # Increased to 2.5x for weekends
    SATURDAY_PENALTY_RATE = 0.25
    SUNDAY_PENALTY_RATE = 0.50
    SPAN_OVERTIME_HOUR = 18  # 6pm in 24-hour format
    
    # Gap penalty rule - specific to Aged Care award
    GAP_PENALTY_HOURS = 10  # Minimum hours required between shifts to avoid gap penalty
    GAP_PENALTY_RATE = 1.0  # 100% penalty rate when shifts are too close together
    
    # Shift penalties based on start time - specific to Aged Care shift workers
    SHIFT_PEN_RULES = {
        'shift': {
            'first_window': {'start': 10, 'end': 13, 'rate': 0.10},  # 10am to 1pm - 10% penalty
            'second_window': {'start': 13, 'end': 16, 'rate': 0.125},  # 1pm to 4pm - 12.5% penalty
            'third_window': {'start': 16, 'end': 24, 'rate': 0.15},  # After 4pm - 15% penalty
        },
        'day': {}  # Day workers don't receive shift penalties
    }
    
    # Weekend rules by worker type
    WEEKEND_RULES = {
        'day': {
            'Saturday': {'is_overtime': True, 'rate': 2.5},  # All hours are overtime at 2.5x
            'Sunday': {'is_overtime': True, 'rate': 2.5}     # All hours are overtime at 2.5x
        },
        'shift': {
            'Saturday': {'penalty_rate': 0.25},  # Penalty rate for non-overtime hours
            'Sunday': {'penalty_rate': 0.50}     # Penalty rate for non-overtime hours
        }
    }
