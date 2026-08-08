"""
Rule engine for pay calculations.

This module contains the calculation interface for the canonical grouped rule
contract used by the live Fast Food, Coles, GRIA, and Woolies rulesets.

The rule engine implements methods in the following logical order:
1. Basic award settings (ordinary hours limits, worker types)
2. Span overtime (work beyond span of hours)
3. Daily overtime (work beyond daily hours limit)
4. Weekly/period overtime (work beyond weekly hours limit)
5. Penalties (weekend rates, shift penalties, time-based penalties)

Dependencies:
- rules module for award-specific rule sets
"""

from copy import deepcopy

from .rules import get_rules_for_award

class PayRules:
    """Calculation helpers over the canonical grouped rule contract.
    
    The rule engine is structured to follow a natural progression of calculations:
    - First setting up the rule context
    - Then calculating span overtime
    - Then daily overtime
    - Then period overtime
    - Finally applying penalties
    
    Both live rulesets expose the same seven grouped dictionaries, so calculation
    code never needs award-specific attribute fallbacks.
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
        self.config = {
            "shift": deepcopy(self.active_rules.SHIFT_RULES),
            "ordinary_time": deepcopy(self.active_rules.ORDINARY_TIME_RULES),
            "day_treatment": deepcopy(self.active_rules.DAY_TREATMENT_RULES),
            "pay_rates": deepcopy(self.active_rules.PAY_RATES),
            "gap_between_shifts": deepcopy(
                self.active_rules.GAP_BETWEEN_SHIFTS_RULE
            ),
            "penalties": deepcopy(self.active_rules.ORDINARY_HOUR_PENALTIES),
            "top_up": deepcopy(self.active_rules.TOP_UP_RULES),
        }
    
    #
    # HOURS LIMIT METHODS - Basic configuration for calculating overtime
    #
    
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

    def calculate_weekly_ordinary_hours(self, hours: float, worker_type: str = 'shift', employment_type: str = 'full_time', contracted_hours: float = None, period_weeks: int = 1, basis: str | None = None) -> float:
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
            if configuration.get("part_time_uses_contracted_hours", False):
                weekly_limit = contracted_hours
                
        # A pay-period threshold is supplied as its total (for example 76 for
        # a fortnight); a weekly threshold applies independently each week.
        configured_basis = configuration.get("basis", "weekly")
        if basis is None:
            basis = (
                configured_basis.get(employment_type, "weekly")
                if isinstance(configured_basis, dict)
                else configured_basis
            )
        multiplier = period_weeks if basis == "weekly" else 1
        return min(hours, weekly_limit * multiplier)
    
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
        rule = self.config["day_treatment"].get(day, {}).get(worker_type, {})
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
        windows = self.config["ordinary_time"].get("span_overtime", {}).get(worker_type, {})
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

    #
    # PENALTY METHODS - For calculating various types of penalties
    #
    
    def get_penalty_rate(
        self, day: str, worker_type: str, employment_type: str | None = None
    ) -> float:
        """
        Get the penalty rate for non-overtime hours on weekends for shift workers.
        
        Args:
            day: Day of the week ('Monday', 'Tuesday', etc.)
            worker_type: Type of worker ('day' or 'shift')
            
        Returns:
            float: Penalty rate multiplier (e.g., 0.25 for 25% loading)
        """
        rule = self.config["day_treatment"].get(day, {}).get(worker_type, {})
        if rule.get("base_classification") == "overtime":
            return 0
        if employment_type == "casual":
            return rule.get("casual_rate", rule.get("ordinary_loading", 0))
        return rule.get("ordinary_loading", 0)
    
    def check_shift_gap_penalty(self, current_shift_start: float, previous_shift_end: float,
                               current_day: str = None, previous_day: str = None,
                               employment_type: str | None = None) -> dict:
        """
        Check if a gap penalty should be applied between two shifts.
        
        If the active grouped rules require a minimum gap between shifts, a
        shorter gap attracts the configured loading.
        
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
        gap_rule = self.config["gap_between_shifts"]
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
                'penalty_rate': (
                    gap_rule.get("casual_rate", gap_rule.get("loading", 0))
                    if employment_type == "casual" else gap_rule.get("loading", 0)
                )
            }
        
        return {'applies': False, 'penalty_rate': 0}
    
    def calculate_penalties(
        self, start_time: float, end_time: float, day: str, worker_type: str,
        employment_type: str | None = None,
    ) -> list:
        """
        Calculate all applicable penalties for a shift using the unified penalty structure.
        
        This method processes both shift-based and time-based penalties from the
        canonical penalty group. It handles shifts that cross midnight and correctly
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
        penalties_config = self.config["penalties"]
        if not penalties_config:
            return []
            
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

            penalty_type = penalty['type']
            match_on = penalty.get('basis', penalty.get('match_on', 'start'))
            penalty_days = penalty.get('days')

            # Handle shift-based penalties (apply to the whole shift when the trigger matches)
            if penalty_type == 'shift_based':
                if penalty_days is not None and day not in penalty_days:
                    continue
                if penalty_days is None and day in ['Saturday', 'Sunday']:
                    continue
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
                            'rate': self._selected_penalty_rate(penalty, employment_type),
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
                            'rate': self._selected_penalty_rate(penalty, employment_type),
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
                        'rate': self._selected_penalty_rate(penalty, employment_type),
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

                # A time-of-day window repeats every calendar day. Project it
                # onto the shift's continuous timeline so an overnight shift
                # can receive every applicable loading without becoming
                # multiple roster entries.
                for overlap_start, overlap_end in self._time_window_overlaps(
                    start_time, normalized_end_time, window_start, window_end
                ):
                    calendar_day = self._calendar_day_for_time(day, overlap_start)
                    if penalty_days is not None and calendar_day not in penalty_days:
                        continue
                    if penalty_days is None and calendar_day in ['Saturday', 'Sunday']:
                        continue
                    penalties.append({
                        'type': 'time_based',
                        'start': overlap_start % 24,
                        'end': overlap_end % 24,
                        'rate': self._selected_penalty_rate(penalty, employment_type),
                        'description': penalty['description'],
                        'hours': overlap_end - overlap_start,
                        'basis': 'time'
                    })
                    
        return penalties

    @staticmethod
    def _calendar_day_for_time(start_day: str, time_on_timeline: float) -> str:
        """Return the actual calendar day for a point on a shift timeline."""
        days = [
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday",
        ]
        return days[(days.index(start_day) + int(time_on_timeline // 24)) % len(days)]

    @staticmethod
    def _time_window_overlaps(
        start_time: float, end_time: float, window_start: float, window_end: float
    ) -> list[tuple[float, float]]:
        """Return every overlap of a repeating time-of-day window and a shift.

        The shift is a continuous timeline: 22:00–03:00 is represented as
        22–27. Penalty windows repeat every 24 hours on that same timeline,
        covering arbitrary boundaries such as 23:00 as well as midnight.
        """
        if end_time <= start_time:
            return []

        duration = window_end - window_start
        if duration < 0:
            duration += 24
        if duration <= 0:
            return []

        first_day = int(start_time // 24) - 1
        last_day = int(end_time // 24) + 1
        overlaps = []
        for day_offset in range(first_day, last_day + 1):
            period_start = window_start + (day_offset * 24)
            period_end = period_start + duration
            overlap_start = max(start_time, period_start)
            overlap_end = min(end_time, period_end)
            cursor = overlap_start
            while cursor < overlap_end:
                next_midnight = (int(cursor // 24) + 1) * 24
                segment_end = min(overlap_end, next_midnight)
                overlaps.append((cursor, segment_end))
                cursor = segment_end
        return overlaps

    @staticmethod
    def _selected_penalty_rate(penalty: dict, employment_type: str | None) -> float:
        """Choose an explicitly configured casual loading when one exists.

        Penalty rates are additional loadings.  This selector does not combine
        rates or infer an interaction: award-specific functions and values
        define the result directly.
        """
        if employment_type == "casual":
            return penalty.get("casual_rate", penalty["rate"])
        return penalty["rate"]

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
