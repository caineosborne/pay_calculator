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
import uuid

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

    def __init__(self, data: PayRequest, owner_id: uuid.UUID | None = None):
        """
        Initialize calculator with request data.
        
        Args:
            data (PayRequest): Contains hourly rate, worker type, award, and shifts to process
        """
        self.data = data
        self.worker_type = data.worker_type.value if hasattr(data.worker_type, 'value') else data.worker_type
        
        # Keep this calculation's rules isolated from every other request.
        award = data.award.value if hasattr(data.award, 'value') else data.award
        self.rules = PayRules(award, data.rule_configuration, owner_id)
        
        # Get employment type and contracted hours
        self.employment_type = data.employment_type.value if hasattr(data.employment_type, 'value') else data.employment_type
        self.contracted_hours = data.contracted_hours
        self.period_weeks = 2
        self.public_holidays = {
            (item.week, item.day) for item in data.public_holidays
        }
        if self.public_holidays and "public_holiday" not in self.rules.config["day_treatment"]:
            raise ValueError(
                "The selected ruleset does not define public-holiday treatment."
            )
        self.long_day_used_weeks = set()
        self._minimum_expanded_ids = set()
        self._minimum_expansion_hours = {}
        
        self.total_hours = 0
        self.total_ordinary_hours = 0
        self.breakdown = {}
        self.ordered_days = []
        
        # For tracking the previous shift end time and day (needed for gap penalty)
        self.previous_shift_end = None
        self.previous_shift_day = None

    def _convert_ordinary_to_overtime(self, day: str, hours: float, rule_name: str) -> float:
        """Move remaining ordinary hours on one day to overtime."""
        if self.breakdown[day].get('manual_ordinary', False):
            return 0
        overtime_from_ordinary = min(self.breakdown[day]['ordinary'], hours)
        if overtime_from_ordinary <= 0:
            return 0
        breakdown = self.breakdown[day]
        breakdown['ordinary'] -= overtime_from_ordinary
        breakdown['overtime'] += overtime_from_ordinary
        breakdown['penalty'] = max(breakdown['penalty'] - overtime_from_ordinary, 0)
        self._remove_hourly_penalty_hours(breakdown, overtime_from_ordinary)
        breakdown['overtime_rate'] = self.rules.get_overtime_rate(
            day.rsplit(' - ', 1)[-1], breakdown['overtime']
        )
        if rule_name not in breakdown['applied_rules']:
            breakdown['applied_rules'].append(rule_name)
        return overtime_from_ordinary

    def _period_day_groups(self, basis: str) -> list[list[str]]:
        if basis == "pay_period":
            return [self.ordered_days]
        groups = defaultdict(list)
        for day in self.ordered_days:
            groups[day.split(' - ', 1)[0]].append(day)
        return list(groups.values())

    def _period_basis(self, key: str = "basis") -> str:
        value = self.rules.config["ordinary_time"]["period"].get(key, "weekly")
        return value.get(self.employment_type, "weekly") if isinstance(value, dict) else value

    def _is_public_holiday(self, shift: Shift) -> bool:
        return shift.public_holiday or (shift.week, shift.day) in self.public_holidays

    def _overnight_day_treatment_penalties(
        self, shift: Shift, end_time: float, break_duration: float,
        ordinary_hours: float, daily_hours: float,
    ) -> list[dict]:
        """Return ordinary-day loadings split across calendar-day segments.

        Shifts remain a single logical workday for daily/period overtime and
        gap calculations, but each attendance segment uses its actual calendar
        day. This avoids treating Friday 22:00–03:00 as five Friday hours.
        """
        days = [
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday",
        ]
        start_day_index = days.index(shift.day)
        gross_duration = end_time - shift.start
        if gross_duration <= 0:
            return []

        penalties = []
        cursor = shift.start
        while cursor < end_time:
            next_midnight = (int(cursor // 24) + 1) * 24
            segment_end = min(end_time, next_midnight)
            day_offset = int(cursor // 24)
            calendar_day = days[(start_day_index + day_offset) % len(days)]
            rate = self.rules.get_penalty_rate(
                calendar_day, self.worker_type, self.employment_type
            )
            if rate > 0:
                gross_hours = segment_end - cursor
                # A break with no entered time is apportioned across the
                # calendar-day attendance segments. A manual lunch time is
                # already represented by separate worked periods upstream.
                paid_hours = max(
                    0, gross_hours - (break_duration * gross_hours / gross_duration)
                )
                ordinary_share = paid_hours * (ordinary_hours / daily_hours) if daily_hours else 0
                penalties.append({
                    "start": cursor % 24,
                    "end": segment_end % 24,
                    "hours": ordinary_share,
                    "rate": rate,
                    "description": f"{calendar_day} Penalty ({int(rate * 100)}%)",
                })
            cursor = segment_end
        return penalties

    def _attendance_rules(self) -> dict:
        return self.rules.config["shift"]

    def _overtime_multiplier(self, key: str, day: str, hours: float) -> float:
        rates = self.rules.config["pay_rates"]["overtime"]
        if key in rates:
            rate = rates[key]
            if self.employment_type == "casual":
                return rate.get("casual", rate.get("multiplier", self.rules.get_overtime_rate(day, hours)))
            return rate.get("multiplier", self.rules.get_overtime_rate(day, hours))
        return self.rules.get_overtime_rate(day, hours)

    def _calculate_overtime_pay(self, day: str, breakdown: dict) -> float:
        """Pay OT from the explicit rate for this employment type.

        Overtime values are total multipliers.  No ordinary casual loading is
        added on top of them.
        """
        hours = breakdown.get("overtime", 0)
        key = breakdown.get("overtime_rate_key", "weekday")
        if hours <= 0:
            return 0
        rates = self.rules.config["pay_rates"]["overtime"]
        tier = rates.get("two_tier", {})
        # A two-tier rule applies to every configured work day, regardless of
        # whether that day's OT uses the weekday, manual, Saturday or Sunday
        # base rate.  Public-holiday treatment remains a separately configured
        # fixed rate.
        if (
            key != "public_holiday"
            and tier.get("enabled", False)
            and day in tier.get("days", [])
        ):
            threshold = tier.get("threshold", 0)
            standard_hours = min(hours, threshold)
            extended_hours = max(hours - threshold, 0)
            return self.data.hourly_rate * (
                standard_hours * self._overtime_multiplier(key, day, hours)
                + extended_hours * self._overtime_multiplier("extended", day, hours)
            )
        return hours * self.data.hourly_rate * self._overtime_multiplier(key, day, hours)

    def _add_daily_pay_amounts(self) -> None:
        """Add an auditable pay total and components to each workday result.

        These values are deliberately calculated after period overtime and
        ordinary-hour loadings have been finalised, so the amount shown beside
        a day matches the amount included in the overall pay total.
        """
        casual_loading = self.rules.config["ordinary_time"].get(
            "ordinary_rates", {}
        ).get("casual_loading", 0)

        for key, breakdown in self.breakdown.items():
            day_name = key.rsplit(" - ", 1)[-1]
            ordinary_pay = breakdown.get("ordinary", 0) * self.data.hourly_rate
            ordinary_pay += (
                breakdown.get("casual_ordinary", 0)
                * self.data.hourly_rate
                * casual_loading
            )
            overtime_pay = self._calculate_overtime_pay(day_name, breakdown)
            penalty_pay = (
                breakdown.get("penalty", 0)
                * self.data.hourly_rate
                * breakdown.get("penalty_rate", 0)
                + breakdown.get("gap_penalty", 0)
                * self.data.hourly_rate
                * breakdown.get("gap_penalty_rate", 0)
                + breakdown.get("shift_penalty", 0)
                * self.data.hourly_rate
                * breakdown.get("shift_penalty_rate", 0)
                + sum(
                    penalty.get("hours", 0)
                    * self.data.hourly_rate
                    * penalty.get("rate", 0)
                    for penalty in breakdown.get("hourly_penalties", [])
                )
            )
            topup_pay = breakdown.get("topup", 0) * self.data.hourly_rate

            breakdown["ordinary_pay"] = round(ordinary_pay, 2)
            breakdown["overtime_pay"] = round(overtime_pay, 2)
            breakdown["penalty_pay"] = round(penalty_pay, 2)
            breakdown["topup_pay"] = round(topup_pay, 2)
            breakdown["pay"] = round(
                ordinary_pay + overtime_pay + penalty_pay + topup_pay, 2
            )

    def _expand_minimum_shift(self, shift: Shift) -> Shift:
        """Extend paid attendance to an award's minimum engagement."""
        minimum_rule = self._attendance_rules().get("minimum_paid_shift_hours", {})
        if isinstance(minimum_rule, dict) and minimum_rule.get("variation") == "employment_type":
            minimum = minimum_rule.get(self.employment_type)
        else:
            minimum = minimum_rule.get(self.employment_type, minimum_rule.get(self.worker_type))
        if (
            not minimum
            or shift.minimum_engagement_exempt
            or shift.start is None
            or shift.end is None
        ):
            return shift
        end_time = self._normalized_end(shift)
        break_duration = shift.break_duration if shift.break_duration is not None else self._attendance_rules().get("default_break_hours", 0.5)
        required_end = shift.start + break_duration + minimum
        if end_time >= required_end:
            return shift
        expanded = shift.model_copy(update={"end": required_end})
        self._minimum_expanded_ids.add(id(expanded))
        self._minimum_expansion_hours[id(expanded)] = minimum
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

    def _finalize_ordinary_loadings(self, breakdown: dict) -> None:
        """Apply ordinary-only loadings after period OT has finished.

        Eligibility is assessed while processing a workday, but no loading
        hours are final until all remaining ordinary hours have survived the
        period OT pass.
        """
        ordinary_hours = breakdown.get("ordinary", 0)
        breakdown["penalty"] = (
            ordinary_hours if breakdown.get("penalty_rate", 0) > 0 else 0
        )
        breakdown["shift_penalty"] = (
            ordinary_hours if breakdown.get("shift_penalty_rate", 0) > 0 else 0
        )
        breakdown["gap_penalty"] = (
            ordinary_hours if breakdown.get("gap_penalty_rate", 0) > 0 else 0
        )
        # Penalties are allocated only after every overtime pass. Time-window
        # penalties use their qualifying hours less OT already assigned before
        # period allocation; later period OT has already been removed from the
        # candidate by _remove_hourly_penalty_hours.
        preallocated_overtime = breakdown.get("preallocated_overtime", 0)
        for penalty in breakdown.get("hourly_penalties", []):
            penalty["hours"] = round(max(0, penalty.get("hours", 0) - preallocated_overtime), 6)

        applied_rules = breakdown["applied_rules"]
        for hours_key, rate_key, label_key in (
            ("penalty", "penalty_rate", "penalty_label"),
            ("shift_penalty", "shift_penalty_rate", "shift_penalty_label"),
            ("gap_penalty", "gap_penalty_rate", "gap_penalty_label"),
        ):
            if breakdown.get(hours_key, 0) > 0 and breakdown.get(rate_key, 0) > 0:
                label = breakdown.get(label_key)
                if label and label not in applied_rules:
                    applied_rules.append(label)
        for penalty in breakdown.get("hourly_penalties", []):
            label = penalty.get("description")
            if penalty.get("hours", 0) > 0 and label and label not in applied_rules:
                applied_rules.append(label)
        # Casual ordinary loading is only for ordinary time without another
        # ordinary-hours loading. Penalty rates already contain the award's
        # explicit casual loading where one applies.
        breakdown["casual_ordinary"] = 0
        if self.employment_type == "casual":
            whole_shift_loading = any((
                breakdown.get("penalty_rate", 0),
                breakdown.get("shift_penalty_rate", 0),
                breakdown.get("gap_penalty_rate", 0),
            ))
            hourly_loading_hours = sum(
                item.get("hours", 0) for item in breakdown.get("hourly_penalties", [])
            )
            breakdown["casual_ordinary"] = 0 if whole_shift_loading else max(
                0, ordinary_hours - hourly_loading_hours
            )

    def _calculate_single_shift_hours(self, shift: Shift) -> dict:
        """Calculate hours breakdown for a single shift.
        
        This follows a three-phase calculation:
        1. Detect if hours are overtime (span, daily limit, weekly limit, or weekend for day workers)
        2. Calculate overtime rates (2x on Sunday, 1.5x otherwise)
        3. For remaining ordinary hours, calculate penalties for shift workers on weekends
        4. Apply a configured gap penalty if this shift starts too soon after the previous one
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
        holiday_rule = self.rules.config["day_treatment"].get("public_holiday", {}).get(self.worker_type, {})
        # An OT conversion on an ordinary weekend (for example, daily or
        # period OT on Sunday) still uses that day's OT rate.  Weekend base
        # classification determines whether all hours are OT; it does not
        # determine the rate for OT that arises later.
        day_rule = self.rules.config["day_treatment"].get(shift.day, {}).get(
            self.worker_type, {}
        )
        overtime_rate_key = day_rule.get("overtime_rate_key", "weekday")

        if id(shift) in self._minimum_expansion_hours:
            applied_rules.append(
                f"Minimum paid shift ({self._minimum_expansion_hours[id(shift)]} hours)"
            )

        # Explicit classifications take precedence over every overtime rule.
        # Manual ordinary remains eligible for the ordinary-hour penalties below.
        if shift.manual_ordinary:
            applied_rules.append("Manual Ordinary")
        elif shift.manual_overtime:
            overtime_hours = daily_hours
            ordinary_hours = 0
            # Manual OT only overrides classification. Use the same rate
            # selection as any other overtime on this calendar day, including
            # the public-holiday rate where applicable.
            overtime_rate_key = (
                holiday_rule.get("overtime_rate_key", "public_holiday")
                if is_public_holiday
                else day_rule.get("overtime_rate_key", "weekday")
            )
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
            overtime_rate_key = day_rule.get("overtime_rate_key", shift.day.lower())
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
                applied_rules.append("Long day")
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
                shift.start, self.previous_shift_end, shift.day, self.previous_shift_day,
                self.employment_type,
            )
        gap_penalty_rate = gap_penalty.get('penalty_rate', 0)
        gap_penalty_hours = 0
        gap_penalty_label = (
            f"Gap Penalty ({int(gap_penalty_rate * 100)}%)"
            if gap_penalty.get('applies', False) else None
        )

        # Phase 3: Calculate normal penalties (unified approach). A broken
        # break-between-shifts rule is the highest-priority loading: it pays
        # alone and suppresses weekend, shift and time-of-day loadings.
        has_gap_penalty = gap_penalty.get('applies', False)
        penalty_rate = 0 if has_gap_penalty else (
            (
                holiday_rule.get("casual_rate", holiday_rule.get("ordinary_loading", 0))
                if self.employment_type == "casual" else holiday_rule.get("ordinary_loading", 0)
            ) if is_public_holiday else self.rules.get_penalty_rate(
                shift.day, self.worker_type, self.employment_type
            )
        )
        penalty_hours = ordinary_hours if penalty_rate > 0 else 0
        penalty_label = (
            f"{'Public Holiday Loading' if is_public_holiday else f'{shift.day} Penalty'} ({int(penalty_rate * 100)}%)"
            if penalty_rate > 0 else None
        )
        
        # Then, calculate all other penalties using the unified approach
        all_penalties = [] if (is_public_holiday or has_gap_penalty) else self.rules.calculate_penalties(
            shift.start, end_time, shift.day, self.worker_type, self.employment_type
        )
        
        # Set up the detailed penalty structures
        shift_penalty_rate = 0
        shift_penalty_hours = 0
        hourly_penalty_details = []

        # Day-based treatments must use the actual calendar day after
        # midnight. Store them as timed components so the pre- and
        # post-midnight portions can carry different weekend loadings.
        if end_time > 24 and not has_gap_penalty and not is_public_holiday:
            penalty_rate = 0
            penalty_hours = 0
            penalty_label = None
            hourly_penalty_details.extend(
                self._overnight_day_treatment_penalties(
                    shift, end_time, break_duration, ordinary_hours, daily_hours
                )
            )
        
        # Process each penalty from the unified structure
        shift_penalty_label = None
        for penalty in all_penalties:
            if penalty['type'] == 'shift_based':
                # For shift-based penalties, apply to all ordinary hours
                shift_penalty_rate = penalty['rate']
                shift_penalty_hours = ordinary_hours
                shift_penalty_label = penalty.get('description')
            elif penalty['type'] == 'time_based':
                # For time-based penalties, add to the hourly penalty details
                hourly_penalty_details.append({
                    'start': penalty['start'],
                    'end': penalty['end'],
                    'hours': penalty['hours'],
                    'rate': penalty['rate'],
                    'description': penalty['description']
                })

        # Store the end time and day of this shift for future gap penalty calculations
        self.previous_shift_end = end_time
        self.previous_shift_day = shift.day
        
        return {
            'total': daily_hours,
            'ordinary': ordinary_hours,
            'overtime': overtime_hours,
            'penalty': penalty_hours,
            'penalty_rate': penalty_rate,
            'penalty_label': penalty_label,
            'overtime_rate': overtime_rate,
            'overtime_rate_key': overtime_rate_key,
            'break': break_duration,
            'gap_penalty': gap_penalty_hours,
            'gap_penalty_rate': gap_penalty_rate,
            'gap_penalty_label': gap_penalty_label,
            'shift_penalty': shift_penalty_hours,
            'shift_penalty_rate': shift_penalty_rate,
            'shift_penalty_label': shift_penalty_label,
            'hourly_penalties': hourly_penalty_details,
            'preallocated_overtime': overtime_hours,
            'manual_ordinary': shift.manual_ordinary,
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
            # A mixed day is calculated as ordinary at the combined-day level;
            # public-holiday loading is added back to the flagged segment
            # below. This prevents one flagged segment from marking the whole
            # logical workday as a public holiday.
            public_holiday=all(item.public_holiday for item in ordered_periods),
            manual_overtime=any(item.manual_overtime for item in ordered_periods),
            manual_ordinary=any(item.manual_ordinary for item in ordered_periods),
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
        if combined_shift.manual_ordinary:
            ordinary_hours = total_hours
            overtime_hours = 0
        elif combined_shift.manual_overtime or self.rules.is_overtime_day(shift.day, self.worker_type):
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
        breakdown['manual_ordinary'] = combined_shift.manual_ordinary
        breakdown['preallocated_overtime'] = overtime_hours
        breakdown['penalty'] = (
            ordinary_hours
            if self.rules.get_penalty_rate(
                shift.day, self.worker_type, self.employment_type
            ) > 0
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
        # trigger. Time-based and calendar-day treatments must not include
        # gaps between periods (including a manually entered lunch).
        hourly_penalties = []
        ordinary_proportion = ordinary_hours / total_hours if total_hours else 0
        splits_calendar_day = self._normalized_end(combined_shift) > 24
        for item, item_hours in zip(ordered_periods, period_hours):
            item_end = self._normalized_end(item)
            if not self._is_public_holiday(item) and not breakdown.get("gap_penalty_rate", 0):
                if splits_calendar_day:
                    hourly_penalties.extend(
                        self._overnight_day_treatment_penalties(
                            item,
                            item_end,
                            item.break_duration or 0,
                            item_hours * ordinary_proportion,
                            item_hours,
                        )
                    )
                for penalty in self.rules.calculate_penalties(
                    item.start, item_end, item.day, self.worker_type, self.employment_type
                ):
                    if penalty['type'] == 'time_based':
                        hourly_penalties.append({
                            'start': penalty['start'],
                            'end': penalty['end'],
                            'hours': penalty['hours'],
                            'rate': penalty['rate'],
                            'description': penalty['description'],
                        })
        breakdown['hourly_penalties'] = hourly_penalties
        mixed_public_holiday_periods = [
            (item, hours) for item, hours in zip(ordered_periods, period_hours)
            if item.public_holiday
        ]
        if mixed_public_holiday_periods and not all(
            item.public_holiday for item in ordered_periods
        ):
            holiday_rule = self.rules.config["day_treatment"].get(
                "public_holiday", {}
            ).get(self.worker_type, {})
            holiday_rate = (
                holiday_rule.get("casual_rate", holiday_rule.get("ordinary_loading", 0))
                if self.employment_type == "casual"
                else holiday_rule.get("ordinary_loading", 0)
            )
            ordinary_proportion = ordinary_hours / total_hours if total_hours else 0
            for item, item_hours in mixed_public_holiday_periods:
                holiday_hours = item_hours * ordinary_proportion
                if holiday_hours and holiday_rate:
                    breakdown['hourly_penalties'].append({
                        'start': item.start,
                        'end': self._normalized_end(item),
                        'hours': holiday_hours,
                        'rate': holiday_rate,
                        'description': 'Public Holiday Loading',
                    })
        for period in ordered_periods:
            minimum = self._minimum_expansion_hours.get(id(period))
            label = f"Minimum paid shift ({minimum} hours)" if minimum else None
            if label and label not in breakdown['applied_rules']:
                breakdown['applied_rules'].append(label)

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
                        "manual_ordinary": previous.manual_ordinary or period.manual_ordinary,
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
            'gap_penalty_label': None,
            'shift_penalty': 0,
            'shift_penalty_rate': 0,
            'shift_penalty_label': None,
            'casual_ordinary': 0,
            'manual_ordinary': False,
            'penalty_label': None,
            'preallocated_overtime': 0,
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

        # Apply the days cap first: after the configured number of worked
        # days in a week or pay period, every remaining ordinary hour is OT.
        period_config = self.rules.config["ordinary_time"]["period"]
        basis = self._period_basis()
        days_basis = self._period_basis("max_work_days_basis")
        max_days = period_config.get("max_work_days")
        if max_days is not None:
            for group in self._period_day_groups(days_basis):
                eligible_days = [
                    day for day in group
                    if not self.breakdown[day].get("manual_ordinary", False)
                ]
                for day in eligible_days[max_days:]:
                    self._convert_ordinary_to_overtime(
                        day, self.breakdown[day]['ordinary'], "Maximum day overtime"
                    )

        for group in self._period_day_groups(basis):
            eligible_days = [
                day for day in group
                if not self.breakdown[day].get("manual_ordinary", False)
            ]
            ordinary_hours = sum(self.breakdown[day]['ordinary'] for day in eligible_days)
            limit = self.rules.calculate_weekly_ordinary_hours(
                ordinary_hours, self.worker_type, self.employment_type,
                self.contracted_hours, self.period_weeks if basis == "pay_period" else 1, basis,
            )
            remaining = max(ordinary_hours - limit, 0)
            for day in reversed(eligible_days):
                if remaining == 0:
                    break
                remaining -= self._convert_ordinary_to_overtime(
                    day, remaining, "Period Overtime"
                )

        # BBS and other whole-day loadings are paid only on the final ordinary
        # balance, after period OT has completed its reverse allocation.
        for day in self.breakdown.values():
            self._finalize_ordinary_loadings(day)

        # Apply a contracted-hours top-up only when the employee's total worked
        # hours fall short of their contracted-period target. Overtime counts as
        # worked time; it must not create a top-up entitlement.
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

        # Expose the final amount for every logical workday. This is useful
        # for validating a calculation without having to reconstruct it from
        # the fortnight totals.
        self._add_daily_pay_amounts()

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
        casual_ordinary_loading = self.rules.config["ordinary_time"].get(
            "ordinary_rates", {}
        ).get("casual_loading", 0)
        casual_ordinary_pay = sum(
            day.get("casual_ordinary", 0) * self.data.hourly_rate
            * casual_ordinary_loading
            for day in self.breakdown.values()
        )
        ordinary_pay = round(ordinary_pay + casual_ordinary_pay, 2)
        
        # Calculate topup pay
        topup_pay = round(topup_hours * self.data.hourly_rate, 2)
        
        # Calculate overtime pay using day-specific rates. Two-tier awards pay
        # the initial overtime hours at the standard rate and only the balance
        # at the higher rate.
        overtime_pay = sum(
            self._calculate_overtime_pay(day.rsplit(' - ', 1)[-1], breakdown)
            for day, breakdown in self.breakdown.items()
        )
        overtime_pay = round(overtime_pay, 2)
        
        # Penalties are loadings on ordinary hours, so these hours deliberately
        # overlap ordinary hours rather than forming a separate hour category.
        penalty_pay = sum(
            self.breakdown[day].get('penalty', 0) * self.data.hourly_rate * self.breakdown[day].get('penalty_rate', 1.0)
            for day in self.breakdown
        )
        penalty_pay = round(penalty_pay, 2)
        
        # Calculate configured gap penalty pay.
        gap_penalty_pay = sum(
            self.breakdown[day].get('gap_penalty', 0) * self.data.hourly_rate * self.breakdown[day].get('gap_penalty_rate', 0)
            for day in self.breakdown
        )
        gap_penalty_pay = round(gap_penalty_pay, 2)
        
        # Calculate whole-shift penalty pay.
        shift_penalty_pay = sum(
            self.breakdown[day].get('shift_penalty', 0) * self.data.hourly_rate * self.breakdown[day].get('shift_penalty_rate', 0)
            for day in self.breakdown
        )
        shift_penalty_pay = round(shift_penalty_pay, 2)
        
        # Calculate time-based penalty pay.
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
        
        span = config["ordinary_time"].get("span_overtime", {}).get(self.worker_type, {}).get("default", {})
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
        period_basis = self._period_basis()
        weekly_overtime_threshold = self.rules.calculate_weekly_ordinary_hours(
            float('inf'), self.worker_type, self.employment_type, None,
            self.period_weeks if period_basis == "pay_period" else 1,
        )
        if self.employment_type == 'part_time' and self.contracted_hours is not None:
            if config["ordinary_time"]["period"].get("part_time_uses_contracted_hours", False):
                weekly_overtime_threshold = self.contracted_hours * (
                    self.period_weeks if period_basis == "pay_period" else 1
                )
            
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
                'basis': period_basis,
                'max_work_days': config["ordinary_time"]["period"].get("max_work_days"),
                'max_work_days_basis': self._period_basis("max_work_days_basis"),
                'rate': f"{overtime_rates['weekday']['multiplier']}x"
            },
            saturday_rules=config["day_treatment"].get("Saturday", {}).get(self.worker_type, {}),
            sunday_rules=config["day_treatment"].get("Sunday", {}).get(self.worker_type, {}),
            employment_type=self.employment_type,
            contracted_hours=self.contracted_hours,
            use_contracted_hours_for_overtime=config["ordinary_time"]["period"].get("part_time_uses_contracted_hours", False),
            pt_employees_entitled_to_contracted_topup=pt_entitled_to_topup,
            ft_employees_entitled_to_contracted_topup=ft_entitled_to_topup
        )
        
        # Add the gap rule when configured.
        if config["gap_between_shifts"].get("minimum_hours"):
            ruleset.gap_penalty = {
                'threshold': f"Less than {config['gap_between_shifts']['minimum_hours']} hours between shifts",
                'rate': f"{config['gap_between_shifts'].get('loading', 0)}x penalty"
            }
            
        penalties = {}
        for penalty_name, penalty in config["penalties"].items():
            applies_to = penalty.get('applies_to', [])
            if self.worker_type not in applies_to:
                continue

            penalties[penalty_name] = penalty
        ruleset.penalties = penalties
        ruleset.configuration = config

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
