# Ruleset Schema

This document explains the current award rules format used by the pay calculator.

## Source Of Truth

- Award lookup lives in `config/awards.json`.
- Rule behavior lives in Python rule classes under `backend/services/rules/`.
- The runtime engine interprets those Python classes through `backend/services/rule_engine.py`.

## Award Registry

`config/awards.json` is the master list of awards that appear in the UI and can be selected by the API.

Each entry has:
- `key`: stable API identifier, sent in requests and used by the backend rule factory
- `label`: human-readable name shown in the frontend
- `module`: Python module name under `backend/services/rules/` without `.py`
- `class_name`: Python class inside that module
- `default`: optional flag for the default award

Example:

```json
{
  "key": "clerks_private_sector",
  "label": "Clerks Private Sector Award",
  "module": "clerks_private_sector_rules",
  "class_name": "ClerksPrivateSectorRules"
}
```

## Rule Class Contract

Each award file defines one class with class attributes. The engine reads those attributes directly.

Common attributes:
- `ORDINARY_HOURS_LIMIT_DAILY`
- `ORDINARY_HOURS_LIMIT_WEEKLY`
- `DAY_WORKER_ORDINARY_HOURS_DAILY`
- `DAY_WORKER_ORDINARY_HOURS_WEEKLY`
- `STANDARD_OVERTIME_RATE`
- `EXTENDED_OVERTIME_RATE`
- `SUNDAY_OVERTIME_RATE`
- `SATURDAY_OVERTIME_RATE`
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
- `HOURS_PEN_RULES`

## Time-Based Concepts

The engine supports three ways to classify a shift-level rule:

- `basis: "start"` means match based on shift start time
- `basis: "end"` means match based on shift end time
- `basis: "duration"` means match based on total shift length, regardless of clock time

`basis` only applies to `shift_based` penalties.

### `start`

Use this when the rule depends on when the shift begins.

Example:

```python
{
    "type": "shift_based",
    "basis": "start",
    "start": 13,
    "end": 18,
    "rate": 0.15,
    "description": "Afternoon shift loading",
    "applies_to": ["shift"]
}
```

### `end`

Use this when the rule depends on when the shift finishes.

Example:

```python
{
    "type": "shift_based",
    "basis": "end",
    "start": 19,
    "end": 24,
    "rate": 0.15,
    "description": "Shift finishes after 7pm",
    "applies_to": ["shift"]
}
```

This is the right shape for rules like:
- finishes after 7pm and at or before midnight
- finishes after midnight and at or before 7am

### `duration`

Use this when the rule depends on how long the shift runs.

Example:

```python
{
    "type": "shift_based",
    "basis": "duration",
    "start": 10,
    "end": 24,
    "rate": 0.2,
    "description": "10 hour shift loading",
    "applies_to": ["day", "shift"]
}
```

This matches any 10-hour shift regardless of start time.

## Penalties

`PENALTIES` is for penalty rules the engine can evaluate from a shift's day/time information.

Supported penalty types:
- `shift_based`
- `time_based`

### `shift_based`

Applies the loading to the whole shift once the trigger matches.

Required fields:
- `type: "shift_based"`
- `start`
- `end`
- `rate`
- `description`
- `applies_to`

Optional fields:
- `basis`
- `days`

### `time_based`

Applies the loading only to the overlapping time window.

Required fields:
- `type: "time_based"`
- `start`
- `end`
- `rate`
- `description`
- `applies_to`

Optional fields:
- `days`

## `days`

`days` is an optional filter on a penalty entry.

Use it when a penalty should only apply on specific calendar days.

Examples:

```python
"days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
```

```python
"days": ["Saturday"]
```

```python
"days": ["Sunday"]
```

Important:
- weekend penalties should be marked with `days`
- if a penalty has no `days` entry, the engine treats it as a weekday-style penalty
- public holidays are not a first-class date type in the current request model

## Weekend Rules

`WEEKEND_RULES` still exists for compatibility and for summary output.

It is not the primary place to define weekend loadings for awards that use the newer penalty format.

Current use:
- summary display
- compatibility with older award logic
- fallback behavior in some engine paths

For new rulesets:
- keep weekend loadings in `PENALTIES` with explicit `days`
- use `WEEKEND_RULES` only if the engine path still expects it

## Gap Rules

Gap penalties are represented by:
- `GAP_PENALTY_HOURS`
- `GAP_PENALTY_RATE`

This is one global threshold and one global rate per award.

It does not currently support:
- different gap rules for day vs shift workers
- different gap rules by employment type

## Public Holidays

Public holidays are not currently a first-class input in the API.

That means:
- the frontend does not send a dedicated public-holiday flag
- the backend does not look up holiday calendars
- a `days` value like `"PUBLIC_HOLIDAY"` is only meaningful if the caller explicitly sends it

So public-holiday treatment is not fully supported yet.

## Practical Meaning Of Fields

- `key`: backend/API award identifier
- `label`: UI display text
- `module`: Python file name
- `class_name`: Python class name
- `basis`: how a `shift_based` penalty is matched
- `start` / `end`: the trigger window or rule window
- `duration`: total shift length trigger
- `days`: explicit day filter

## Minimal Workflow For A New Award

1. Add the rule class file in `backend/services/rules/`.
2. Add one entry to `config/awards.json`.
3. Make sure the rule class exposes the attributes the engine expects.

## Current Limitation

The engine is still partially implicit. Some award concepts are represented in Python only and are not yet described by a formal machine-readable schema.

If you want a fully strict schema later, the next step would be to move the rule contract into a structured JSON or YAML schema and generate the Python classes from it.
