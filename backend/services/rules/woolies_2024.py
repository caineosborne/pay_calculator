"""
Rule engine for Woolworths ward pay calculations.

This module contains business rules and constants used in Aged Care award pay calculations.
"""

class Woolies2024Rules:
    """
    Business rules for Woolworths pay calculations.
    """

    ORDINARY_HOURS_LIMIT_DAILY = 9 #employees can work 11 horus one day - not configured
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    DAY_WORKER_ORDINARY_HOURS_DAILY = 9
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38

    DAILY_OVERTIME_CONFIGURATION = {
          "variation": "default",
          "default": 9,
      }

    WEEKLY_OVERTIME_CONFIGURATION = {
          "variation": "employment_type",
          "full_time": 76,
          "part_time": 38,
          "casual": 38,
          "basis": {
              "full_time": "pay_period",
              "part_time": "weekly",
              "casual": "weekly",
          },
          "max_work_days": 10,
          "max_work_days_basis": "pay_period",
      }

    # Part time overtime rules
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = False  # Emmployees can work additional hours 

    # Contracted hours top-up rules
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True  # If True, part-time employees get top-up to contracted hours
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True  # If True, full-time employees get top-up to contracted hours

    # Rate multipliers
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2.0  # Monday–Friday overtime after the first two hours
    SUNDAY_OVERTIME_RATE = 2.0  # Increased to 2x for Sunday
    SATURDAY_OVERTIME_RATE = 1.5 # Saturday covered by the standard extended OT reules. 
    EXTENDED_OVERTIME_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday']

    # Double pay after 3 hours. 
    TWO_TIER_OVERTIME = True
    TWO_TIER_OVERTIME_THRESHOLD = 3  # Not applicable


    # Span overtime settings
    APPLY_SPAN_OVERTIME = True  
    SPAN_OVERTIME_START_HOUR = 7  # Span overtime morning cut-off (7am)
    SPAN_OVERTIME_HOUR = 23  # Span overtime evening cut-off (11pm)

    # Gap penalty rule -
    GAP_PENALTY_HOURS = 10  # Minimum hours required between shifts to avoid gap penalty - 10 by agreement
    GAP_PENALTY_RATE = 1.0  # 100% penalty rate when shifts are too close together


    PENALTIES = {
      "evening_hours_6pm_to_11pm": {
          "type": "time_based",
          "basis": "time",
          "start": 18,
          "end": 23,
          "rate": 0.25,
          "description": "Evening hours loading (25%)",
          "applies_to": ["day", "shift"],
          "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      },
  }


    # Weekend rules by worker type
    WEEKEND_RULES = {
        'day': {
            'Saturday': {'is_overtime': False, 'penalty_rate': 0.25},  # All hours are overtime at 2.5x
            'Sunday': {'is_overtime': False, 'penalty_rate': 0.5}     # All hours are overtime at 2.5x
        },
        'shift': {
            'Saturday': {'penalty_rate': 0.5},  # Penalty rate for non-overtime hours
            'Sunday': {'penalty_rate': 0.75}     # Penalty rate for non-overtime hours
        }
    }
