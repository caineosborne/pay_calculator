# Simplification Notes

This document tracks legacy fields, compatibility shims, and cleanup candidates that are safe to review later.

## Current Notes

- `HOURS_PEN_RULES` is a legacy hourly-penalty path. The current engine prefers `PENALTIES`, so this field is only needed for fallback compatibility.
- `WEEKEND_RULES` still exists for summary and compatibility, but the newer penalty handling is driven by `PENALTIES` plus explicit `days` filters.
- `Nurses_rules.py` was a backward-compatibility wrapper and has been removed.
- `config/awards.json` is the award registry, not a full rules schema. The actual award rules still live in Python classes.
- Public holidays are not a first-class input yet. Any `PUBLIC_HOLIDAY` day label is only useful if the caller explicitly supplies it.

## Potential Cleanup Candidates

- Remove `HOURS_PEN_RULES` from awards that only use `PENALTIES`.
- Simplify `WEEKEND_RULES` once all awards have migrated to explicit `days`-based penalties.
- Decide whether the engine should keep supporting legacy fallback paths in `rule_engine.py`.
- Consider a formal machine-readable schema for award rules if future awards should be generated or validated automatically.
