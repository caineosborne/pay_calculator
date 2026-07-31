# Ruleset Schema and Runtime Behaviour

This document describes the award-rule format currently used by the pay calculator, how the engine applies those rules, and which fields remain only for legacy compatibility.

It documents the software behaviour. It is not a substitute for validating award clauses, rates, classifications, or enterprise-agreement conditions against the relevant industrial instrument.

## Source of truth

- Award lookup and registration live in `config/awards.json`.
- Award rule values live in Python classes under `backend/services/rules/`.
- Runtime interpretation lives in `backend/services/rule_engine.py` and `backend/services/pay_calculator.py`.
- Request and response shapes live in `backend/models/`.

The registry is the single source for available award keys. Each entry contains:

- `key`: stable API identifier.
- `label`: display label.
- `module`: Python module under `backend/services/rules/`, without `.py`.
- `class_name`: rule class inside that module.
- `default`: optional metadata flag; award selection is currently explicit in the request.

Example:

```json
{
  "key": "clerks_private_sector",
  "label": "Clerks Private Sector Award",
  "module": "clerks_private_sector_rules",
  "class_name": "ClerksPrivateSectorRules"
}
```

## Rule class contract

Each award file defines one class with class attributes. The engine reads these attributes directly.

Common fields are:

- `ORDINARY_HOURS_LIMIT_DAILY`
- `ORDINARY_HOURS_LIMIT_WEEKLY`
- `DAY_WORKER_ORDINARY_HOURS_DAILY`
- `DAY_WORKER_ORDINARY_HOURS_WEEKLY`
- `STANDARD_OVERTIME_RATE`
- `EXTENDED_OVERTIME_RATE`
- `SUNDAY_OVERTIME_RATE`
- `SATURDAY_OVERTIME_RATE`
- `EXTENDED_OVERTIME_DAYS`
- `TWO_TIER_OVERTIME`
- `TWO_TIER_OVERTIME_THRESHOLD`
- `APPLY_SPAN_OVERTIME`
- `SPAN_OVERTIME_HOUR`
- `GAP_PENALTY_HOURS`
- `GAP_PENALTY_RATE`
- `USE_CONTRACTED_HOURS_FOR_PT_OVERTIME`
- `PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP`
- `FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP`
- `DEFAULT_BREAK`
- `WEEKEND_RULES`
- `PENALTIES`

