"""
Rule factory for selecting appropriate award rules.

This module provides a factory function that returns the appropriate rule set
based on the specified award type.
"""

from .aged_care_rules import AgedCareRules
from .hospitality_rules import HospitalityRules
from .child_care_rules import ChildCareRules
from .nurses_award_rules import NursesAwardRules
from .eb11_rules import EB11Rules

def get_rules_for_award(award: str):
    """
    Factory function to get the appropriate rule set based on award type.
    
    Args:
        award: String identifier for the award ('aged_care', 'hospitality', 'child_care', 
        'nurses_award', or 'eb11')
        
    Returns:
        Rule class for the specified award
    """
    award_map = {
        'aged_care': AgedCareRules,
        'hospitality': HospitalityRules,
        'child_care': ChildCareRules,
        'nurses_award': NursesAwardRules,
        'eb11': EB11Rules,
    }
    
    # Default to hospitality if award not found
    return award_map.get(award.lower(), HospitalityRules)
