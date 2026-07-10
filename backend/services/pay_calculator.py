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
        
        # Set the active award rules
        award = data.award.value if hasattr(data.award, 'value') else data.award
        PayRules.set_award(award)
        
        # Get employment type and contracted hours
        self.employment_type = data.employment_type.value if hasattr(data.employment_type, 'value') else data.employment_type
        self.contracted_hours = data.contracted_hours
        self.period_weeks = 2
        
        self.total_hours = 0
        self.total_ordinary_hours = 0
        self.total_daily_overtime = 0
        self.total_penalty_hours = 0
        self.total_topup_hours = 0  # For contracted hours top-up
        self.breakdown = {}
        self.ordered_days = []
        
        # For tracking the previous shift end time and day (needed for gap penalty)
        self.previous_shift_end = None
        self.previous_shift_day = None

    def calculate_daily_hours(self, shift: Shift) -> dict:
        """Calculate hours breakdown for a single shift.
        
        This follows a three-phase calculation:
        1. Detect if hours are overtime (span, daily limit, weekly limit, or weekend for day workers)
        2. Calculate overtime rates (2x on Sunday, 1.5x otherwise)
        3. For remaining ordinary hours, calculate penalties for shift workers on weekends
        4. Apply gap penalty if this shift starts too soon after the previous one (Aged Care award only)
        """
        if not (shift.start is not None and shift.end is not None):
            return self._get_empty_day_breakdown()

        rules = PayRules.get_active_rules()
        break_duration = shift.break_duration if shift.break_duration is not None else rules.DEFAULT_BREAK
        end_time = shift.end if shift.end > shift.start else shift.end + 24
        daily_hours = max(0, (end_time - shift.start) - break_duration)
        
        applied_rules = []
        
        # Phase 1: Detect overtime conditions
        overtime_hours = 0
        ordinary_hours = daily_hours
        
        # 1a. Day workers: All weekend hours are overtime
        if PayRules.is_overtime_day(shift.day, self.worker_type):
            overtime_hours = daily_hours
            ordinary_hours = 0
            applied_rules.append(f"{shift.day} Overtime")
        else:
            # 1b. Check for span overtime (after 6pm for day workers)
            span_ot = PayRules.calculate_span_overtime(shift.start, shift.end, daily_hours, self.worker_type)
            if span_ot > 0:
                overtime_hours += span_ot
                ordinary_hours -= span_ot
                applied_rules.append("Span Overtime")
            
            # 1c. Check daily hours limit
            daily_limit = PayRules.get_ordinary_hours_daily_limit(self.worker_type)
            if ordinary_hours > daily_limit:
                daily_ot = ordinary_hours - daily_limit
                overtime_hours += daily_ot
                ordinary_hours = daily_limit
                applied_rules.append("Daily Overtime")
        
        # Phase 2: Apply appropriate overtime rate
        # Note: Weekly overtime is handled in process_weekly_overtime
        overtime_rate = PayRules.get_overtime_rate(shift.day, overtime_hours) if overtime_hours > 0 else 0
        
        # Phase 3: Calculate penalties (unified approach)
        # First, get weekend penalties if applicable
        penalty_rate = PayRules.get_penalty_rate(shift.day, self.worker_type)
        penalty_hours = ordinary_hours if penalty_rate > 0 else 0
        if penalty_hours > 0:
            applied_rules.append(f"{shift.day} Penalty ({int(penalty_rate * 100)}%)")
        
        # Then, calculate all other penalties using the unified approach
        all_penalties = PayRules.calculate_penalties(shift.start, end_time, shift.day, self.worker_type)
        
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
        
        # For backward compatibility, also calculate using the old methods
        if not all_penalties:
            # Legacy Phase 4: Apply shift start penalties for Aged Care shift workers
            shift_penalty = PayRules.calculate_shift_start_penalty(shift.start, self.worker_type)
            shift_penalty_rate = shift_penalty.get('penalty_rate', 0)
            shift_penalty_hours = ordinary_hours if shift_penalty.get('applies', False) else 0
            
            if shift_penalty_hours > 0:
                applied_rules.append(shift_penalty.get('description', ''))
            
            # Legacy Phase 5: Apply hourly penalties for Hospitality workers (both day and shift)
            hourly_penalties = PayRules.calculate_hourly_penalties(shift.start, end_time, shift.day)
            hourly_penalty_details = hourly_penalties
            for penalty in hourly_penalties:
                applied_rules.append(penalty.get('description', ''))
        
        # Phase 6: Check for gap penalty (applied across all award types)
        gap_penalty = {'applies': False, 'penalty_rate': 0}
        if self.previous_shift_end is not None and self.previous_shift_day is not None:
            gap_penalty = PayRules.check_shift_gap_penalty(
                shift.start, 
                self.previous_shift_end,
                shift.day,
                self.previous_shift_day
            )
            
        # Store the end time and day of this shift for future gap penalty calculations
        self.previous_shift_end = end_time
        self.previous_shift_day = shift.day
        
        # Apply gap penalty if applicable
        gap_penalty_rate = gap_penalty.get('penalty_rate', 0)
        gap_penalty_hours = ordinary_hours if gap_penalty.get('applies', False) else 0
        
        if gap_penalty_hours > 0:
            applied_rules.append(f"Gap Penalty ({int(gap_penalty_rate * 100)}%)")
        
        return {
            'total': daily_hours,
            'ordinary': ordinary_hours,
            'overtime': overtime_hours,
            'penalty': penalty_hours,
            'penalty_rate': penalty_rate,
            'overtime_rate': overtime_rate,
            'break': break_duration,
            'gap_penalty': gap_penalty_hours,
            'gap_penalty_rate': gap_penalty_rate,
            'shift_penalty': shift_penalty_hours,
            'shift_penalty_rate': shift_penalty_rate,
            'hourly_penalties': hourly_penalty_details,
            'topup': 0,  # Initialize topup to 0
            'applied_rules': applied_rules
        }

    def _get_empty_day_breakdown(self) -> dict:
        """
        Get default values for a day with no hours.
        
        Returns:
            dict: Default breakdown structure with zero values
        """
        rules = PayRules.get_active_rules()
        return {
            'total': 0,
            'ordinary': 0,
            'overtime': 0,
            'penalty': 0,
            'gap_penalty': 0,
            'gap_penalty_rate': 0,
            'shift_penalty': 0,
            'shift_penalty_rate': 0,
            'hourly_penalties': [],
            'topup': 0,  # Add topup field
            'break': rules.DEFAULT_BREAK,
            'applied_rules': []
        }

    def process_weekly_overtime(self) -> None:
        """
        Process fortnightly overtime after all daily calculations.
        
        Adjusts daily breakdowns to account for the fortnightly overtime limit,
        working backwards from the end of the fortnight.
        
        When hours are converted from ordinary to overtime:
        1. They lose any penalty rates they had (penalty hours are reduced)
        2. They get the appropriate overtime rate for that day (1.5x or 2x)
        """
        rules = PayRules.get_active_rules()
        
        # Get weekly limit based on worker type, employment type, and contracted hours
        weekly_limit = PayRules.calculate_weekly_ordinary_hours(
            self.total_ordinary_hours, 
            self.worker_type,
            self.employment_type,
            self.contracted_hours,
            self.period_weeks
        )
        
        weekly_overtime_remaining = max(self.total_ordinary_hours - weekly_limit, 0)
        
        if weekly_overtime_remaining > 0:
            for day in reversed(self.ordered_days):
                daily_ordinary = self.breakdown[day]['ordinary']
                overtime_from_ordinary = min(daily_ordinary, weekly_overtime_remaining)
                
                if overtime_from_ordinary > 0:
                    self.breakdown[day]['ordinary'] -= overtime_from_ordinary
                    self.breakdown[day]['overtime'] += overtime_from_ordinary
                    
                    # Remove these hours from penalty if they were getting penalties
                    if self.breakdown[day]['penalty'] > 0:
                        self.breakdown[day]['penalty'] -= overtime_from_ordinary
                    
                    # Set the overtime rate for the day (2x for Sunday, 1.5x otherwise)
                    # For two-tier overtime, we need to pass the current amount of overtime
                    current_overtime = self.breakdown[day]['overtime']
                    self.breakdown[day]['overtime_rate'] = PayRules.get_overtime_rate(day, current_overtime)
                    
                    if 'Period Overtime' not in self.breakdown[day]['applied_rules']:
                        self.breakdown[day]['applied_rules'].append('Period Overtime')
                    weekly_overtime_remaining -= overtime_from_ordinary

                if weekly_overtime_remaining == 0:
                    break
                    
    def process_contracted_hours_topup(self) -> None:
        """
        Process contracted hours top-up after all other calculations.
        
        If an employee is entitled to contracted hours and has worked less than their contracted hours,
        adds a top-up to reach the contracted hours.
        """
        rules = PayRules.get_active_rules()
        
        # Check if employee is entitled to contracted hours top-up
        is_entitled = False
        if self.employment_type == 'part_time' and hasattr(rules, 'PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP'):
            is_entitled = rules.PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP
        elif self.employment_type == 'full_time' and hasattr(rules, 'FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP'):
            is_entitled = rules.FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP
            
        # If not entitled or no contracted hours, return
        if not is_entitled or not self.contracted_hours:
            return
            
        # Calculate ordinary hours (after overtime processing)
        ordinary_hours = 0
        for day in self.breakdown:
            ordinary_hours += self.breakdown[day]['ordinary']
            
        # Calculate top-up hours needed
        topup_hours = max(0, (self.contracted_hours * self.period_weeks) - ordinary_hours)
        if topup_hours <= 0:
            return
            
        # Add top-up hours to the breakdown
        # We'll add it to the last day as a separate entry
        if self.ordered_days:
            last_day = self.ordered_days[-1]
            self.breakdown[last_day]['topup'] = topup_hours
            if 'Contracted Hours Top-up' not in self.breakdown[last_day]['applied_rules']:
                self.breakdown[last_day]['applied_rules'].append('Contracted Hours Top-up')
        else:
            # If no days worked, create a dummy entry for Monday
            self.breakdown['Week 1 - Monday'] = self._get_empty_day_breakdown()
            self.breakdown['Week 1 - Monday']['topup'] = topup_hours
            self.breakdown['Week 1 - Monday']['applied_rules'].append('Contracted Hours Top-up')
            self.ordered_days.append('Week 1 - Monday')
            
        # Update total top-up hours
        self.total_topup_hours = topup_hours

    def calculate_pay(self) -> PayResponse:
        """
        Main method to calculate all pay components.
        
        Processes all shifts, calculates various pay rates,
        and produces final breakdown of pay and hours.
        
        Returns:
            PayResponse: Complete calculation results
        """
        # Process each shift
        for shift in self.data.shifts:
            day_breakdown = self.calculate_daily_hours(shift)
            breakdown_key = f"Week {shift.week} - {shift.day}"
            
            if day_breakdown['total'] > 0:
                self.ordered_days.append(breakdown_key)
                self.total_ordinary_hours += day_breakdown['ordinary']
                self.total_daily_overtime += day_breakdown['overtime']
                self.total_penalty_hours += day_breakdown['penalty']
                # Add gap penalty hours to penalty hours total if applicable
                if day_breakdown.get('gap_penalty', 0) > 0:
                    self.total_penalty_hours += day_breakdown['gap_penalty']
                self.total_hours += day_breakdown['total']
            
            self.breakdown[breakdown_key] = day_breakdown

        # Process weekly overtime
        self.process_weekly_overtime()

        # Process contracted hours top-up
        self.process_contracted_hours_topup()

        # Calculate final totals using the employment type and contracted hours
        weekly_limit = PayRules.calculate_weekly_ordinary_hours(
            self.total_ordinary_hours, 
            self.worker_type,
            self.employment_type,
            self.contracted_hours,
            self.period_weeks
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
        
        # Calculate overtime pay using day-specific rates
        rules = PayRules.get_active_rules()
        overtime_pay = sum(
            self.breakdown[day]['overtime'] * self.data.hourly_rate * self.breakdown[day].get('overtime_rate', rules.STANDARD_OVERTIME_RATE)
            for day in self.breakdown
        )
        overtime_pay = round(overtime_pay, 2)
        
        # Calculate penalty pay (only applies to shift workers)
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
        for day in self.breakdown:
            for penalty in self.breakdown[day].get('hourly_penalties', []):
                hourly_penalty_pay += penalty.get('hours', 0) * self.data.hourly_rate * penalty.get('rate', 0)
        hourly_penalty_pay = round(hourly_penalty_pay, 2)
        
        # Combine all penalty types for total penalty pay
        total_penalty_pay = round(penalty_pay + gap_penalty_pay + shift_penalty_pay + hourly_penalty_pay, 2)
        
        # Include topup_pay in total_pay
        total_pay = round(ordinary_pay + overtime_pay + total_penalty_pay + topup_pay, 2)

        # Generate ruleset summary based on worker type
        rules = PayRules.get_active_rules()
        
        # Handle span hours display based on whether the award uses span overtime
        span_hours_display = "N/A"
        span_rate_display = "N/A"
        
        if hasattr(rules, 'APPLY_SPAN_OVERTIME'):
            if rules.APPLY_SPAN_OVERTIME and self.worker_type == 'day':
                span_hours_display = f"After {rules.SPAN_OVERTIME_HOUR}:00"
                span_rate_display = f"{rules.STANDARD_OVERTIME_RATE}x"
        elif hasattr(rules, 'SPAN_OVERTIME_HOUR') and self.worker_type == 'day':
            span_hours_display = f"After {rules.SPAN_OVERTIME_HOUR}:00"
            span_rate_display = f"{rules.STANDARD_OVERTIME_RATE}x"
            
        # Determine the appropriate weekly overtime threshold for the ruleset summary
        weekly_overtime_threshold = rules.ORDINARY_HOURS_LIMIT_WEEKLY * self.period_weeks
        if self.worker_type == 'day':
            weekly_overtime_threshold = rules.DAY_WORKER_ORDINARY_HOURS_WEEKLY * self.period_weeks
        elif self.employment_type == 'part_time' and self.contracted_hours is not None:
            if hasattr(rules, 'USE_CONTRACTED_HOURS_FOR_PT_OVERTIME') and rules.USE_CONTRACTED_HOURS_FOR_PT_OVERTIME:
                weekly_overtime_threshold = self.contracted_hours * self.period_weeks
            
        # Get the contracted hours top-up settings
        pt_entitled_to_topup = getattr(rules, 'PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP', False)
        ft_entitled_to_topup = getattr(rules, 'FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP', False)
        
        ruleset = RulesetSummary(
            span_hours={
                'threshold': span_hours_display,
                'rate': span_rate_display
            },
            daily_overtime={
                'threshold': rules.ORDINARY_HOURS_LIMIT_DAILY if self.worker_type == 'shift' else rules.DAY_WORKER_ORDINARY_HOURS_DAILY,
                'rate': f"{rules.STANDARD_OVERTIME_RATE}x"
            },
            weekly_overtime={
                'threshold': weekly_overtime_threshold,
                'rate': f"{rules.STANDARD_OVERTIME_RATE}x"
            },
            # Handle weekend rules structure for older vs. newer rule formats
            # Some rules have WEEKEND_RULES organized by worker type first, others by day first
            saturday_rules=(rules.WEEKEND_RULES[self.worker_type]['Saturday'] 
                          if self.worker_type in rules.WEEKEND_RULES 
                          else rules.WEEKEND_RULES.get('Saturday', {})),
            sunday_rules=(rules.WEEKEND_RULES[self.worker_type]['Sunday'] 
                        if self.worker_type in rules.WEEKEND_RULES 
                        else rules.WEEKEND_RULES.get('Sunday', {})),
            employment_type=self.employment_type,
            contracted_hours=self.contracted_hours,
            use_contracted_hours_for_overtime=getattr(rules, 'USE_CONTRACTED_HOURS_FOR_PT_OVERTIME', False),
            pt_employees_entitled_to_contracted_topup=pt_entitled_to_topup,
            ft_employees_entitled_to_contracted_topup=ft_entitled_to_topup
        )
        
        # Add gap penalty rule if applicable (Aged Care award only)
        if hasattr(rules, 'GAP_PENALTY_HOURS'):
            ruleset.gap_penalty = {
                'threshold': f"Less than {rules.GAP_PENALTY_HOURS} hours between shifts",
                'rate': f"{rules.GAP_PENALTY_RATE}x penalty"
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
            applied_rules=ruleset
        )

    def calculate_daily_pay(self, hours: dict) -> dict:
        """Calculate pay breakdown for a day."""
        base_rate = self.hourly_rate
        penalty_rate = hours.get('penalty_rate', 0)
        overtime_rate = hours.get('overtime_rate', PayRules.get_active_rules().STANDARD_OVERTIME_RATE)
        
        ordinary_pay = hours['ordinary'] * base_rate
        overtime_pay = hours['overtime'] * base_rate * overtime_rate
        penalty_pay = hours['penalty'] * base_rate * penalty_rate
        
        return {
            'ordinary_pay': ordinary_pay,
            'overtime_pay': overtime_pay,
            'penalty_pay': penalty_pay,
            'total_pay': ordinary_pay + overtime_pay + penalty_pay
        }
