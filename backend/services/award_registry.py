"""
Shared award registry utilities.

This module reads the single source of truth for available awards from the
frontend JSON registry so backend validation and frontend options stay aligned.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


AWARDS_REGISTRY_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "awards.json"
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
    for award in load_awards():
        if award.get("default"):
            return award["key"]
    return load_awards()[0]["key"]


def public_awards() -> list[dict]:
    return [
        {
            "key": award["key"],
            "label": award["label"],
            "default": bool(award.get("default", False)),
        }
        for award in load_awards()
    ]
