"""
Rule factory for selecting appropriate award rules.

This module provides a factory function that returns the appropriate rule set
based on the specified award type.
"""

from importlib import import_module

from services.award_registry import load_awards


def _build_award_map() -> dict[str, type]:
    award_map = {}
    for award in load_awards():
        module = import_module(f"services.rules.{award['module']}")
        award_map[award["key"].lower()] = getattr(module, award["class_name"])
    return award_map

def get_rules_for_award(award: str):
    """
    Factory function to get the appropriate rule set based on award type.
    
    Args:
        award: String identifier for the award
        
    Returns:
        Rule class for the specified award
    """
    award_map = _build_award_map()
    
    normalized_award = award.lower() if isinstance(award, str) else ""
    try:
        return award_map[normalized_award]
    except KeyError as exc:
        raise ValueError(f"Unknown award: {award!r}") from exc
