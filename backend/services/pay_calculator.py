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

from ..models.request_models import PayRequest, Shift
from ..models.response_models import PayResponse
from .rule_engine import PayRules

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
        """Calculate hours breakdown for a single shift."""
        if not (shift.start is not None and shift.end is not None and shift.end > shift.start):
            return self._get_empty_day_breakdown()

        break_duration = shift.break_duration if shift.break_duration is not None else PayRules.DEFAULT_BREAK
        daily_hours = max(0, (shift.end - shift.start) - break_duration)
        
        applied_rules = []
        
        # Calculate span overtime (after 6pm for day workers)
        span_overtime = PayRules.calculate_span_overtime(shift.start, shift.end, daily_hours, self.worker_type)
        if span_overtime > 0:
            applied_rules.append("Span Overtime")
        remaining_hours = daily_hours - span_overtime
        
        # Get daily ordinary hours limit based on worker type
        daily_limit = PayRules.get_ordinary_hours_daily_limit(self.worker_type)
        daily_ordinary_hours = min(remaining_hours, daily_limit)
        daily_ot = max(remaining_hours - daily_limit, 0)
        if daily_ot > 0:
            applied_rules.append("Daily Overtime")
        daily_overtime = span_overtime + daily_ot
        
        # Get weekend rates based on worker type
        weekend_rules = PayRules.get_weekend_rate(shift.day, self.worker_type)
        
        # Initialize penalty hours to 0
        penalty_hours = 0
        
        # Handle weekend work differently for day workers (overtime) vs shift workers (penalties)
        if weekend_rules['is_overtime']:
            # For day workers, weekend work counts as overtime with specific rates
            daily_overtime += daily_ordinary_hours
            daily_ordinary_hours = 0
            applied_rules.append(f"{shift.day} Overtime")
        else:
            # For shift workers, apply penalty rates to ordinary hours
            penalty_rate = weekend_rules['penalty_rate']
            if penalty_rate > 0:
                penalty_hours = daily_ordinary_hours
                applied_rules.append(f"{shift.day} Penalty ({int(penalty_rate * 100)}%)")
            
        return {
            'total': daily_hours,
            'ordinary': daily_ordinary_hours,
            'overtime': daily_overtime,
            'penalty': penalty_hours,
            'penalty_rate': weekend_rules.get('penalty_rate', 0),
            'overtime_rate': weekend_rules.get('rate', PayRules.OVERTIME_RATE),
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
            self.breakdown[day]['overtime'] * self.data.hourly_rate * self.breakdown[day].get('overtime_rate', PayRules.OVERTIME_RATE)
            for day in self.breakdown
        )
        overtime_pay = round(overtime_pay, 2)
        
        # Calculate penalty pay (only applies to shift workers)
        penalty_pay = sum(
            self.breakdown[day]['penalty'] * self.data.hourly_rate * self.breakdown[day]['penalty_rate']
            for day in self.breakdown
        )
        penalty_pay = round(penalty_pay, 2)
        
        total_pay = round(ordinary_pay + overtime_pay + penalty_pay, 2)

        return PayResponse(
            total_hours=round(self.total_hours, 2),
            total_pay=total_pay,
            daily_breakdown=self.breakdown,
            ordinary_hours=weekly_ordinary_hours,
            overtime_hours=total_overtime_hours,
            ordinary_pay=ordinary_pay,
            overtime_pay=overtime_pay,
            penalty_pay=penalty_pay
        )

    def calculate_daily_pay(self, hours: dict) -> dict:
        """Calculate pay breakdown for a day."""
        base_rate = self.hourly_rate
        penalty_rate = hours.get('penalty_rate', 0)
        
        ordinary_pay = hours['ordinary'] * base_rate
        overtime_pay = hours['overtime'] * base_rate * PayRules.OVERTIME_RATE
        penalty_pay = hours['penalty'] * base_rate * penalty_rate
        
        return {
            'ordinary_pay': ordinary_pay,
            'overtime_pay': overtime_pay,
            'penalty_pay': penalty_pay,
            'total_pay': ordinary_pay + overtime_pay + penalty_pay
        }