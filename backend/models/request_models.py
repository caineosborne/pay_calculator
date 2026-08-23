"""
Request models for the pay calculator API.

This module defines the data structures for incoming requests, including:
- Shift: Individual shift details including start/end times and breaks
- PayRequest: Complete request containing hourly rate and list of shifts

These models use Pydantic for automatic validation and type checking.
"""

from pydantic import BaseModel, Field
from typing import Any, List, Optional
from enum import Enum

from services.award_registry import award_keys

class WorkerType(str, Enum):
    """
    Enum for worker types.
    
    Values:
        SHIFT: Shift worker with overtime and penalty rates
        DAY: Day worker with different calculation rules
    """
    SHIFT = "shift"
    DAY = "day"

def _enum_name(value: str) -> str:
    return value.upper().replace("-", "_")


AwardType = Enum(
    "AwardType",
    {_enum_name(award_key): award_key for award_key in award_keys()},
    type=str,
)

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
        start (Optional[float]): Start time in decimal hours (0-47)
        end (Optional[float]): End time in decimal hours (0-47)
        break_duration (Optional[float]): Break duration in hours, defaults to 0.5
    """
    day: str
    week: int = Field(default=1, ge=1, le=2)
    # Decimal hours preserve minute-level entries: 09:15 is sent as 9.25.
    # Values over 24 retain support for explicitly entered next-day times.
    start: Optional[float] = Field(None, ge=0, le=47)
    end: Optional[float] = Field(None, ge=0, le=47)
    break_duration: Optional[float] = Field(default=0.5, ge=0, le=24)
    # Public-holiday status belongs to an individual attendance segment. This
    # allows two segments on the same day to be treated differently.
    public_holiday: bool = False
    # The frontend uses this only when a single rostered shift is split around
    # an entered unpaid lunch. These are attendance segments, not engagements.
    minimum_engagement_exempt: bool = False
    manual_overtime: bool = False
    manual_ordinary: bool = False


class WorkdayReference(BaseModel):
    """A manually selected logical workday, used for public holidays."""
    week: int = Field(ge=1, le=2)
    day: str

class PayRequest(BaseModel):
    """
    Complete pay calculation request.
    
    Attributes:
        hourly_rate (float): Base hourly rate
        worker_type (WorkerType): Type of worker (shift or day)
        award (AwardType): Type of award
        employment_type (EmploymentType): Type of employment (full_time, part_time, casual)
        contracted_hours (Optional[float]): Contracted hours per week (required for part_time)
        shifts (List[Shift]): List of shifts to calculate pay for
    """
    hourly_rate: float = Field(gt=0)
    worker_type: WorkerType = Field(default=WorkerType.SHIFT)
    award: AwardType
    employment_type: EmploymentType = Field(default=EmploymentType.FULL_TIME)
    contracted_hours: Optional[float] = None
    rule_configuration: Optional[str] = Field(default=None, max_length=200)
    # Unsaved editor values may be evaluated for this request only. They are
    # validated and converted to literal rule dictionaries; nothing is stored.
    rule_source: Optional[str] = Field(default=None, max_length=500_000)
    rule_questionnaire: Optional[dict[str, Any]] = None
    shifts: List[Shift]
    public_holidays: List[WorkdayReference] = Field(default_factory=list)
