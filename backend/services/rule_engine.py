"""
Rule engine for pay calculations.

This module contains all business rules and constants used in pay calculations.
It provides a central location for managing calculation rules, making it easier
to modify business logic without changing the calculation code.

Dependencies:
- None (pure business logic)
"""

class PayRules:
    """
    Centralized business rules for pay calculations.
    
    This class contains all constants and methods related to pay calculation rules.
    All values are maintained here to ensure consistency across the application.
    """
    
    # Time rules for shift workers
    ORDINARY_HOURS_LIMIT_DAILY = 10
    ORDINARY_HOURS_LIMIT_WEEKLY = 38
    DEFAULT_BREAK = 0.5

    # Time rules for day workers
    DAY_WORKER_ORDINARY_HOURS_DAILY = 10  # Standard 7.6 hour day
    DAY_WORKER_ORDINARY_HOURS_WEEKLY = 38  # Same weekly limit
    DEFAULT_BREAK = 0.5

    # Rate multipliers
    OVERTIME_RATE = 1.5
    SATURDAY_PENALTY_RATE = 0.25
    SUNDAY_PENALTY_RATE = 0.50
    SPAN_OVERTIME_HOUR = 18  # 6pm in 24-hour format
    
    # Weekend rules by worker type
    WEEKEND_RULES = {
        'day': {
            'Saturday': {'is_overtime': True, 'rate': 1.5},  # Overtime on Saturday
            'Sunday': {'is_overtime': True, 'rate': 2.0}     # Double time on Sunday
        },
        'shift': {
            'Saturday': {'is_overtime': False, 'penalty_rate': 0.25},  # Penalty rate
            'Sunday': {'is_overtime': False, 'penalty_rate': 0.50}     # Penalty rate
        }
    }

    @staticmethod
    def calculate_span_overtime(start_time: float, end_time: float, daily_hours: float, worker_type: str) -> float:
        """Calculate overtime hours for work done after 6pm (day workers only)."""
        if worker_type != 'day':
            return 0
            
        if end_time <= PayRules.SPAN_OVERTIME_HOUR:
            return 0
            
        overtime_start = max(start_time, PayRules.SPAN_OVERTIME_HOUR)
        return min(end_time - overtime_start, daily_hours)

    @staticmethod
    def get_ordinary_hours_daily_limit(worker_type: str) -> float:
        """Get daily ordinary hours limit based on worker type."""
        return PayRules.DAY_WORKER_ORDINARY_HOURS_DAILY if worker_type == 'day' else PayRules.ORDINARY_HOURS_LIMIT_DAILY

    @staticmethod
    def calculate_weekly_ordinary_hours(hours: float, worker_type: str = 'shift') -> float:
        """Calculate ordinary hours for the week."""
        weekly_limit = PayRules.DAY_WORKER_ORDINARY_HOURS_WEEKLY if worker_type == 'day' else PayRules.ORDINARY_HOURS_LIMIT_WEEKLY
        return min(hours, weekly_limit)

    @staticmethod
    def get_weekend_rate(day: str, worker_type: str = 'shift') -> dict:
        """
        Get weekend work rules based on worker type.
        For shift workers: returns penalty rates
        For day workers: indicates overtime status and rate
        
        Returns:
            dict with keys:
            - is_overtime (bool): whether the hours count as overtime
            - rate (float): overtime rate if is_overtime is True
            - penalty_rate (float): penalty rate if is_overtime is False
        """
        if day not in ['Saturday', 'Sunday']:
            return {'is_overtime': False, 'penalty_rate': 0, 'rate': 0}
            
        rules = PayRules.WEEKEND_RULES.get(worker_type, {}).get(day, {})
        return {
            'is_overtime': rules.get('is_overtime', False),
            'rate': rules.get('rate', 0),
            'penalty_rate': rules.get('penalty_rate', 0)
        }