"""
Shared award registry utilities.

This module reads the single source of truth for available awards from the
backend JSON registry so backend validation and frontend options stay aligned.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


AWARDS_REGISTRY_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "awards.json"
)
DISCLAIMERS_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "disclaimers.json"
)


@lru_cache(maxsize=1)
def load_awards() -> list[dict]:
    with AWARDS_REGISTRY_PATH.open("r", encoding="utf-8") as awards_file:
        awards = json.load(awards_file)

    if not isinstance(awards, list):
        raise ValueError("Awards registry must be a list.")

    return awards


def award_keys() -> list[str]:
    return [award["key"] for award in load_awards()]


def default_award_key() -> str:
    raise RuntimeError("No default award is configured; an award must be selected explicitly.")


def public_awards() -> list[dict]:
    return [
        {
            "key": award["key"],
            "label": award["label"],
            "tab_label": award["public_tab"],
            "default": bool(award.get("default", False)),
            "calculator_mode": award.get("calculator_mode", "shift"),
            "academic_scheme": award.get("academic_scheme"),
            # Classification rates are configuration data so they can be
            # updated annually without changing the frontend application.
            "hourly_rate_options": award.get("hourly_rate_options", []),
        }
        for award in load_awards()
        if award.get("public", True) and award.get("public_tab")
    ]


def award_for_key(award_key: str) -> dict:
    """Return one registered calculator definition."""
    for award in load_awards():
        if award["key"] == award_key:
            return award
    raise ValueError(f"Unknown award: {award_key!r}")


@lru_cache(maxsize=1)
def public_disclaimers() -> dict:
    """Return the public calculator and award-specific limitations copy."""
    with DISCLAIMERS_CONFIG_PATH.open("r", encoding="utf-8") as disclaimers_file:
        disclaimers = json.load(disclaimers_file)

    if not isinstance(disclaimers, dict) or not isinstance(
        disclaimers.get("generic"), dict
    ):
        raise ValueError("Disclaimers configuration must include a generic notice.")

    return disclaimers
