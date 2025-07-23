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

    @classmethod
    def check_shift_gap_penalty(cls, current_shift_start: float, previous_shift_end: float, 
                               current_day: str = None, previous_day: str = None) -> dict:
        """
        Check if a gap penalty should be applied between two shifts.
        This rule only applies to the Aged Care award.
        
        Args:
            current_shift_start: Start time of the current shift (in hours)
            previous_shift_end: End time of the previous shift (in hours)
            current_day: Day of the week for the current shift
            previous_day: Day of the week for the previous shift
            
        Returns:
            dict with keys:
            - applies (bool): Whether the gap penalty applies
            - penalty_rate (float): The penalty rate to apply
        """
        rules = cls.get_active_rules()
        
        # Only Aged Care award has gap penalty rule
        if not hasattr(rules, 'GAP_PENALTY_HOURS'):
            return {'applies': False, 'penalty_rate': 0}
        
        # Define the order of days in a week
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # If days are different, calculate the hours between shifts properly
        if current_day and previous_day and current_day != previous_day:
            # Get indices of days in the week
            current_day_idx = days_order.index(current_day)
            previous_day_idx = days_order.index(previous_day)
            
            # Calculate days difference (considering circular week)
            days_diff = (current_day_idx - previous_day_idx) % 7
            if days_diff == 0:  # Full week difference (same day but a week later)
                days_diff = 7
                
            # Calculate the total hours between shifts
            if days_diff == 1:  # Consecutive days
                # For consecutive days: Add the remaining hours of previous day and the hours until current shift
                hours_between_shifts = (24 - previous_shift_end) + current_shift_start
            else:
                # For non-consecutive days: Add hours for all complete days in between plus partial days
                hours_between_shifts = (24 - previous_shift_end) + current_shift_start + ((days_diff - 1) * 24)
        else:
            # If no day information or same day, use direct calculation
            if current_shift_start >= previous_shift_end:
                # Shifts on the same day
                hours_between_shifts = current_shift_start - previous_shift_end
            else:
                # Second shift wraps to next day
                hours_between_shifts = (24 - previous_shift_end) + current_shift_start
        
        # Check if the gap penalty applies (shifts less than the required minimum hours apart)
        if hours_between_shifts < rules.GAP_PENALTY_HOURS:
            return {
                'applies': True,
                'penalty_rate': rules.GAP_PENALTY_RATE
            }
        
        return {'applies': False, 'penalty_rate': 0}