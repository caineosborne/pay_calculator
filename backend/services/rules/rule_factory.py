"""
Rule factory for selecting appropriate award rules.

This module provides a factory function that returns the appropriate rule set
based on the specified award type.
"""

from importlib import import_module

from services.award_registry import default_award_key, load_awards


def _build_award_map() -> dict[str, type]:
    award_map = {}
    for award in load_awards():
        module = import_module(f"services.rules.{award['module']}")
        award_map[award["key"]] = getattr(module, award["class_name"])
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
    
    # Default to the configured default award if not found
    return award_map.get(award.lower(), award_map[default_award_key()])
