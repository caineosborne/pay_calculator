"""Request and response contracts for date-based academic activity pay."""

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class AcademicEligibility(str, Enum):
    STANDARD = "standard"
    RELEVANT_PHD = "relevant_phd"
    FULL_COORDINATOR = "full_coordinator"


class AcademicWorkKind(str, Enum):
    ACTIVITY = "activity"
    DIRECT_HOURS = "direct_hours"


class AcademicCourse(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=100)
    name: str | None = Field(default=None, max_length=200)
    eligibility: AcademicEligibility = AcademicEligibility.STANDARD


class AcademicWorkItem(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    kind: AcademicWorkKind
    date: date
    occasion_id: str = Field(min_length=1, max_length=100)
    course_id: str | None = Field(default=None, max_length=100)
    topic: str | None = Field(default=None, max_length=300)
    activity: str = Field(min_length=1, max_length=100)
    variant: str | None = Field(default=None, max_length=100)
    delivered_quantity: float | None = Field(default=None, gt=0, le=24)
    actual_hours: float | None = Field(default=None, gt=0, le=24)
    actual_associated_hours: float | None = Field(default=None, ge=0, le=200)
    required_or_approved: bool = False
    classification_override: str | None = Field(default=None, pattern="^(original|repeat)$")
    override_reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_kind_fields(self):
        if self.kind == AcademicWorkKind.ACTIVITY and self.delivered_quantity is None:
            raise ValueError("Activity work requires delivered_quantity.")
        if self.kind == AcademicWorkKind.DIRECT_HOURS and self.actual_hours is None:
            raise ValueError("Direct-hours work requires actual_hours.")
        if self.classification_override and not (self.override_reason or "").strip():
            raise ValueError("A classification override requires a reason.")
        return self


class AcademicPayRequest(BaseModel):
    scheme: str = Field(min_length=1, max_length=100)
    period_start: date
    courses: list[AcademicCourse]
    work_items: list[AcademicWorkItem]
    lookback_items: list[AcademicWorkItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_start.weekday() != 0:
            raise ValueError("Academic pay periods must start on a Monday.")
        period_end = self.period_start.fromordinal(self.period_start.toordinal() + 13)
        lookback_start = self.period_start.fromordinal(self.period_start.toordinal() - 7)
        for item in self.work_items:
            if not self.period_start <= item.date <= period_end:
                raise ValueError(f"Work item {item.id!r} is outside the selected fortnight.")
        for item in self.lookback_items:
            if not lookback_start <= item.date < self.period_start:
                raise ValueError(f"Lookback item {item.id!r} must be in the preceding seven days.")
        ids = [item.id for item in [*self.lookback_items, *self.work_items]]
        if len(ids) != len(set(ids)):
            raise ValueError("Academic work item IDs must be unique.")
        course_ids = [course.id for course in self.courses]
        if len(course_ids) != len(set(course_ids)):
            raise ValueError("Academic course IDs must be unique.")
        return self


class AcademicLineResult(BaseModel):
    id: str
    date: date
    occasion_id: str
    course_id: str | None
    course_code: str | None
    topic: str | None
    activity: str
    activity_label: str
    variant: str
    payment_basis: str
    automatic_classification: str
    final_classification: str
    classification_label: str
    repeat_match_id: str | None = None
    classification_reason: str
    override_reason: str | None = None
    rate_code: str
    rate: float
    rate_effective_from: date
    quantity: float
    quantity_label: str
    incorporated_hours: float
    actual_associated_hours: float | None = None
    associated_hours_variance: float | None = None
    paid_hours: float
    pay: float
    warnings: list[str] = Field(default_factory=list)


class AcademicOccasionResult(BaseModel):
    occasion_id: str
    date: date
    credited_hours: float
    minimum_hours: float
    shortfall_hours: float
    item_ids: list[str]


class AcademicPayResponse(BaseModel):
    scheme: str
    scheme_label: str
    period_start: date
    period_end: date
    line_items: list[AcademicLineResult]
    occasions: list[AcademicOccasionResult]
    activity_pay: float
    direct_hours_pay: float
    total_pay: float
    delivered_hours: float
    direct_hours: float
    incorporated_hours: float
    actual_associated_hours: float
    review_warnings: list[str]
    ruleset: dict[str, Any]
