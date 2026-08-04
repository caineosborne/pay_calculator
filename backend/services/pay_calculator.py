"""
Core pay calculation service.

This module contains the main business logic for calculating pay based on
shifts worked. It implements all pay rules and produces detailed breakdowns
of hours worked and pay earned.

Dependencies:
- models.request_models: Input data structures
- models.response_models: Output data structures
- services.rule_engine: Business rules and constants
"""

from collections import defaultdict

from models.request_models import PayRequest, Shift
from models.response_models import PayResponse, RulesetSummary
from services.rule_engine import PayRules

class PayCalculator:
    """
    Main calculator class for processing pay calculations.
    
    This class takes shift data and applies business rules to calculate
    various types of pay (ordinary, overtime, penalty) and provides
    detailed breakdowns of hours worked.
    """

    def __init__(self, data: PayRequest):
        """
        Initialize calculator with request data.
        
        Args:
            data (PayRequest): Contains hourly rate, worker type, award, and shifts to process
        """
        self.data = data
        self.worker_type = data.worker_type.value if hasattr(data.worker_type, 'value') else data.worker_type
        
        # Keep this calculation's rules isolated from every other request.
        award = data.award.value if hasattr(data.award, 'value') else data.award
        self.rules = PayRules(award, data.rule_configuration)
        
        # Get employment type and contracted hours
        self.employment_type = data.employment_type.value if hasattr(data.employment_type, 'value') else data.employment_type
        self.contracted_hours = data.contracted_hours
        self.period_weeks = 2
        self.public_holidays = {
            (item.week, item.day) for item in data.public_holidays
        }
        if self.public_holidays and "public_holiday" not in self.rules.config["day_rules"]:
            raise ValueError(
                "The selected ruleset does not define public-holiday treatment."
            )
        self.long_day_used_weeks = set()
        self._minimum_expanded_ids = set()
        
        self.total_hours = 0
        self.total_ordinary_hours = 0
        self.breakdown = {}
        self.ordered_days = []
        
        # For tracking the previous shift end time and day (needed for gap penalty)
        self.previous_shift_end = None
        self.previous_shift_day = None

    def _is_public_holiday(self, shift: Shift) -> bool:
        return (shift.week, shift.day) in self.public_holidays

    def _attendance_rules(self) -> dict:
        return self.rules.config["attendance"]

    def _overtime_multiplier(self, key: str, day: str, hours: float) -> float:
        rates = self.rules.config["pay_rates"]["overtime"]
        if key in rates:
            return rates[key].get("multiplier", self.rules.get_overtime_rate(day, hours))
        return self.rules.get_overtime_rate(day, hours)

    def _expand_minimum_shift(self, shift: Shift) -> Shift:
        """Extend paid attendance to an award's minimum engagement."""
        minimum = self._attendance_rules().get("minimum_paid_shift_hours", {}).get(
            self.worker_type
        )
        if not minimum or shift.start is None or shift.end is None:
            return shift
        end_time = self._normalized_end(shift)
        break_duration = shift.break_duration if shift.break_duration is not None else self._attendance_rules().get("default_break_hours", 0.5)
        required_end = shift.start + break_duration + minimum
        if end_time >= required_end:
            return shift
        expanded = shift.model_copy(update={"end": required_end})
        self._minimum_expanded_ids.add(id(expanded))
        return expanded

    @staticmethod
    def _remove_hourly_penalty_hours(breakdown: dict, hours: float) -> None:
        """Remove the latest penalty-eligible hours when ordinary time becomes OT."""
        remaining = hours
        for penalty in reversed(breakdown.get("hourly_penalties", [])):
            removed = min(penalty.get("hours", 0), remaining)
            penalty["hours"] = round(penalty.get("hours", 0) - removed, 6)
            remaining -= removed
            if remaining <= 0:
                break

    def _calculate_single_shift_hours(self, shift: Shift) -> dict:
        """Calculate hours breakdown for a single shift.
        
        This follows a three-phase calculation:
        1. Detect if hours are overtime (span, daily limit, weekly limit, or weekend for day workers)
        2. Calculate overtime rates (2x on Sunday, 1.5x otherwise)
        3. For remaining ordinary hours, calculate penalties for shift workers on weekends
        4. Apply gap penalty if this shift starts too soon after the previous one (Aged Care award only)
        """
        if not (shift.start is not None and shift.end is not None):
            return self._get_empty_day_breakdown()

        default_break = self._attendance_rules().get("default_break_hours", 0.5)
        break_duration = (
            shift.break_duration
            if shift.break_duration is not None
            else default_break
        )
        end_time = shift.end if shift.end > shift.start else shift.end + 24
        daily_hours = max(0, (end_time - shift.start) - break_duration)
        
        applied_rules = []
        
        # Phase 1: Detect overtime conditions
        overtime_hours = 0
        ordinary_hours = daily_hours
        
        is_public_holiday = self._is_public_holiday(shift)
        holiday_rule = self.rules.config["day_rules"].get("public_holiday", {}).get(self.worker_type, {})
        overtime_rate_key = "weekday"

        # Explicit/manual OT has the highest base-classification priority.
        if shift.manual_overtime:
            overtime_hours = daily_hours
            ordinary_hours = 0
            overtime_rate_key = "manual"
            applied_rules.append("Manual Overtime")
        # Public-holiday day treatment is intentionally applied with the
        # time/day base classifiers, before daily and period limits.
        elif is_public_holiday and holiday_rule.get("base_classification") == "overtime":
            overtime_hours = daily_hours
            ordinary_hours = 0
            overtime_rate_key = holiday_rule.get("overtime_rate_key", "public_holiday")
            applied_rules.append("Public Holiday Overtime")
        # 1a. Day workers: All weekend hours are overtime
        elif self.rules.is_overtime_day(shift.day, self.worker_type):
            overtime_hours = daily_hours
            ordinary_hours = 0
            overtime_rate_key = self.rules.config["day_rules"].get(shift.day, {}).get(self.worker_type, {}).get("overtime_rate_key", shift.day.lower())
            applied_rules.append(f"{shift.day} Overtime")
        else:
            # 1b. Check for span overtime outside the configured day-worker span.
            span_ot = self.rules.calculate_span_overtime(shift.start, end_time, daily_hours, self.worker_type, shift.day)
            if span_ot > 0:
                overtime_hours += span_ot
                ordinary_hours -= span_ot
                applied_rules.append("Span Overtime")
            
            # 1c. Check daily hours limit
            daily_limit = self.rules.get_ordinary_hours_daily_limit(
                self.worker_type, self.employment_type
            )
            long_day = self.rules.config["ordinary_time"].get("long_day", {})
            if (
                long_day.get("uses_per_week", 0) > 0
                and shift.week not in self.long_day_used_weeks
                and ordinary_hours > daily_limit
            ):
                daily_limit = long_day.get("ordinary_limit_hours", daily_limit)
                self.long_day_used_weeks.add(shift.week)
                applied_rules.append("Weekly Long Day Allowance")
            if ordinary_hours > daily_limit:
                daily_ot = ordinary_hours - daily_limit
                overtime_hours += daily_ot
                ordinary_hours = daily_limit
                applied_rules.append("Daily Overtime")
        
        # Phase 2: Apply appropriate overtime rate
        # Period overtime is reassigned after every shift has been processed.
        overtime_rate = self._overtime_multiplier(overtime_rate_key, shift.day, overtime_hours)
        # BBS has priority over ordinary-hour penalties, but remains a loading
        # on the final ordinary portion in this release.
        gap_penalty = {'applies': False, 'penalty_rate': 0}
        if self.previous_shift_end is not None and self.previous_shift_day is not None:
            gap_penalty = self.rules.check_shift_gap_penalty(
                shift.start, self.previous_shift_end, shift.day, self.previous_shift_day
            )
        gap_penalty_rate = gap_penalty.get('penalty_rate', 0)
        gap_penalty_hours = ordinary_hours if gap_penalty.get('applies', False) else 0
        if gap_penalty_hours > 0:
            applied_rules.append(f"Gap Penalty ({int(gap_penalty_rate * 100)}%)")

        # Phase 3: Calculate normal penalties (unified approach)
        # First, get weekend penalties if applicable
        penalty_rate = (
            holiday_rule.get("ordinary_loading", 0)
            if is_public_holiday else self.rules.get_penalty_rate(shift.day, self.worker_type)
        )
        penalty_hours = ordinary_hours if penalty_rate > 0 else 0
        if penalty_hours > 0:
            label = "Public Holiday Loading" if is_public_holiday else f"{shift.day} Penalty"
            applied_rules.append(f"{label} ({int(penalty_rate * 100)}%)")
        
        # Then, calculate all other penalties using the unified approach
        all_penalties = [] if is_public_holiday else self.rules.calculate_penalties(shift.start, end_time, shift.day, self.worker_type)
        
        # Set up the detailed penalty structures
        shift_penalty_rate = 0
        shift_penalty_hours = 0
        hourly_penalty_details = []
        
        # Process each penalty from the unified structure
        for penalty in all_penalties:
            applied_rules.append(penalty.get('description', ''))
            
            if penalty['type'] == 'shift_based':
                # For shift-based penalties, apply to all ordinary hours
                shift_penalty_rate = penalty['rate']
                shift_penalty_hours = ordinary_hours
            elif penalty['type'] == 'time_based':
                # For time-based penalties, add to the hourly penalty details
                hourly_penalty_details.append({
                    'start': penalty['start'],
                    'end': penalty['end'],
                    'hours': penalty['hours'],
                    'rate': penalty['rate'],
                    'description': penalty['description']
                })

        # A time loading can never attach to base overtime.  The detailed
        # interval allocator later removes any hours converted by period OT.
        for penalty in hourly_penalty_details:
            penalty['hours'] = min(penalty['hours'], ordinary_hours)
        
        # For backward compatibility, also calculate using the old methods
        if not all_penalties:
            # Legacy Phase 4: Apply shift start penalties for Aged Care shift workers
            shift_penalty = self.rules.calculate_shift_start_penalty(shift.start, self.worker_type)
            shift_penalty_rate = shift_penalty.get('penalty_rate', 0)
            shift_penalty_hours = ordinary_hours if shift_penalty.get('applies', False) else 0
            
            if shift_penalty_hours > 0:
                applied_rules.append(shift_penalty.get('description', ''))
            
            # Legacy Phase 5: Apply hourly penalties for Hospitality workers (both day and shift)
            hourly_penalties = self.rules.calculate_hourly_penalties(shift.start, end_time, shift.day)
            hourly_penalty_details = hourly_penalties
            for penalty in hourly_penalties:
                applied_rules.append(penalty.get('description', ''))
        
        # Store the end time and day of this shift for future gap penalty calculations
        self.previous_shift_end = end_time
        self.previous_shift_day = shift.day
        
        return {
            'total': daily_hours,
            'ordinary': ordinary_hours,
            'overtime': overtime_hours,
            'penalty': penalty_hours,
            'penalty_rate': penalty_rate,
            'overtime_rate': overtime_rate,
            'overtime_rate_key': overtime_rate_key,
            'break': break_duration,
            'gap_penalty': gap_penalty_hours,
            'gap_penalty_rate': gap_penalty_rate,
            'shift_penalty': shift_penalty_hours,
            'shift_penalty_rate': shift_penalty_rate,
            'hourly_penalties': hourly_penalty_details,
            'topup': 0,  # Initialize topup to 0
            'applied_rules': applied_rules
        }

    @staticmethod
    def _normalized_end(shift: Shift) -> float:
        """Return an end time on the shift's start-day timeline."""
        return shift.end if shift.end > shift.start else shift.end + 24

    def calculate_daily_hours(self, shift: Shift, periods: list[Shift] | None = None) -> dict:
        """Calculate one logical workday, optionally made up of split periods.

        A single period deliberately follows the pre-existing calculation path.
        For a split day, daily limits and whole-shift rules use the combined
        workday, while hourly penalties are calculated from actual attendance.
        """
        periods = periods or [shift]
        if len(periods) == 1:
            return self._calculate_single_shift_hours(periods[0])

        ordered_periods = sorted(periods, key=lambda item: item.start)
        first_start = ordered_periods[0].start
        final_end = max(self._normalized_end(item) for item in ordered_periods)
        total_break = sum(item.break_duration or 0 for item in ordered_periods)
        combined_shift = Shift(
            week=shift.week,
            day=shift.day,
            start=first_start,
            end=final_end,
            break_duration=total_break,
            manual_overtime=any(item.manual_overtime for item in ordered_periods),
        )

        # Reuse the existing whole-shift and gap-rule behaviour, then replace
        # the fields which must be calculated from the individual attendance
        # periods rather than the elapsed span between them.
        breakdown = self._calculate_single_shift_hours(combined_shift)
        period_hours = [
            max(0, self._normalized_end(item) - item.start - (item.break_duration or 0))
            for item in ordered_periods
        ]
        total_hours = sum(period_hours)
        rules = self.rules.active_rules
        config = self.rules.config
        overtime_rates = config["pay_rates"]["overtime"]

        if self.rules.is_overtime_day(shift.day, self.worker_type):
            overtime_hours = total_hours
            ordinary_hours = 0
        else:
            span_overtime = sum(
                self.rules.calculate_span_overtime(
                    item.start,
                    self._normalized_end(item),
                    hours,
                    self.worker_type,
                    shift.day,
                )
                for item, hours in zip(ordered_periods, period_hours)
            )
            ordinary_hours = max(0, total_hours - span_overtime)
            daily_limit = self.rules.get_ordinary_hours_daily_limit(
                self.worker_type, self.employment_type
            )
            daily_overtime = max(0, ordinary_hours - daily_limit)
            ordinary_hours -= daily_overtime
            overtime_hours = span_overtime + daily_overtime

        breakdown['total'] = total_hours
        breakdown['ordinary'] = ordinary_hours
        breakdown['overtime'] = overtime_hours
        breakdown['overtime_rate'] = (
            self.rules.get_overtime_rate(shift.day, overtime_hours)
            if overtime_hours > 0 else 0
        )
        breakdown['break'] = total_break
        breakdown['penalty'] = (
            ordinary_hours
            if self.rules.get_penalty_rate(shift.day, self.worker_type) > 0
            else 0
        )
        # Whole-shift and gap loadings continue to apply to ordinary hours
        # only, even though their trigger was evaluated from the combined day.
        breakdown['shift_penalty'] = (
            ordinary_hours if breakdown.get('shift_penalty_rate', 0) > 0 else 0
        )
        breakdown['gap_penalty'] = (
            ordinary_hours if breakdown.get('gap_penalty_rate', 0) > 0 else 0
        )

        # Whole-shift penalties retain the combined earliest-start/latest-end
        # trigger. Time-based penalties must not include gaps between periods.
        hourly_penalties = []
        for item in ordered_periods:
            item_end = self._normalized_end(item)
            for penalty in self.rules.calculate_penalties(
                item.start, item_end, item.day, self.worker_type
            ):
                if penalty['type'] == 'time_based':
                    hourly_penalties.append({
                        'start': penalty['start'],
                        'end': penalty['end'],
                        'hours': penalty['hours'],
                        'rate': penalty['rate'],
                        'description': penalty['description'],
                    })
            if not self.rules.config["penalties"]:
                hourly_penalties.extend(
                    self.rules.calculate_hourly_penalties(item.start, item_end, item.day)
                )
        breakdown['hourly_penalties'] = hourly_penalties

        # The original method labels the same rules while calculating the
        # elapsed span. Keep labels useful without repeating them per period.
        breakdown['applied_rules'] = list(dict.fromkeys(breakdown['applied_rules']))
        return breakdown

    def _validate_and_group_shifts(self) -> list[tuple[int, str, list[Shift]]]:
        """Group input by workday and reject overlapping attendance periods."""
        grouped = defaultdict(list)
        for shift in self.data.shifts:
            grouped[(shift.week, shift.day)].append(self._expand_minimum_shift(shift))

        day_order = {
            day: index for index, day in enumerate(
                ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            )
        }
        result = []
        for (week, day), periods in sorted(
            grouped.items(), key=lambda item: (item[0][0], day_order[item[0][1]])
        ):
            ordered = sorted(periods, key=lambda item: item.start)
            merged = []
            for period in ordered:
                if merged and period.start < self._normalized_end(merged[-1]):
                    if id(period) not in self._minimum_expanded_ids and id(merged[-1]) not in self._minimum_expanded_ids:
                        raise ValueError(
                            f"Overlapping shifts are not allowed for Week {week} - {day}."
                        )
                    previous = merged.pop()
                    merged.append(previous.model_copy(update={
                        "end": max(self._normalized_end(previous), self._normalized_end(period)),
                        "break_duration": (previous.break_duration or 0) + (period.break_duration or 0),
                        "manual_overtime": previous.manual_overtime or period.manual_overtime,
                    }))
                else:
                    merged.append(period)
            result.append((week, day, merged))
        return result

    def _get_empty_day_breakdown(self) -> dict:
        """
        Get default values for a day with no hours.
        
        Returns:
            dict: Default breakdown structure with zero values
        """
        return {
            'total': 0,
            'ordinary': 0,
            'overtime': 0,
            'penalty': 0,
            'gap_penalty': 0,
            'gap_penalty_rate': 0,
            'shift_penalty': 0,
            'shift_penalty_rate': 0,
            'overtime_rate_key': 'weekday',
            'hourly_penalties': [],
            'topup': 0,  # Add topup field
            'break': self._attendance_rules().get("default_break_hours", 0.5),
            'applied_rules': []
        }

    def calculate_pay(self) -> PayResponse:
        """
        Main method to calculate all pay components.
        
        Processes all shifts, calculates various pay rates,
        and produces final breakdown of pay and hours.
        
        Returns:
            PayResponse: Complete calculation results
        """
        # Process each logical workday. A day may contain one or more periods.
        for week, day, periods in self._validate_and_group_shifts():
            shift = periods[0]
            day_breakdown = self.calculate_daily_hours(shift, periods)
            breakdown_key = f"Week {week} - {day}"
            
            if day_breakdown['total'] > 0:
                self.ordered_days.append(breakdown_key)
                self.total_ordinary_hours += day_breakdown['ordinary']
                self.total_hours += day_breakdown['total']
            
            self.breakdown[breakdown_key] = day_breakdown

        # Convert the latest ordinary hours to overtime when the fortnightly
        # limit is exceeded. Working backwards keeps earlier shifts ordinary.
        weekly_limit = self.rules.calculate_weekly_ordinary_hours(
            self.total_ordinary_hours, 
            self.worker_type,
            self.employment_type,
            self.contracted_hours,
            self.period_weeks
        )
        weekly_overtime_remaining = max(
            self.total_ordinary_hours - weekly_limit,
            0,
        )
        for day in reversed(self.ordered_days):
            if weekly_overtime_remaining == 0:
                break
            overtime_from_ordinary = min(
                self.breakdown[day]['ordinary'],
                weekly_overtime_remaining,
            )
            if overtime_from_ordinary == 0:
                continue

            self.breakdown[day]['ordinary'] -= overtime_from_ordinary
            self.breakdown[day]['overtime'] += overtime_from_ordinary
            self.breakdown[day]['penalty'] = max(
                self.breakdown[day]['penalty'] - overtime_from_ordinary,
                0,
            )
            self._remove_hourly_penalty_hours(
                self.breakdown[day], overtime_from_ordinary
            )
            current_overtime = self.breakdown[day]['overtime']
            self.breakdown[day]['overtime_rate'] = (
                self.rules.get_overtime_rate(day, current_overtime)
            )
            if 'Period Overtime' not in self.breakdown[day]['applied_rules']:
                self.breakdown[day]['applied_rules'].append(
                    'Period Overtime'
                )
            weekly_overtime_remaining -= overtime_from_ordinary

        # Apply a contracted-hours top-up only when the employee's total worked
        # hours fall short of their contracted-period target. Overtime counts as
        # worked time; it must not create a top-up entitlement.
        rules = self.rules.active_rules
        config = self.rules.config
        overtime_rates = config["pay_rates"]["overtime"]
        is_entitled_to_topup = (
            self.employment_type == 'part_time'
            and config["top_up"].get("part_time", False)
        ) or (
            self.employment_type == 'full_time'
            and config["top_up"].get("full_time", False)
        )
        if is_entitled_to_topup and self.contracted_hours:
            worked_hours_after_overtime = sum(
                day['total'] for day in self.breakdown.values()
            )
            contracted_topup = max(
                0,
                (self.contracted_hours * self.period_weeks)
                - worked_hours_after_overtime,
            )
            if contracted_topup > 0:
                if self.ordered_days:
                    topup_day = self.ordered_days[-1]
                else:
                    topup_day = 'Week 1 - Monday'
                    self.breakdown[topup_day] = self._get_empty_day_breakdown()
                    self.ordered_days.append(topup_day)

                self.breakdown[topup_day]['topup'] = contracted_topup
                if (
                    'Contracted Hours Top-up'
                    not in self.breakdown[topup_day]['applied_rules']
                ):
                    self.breakdown[topup_day]['applied_rules'].append(
                        'Contracted Hours Top-up'
                    )
        # Recalculate ordinary, overtime and topup hours after processing
        ordinary_hours = 0
        overtime_hours = 0
        topup_hours = 0
        
        for day in self.breakdown:
            ordinary_hours += self.breakdown[day]['ordinary']
            overtime_hours += self.breakdown[day]['overtime']
            topup_hours += self.breakdown[day].get('topup', 0)
        
        # Calculate pay
        ordinary_pay = round(ordinary_hours * self.data.hourly_rate, 2)
        
        # Calculate topup pay
        topup_pay = round(topup_hours * self.data.hourly_rate, 2)
        
        # Calculate overtime pay using day-specific rates. Two-tier awards pay
        # the initial overtime hours at the standard rate and only the balance
        # at the higher rate.
        overtime_pay = sum(
            self.rules.calculate_overtime_pay(
                day.rsplit(' - ', 1)[-1], self.breakdown[day]['overtime'], self.data.hourly_rate
            ) if self.breakdown[day].get('overtime_rate_key', 'weekday') == 'weekday' else
            self.breakdown[day]['overtime'] * self.data.hourly_rate * self._overtime_multiplier(
                self.breakdown[day].get('overtime_rate_key'),
                day.rsplit(' - ', 1)[-1], self.breakdown[day]['overtime'],
            )
            for day in self.breakdown
        )
        overtime_pay = round(overtime_pay, 2)
        
        # Penalties are loadings on ordinary hours, so these hours deliberately
        # overlap ordinary hours rather than forming a separate hour category.
        penalty_pay = sum(
            self.breakdown[day].get('penalty', 0) * self.data.hourly_rate * self.breakdown[day].get('penalty_rate', 1.0)
            for day in self.breakdown
        )
        penalty_pay = round(penalty_pay, 2)
        
        # Calculate gap penalty pay (Aged Care award only)
        gap_penalty_pay = sum(
            self.breakdown[day].get('gap_penalty', 0) * self.data.hourly_rate * self.breakdown[day].get('gap_penalty_rate', 0)
            for day in self.breakdown
        )
        gap_penalty_pay = round(gap_penalty_pay, 2)
        
        # Calculate shift start penalty pay (Aged Care shift workers only)
        shift_penalty_pay = sum(
            self.breakdown[day].get('shift_penalty', 0) * self.data.hourly_rate * self.breakdown[day].get('shift_penalty_rate', 0)
            for day in self.breakdown
        )
        shift_penalty_pay = round(shift_penalty_pay, 2)
        
        # Calculate hourly time-based penalties (Hospitality award)
        hourly_penalty_pay = 0
        time_based_penalty_hours = 0
        for day in self.breakdown:
            for penalty in self.breakdown[day].get('hourly_penalties', []):
                hourly_penalty_pay += penalty.get('hours', 0) * self.data.hourly_rate * penalty.get('rate', 0)
                time_based_penalty_hours += penalty.get('hours', 0)
        hourly_penalty_pay = round(hourly_penalty_pay, 2)
        time_based_penalty_hours = round(time_based_penalty_hours, 2)
        
        # Combine all penalty types for total penalty pay
        total_penalty_pay = round(penalty_pay + gap_penalty_pay + shift_penalty_pay + hourly_penalty_pay, 2)
        
        # Include topup_pay in total_pay
        total_pay = round(ordinary_pay + overtime_pay + total_penalty_pay + topup_pay, 2)

        # Generate ruleset summary based on worker type.
        # Handle span hours display based on whether the award uses span overtime
        span_hours_display = "N/A"
        span_rate_display = "N/A"
        
        span = config["ordinary_time"].get("windows", {}).get(self.worker_type, {}).get("default", {})
        if span.get("enabled", True) and self.worker_type == 'day':
                span_parts = []
                if span.get("start") is not None:
                    span_parts.append(f"Before {span['start']}:00")
                if span.get("end") is not None:
                    span_parts.append(f"After {span['end']}:00")
                span_hours_display = ' or '.join(span_parts) or "Not applicable"
                if overtime_rates.get("two_tier", {}).get("enabled", False):
                    span_rate_display = (
                        f"First {overtime_rates['two_tier'].get('threshold', 0)} overtime hours "
                        f"at {overtime_rates['weekday']['multiplier']}x; then "
                        f"{overtime_rates['extended']['multiplier']}x"
                    )
                else:
                    span_rate_display = f"{overtime_rates['weekday']['multiplier']}x"
            
        # Determine the appropriate weekly overtime threshold for the ruleset summary
        weekly_overtime_threshold = self.rules.calculate_weekly_ordinary_hours(
            float('inf'), self.worker_type, self.employment_type, None, 1
        ) * self.period_weeks
        if self.employment_type == 'part_time' and self.contracted_hours is not None:
            if config["top_up"].get("use_contracted_hours_for_pt_overtime", False):
                weekly_overtime_threshold = self.contracted_hours * self.period_weeks
            
        # Get the contracted hours top-up settings
        pt_entitled_to_topup = config["top_up"].get("part_time", False)
        ft_entitled_to_topup = config["top_up"].get("full_time", False)
        
        ruleset = RulesetSummary(
            span_hours={
                'threshold': span_hours_display,
                'rate': span_rate_display
            },
            daily_overtime={
                'threshold': self.rules.get_ordinary_hours_daily_limit(self.worker_type, self.employment_type),
                'rate': f"{overtime_rates['weekday']['multiplier']}x"
            },
            weekly_overtime={
                'threshold': weekly_overtime_threshold,
                'rate': f"{overtime_rates['weekday']['multiplier']}x"
            },
            saturday_rules=config["day_rules"].get("Saturday", {}).get(self.worker_type, {}),
            sunday_rules=config["day_rules"].get("Sunday", {}).get(self.worker_type, {}),
            employment_type=self.employment_type,
            contracted_hours=self.contracted_hours,
            use_contracted_hours_for_overtime=config["top_up"].get("use_contracted_hours_for_pt_overtime", False),
            pt_employees_entitled_to_contracted_topup=pt_entitled_to_topup,
            ft_employees_entitled_to_contracted_topup=ft_entitled_to_topup
        )
        
        # Add gap penalty rule if applicable (Aged Care award only)
        if config["bbs"].get("minimum_hours"):
            ruleset.gap_penalty = {
                'threshold': f"Less than {config['bbs']['minimum_hours']} hours between shifts",
                'rate': f"{config['bbs'].get('loading', 0)}x penalty"
            }
            
        # Add shift start penalties if applicable (Aged Care shift workers only)
        if hasattr(rules, 'SHIFT_PEN_RULES') and self.worker_type == 'shift':
            shift_rules = rules.SHIFT_PEN_RULES.get('shift', {})
            if 'first_window' in shift_rules:
                ruleset.shift_start_penalties = {
                    'first_window': f"{shift_rules['first_window']['start']}:00-{shift_rules['first_window']['end']}:00 ({int(shift_rules['first_window']['rate'] * 100)}%)",
                    'second_window': f"{shift_rules['second_window']['start']}:00-{shift_rules['second_window']['end']}:00 ({int(shift_rules['second_window']['rate'] * 100)}%)",
                    'third_window': f"{shift_rules['third_window']['start']}:00-{shift_rules['third_window']['end']}:00 ({int(shift_rules['third_window']['rate'] * 100)}%)"
                }
                
        # Add hourly time penalties if applicable (Hospitality award)
        if hasattr(rules, 'HOURS_PEN_RULES'):
            hours_rules = rules.HOURS_PEN_RULES
            hourly_penalties = {}
            
            # Only add entries for penalties that exist in the rules
            if 'evening' in hours_rules:
                hourly_penalties['evening'] = f"{hours_rules['evening']['start']}:00-{hours_rules['evening']['end']}:00 ({int(hours_rules['evening']['rate'] * 100)}%)"
            
            if 'night' in hours_rules:
                hourly_penalties['night'] = f"{hours_rules['night']['start']}:00-{hours_rules['night']['end']}:00 ({int(hours_rules['night']['rate'] * 100)}%)"
            
            if hourly_penalties:  # Only add note if we have penalties
                hourly_penalties['note'] = "Applies on weekdays only (not on weekends)"
                
            ruleset.hourly_penalties = hourly_penalties

        if hasattr(rules, 'PENALTIES'):
            penalties = {}

            for penalty_name, penalty in rules.PENALTIES.items():
                applies_to = penalty.get('applies_to', [])
                if self.worker_type not in applies_to:
                    continue

                penalties[penalty_name] = {
                    'type': penalty.get('type'),
                    'basis': penalty.get('basis', penalty.get('match_on', 'start')),
                    'start': penalty.get('start'),
                    'end': penalty.get('end'),
                    'rate': penalty.get('rate'),
                }

            ruleset.penalties = penalties

        return PayResponse(
            total_hours=round(self.total_hours + topup_hours, 2),  # Include topup in total hours
            total_pay=total_pay,
            daily_breakdown=self.breakdown,
            ordinary_hours=ordinary_hours,
            overtime_hours=overtime_hours,
            topup_hours=topup_hours,  # Add topup hours
            ordinary_pay=ordinary_pay,
            overtime_pay=overtime_pay,
            topup_pay=topup_pay,  # Add topup pay
            penalty_pay=total_penalty_pay,  # Combined penalty pay
            gap_penalty_pay=gap_penalty_pay,  # Individual penalty components
            shift_penalty_pay=shift_penalty_pay,
            hourly_penalty_pay=hourly_penalty_pay,
            time_based_penalty_hours=time_based_penalty_hours,
            applied_rules=ruleset
        )
