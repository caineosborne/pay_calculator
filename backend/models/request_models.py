"""
Request models for the pay calculator API.

This module defines the data structures for incoming requests, including:
- Shift: Individual shift details including start/end times and breaks
- PayRequest: Complete request containing hourly rate and list of shifts

These models use Pydantic for automatic validation and type checking.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class WorkerType(str, Enum):
    """
    Enum for worker types.
    
    Values:
        SHIFT: Shift worker with overtime and penalty rates
        DAY: Day worker with different calculation rules
    """
    SHIFT = "shift"
    DAY = "day"

class AwardType(str, Enum):
    """
    Enum for award types.
    
    Values:
        AGED_CARE: Aged Care Award
        HOSPITALITY: Hospitality Award
        CHILD_CARE: Child Care Award
        NURSES_AWARD: Nurses & Midwives Award
        EB11: Queensland Health EB11
    """
    AGED_CARE = "aged_care"
    HOSPITALITY = "hospitality"
    CHILD_CARE = "child_care"
    NURSES_AWARD = "nurses_award"
    EB11 = "eb11"

class EmploymentType(str, Enum):
    """
    Enum for employment types.
    
    Values:
        FULL_TIME: Full-time employment
        PART_TIME: Part-time employment
        CASUAL: Casual employment
    """
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CASUAL = "casual"

class Shift(BaseModel):
    """
    Represents a single work shift.
    
    Attributes:
        day (str): Day of the week
        start (Optional[int]): Start hour (0-23)
        end (Optional[int]): End hour (0-23)
        break_duration (Optional[float]): Break duration in hours, defaults to 0.5
    """
    day: str
    start: Optional[int] = Field(None, ge=0, le=47)  # Allow times up to 47 (24 + 23) for next day shifts
    end: Optional[int] = Field(None, ge=0, le=47)    # Allow times up to 47 (24 + 23) for next day shifts
    break_duration: Optional[float] = Field(default=0.5, ge=0, le=24)

class PayRequest(BaseModel):
    """
    Complete pay calculation request.
    
    Attributes:
        hourly_rate (float): Base hourly rate
        worker_type (WorkerType): Type of worker (shift or day)
        award (AwardType): Type of award (aged_care or hospitality)
        employment_type (EmploymentType): Type of employment (full_time, part_time, casual)
        contracted_hours (Optional[float]): Contracted hours per week (required for part_time)
        shifts (List[Shift]): List of shifts to calculate pay for
    """
    hourly_rate: float = Field(gt=0)
    worker_type: WorkerType = Field(default=WorkerType.SHIFT)
    award: AwardType = Field(default=AwardType.HOSPITALITY)
    employment_type: EmploymentType = Field(default=EmploymentType.FULL_TIME)
    contracted_hours: Optional[float] = None
    shifts: List[Shift]