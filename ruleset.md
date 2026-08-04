# Ruleset Schema and Runtime Behaviour

Last reviewed against the current codebase: 3 August 2026.

This document describes the award-rule format currently used by the pay calculator, how the engine applies those rules, and which fields remain only for legacy compatibility.

It documents the software behaviour. It is not a substitute for validating award clauses, rates, classifications, or enterprise-agreement conditions against the relevant industrial instrument.

## Source of truth

- Award lookup and registration live in `config/awards.json`.
- Built-in award rule values live in Python classes under `backend/services/rules/`.
- Saved custom configurations live under `backend/custom_rules/` and are tied to
  a registered base award.
- Runtime interpretation lives in `backend/services/rule_engine.py` and `backend/services/pay_calculator.py`.
- Request and response shapes live in `backend/models/`.

The registry is the single source for available award keys. The backend imports
every registered module at startup, so an invalid `module` or `class_name`
prevents the service from starting. Each entry contains:

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

Each award file defines one class with class attributes. The engine reads these
attributes directly.

### Preferred grouped contract

New built-in rulesets use the following grouped attributes. `ordinary` is
defined in one place only: `ORDINARY_TIME_RULES`. Hours are temporary
ordinary-eligible time while OT classifiers run, then final ordinary hours or
overtime; a penalty is a loading, never a third hour bucket.

- `ATTENDANCE_RULES`: default unpaid break and worker-type minimum paid shift.
- `ORDINARY_TIME_RULES`: ordinary time windows, daily limits, optional first
  long-day-per-week exception, and period limits.
- `DAY_RULES`: worker-type treatment for Saturday, Sunday and public holidays
  (`base_classification`, `ordinary_loading`, `overtime_rate_key`).
- `PAY_RATES`: total overtime multipliers keyed by source. A multiplier is
  total pay (for example `1.5`); a loading is extra ordinary pay (for example
  `0.25`).
- `BBS_RULE`: minimum shift gap and its ordinary-hours loading.
- `PENALTIES`: unified ordinary-hour shift/time loadings.
- `TOP_UP_RULES`: contracted-hours overtime and top-up entitlement settings.

Built-ins are projected into this contract at registry load. Saved custom
rules may use the legacy fields below during migration.

### Supported calculation fields

The following fields are supported where the award needs the corresponding
behaviour. They are not all required by class validation:

- `EXTENDED_OVERTIME_DAYS`
- `TWO_TIER_OVERTIME_THRESHOLD`
- `APPLY_SPAN_OVERTIME`
- `SPAN_OVERTIME_START_HOUR`
- `SPAN_OVERTIME_HOUR`
- `GAP_PENALTY_HOURS`
- `GAP_PENALTY_RATE`
- `USE_CONTRACTED_HOURS_FOR_PT_OVERTIME`
- `PT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP`
- `FT_EMPLOYEES_ENTITLED_TO_CONTRACTED_TOPUP`
- `DEFAULT_BREAK`
- `WEEKEND_RULES`
- `PENALTIES`