`HOURS_PEN_RULES` may also appear in older rulesets; its status is described under [Legacy and compatibility fields](#legacy-and-compatibility-fields).

## Calculation order

For each shift, the calculator generally applies rules in this order:

1. Calculate worked hours after the configured break.
2. Mark all day-worker Saturday/Sunday hours as overtime when `WEEKEND_RULES` says `is_overtime: True`.
3. Apply span overtime where `APPLY_SPAN_OVERTIME` is enabled. Span overtime currently applies to day workers only.
4. Apply the daily ordinary-hours limit.
5. Apply the relevant overtime rate, including two-tier logic when enabled.
6. Apply weekend penalty loadings to remaining ordinary hours for shift workers.
7. Apply configured `PENALTIES` entries.
8. Apply the gap penalty when the interval from the previous shift is below the configured threshold.
9. After all shifts, apply period/weekly overtime and contracted-hours top-up processing.

When ordinary hours are converted to overtime during period processing, the converted hours lose their ordinary-time penalty loading.

## Weekend rules

`WEEKEND_RULES` is the current and supported structure for weekend overtime and weekend penalty treatment. It is not a legacy field.

The preferred shape is worker type first, followed by day:

```python
WEEKEND_RULES = {
    'day': {
        'Saturday': {'is_overtime': True},
        'Sunday': {'is_overtime': True},
    },
    'shift': {
        'Saturday': {
            'is_overtime': False,
            'rate': None,
            'penalty_rate': 0.50,
        },
        'Sunday': {
            'is_overtime': False,
            'rate': None,
            'penalty_rate': 0.75,
        },
    },
}
```

Business meaning:

- For day workers, `is_overtime: True` moves all hours on that weekend day into overtime.
- For shift workers, `is_overtime: False` leaves ordinary hours as ordinary hours and applies `penalty_rate` to those hours.
- `rate` is used for day-worker weekend overtime summaries where supplied. Shift-worker overtime rates are selected through the award's overtime-rate fields.
- Weekend penalty hours are separate from overtime hours and are calculated only on the ordinary portion of the shift.

The engine also accepts the older day-first shape for compatibility, but new rulesets should use the worker-type-first shape.

## Penalties: current format and business commentary

`PENALTIES` is the current unified structure for shift-start and time-window loadings that are not represented by the weekend rules.

Each entry contains:

- `type`: `shift_based` or `time_based`.
- `basis`: for `shift_based`, normally `start`, `end`, or `duration`.
- `start` and `end`: the trigger window or time window.
- `rate`: additional loading expressed as a decimal, such as `0.15` for 15%.
- `description`: business-facing explanation shown in applied-rule output.
- `applies_to`: `day`, `shift`, or both.
- `days`: optional explicit calendar-day filter.

### Shift-based penalties

A shift-based penalty answers: “Does this shift meet the award's trigger?” If it does, the loading applies to the whole ordinary portion of the shift—not only to the hours inside the trigger window.

Typical business uses include:

- a shift beginning in an afternoon or evening window;
- a shift finishing in a particular window;
- a shift meeting a duration threshold.

Use `basis: 'start'` for a start-time rule, `basis: 'end'` for a finish-time rule, and `basis: 'duration'` for a shift-length rule. If `basis` is omitted, the engine currently defaults to `start`.

Example:

```python
{
    'type': 'shift_based',
    'basis': 'start',
    'start': 16,
    'end': 24,
    'rate': 0.15,
    'description': 'Evening Shift Penalty (15%)',
    'applies_to': ['shift'],
}
```

### Time-based penalties

A time-based penalty answers: “How many worked hours overlap the penalty window?” The loading applies only to the overlapping hours.

This is appropriate for rules such as evening or overnight hours where the penalty changes during a shift. The engine handles windows that cross midnight and returns the overlapping hours in the breakdown.

### Penalty interaction rules

- Entries are filtered by `applies_to`.
- An entry with `days` applies only when the shift day is listed.
- An entry without `days` is treated as a weekday-style penalty and is skipped on Saturday and Sunday.
- Weekend treatment therefore comes from `WEEKEND_RULES` unless a penalty is explicitly day-filtered.
- Penalty pay is additive to base ordinary/overtime pay and is reported separately.
- Penalties do not automatically convert ordinary hours into overtime.
- When period overtime converts ordinary hours into overtime, those converted hours no longer receive ordinary-time penalty loading.

## Time-window conventions

The engine supports these `basis` values for `shift_based` penalties:

- `start`: match against the shift start time.
- `end`: match against the shift end time.
- `duration`: match against total shift length.

Windows use 24-hour values. An overnight window is represented with an end lower than its start, for example `start: 24, end: 4` or `start: 22, end: 6`.

`basis` does not apply to `time_based` penalties; those are always evaluated by overlap with worked hours.

## Gap penalties

Gap penalties are represented by:

- `GAP_PENALTY_HOURS`: minimum required interval between shifts.
- `GAP_PENALTY_RATE`: additional loading, expressed as a multiplier/loading value.

When the gap between consecutive shifts is less than the threshold, the current shift's ordinary hours receive the gap penalty. The current implementation supports one global threshold and rate per award. It does not support different gap rules by worker type or employment type.

## Overtime and contracted hours

- Daily overtime begins after the relevant ordinary-hours daily limit.
- Weekly/period overtime is processed after all shifts have been initially classified.
- `TWO_TIER_OVERTIME` enables the extended rate after `TWO_TIER_OVERTIME_THRESHOLD` overtime hours on configured days.
- `USE_CONTRACTED_HOURS_FOR_PT_OVERTIME` allows a part-time contracted-hours threshold to replace the standard weekly threshold.
- Contracted-hours top-up is separately controlled by the full-time and part-time entitlement fields.
- `APPLY_SPAN_OVERTIME` and `SPAN_OVERTIME_HOUR` define span overtime for day workers where the award uses it.

## Breaks

The request model defaults each shift's `break_duration` to `0.5` hours. If a shift explicitly provides no break value, the calculator falls back to the active rule class's `DEFAULT_BREAK`.

## Public holidays

Public holidays are not currently a first-class input in the API:

- the frontend does not send a dedicated public-holiday flag;
- the backend does not look up holiday calendars;
- a day value such as `PUBLIC_HOLIDAY` has no automatic meaning unless the caller and rules explicitly support it.

Public-holiday treatment is therefore not fully implemented.

## Legacy and compatibility fields

The following are legacy or compatibility paths, not the preferred format for new rulesets:

- `HOURS_PEN_RULES`: older hourly-penalty mapping. The current engine prefers `PENALTIES`; it is consulted by fallback logic when no `PENALTIES` structure is present.
- `SHIFT_PEN_RULES`: older shift-start penalty mapping. It is used only by fallback calculation and older summary-generation code.
- `calculate_shift_start_penalty`: compatibility method for rulesets without `PENALTIES`.
- `calculate_hourly_penalties`: compatibility method for rulesets using `HOURS_PEN_RULES`.
- Day-first `WEEKEND_RULES`: still accepted, but worker-type-first is the preferred shape.
- `SATURDAY_PENALTY_RATE` and `SUNDAY_PENALTY_RATE`: retained in several classes for compatibility/documentation; the active weekend calculation reads the detailed `WEEKEND_RULES` entries.

`WEEKEND_RULES` itself is not legacy. It remains the active source for weekend overtime and weekend penalty classification.

## Practical meaning of fields

- `key`: backend/API award identifier.
- `label`: UI display name.
- `module`: Python file name without `.py`.
- `class_name`: Python rule class name.
- `basis`: how a shift-based penalty is matched.
- `start` / `end`: trigger or overlap window.
- `days`: explicit calendar-day filter.
- `rate`: decimal loading for penalties, or multiplier where used by weekend/overtime rules.
- `applies_to`: worker types receiving the rule.

## Adding an award

1. Add one rule class in `backend/services/rules/`.
2. Add one registry entry to `config/awards.json`.
3. Expose the fields required by the engine paths used by that award.
4. Add tests covering ordinary hours, overtime, weekend treatment, penalties, breaks, and any gap/top-up behaviour.

The project does not yet enforce a formal machine-readable schema for every field, so a ruleset can be syntactically valid while still being semantically incomplete or inconsistent with the engine's supported behaviour.
