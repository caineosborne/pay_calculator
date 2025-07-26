"""
Rule engine for Nurses pay calculations.
This module imports and re-exports rules for various nursing awards and agreements.
"""

from .nurses_award_rules import NursesAwardRules
from .eb11_rules import EB11Rules

# Re-export the classes for backward compatibility
__all__ = ['NursesAwardRules', 'EB11Rules']