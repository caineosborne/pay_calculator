"""
Rule engine for pay calculations.

This module contains the pay calculation rules interface that adapts to
different awards. It uses the rule factory to get the appropriate rule set
based on the specified award.

Dependencies:
- rules module for award-specific rule sets
"""

from .rules import get_rules_for_award

class PayRules:
    """
    Adapter class for award-specific calculation rules.
    
    This class dynamically adapts to the selected award by using
    the appropriate rule set from the rules module.
    """
    
    # Default award if none is specified
    _DEFAULT_AWARD = 'hospitality'
    
    # Class variable to store the active rules
    _active_rules = None
    
    @classmethod
    def set_award(cls, award: str = None):
        """
        Set the active award rules.
        
        Args:
            award: String identifier for the award ('aged_care' or 'hospitality')
        """
        award = award or cls._DEFAULT_AWARD
        cls._active_rules = get_rules_for_award(award)
    
    @classmethod
    def get_active_rules(cls):
        """Get the currently active rule set."""
        if cls._active_rules is None:
            cls.set_award(cls._DEFAULT_AWARD)
        return cls._active_rules
    
    @classmethod
    def is_overtime_day(cls, day: str, worker_type: str) -> bool:
        """Determine if all hours on this day are automatically overtime."""
        rules = cls.get_active_rules()
        if worker_type == 'day' and day in ['Saturday', 'Sunday']:
            return True
        return False

    @classmethod
    def get_overtime_rate(cls, day: str) -> float:
        """Get the overtime multiplier for a given day."""
        rules = cls.get_active_rules()
        if day == 'Sunday':
            return rules.SUNDAY_OVERTIME_RATE
        elif day == 'Saturday':
            return rules.SATURDAY_OVERTIME_RATE
        return rules.STANDARD_OVERTIME_RATE

    @classmethod
    def get_penalty_rate(cls, day: str, worker_type: str) -> float:
        """Get the penalty rate for non-overtime hours on weekends for shift workers."""
        rules = cls.get_active_rules()
        if worker_type != 'shift' or day not in ['Saturday', 'Sunday']:
            return 0
        weekend_rules = rules.WEEKEND_RULES.get('shift', {}).get(day, {})
        return weekend_rules.get('penalty_rate', 0)

    @classmethod
    def calculate_span_overtime(cls, start_time: float, end_time: float, daily_hours: float, worker_type: str) -> float:
        """Calculate overtime hours for work done after 6pm (day workers only)."""
        rules = cls.get_active_rules()
        if worker_type != 'day':
            return 0
            
        if end_time <= rules.SPAN_OVERTIME_HOUR:
            return 0
            
        overtime_start = max(start_time, rules.SPAN_OVERTIME_HOUR)
        return min(end_time - overtime_start, daily_hours)

    @classmethod
    def get_ordinary_hours_daily_limit(cls, worker_type: str) -> float:
        """Get daily ordinary hours limit based on worker type."""
        rules = cls.get_active_rules()
        return rules.DAY_WORKER_ORDINARY_HOURS_DAILY if worker_type == 'day' else rules.ORDINARY_HOURS_LIMIT_DAILY

    @classmethod
    def calculate_weekly_ordinary_hours(cls, hours: float, worker_type: str = 'shift') -> float:
        """Calculate ordinary hours for the week."""
        rules = cls.get_active_rules()
        weekly_limit = rules.DAY_WORKER_ORDINARY_HOURS_WEEKLY if worker_type == 'day' else rules.ORDINARY_HOURS_LIMIT_WEEKLY
        return min(hours, weekly_limit)

    @classmethod
    def get_weekend_rate(cls, day: str, worker_type: str = 'shift') -> dict:
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
        rules = cls.get_active_rules()
        
        if day not in ['Saturday', 'Sunday']:
            return {'is_overtime': False, 'penalty_rate': 0, 'rate': cls.get_overtime_rate(day)}
            
        weekend_rules = rules.WEEKEND_RULES.get(worker_type, {}).get(day, {})
        
        # For shift workers, we want both penalty rates and overtime rates
        if worker_type == 'shift':
            return {
                'is_overtime': weekend_rules.get('is_overtime', False),
                'rate': cls.get_overtime_rate(day),  # Always use overtime rate for overtime hours
                'penalty_rate': weekend_rules.get('penalty_rate', 0)
            }
        
        # For day workers, use the weekend-specific rates
        return {
            'is_overtime': weekend_rules.get('is_overtime', False),
            'rate': weekend_rules.get('rate', cls.get_overtime_rate(day)),
            'penalty_rate': weekend_rules.get('penalty_rate', 0)
        }