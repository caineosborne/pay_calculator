"""
Rule engine for pay calculations.

This module contains the pay calculation rules interface that adapts to
different awards. It uses the rule factory to get the appropriate rule set
based on the specified award.

The rule engine implements methods in the following logical order:
1. Basic award settings (ordinary hours limits, worker types)
2. Span overtime (work beyond span of hours)
3. Daily overtime (work beyond daily hours limit)
4. Weekly/period overtime (work beyond weekly hours limit)
5. Penalties (weekend rates, shift penalties, time-based penalties)

Dependencies:
- rules module for award-specific rule sets
"""

from .rules import get_rules_for_award
from .rule_schema import canonical_rules

class PayRules:
    """
    Adapter class for award-specific calculation rules.
    
    This class dynamically adapts to the selected award by using
    the appropriate rule set from the rules module. It provides a unified
    interface for accessing rules across different awards, handling differences
    in rule structures gracefully.
    
    The rule engine is structured to follow a natural progression of calculations:
    - First setting up the rule context
    - Then calculating span overtime
    - Then daily overtime
    - Then period overtime
    - Finally applying penalties
    
    All methods are designed to be self-contained and handle edge cases across
    different awards.
    """
    
    def __init__(
        self,
        award: str,
        configuration_identifier: str = None,
    ):
        if not award:
            raise ValueError("An award must be selected.")
        # Store the selected class on this adapter instance. A class-level value
        # would allow one request to replace the rules used by another request.
        self.active_rules = get_rules_for_award(
            award, configuration_identifier
        )
        self.config = canonical_rules(self.active_rules)
    
    #
    # HOURS LIMIT METHODS - Basic configuration for calculating overtime
    #
    
    def _configured_overtime_limit(
        self, attribute: str, worker_type: str, employment_type: str | None
    ) -> float | None:
        configuration = getattr(self.active_rules, attribute, None)
        if not isinstance(configuration, dict):
            return None
        variation = configuration.get('variation')
        if variation == 'default':
            return configuration.get('default')
        if variation == 'worker_type':
            return configuration.get(worker_type)
        if variation == 'employment_type' and employment_type is not None:
            return configuration.get(employment_type)
        return None

    def get_ordinary_hours_daily_limit(
        self, worker_type: str, employment_type: str | None = None
    ) -> float:
        """
        Get daily ordinary hours limit based on worker type.
        
        Args:
            worker_type: Type of worker ('day' or 'shift')
            
        Returns:
            float: Maximum ordinary hours allowed per day before overtime applies
        """
        configuration = self.config["ordinary_time"]["daily"]
        if isinstance(configuration, dict):
            variation = configuration.get("variation")
            if variation == "default":
                return configuration["default"]
            if variation == "employment_type" and employment_type:
                return configuration[employment_type]
            return configuration[worker_type]
        return configuration

    def calculate_weekly_ordinary_hours(self, hours: float, worker_type: str = 'shift', employment_type: str = 'full_time', contracted_hours: float = None, period_weeks: int = 1) -> float:
        """
        Calculate ordinary hours for the week.
        
        Args:
            hours: Total hours worked in the week
            worker_type: Type of worker ('day' or 'shift')
            employment_type: Type of employment ('full_time', 'part_time', 'casual')
            contracted_hours: Contracted hours per week for part-time employees
            
        Returns:
            float: Maximum ordinary hours allowed per week (capped at weekly limit)
        """
        configuration = self.config["ordinary_time"]["period"]
        if configuration.get("variation") == "default":
            weekly_limit = configuration["default"]
        elif configuration.get("variation") == "employment_type" and employment_type:
            weekly_limit = configuration[employment_type]
        else:
            weekly_limit = configuration[worker_type]
        
        # For part-time employees, use contracted hours if configured in the rules
        if employment_type == 'part_time' and contracted_hours is not None:
            if self.config["top_up"].get("use_contracted_hours_for_pt_overtime", False):
                weekly_limit = contracted_hours
                
        return min(hours, weekly_limit * period_weeks)
    
    #
    # OVERTIME METHODS - For calculating various types of overtime
    #
    
    def is_overtime_day(self, day: str, worker_type: str) -> bool:
        """
        Determine if all hours on this day are automatically overtime.
        
        Args:
            day: Day of the week ('Monday', 'Tuesday', etc.)
            worker_type: Type of worker ('day' or 'shift')
            
        Returns:
            bool: True if all hours on this day count as overtime, False otherwise
        """
        rule = self.config["day_rules"].get(day, {}).get(worker_type, {})
        return rule.get("base_classification") == "overtime"

    def calculate_span_overtime(self, start_time: float, end_time: float, daily_hours: float, worker_type: str, day: str | None = None) -> float:
        """
        Calculate overtime hours for work done outside the span of hours (typically after 6pm for day workers).
        This is the first overtime calculation to be applied.
        
        Args:
            start_time: Start time of the shift (in 24-hour format)
            end_time: End time of the shift (in 24-hour format)
            daily_hours: Total hours worked in the day
            worker_type: Type of worker ('day' or 'shift')
            
        Returns:
            float: Hours of span overtime to be applied
        """
        # Span overtime only applies to day workers
        if worker_type != 'day':
            return 0
        windows = self.config["ordinary_time"].get("windows", {}).get(worker_type, {})
        window = windows.get(day, windows.get("default", {}))
        if not window.get("enabled", True):
            return 0
        after_cutoff = window.get("end")
        before_cutoff = window.get("start")
        before_hours = (
            max(0, min(end_time, before_cutoff) - start_time)
            if before_cutoff is not None
            else 0
        )
        after_hours = (
            max(0, end_time - max(start_time, after_cutoff))
            if after_cutoff is not None
            else 0
        )
        return min(before_hours + after_hours, daily_hours)
    
    def get_overtime_rate(self, day: str, hours_of_overtime: float = 0) -> float:
        """
        Get the overtime multiplier for a given day and amount of overtime.
        
        Args:
            day: Day of the week ('Monday', 'Tuesday', etc.)
            hours_of_overtime: Amount of overtime hours already worked (for two-tier overtime)
            
        Returns:
            float: Overtime rate multiplier (e.g., 1.5 for time-and-a-half)
        """
        overtime = self.config["pay_rates"]["overtime"]
        tier = overtime.get("two_tier", {})
        extended_overtime_days = tier.get("days", ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])

        # Use segmented overtime on configured days.
        if (
            day in extended_overtime_days
            and tier.get("enabled", False)
        ):
            if hours_of_overtime > tier.get("threshold", 0):
                return overtime["extended"]["multiplier"]
            return overtime["weekday"]["multiplier"]

        # Different overtime rates for weekend days or rulesets without segmented overtime.
        if day == 'Sunday':
            return overtime["sunday"]["multiplier"]
        elif day == 'Saturday':
            return overtime["saturday"]["multiplier"]

        # Default to standard overtime rate for weekdays and flat-rate rulesets.
        return overtime["weekday"]["multiplier"]

    def calculate_overtime_pay(
        self, day: str, overtime_hours: float, hourly_rate: float
    ) -> float:
        """Calculate overtime pay, splitting configured two-tier rates."""
        if overtime_hours <= 0:
            return 0

        overtime = self.config["pay_rates"]["overtime"]
        tier = overtime.get("two_tier", {})
        extended_days = tier.get("days", ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
        if (
            day in extended_days
            and tier.get("enabled", False)
        ):
            threshold = tier.get("threshold", 0)
            standard_hours = min(overtime_hours, threshold)
            extended_hours = max(overtime_hours - threshold, 0)
            return hourly_rate * (
                standard_hours * overtime["weekday"]["multiplier"]
                + extended_hours * overtime["extended"]["multiplier"]
            )

        return overtime_hours * hourly_rate * self.get_overtime_rate(
            day, overtime_hours
        )

    #
    # PENALTY METHODS - For calculating various types of penalties
    #
    
    def get_penalty_rate(self, day: str, worker_type: str) -> float:
        """
        Get the penalty rate for non-overtime hours on weekends for shift workers.
        
        Args:
            day: Day of the week ('Monday', 'Tuesday', etc.)
            worker_type: Type of worker ('day' or 'shift')
            
        Returns:
            float: Penalty rate multiplier (e.g., 0.25 for 25% loading)
        """
        rule = self.config["day_rules"].get(day, {}).get(worker_type, {})
        if rule.get("base_classification") == "overtime":
            return 0
        return rule.get("ordinary_loading", 0)
    
    def calculate_shift_start_penalty(self, start_time: float, worker_type: str) -> dict:
        """
        Calculate penalty rate based on shift start time (primarily for Aged Care shift workers).
        
        Args:
            start_time: Start time of the shift (in 24-hour format)
            worker_type: Type of worker ('shift' or 'day')
            
        Returns:
            dict with keys:
            - applies (bool): Whether the shift start penalty applies
            - penalty_rate (float): The penalty rate to apply
            - description (str): Description of the penalty for reporting
        """
        rules = self.active_rules
        
        # Only apply if the award has shift start time penalty rules
        if not hasattr(rules, 'SHIFT_PEN_RULES'):
            return {'applies': False, 'penalty_rate': 0, 'description': ''}
            
        # Get the shift penalty rules for this worker type
        shift_pen_rules = rules.SHIFT_PEN_RULES.get(worker_type, {})
        if not shift_pen_rules:
            return {'applies': False, 'penalty_rate': 0, 'description': ''}
            
        # Check if the shift start time falls within any of the penalty windows
        for window_name, window in shift_pen_rules.items():
            if window['start'] <= start_time < window['end']:
                return {
                    'applies': True,
                    'penalty_rate': window['rate'],
                    'description': f"Shift Pen after {window['start']}:00 ({int(window['rate'] * 100)}%)"
                }
                
        return {'applies': False, 'penalty_rate': 0, 'description': ''}
    
    def check_shift_gap_penalty(self, current_shift_start: float, previous_shift_end: float,
                               current_day: str = None, previous_day: str = None) -> dict:
        """
        Check if a gap penalty should be applied between two shifts.
        
        This rule is primarily for the Aged Care award, which requires a minimum
        gap between shifts. If shifts are too close together, a penalty applies.
        
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
        gap_rule = self.config["bbs"]
        if not gap_rule.get("minimum_hours"):
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
        if hours_between_shifts < gap_rule["minimum_hours"]:
            return {
                'applies': True,
                'penalty_rate': gap_rule.get("loading", 0)
            }
        
        return {'applies': False, 'penalty_rate': 0}
    
    def calculate_penalties(self, start_time: float, end_time: float, day: str, worker_type: str) -> list:
        """
        Calculate all applicable penalties for a shift using the unified penalty structure.
        
        This method processes both shift-based and time-based penalties from the PENALTIES
        property of the active ruleset. It handles shifts that cross midnight and correctly
        calculates penalty rates for each segment of the shift.
        
        Args:
            start_time: Start time of the shift (in 24-hour format)
            end_time: End time of the shift (in 24-hour format)
            day: Day of the week for the shift
            worker_type: Type of worker ('shift' or 'day')
            
        Returns:
            List of dicts with keys:
            - type (str): 'shift_based' or 'time_based'
            - start (float): Start time of the penalty period (for time-based)
            - end (float): End time of the penalty period (for time-based)
            - hours (float): Number of hours in this penalty period
            - rate (float): Penalty rate for this period
            - description (str): Description of the penalty for reporting
        """
        rules = self.active_rules
        
        # Only apply if the award has unified penalties structure
        penalties_config = (
            getattr(rules, "PENALTIES")
            if hasattr(rules, "PENALTIES")
            else self.config["penalties"]
        )
        if not penalties_config:
            # Fall back to legacy methods if PENALTIES not defined
            penalties = []
            
            # Try shift penalties
            shift_penalty = self.calculate_shift_start_penalty(start_time, worker_type)
            if shift_penalty['applies']:
                penalties.append({
                    'type': 'shift_based',
                    'rate': shift_penalty['penalty_rate'],
                    'description': shift_penalty['description'],
                    'hours': end_time - start_time if end_time > start_time else (24 - start_time) + end_time
                })
                
            # Try hourly penalties
            hourly_penalties = self.calculate_hourly_penalties(start_time, end_time, day)
            for hp in hourly_penalties:
                penalties.append({
                    'type': 'time_based',
                    'start': hp['start'],
                    'end': hp['end'],
                    'rate': hp['rate'],
                    'description': hp['description'],
                    'hours': hp['hours']
                })
                
            return penalties
            
        # Normalize end time (handle shifts that go past midnight)
        normalized_end_time = end_time
        if end_time < start_time:
            normalized_end_time += 24
            
        penalties = []
        
        # Process each penalty definition
        for penalty_name, penalty in penalties_config.items():
            # Skip if this penalty doesn't apply to this worker type
            if worker_type not in penalty.get('applies_to', []):
                continue

            penalty_days = penalty.get('days')
            if penalty_days is not None and day not in penalty_days:
                continue

            if penalty_days is None and day in ['Saturday', 'Sunday']:
                continue
            
            penalty_type = penalty['type']
            match_on = penalty.get('basis', penalty.get('match_on', 'start'))

            # Handle shift-based penalties (apply to the whole shift when the trigger matches)
            if penalty_type == 'shift_based':
                window_start = penalty.get('start')
                window_end = penalty.get('end')

                if window_start is None or window_end is None:
                    continue

                if match_on == 'duration':
                    duration_hours = normalized_end_time - start_time
                    min_duration = penalty.get('duration', penalty.get('min_duration', window_start))
                    max_duration = penalty.get('duration_end', penalty.get('max_duration', window_end))
                    if min_duration <= duration_hours < max_duration:
                        penalties.append({
                            'type': 'shift_based',
                            'rate': penalty['rate'],
                            'description': penalty['description'],
                            'hours': duration_hours,
                            'basis': 'duration'
                        })
                    continue

                if match_on == 'start_and_end':
                    finish_start = penalty.get('finish_start')
                    finish_end = penalty.get('finish_end')
                    if finish_start is None or finish_end is None:
                        continue
                    shift_starts_in_window = self._time_in_window(
                        start_time, window_start, window_end
                    )
                    shift_ends_in_window = self._time_in_window(
                        normalized_end_time % 24, finish_start, finish_end
                    )
                    if shift_starts_in_window and shift_ends_in_window:
                        penalties.append({
                            'type': 'shift_based',
                            'rate': penalty['rate'],
                            'description': penalty['description'],
                            'hours': normalized_end_time - start_time,
                            'basis': 'start_and_end'
                        })
                    continue

                trigger_time = start_time if match_on != 'end' else (normalized_end_time % 24)
                if self._time_in_window(trigger_time, window_start, window_end):
                    total_hours = normalized_end_time - start_time
                    penalties.append({
                        'type': 'shift_based',
                        'rate': penalty['rate'],
                        'description': penalty['description'],
                        'hours': total_hours,
                        'basis': match_on
                    })

            # Handle time-based penalties (apply to specific hours)
            elif penalty_type == 'time_based':
                window_start = penalty.get('start')
                window_end = penalty.get('end')

                if window_start is None or window_end is None:
                    continue

                # Time-based penalties are always evaluated against worked hours.
                overlap_start = max(start_time, window_start)
                overlap_end = min(normalized_end_time, window_end if window_end >= window_start else window_end + 24)

                # If there's an overlap, add it to the penalties
                if overlap_start < overlap_end:
                    overlap_hours = overlap_end - overlap_start

                    # Normalize times back to 0-24 range for display
                    display_start = overlap_start % 24
                    display_end = overlap_end % 24

                    penalties.append({
                        'type': 'time_based',
                        'start': display_start,
                        'end': display_end,
                        'rate': penalty['rate'],
                        'description': penalty['description'],
                        'hours': overlap_hours,
                        'basis': 'time'
                    })
                    
        return penalties

    @staticmethod
    def _time_in_window(time_value: float, window_start: float, window_end: float) -> bool:
        """
        Determine whether a clock time falls within a window, handling overnight windows.
        """
        if window_end < window_start:
            window_end += 24
            if time_value < window_start:
                time_value += 24

        return window_start <= time_value < window_end
    
    def calculate_hourly_penalties(self, start_time: float, end_time: float, day: str = None) -> list:
        """
        Calculate hourly penalties for specific time periods.
        
        This method identifies penalty periods when shifts overlap with defined
        penalty windows (e.g., overnight hours). It handles shifts that cross midnight
        and correctly calculates penalty rates for each segment of the shift.
        
        Args:
            start_time: Start time of the shift (in 24-hour format)
            end_time: End time of the shift (in 24-hour format)
            day: Day of the week for the shift
            
        Returns:
            List of dicts with keys:
            - start (float): Start time of the penalty period
            - end (float): End time of the penalty period
            - hours (float): Number of hours in this penalty period
            - rate (float): Penalty rate for this period
            - description (str): Description of the penalty for reporting
        """
        rules = self.active_rules
        
        # Only apply if the award has hourly penalty rules
        if not hasattr(rules, 'HOURS_PEN_RULES'):
            return []
            
        # Don't apply hourly penalties on weekends (they have their own penalty rates)
        if day in ['Saturday', 'Sunday']:
            return []
            
        # Normalize end time (handle shifts that go past midnight)
        normalized_end_time = end_time
        if end_time < start_time:
            normalized_end_time += 24
            
        penalty_periods = []
        
        # Check each penalty window
        for window_name, window in rules.HOURS_PEN_RULES.items():
            window_start = window['start']
            window_end = window['end']
            
            # Handle windows that cross midnight
            if window_end < window_start:
                window_end += 24
                
            # Calculate overlap with the shift
            overlap_start = max(start_time, window_start)
            overlap_end = min(normalized_end_time, window_end)
            
            # If there's an overlap, add it to the penalty periods
            if overlap_start < overlap_end:
                penalty_hours = overlap_end - overlap_start
                penalty_periods.append({
                    'start': overlap_start % 24,  # Normalize back to 0-24 range
                    'end': overlap_end % 24,      # Normalize back to 0-24 range
                    'hours': penalty_hours,
                    'rate': window['rate'],
                    'description': f"Hours Pen {int(window_start)}:00-{int(window_end % 24)}:00 ({int(window['rate'] * 100)}%)"
                })
                
        return penalty_periods
