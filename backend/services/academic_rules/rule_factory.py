"""Resolve registered academic activity rulesets without touching shift rules."""

from importlib import import_module

from services.award_registry import award_for_key


def get_academic_ruleset(scheme: str):
    definition = award_for_key(scheme)
    if definition.get("calculator_mode") != "academic_activity":
        raise ValueError(f"Calculator {scheme!r} is not an academic activity scheme.")
    module = import_module(
        f"services.academic_rules.{definition['module']}"
    )
    return getattr(module, definition["class_name"])
