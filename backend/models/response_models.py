"""
Response models for the pay calculator API.

This module defines the structure of API responses, ensuring consistent
output format and type safety. The PayResponse model includes all necessary
fields for displaying pay calculation results to the user.
"""

from pydantic import BaseModel
from typing import Dict

class PayResponse(BaseModel):
    """
    Response containing all pay calculation results.
    
    Attributes:
        total_hours (float): Total hours worked
        total_pay (float): Total pay including all rates
        daily_breakdown (Dict[str, dict]): Detailed breakdown per day
        ordinary_hours (float): Regular hours worked
        overtime_hours (float): Overtime hours worked
        ordinary_pay (float): Pay at regular rate
        overtime_pay (float): Pay at overtime rate
        penalty_pay (float): Additional penalty rate pay
    """
    total_hours: float
    total_pay: float
    daily_breakdown: Dict[str, dict]
    ordinary_hours: float
    overtime_hours: float
    ordinary_pay: float
    overtime_pay: float
    penalty_pay: float