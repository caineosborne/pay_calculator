"""
Rule factory for selecting appropriate award rules.

This module provides a factory function that returns the appropriate rule set
based on the specified award type.
"""

from importlib import import_module

from services.award_registry import default_award_key, load_awards
from services.rule_configurations import (
    BUILTIN_ID_PREFIX,
    RuleConfigurationError,
    load_custom_rule_class,
)


def _build_award_map() -> dict[str, type]:
    award_map = {}
    for award in load_awards():
        module = import_module(f"services.rules.{award['module']}")
        award_map[award["key"]] = getattr(module, award["class_name"])
    return award_map

def get_rules_for_award(award: str, configuration_identifier: str | None = None):
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
                configuration_identifier, normalized_award
            )

    award_map = _build_award_map()

    # Default to the configured default award if not found
    return award_map.get(normalized_award, award_map[default_award_key()])
