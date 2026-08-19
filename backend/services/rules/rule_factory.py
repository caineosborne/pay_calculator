"""
Rule factory for selecting appropriate award rules.

This module provides a factory function that returns the appropriate rule set
based on the specified award type.
"""

from importlib import import_module
import uuid

from services.award_registry import load_awards
from services.rule_configurations import (
    BUILTIN_ID_PREFIX,
    RuleConfigurationError,
    load_custom_rule_class,
)
# Built-ins are immutable modules, so resolve them once when the service starts.
BUILTIN_RULES = {}
for award_definition in load_awards():
    if award_definition.get("calculator_mode", "shift") != "shift":
        continue
    award_module = import_module(
        f"services.rules.{award_definition['module']}"
    )
    rule_class = getattr(
        award_module,
        award_definition["class_name"],
    )
    BUILTIN_RULES[award_definition["key"]] = rule_class


def get_rules_for_award(
    award: str,
    configuration_identifier: str | None = None,
    owner_id: uuid.UUID | None = None,
):
    """
    Factory function to get the appropriate rule set based on award type.
    
    Args:
        award: String identifier for the award
        configuration_identifier: Optional built-in or custom configuration ID
        
    Returns:
        Rule class for the specified award
    """
    normalized_award = award.lower()
    if configuration_identifier:
        if configuration_identifier.startswith(BUILTIN_ID_PREFIX):
            configured_award = configuration_identifier.removeprefix(
                BUILTIN_ID_PREFIX
            )
            if configured_award != normalized_award:
                raise RuleConfigurationError(
                    "The selected configuration does not belong to the "
                    "requested award."
                )
        else:
            return load_custom_rule_class(
                configuration_identifier, normalized_award, owner_id
            )

    try:
        return BUILTIN_RULES[normalized_award]
    except KeyError as error:
        raise ValueError(f"Unknown award: {award!r}") from error
