"""
Rule engine for Child Care award pay calculations.

This module contains business rules and constants used in Child Care award pay calculations.
"""

class ChildCareRules:
    """
    Business rules for Child Care award pay calculations.
    """
    
    # Time rules for shift workers
    ORDINARY_HOURS_LIMIT_DAILY = 10  # 10 hours for Full Time
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    # DEFAULT_BREAK = 0.5
    
    # Time rules for day workers
    DAY_WORKER_ORDINARY_HOURS_DAILY = 8  # 8 hours for Part Time
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38
    
    # Part time overtime rules
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = False  # OT is paid when all employees exceed 38 (including part time)
    
    # Contracted hours top-up rules
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True  # Contracted topups are in effect for all employees
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True  # Contracted topups are in effect for all employees
    
    # Rate multipliers
    STANDARD_OVERTIME_RATE = 1.5  # Overtime is 1.5x for the first 2 hours
    EXTENDED_OVERTIME_RATE = 2.0  # 2x after 2 hours
    SUNDAY_OVERTIME_RATE = 2.0
    SATURDAY_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    SATURDAY_PENALTY_RATE = 0.25
    SUNDAY_PENALTY_RATE = 0.50
    
    # Span overtime settings
    APPLY_SPAN_OVERTIME = False  # Not using span overtime for Child Care award
    SPAN_OVERTIME_HOUR = 18  # 6pm in 24-hour format - keeping for reference but not applied
    
    # Gap penalty rule
    GAP_PENALTY_HOURS = 12  # Minimum hours required between shifts to avoid gap penalty
    GAP_PENALTY_RATE = 1.0  # 100% penalty rate when shifts are too close together (insufficient gap penalty)
    
    # Unified penalties structure
    # Type can be "shift_based" (applies to entire shift based on start time) or "time_based" (applies to specific hours)
    PENALTIES = {
        'afternoon_shift': {
            'type': 'shift_based',
            'start': 13,  # 1pm
            'end': 24,    # Midnight
            'rate': 0.10, # 10% penalty
            'description': 'Afternoon Shift Penalty (10%)',
            'applies_to': ['shift', 'day']  # Applies to both shift and day workers
        }
    }
    
    # Legacy penalty structures (commented out - using unified structure instead)
    # SHIFT_PEN_RULES = {
    #     'shift': {
    #         'afternoon': {'start': 13, 'end': 24, 'rate': 0.10},  # Afternoon penalties for shifts starting after 1pm at 10%
    #     },
    #     'day': {
    #         'afternoon': {'start': 13, 'end': 24, 'rate': 0.10},  # Afternoon penalties for shifts starting after 1pm at 10%
    #     }
    # }
    
    # Define empty HOURS_PEN_RULES (needed for compatibility)
    HOURS_PEN_RULES = {}
    
    # Weekend rules by worker type
    WEEKEND_RULES = {
        'day': {
            'Saturday': {'is_overtime': True, 'rate': 1.5},  # OT is paid for weekend
            'Sunday': {'is_overtime': True, 'rate': 2.0}     # OT is paid for weekend
        },
        'shift': {
            'Saturday': {'is_overtime': True, 'rate': 1.5},  # OT is paid for weekend
            'Sunday': {'is_overtime': True, 'rate': 2.0}     # OT is paid for weekend
        }
    }
    
    # Two-tier overtime structure - Child Care specific
    # First 2 hours at 1.5x, then 2.0x after that
    TWO_TIER_OVERTIME = True
    TWO_TIER_OVERTIME_THRESHOLD = 2  # Hours before switching to higher rate
