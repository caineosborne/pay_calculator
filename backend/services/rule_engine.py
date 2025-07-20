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
    STANDARD_OVERTIME_RATE = 1.5
    SUNDAY_OVERTIME_RATE = 2.0
    SATURDAY_PENALTY_RATE = 0.25
    SUNDAY_PENALTY_RATE = 0.50
    SPAN_OVERTIME_HOUR = 18  # 6pm in 24-hour format
    
    # Weekend rules by worker type
    WEEKEND_RULES = {
        'day': {
            'Saturday': {'is_overtime': True},  # All hours are overtime
            'Sunday': {'is_overtime': True}     # All hours are overtime
        },
        'shift': {
            'Saturday': {'penalty_rate': 0.25},  # Penalty rate for non-overtime hours
            'Sunday': {'penalty_rate': 0.50}     # Penalty rate for non-overtime hours
        }
    }
    
    @staticmethod
    def is_overtime_day(day: str, worker_type: str) -> bool:
        """Determine if all hours on this day are automatically overtime."""
        if worker_type == 'day' and day in ['Saturday', 'Sunday']:
            return True
        return False

    @staticmethod
    def get_overtime_rate(day: str) -> float:
        """Get the overtime multiplier for a given day."""
        return PayRules.SUNDAY_OVERTIME_RATE if day == 'Sunday' else PayRules.STANDARD_OVERTIME_RATE

    @staticmethod
    def get_penalty_rate(day: str, worker_type: str) -> float:
        """Get the penalty rate for non-overtime hours on weekends for shift workers."""
        if worker_type != 'shift' or day not in ['Saturday', 'Sunday']:
            return 0
        rules = PayRules.WEEKEND_RULES.get('shift', {}).get(day, {})
        return rules.get('penalty_rate', 0)

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
            return {'is_overtime': False, 'penalty_rate': 0, 'rate': PayRules.OVERTIME_RATE}
            
        rules = PayRules.WEEKEND_RULES.get(worker_type, {}).get(day, {})
        
        # For shift workers, we want both penalty rates and overtime rates
        if worker_type == 'shift':
            return {
                'is_overtime': rules.get('is_overtime', False),
                'rate': PayRules.OVERTIME_RATE,  # Always use overtime rate for overtime hours
                'penalty_rate': rules.get('penalty_rate', 0)
            }
        
        # For day workers, use the weekend-specific rates
        return {
            'is_overtime': rules.get('is_overtime', False),
            'rate': rules.get('rate', PayRules.OVERTIME_RATE),
            'penalty_rate': rules.get('penalty_rate', 0)
        }