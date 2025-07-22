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
            data (PayRequest): Contains hourly rate, worker type, and shifts to process
        """
        self.data = data
        self.worker_type = data.worker_type.value if hasattr(data.worker_type, 'value') else data.worker_type
        self.total_hours = 0
        self.total_ordinary_hours = 0
        self.total_daily_overtime = 0
        self.total_penalty_hours = 0
        self.breakdown = {}
        self.ordered_days = []

    def calculate_daily_hours(self, shift: Shift) -> dict:
        """Calculate hours breakdown for a single shift.
        
        This follows a three-phase calculation:
        1. Detect if hours are overtime (span, daily limit, weekly limit, or weekend for day workers)
        2. Calculate overtime rates (2x on Sunday, 1.5x otherwise)
        3. For remaining ordinary hours, calculate penalties for shift workers on weekends
        """
        if not (shift.start is not None and shift.end is not None):
            return self._get_empty_day_breakdown()

        break_duration = shift.break_duration if shift.break_duration is not None else PayRules.DEFAULT_BREAK
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
        overtime_rate = PayRules.get_overtime_rate(shift.day) if overtime_hours > 0 else 0
        
        # Phase 3: For shift workers, calculate penalties on ordinary hours
        penalty_rate = PayRules.get_penalty_rate(shift.day, self.worker_type)
        penalty_hours = ordinary_hours if penalty_rate > 0 else 0
        if penalty_hours > 0:
            applied_rules.append(f"{shift.day} Penalty ({int(penalty_rate * 100)}%)")
        
        return {
            'total': daily_hours,
            'ordinary': ordinary_hours,
            'overtime': overtime_hours,
            'penalty': penalty_hours,
            'penalty_rate': penalty_rate,
            'overtime_rate': overtime_rate,
            'break': break_duration,
            'applied_rules': applied_rules
        }

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
            'break': PayRules.DEFAULT_BREAK,
            'applied_rules': []
        }

    def process_weekly_overtime(self) -> None:
        """
        Process weekly overtime after all daily calculations.
        
        Adjusts daily breakdowns to account for weekly overtime limits,
        working backwards from the end of the week.
        
        When hours are converted from ordinary to overtime:
        1. They lose any penalty rates they had (penalty hours are reduced)
        2. They get the appropriate overtime rate for that day (1.5x or 2x)
        """
        weekly_limit = PayRules.DAY_WORKER_ORDINARY_HOURS_WEEKLY if self.worker_type == 'day' else PayRules.ORDINARY_HOURS_LIMIT_WEEKLY
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
                    self.breakdown[day]['overtime_rate'] = PayRules.get_overtime_rate(day)
                    
                    if 'Period Overtime' not in self.breakdown[day]['applied_rules']:
                        self.breakdown[day]['applied_rules'].append('Period Overtime')
                    weekly_overtime_remaining -= overtime_from_ordinary

                if weekly_overtime_remaining == 0:
                    break

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
            
            if day_breakdown['total'] > 0:
                self.ordered_days.append(shift.day)
                self.total_ordinary_hours += day_breakdown['ordinary']
                self.total_daily_overtime += day_breakdown['overtime']
                self.total_penalty_hours += day_breakdown['penalty']
                self.total_hours += day_breakdown['total']
            
            self.breakdown[shift.day] = day_breakdown

        # Process weekly overtime
        self.process_weekly_overtime()

        # Calculate final totals
        weekly_ordinary_hours = PayRules.calculate_weekly_ordinary_hours(self.total_ordinary_hours, self.worker_type)
        weekly_limit = PayRules.DAY_WORKER_ORDINARY_HOURS_WEEKLY if self.worker_type == 'day' else PayRules.ORDINARY_HOURS_LIMIT_WEEKLY
        total_overtime_hours = self.total_daily_overtime + max(self.total_ordinary_hours - weekly_limit, 0)

        # Calculate pay
        ordinary_pay = round(weekly_ordinary_hours * self.data.hourly_rate, 2)
        
        # Calculate overtime pay using day-specific rates
        overtime_pay = sum(
            self.breakdown[day]['overtime'] * self.data.hourly_rate * self.breakdown[day].get('overtime_rate', PayRules.STANDARD_OVERTIME_RATE)
            for day in self.breakdown
        )
        overtime_pay = round(overtime_pay, 2)
        
        # Calculate penalty pay (only applies to shift workers)
        penalty_pay = sum(
            self.breakdown[day].get('penalty', 0) * self.data.hourly_rate * self.breakdown[day].get('penalty_rate', 1.0)
            for day in self.breakdown
        )
        penalty_pay = round(penalty_pay, 2)
        
        total_pay = round(ordinary_pay + overtime_pay + penalty_pay, 2)

        # Generate ruleset summary based on worker type
        ruleset = RulesetSummary(
            span_hours={
                'threshold': f"After {PayRules.SPAN_OVERTIME_HOUR}:00",
                'rate': f"{PayRules.STANDARD_OVERTIME_RATE}x"
            },
            daily_overtime={
                'threshold': PayRules.ORDINARY_HOURS_LIMIT_DAILY if self.worker_type == 'shift' else PayRules.DAY_WORKER_ORDINARY_HOURS_DAILY,
                'rate': f"{PayRules.STANDARD_OVERTIME_RATE}x"
            },
            weekly_overtime={
                'threshold': PayRules.ORDINARY_HOURS_LIMIT_WEEKLY if self.worker_type == 'shift' else PayRules.DAY_WORKER_ORDINARY_HOURS_WEEKLY,
                'rate': f"{PayRules.STANDARD_OVERTIME_RATE}x"
            },
            saturday_rules=PayRules.WEEKEND_RULES[self.worker_type]['Saturday'],
            sunday_rules=PayRules.WEEKEND_RULES[self.worker_type]['Sunday']
        )

        return PayResponse(
            total_hours=round(self.total_hours, 2),
            total_pay=total_pay,
            daily_breakdown=self.breakdown,
            ordinary_hours=weekly_ordinary_hours,
            overtime_hours=total_overtime_hours,
            ordinary_pay=ordinary_pay,
            overtime_pay=overtime_pay,
            penalty_pay=penalty_pay,
            applied_rules=ruleset
        )

    def calculate_daily_pay(self, hours: dict) -> dict:
        """Calculate pay breakdown for a day."""
        base_rate = self.hourly_rate
        penalty_rate = hours.get('penalty_rate', 0)
        
        ordinary_pay = hours['ordinary'] * base_rate
        overtime_pay = hours['overtime'] * base_rate * PayRules.STANDARD_OVERTIME_RATE
        penalty_pay = hours['penalty'] * base_rate * penalty_rate
        
        return {
            'ordinary_pay': ordinary_pay,
            'overtime_pay': overtime_pay,
            'penalty_pay': penalty_pay,
            'total_pay': ordinary_pay + overtime_pay + penalty_pay
        }