`HOURS_PEN_RULES` and `SHIFT_PEN_RULES` may appear in older rulesets; their
status is described under [Legacy and compatibility fields](#legacy-and-compatibility-fields).

## Calculation order

For each logical workday (one or more non-overlapping attendance periods), the
calculator applies rules in this order:

1. Expand minimum paid shifts and deduct an unpaid break from ordinary-span
   time before OT time.
2. Apply explicit/manual OT.
3. Apply time-based OT: special days and ordinary-time span.
4. Apply daily OT, including any configured first long day each week.
5. Apply period OT to latest remaining ordinary-eligible hours.
6. Finalise remaining hours as ordinary.
7. Apply BBS/insufficient-gap loading.
8. Apply public-holiday or normal ordinary-hour penalties. Public-holiday
   treatment replaces normal ordinary-hour penalties; BBS remains separate.
9. Apply any contracted-hours top-up and calculate pay.

Overtime rates are calculated when pay is calculated. Two-tier overtime splits
the first-tier and extended-tier hours instead of paying every overtime hour at
the higher rate.

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
        'Saturday': {'is_overtime': False, 'penalty_rate': 0.50},
        'Sunday': {'is_overtime': False, 'penalty_rate': 0.75},
    },
}
```

Business meaning:

- For day workers, `is_overtime: True` moves all hours on that weekend day into overtime.
- For shift workers, `is_overtime: False` leaves ordinary hours as ordinary hours and applies `penalty_rate` to those hours.
- Weekend overtime rates come from `SATURDAY_OVERTIME_RATE` and
  `SUNDAY_OVERTIME_RATE` (or the configured two-tier structure), not from a
  `rate` value inside `WEEKEND_RULES`.
- `penalty_rate` is the only supported weekend loading key. A `rate` value in
  `WEEKEND_RULES` is ignored by the calculator and should not be generated.
- Weekend penalty hours are separate from overtime hours and are calculated only on the ordinary portion of the shift.

The engine also accepts the older day-first shape for compatibility, but new rulesets should use the worker-type-first shape.

## Penalties: current format and business commentary

`PENALTIES` is the current unified structure for shift-start and time-window loadings that are not represented by the weekend rules.

Each entry contains:

- `type`: `shift_based` or `time_based`.
- `basis`: required convention for new entries. Use `time` for `time_based`;
  use `start`, `end`, `duration`, or `start_and_end` for `shift_based`.
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

Use `basis: 'start'` for a start-time rule, `basis: 'end'` for a finish-time
rule, `basis: 'duration'` for a shift-length rule, and `basis: 'start_and_end'`
when both a start and a finish window must match. `start_and_end` also requires
`finish_start` and `finish_end`. If `basis` is omitted, the engine currently
defaults to `start`.

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

This is appropriate for rules such as evening or overnight hours where the
penalty changes during a shift. Use `basis: 'time'`. The engine handles windows
that cross midnight and returns the overlapping hours in the breakdown.

### Penalty interaction rules

- Entries are filtered by `applies_to`.
- An entry with `days` applies only when the shift day is listed.
- An entry without `days` is treated as a weekday-style penalty and is skipped on Saturday and Sunday.
- Weekend treatment therefore comes from `WEEKEND_RULES` unless a penalty is explicitly day-filtered.
- Weekend and shift-based penalties apply only to the ordinary-hours portion.
- Time-based penalties are calculated from worked-hour overlap. They can apply
  to hours that are also overtime; the calculator does not implement an
  automatic “higher rate wins” rule.
- Penalty pay is additive to base ordinary/overtime pay and is reported
  separately. If two applicable penalty entries cover the same hours, both
  loadings are added.
- When period overtime converts ordinary hours into overtime, the general
  weekend penalty-hours field is reduced. Do not rely on period conversion to
  resolve overlapping custom penalty rules.

## Time-window conventions

The engine supports these `basis` values for `shift_based` penalties:

- `start`: match against the shift start time.
- `end`: match against the shift end time.
- `duration`: match against total shift length.
- `start_and_end`: match both shift-start and shift-finish windows.

Windows use 24-hour values. An overnight window is represented with an end lower than its start, for example `start: 24, end: 4` or `start: 22, end: 6`.

For a `time_based` penalty, use `basis: 'time'`; matching is always by overlap
with worked hours.

## Gap penalties

Gap penalties are represented by:

- `GAP_PENALTY_HOURS`: minimum required interval between shifts.
- `GAP_PENALTY_RATE`: additional loading, expressed as a multiplier/loading value.

When the gap between consecutive shifts is less than the threshold, the current shift's ordinary hours receive the gap penalty. The current implementation supports one global threshold and rate per award. It does not support different gap rules by worker type or employment type.

## Overtime and contracted hours

### Configurable daily and weekly limits

New rulesets should use `DAILY_OVERTIME_CONFIGURATION` and
`WEEKLY_OVERTIME_CONFIGURATION` when the daily or weekly limit varies. Each
configuration supports exactly one variation method:

```python
# One limit for every worker and employment type
DAILY_OVERTIME_CONFIGURATION = {"variation": "default", "default": 9}

# A different limit for day and shift workers
WEEKLY_OVERTIME_CONFIGURATION = {
    "variation": "worker_type",
    "day": 38,
    "shift": 40,
}

# A different limit by employment type
DAILY_OVERTIME_CONFIGURATION = {
    "variation": "employment_type",
    "full_time": 10,
    "part_time": 8,
    "casual": 10,
}
```

Do not combine worker-type and employment-type variation in one configuration.
Arbitrary employee cohorts (for example, classification, store, location, or
team) are not supported by the current request model or calculator.

If the configuration is absent or does not match the request, the calculator
falls back to `DAY_WORKER_ORDINARY_HOURS_DAILY` /
`ORDINARY_HOURS_LIMIT_DAILY` and the equivalent weekly fields. Keep these four
required fields present and aligned with any default configuration.

### Other overtime behaviour

- Daily overtime begins after the relevant ordinary-hours daily limit, after
  span overtime has been removed.
- Weekly/period overtime is processed after all shifts have been initially classified.
- `TWO_TIER_OVERTIME` enables the extended rate after `TWO_TIER_OVERTIME_THRESHOLD` overtime hours on configured days.
- `USE_CONTRACTED_HOURS_FOR_PT_OVERTIME` allows a part-time contracted-hours threshold to replace the standard weekly threshold.
- Contracted-hours top-up is separately controlled by the full-time and part-time entitlement fields.
- `APPLY_SPAN_OVERTIME`, `SPAN_OVERTIME_START_HOUR`, and `SPAN_OVERTIME_HOUR`
  define overtime before and/or after the ordinary span for day workers. Omit a
  boundary when that side of the span does not create overtime.

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

- `HOURS_PEN_RULES`: older hourly-penalty mapping. Do not use it in a new
  ruleset. It is consulted only when the class has no `PENALTIES` attribute.
- `SHIFT_PEN_RULES`: older shift-start penalty mapping. Do not use it in a new
  ruleset. It is used only by fallback calculation and older summary-generation
  code.
- `calculate_shift_start_penalty`: compatibility method for rulesets without `PENALTIES`.
- `calculate_hourly_penalties`: compatibility method for rulesets using `HOURS_PEN_RULES`.
- Day-first `WEEKEND_RULES`: still accepted, but worker-type-first is the preferred shape.
- `SATURDAY_PENALTY_RATE` and `SUNDAY_PENALTY_RATE`: unused standalone
  attributes in some old classes. Do not add them; the active weekend
  calculation reads the detailed `WEEKEND_RULES` entries.

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
