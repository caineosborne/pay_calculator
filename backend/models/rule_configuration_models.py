"""API models for editable rule configurations."""

from typing import Any

from pydantic import BaseModel, Field


class RuleSourceValidationRequest(BaseModel):
    base_award: str
    source: str
    questionnaire: dict[str, Any] | None = None


class CreateRuleConfigurationRequest(RuleSourceValidationRequest):
    name: str = Field(min_length=1, max_length=100)


class UpdateRuleConfigurationRequest(BaseModel):
    source: str
    questionnaire: dict[str, Any] | None = None


class RenameRuleConfigurationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
