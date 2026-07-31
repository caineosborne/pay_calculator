"""API models for editable rule configurations."""

from pydantic import BaseModel, Field


class RuleSourceValidationRequest(BaseModel):
    base_award: str
    source: str


class CreateRuleConfigurationRequest(RuleSourceValidationRequest):
    name: str = Field(min_length=1, max_length=100)


class UpdateRuleConfigurationRequest(BaseModel):
    source: str
