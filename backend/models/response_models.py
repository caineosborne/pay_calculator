"""
Response models for the pay calculator API.

This module defines the structure of API responses, ensuring consistent
output format and type safety. The PayResponse model includes all necessary
fields for displaying pay calculation results to the user.
"""

from pydantic import BaseModel
from typing import Dict

class RulesetSummary(BaseModel):
    """
    Summary of pay rules applied for a worker type.
    
    Attributes:
        span_hours (dict): Rules for span hours overtime
        daily_overtime (dict): Rules for daily overtime
        weekly_overtime (dict): Rules for weekly overtime
        saturday_rules (dict): Rules for Saturday work
        sunday_rules (dict): Rules for Sunday work
        gap_penalty (dict, optional): Rules for minimum break between shifts
        penalties (dict, optional): Canonical penalty rules filtered by worker type
        configuration (dict, optional): Complete canonical award configuration
        employment_type (str, optional): Type of employment (full_time, part_time, casual)
        contracted_hours (float, optional): Contracted hours for part-time employees
        use_contracted_hours_for_overtime (bool, optional): Whether part-time employees get overtime after contracted hours
    """
    span_hours: dict
    daily_overtime: dict
    weekly_overtime: dict
    saturday_rules: dict
    sunday_rules: dict
    gap_penalty: dict = None
    penalties: dict = None
    configuration: dict = None
    employment_type: str = None
    contracted_hours: float | None = None
    use_contracted_hours_for_overtime: bool = None
    pt_employees_entitled_to_contracted_topup: bool = None
    ft_employees_entitled_to_contracted_topup: bool = None

class PayResponse(BaseModel):
    """
    Response containing all pay calculation results.
    
    Attributes:
        total_hours (float): Total hours worked
        total_pay (float): Total pay including all rates
        daily_breakdown (Dict[str, dict]): Detailed breakdown per day
        ordinary_hours (float): Regular hours worked
        overtime_hours (float): Overtime hours worked
        topup_hours (float): Contracted hours top-up
        ordinary_pay (float): Pay at regular rate
        overtime_pay (float): Pay at overtime rate
        topup_pay (float): Pay for contracted hours top-up
        penalty_pay (float): Additional penalty rate pay
        gap_penalty_pay (float, optional): Pay for a configured insufficient-gap loading
        shift_penalty_pay (float, optional): Pay for whole-shift penalties
        hourly_penalty_pay (float, optional): Pay for time-based penalties
        applied_rules (RulesetSummary): Summary of rules applied in calculation
    """
    total_hours: float
    total_pay: float
    daily_breakdown: Dict[str, dict]
    ordinary_hours: float
    overtime_hours: float
    topup_hours: float = 0.0
    ordinary_pay: float
    overtime_pay: float
    topup_pay: float = 0.0
    penalty_pay: float
    gap_penalty_pay: float = 0.0
    shift_penalty_pay: float = 0.0
    hourly_penalty_pay: float = 0.0
    time_based_penalty_hours: float = 0.0
    applied_rules: RulesetSummary
