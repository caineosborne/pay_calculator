# Simplification Notes

This document tracks legacy fields, compatibility shims, and cleanup candidates that are safe to review later.

## Current Notes

- `HOURS_PEN_RULES` is a legacy hourly-penalty path. The current engine prefers `PENALTIES`, so this field is only needed for fallback compatibility.
- `SHIFT_PEN_RULES` and `calculate_shift_start_penalty` are legacy shift-start penalty paths used when an award does not define `PENALTIES`.
- `WEEKEND_RULES` is current and supported. It remains the active source for weekend overtime and weekend penalty classification. The worker-type-first shape is preferred; the day-first shape is retained for compatibility.
- `SATURDAY_PENALTY_RATE` and `SUNDAY_PENALTY_RATE` are compatibility/documentation fields in several older rulesets; detailed weekend entries in `WEEKEND_RULES` drive the active calculation.
- `Nurses_rules.py` was a backward-compatibility wrapper and has been removed.
- `config/awards.json` is the award registry, not a full rules schema. The actual award rules still live in Python classes.
- Public holidays are not a first-class input yet. Any `PUBLIC_HOLIDAY` day label is only useful if the caller explicitly supplies it.

## Potential Cleanup Candidates

- Remove `HOURS_PEN_RULES` from awards that only use `PENALTIES`.
- Keep `WEEKEND_RULES` as the active weekend structure; only consider removing alternate day-first shapes after all consumers and rulesets use the worker-type-first format.
- Decide whether the engine should keep supporting legacy fallback paths in `rule_engine.py`.
- Consider a formal machine-readable schema for award rules if future awards should be generated or validated automatically.
