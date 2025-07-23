"""
Rule factory for selecting appropriate award rules.

This module provides a factory function that returns the appropriate rule set
based on the specified award type.
"""

from .aged_care_rules import AgedCareRules
from .hospitality_rules import HospitalityRules
from .child_care_rules import ChildCareRules

def get_rules_for_award(award: str):
    """
    Factory function to get the appropriate rule set based on award type.
    
    Args:
        award: String identifier for the award ('aged_care', 'hospitality', or 'child_care')
        
    Returns:
        Rule class for the specified award
    """
    award_map = {
        'aged_care': AgedCareRules,
        'hospitality': HospitalityRules,
        'child_care': ChildCareRules,
    }
    
    # Default to hospitality if award not found
    return award_map.get(award.lower(), HospitalityRules)
