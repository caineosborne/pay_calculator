"""Business rules for Aged Care award pay calculations."""


class AgedCareRules:
    """Business rules for the Aged Care award."""

    # Ordinary-hours limits
    ORDINARY_HOURS_LIMIT_DAILY = 10
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    DEFAULT_BREAK = 1

    # Day-worker ordinary-hours limits
    DAY_WORKER_ORDINARY_HOURS_DAILY = 8
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38

    # Part-time overtime and contracted-hours top-up
    USE_CONTRACTED_HOURS_FOR_PT_OVERTIME = False
    PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True
    FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP = True

    # Overtime rates
    STANDARD_OVERTIME_RATE = 1.5
    EXTENDED_OVERTIME_RATE = 2.0
    SUNDAY_OVERTIME_RATE = 2.0
    SATURDAY_OVERTIME_RATE = 2.0
    EXTENDED_OVERTIME_DAYS = [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
    ]

    # Weekend penalty loadings for shift workers
    SATURDAY_PENALTY_RATE = 0.25
    SUNDAY_PENALTY_RATE = 0.50

    # Span overtime
    APPLY_SPAN_OVERTIME = True
    SPAN_OVERTIME_HOUR = 18

    # Minimum gap between consecutive shifts
    GAP_PENALTY_HOURS = 10
    GAP_PENALTY_RATE = 1.0

    # Shift-start penalties for shift workers
    PENALTIES = {
        'afternoon_shift_10': {
            'type': 'shift_based',
            'basis': 'start',
            'start': 10,
            'end': 13,
            'rate': 0.10,
            'description': 'Morning Shift Penalty (10%)',
            'applies_to': ['shift'],
        },
        'afternoon_shift': {
            'type': 'shift_based',
            'basis': 'start',
            'start': 13,
            'end': 16,
            'rate': 0.125,
            'description': 'Afternoon Shift Penalty (12.5%)',
            'applies_to': ['shift'],
        },
        'evening_shift': {
            'type': 'shift_based',
            'basis': 'start',
            'start': 16,
            'end': 24,
            'rate': 0.15,
            'description': 'Evening Shift Penalty (15%)',
            'applies_to': ['shift'],
        },
        'evening_shift_cont': {
            'type': 'shift_based',
            'basis': 'start',
            'start': 24,
            'end': 4,
            'rate': 0.15,
            'description': 'Overnight Shift Penalty (15%)',
            'applies_to': ['shift'],
        },
        'evening_shift_am': {
            'type': 'shift_based',
            'basis': 'start',
            'start': 4,
            'end': 6,
            'rate': 0.1,
            'description': 'Early Morning Shift Penalty (10%)',
            'applies_to': ['shift'],
        },
    }

    # Weekend rules by worker type
    WEEKEND_RULES = {
        'day': {
            'Saturday': {'is_overtime': True, 'rate': 2.0},
            'Sunday': {'is_overtime': True, 'rate': 2.0},
        },
        'shift': {
            'Saturday': {
                'is_overtime': False,
                'rate': None,
                'penalty_rate': 0.25,
            },
            'Sunday': {
                'is_overtime': False,
                'rate': None,
                'penalty_rate': 0.50,
            },
        },
    }

    # Aged Care does not use two-tier overtime.
    TWO_TIER_OVERTIME = False
    TWO_TIER_OVERTIME_THRESHOLD = 0
