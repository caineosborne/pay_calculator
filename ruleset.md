# Pay Calculator Ruleset Contract

Last reviewed against the current codebase: 10 August 2026.

This is the canonical contract for award rules consumed by the pay calculator.
It is written for both people and agents authoring rulesets. It describes the
software contract, not industrial-award advice.

## Scope and vocabulary

- A **shift** is one attendance period. A logical **workday** can contain more
  than one non-overlapping shift.
- The request supports exactly two numbered weeks (`1` and `2`), so a
  `pay_period` is a fortnight in the current product.
- `day` is one of `Monday` through `Sunday`.
- `worker_type` is `day` or `shift`; `employment_type` is `full_time`,
  `part_time`, or `casual`.
- A **multiplier** is total pay (for example `1.5` means 150% of base pay).
  A **loading** is extra pay (for example `0.25` means base pay plus 25%).

Hours finish in exactly one base bucket: **ordinary** or **overtime**. A
penalty is a loading on final ordinary hours, not a third hours bucket. The
calculator removes or caps penalty hours when ordinary time becomes overtime.
Separate configured penalties may intentionally add together when they both
match the same ordinary hours.

## Authoring a ruleset

Register an award in `backend/config/awards.json`, then provide a Python class in
`backend/services/rules/`. New rulesets should use this grouped contract:

```python
class ExampleRules:
    SHIFT_RULES = {...}
    ORDINARY_TIME_RULES = {...}
    DAY_TREATMENT_RULES = {...}
    PAY_RATES = {...}
    GAP_BETWEEN_SHIFTS_RULE = {...}
    ORDINARY_HOUR_PENALTIES = {...}
    TOP_UP_RULES = {...}
```

`CANONICAL_RULESET` is not read by the live loader and is not required. All
seven grouped attributes below are required by both the source validator and
the calculator. Do not use legacy flat attributes: the live loader reads the
grouped attributes directly and does not adapt flat fields.

### Required and optional groups

Every group is required as a class attribute. `SHIFT_RULES`,
`GAP_BETWEEN_SHIFTS_RULE`, `ORDINARY_HOUR_PENALTIES`, and `TOP_UP_RULES` may
be empty dictionaries when that family of rules is not used. In practice,
`SHIFT_RULES` will normally retain `default_break_hours` and
`minimum_paid_shift_hours`.

Use an empty dictionary to disable an optional family:

```python
SHIFT_RULES = {}
GAP_BETWEEN_SHIFTS_RULE = {}
ORDINARY_HOUR_PENALTIES = {}
TOP_UP_RULES = {}
```

Do not use `None` in place of a group. The calculator expects dictionaries.
Within a configured rule, prefer the explicit disabling values documented
below rather than an empty partial record.

## Editable custom configurations

The built-in award modules are immutable at runtime. To edit a ruleset in the
application, open **Edit rule configuration**, change the guided fields or
Advanced Python, and save. Saving a built-in creates a new custom copy; saving
an existing custom configuration replaces that custom copy after validation.

Custom configurations are identified as `custom:<award_key>:<slug>`, for
example `custom:fast_food:late-shift-review`. Built-ins use
`builtin:<award_key>`. The API exposes the configuration workflow:

```text
GET  /rule-configurations
GET  /rule-configurations/{id}
POST /rule-configurations/validate
POST /rule-configurations
PUT  /rule-configurations/{id}
```

`POST` creates a custom configuration with `base_award`, `name`, `source`, and
optionally `questionnaire`; `PUT` accepts `source` and optionally
`questionnaire`. The source must parse as Python, define the award's expected
top-level class, and assign all seven grouped attributes. Its detailed values
are then consumed by the calculator, so use this document as the authoring
contract and validate representative calculations before publishing a change.

To calculate with a saved configuration, pass its ID as `rule_configuration`
in `POST /calculate`. The configuration's award must match the request's
`award`; otherwise the API rejects the request. The bulk employee-master CSV
has the same `rule_configuration` column and forwards its value unchanged to
each calculation.

Custom files are stored in `backend/custom_rules` by default, or in the
directory specified by `PAYCHECKER_CUSTOM_RULES_DIR`. A deployment must use
persistent storage for that directory if custom edits must survive restarts or
redeployments. Custom rules execute as trusted Python code; do not expose the
write endpoints to untrusted users.

## Complete minimal example

This is a valid starting point with a daily and weekly OT limit and no
penalties, gap rule, minimum engagement, or top-up.

```python
class ExampleRules:
    SHIFT_RULES = {
        "default_break_hours": 0.5,
        "minimum_paid_shift_hours": {},
    }

    ORDINARY_TIME_RULES = {
        "span_overtime": {},
        "daily": {"variation": "default", "default": 8},
        "period": {
            "variation": "default",
            "default": 38,
            "basis": "weekly",
            "part_time_uses_contracted_hours": False,
        },
    }

    DAY_TREATMENT_RULES = {
        "Saturday": {
            "day": {"base_classification": "ordinary", "ordinary_loading": 0,
                    "overtime_rate_key": "saturday"},
            "shift": {"base_classification": "ordinary", "ordinary_loading": 0,
                      "overtime_rate_key": "saturday"},
        },
        "Sunday": {
            "day": {"base_classification": "ordinary", "ordinary_loading": 0,
                    "overtime_rate_key": "sunday"},
            "shift": {"base_classification": "ordinary", "ordinary_loading": 0,
                      "overtime_rate_key": "sunday"},
        },
    }

    PAY_RATES = {
        "overtime": {
            "weekday": {"multiplier": 1.5},
            "saturday": {"multiplier": 1.5},
            "sunday": {"multiplier": 2.0},
            "extended": {"multiplier": 2.0},
            "two_tier": {"enabled": False, "threshold": 0, "days": []},
        }
    }

    GAP_BETWEEN_SHIFTS_RULE = {}
    ORDINARY_HOUR_PENALTIES = {}
    TOP_UP_RULES = {"part_time": False, "full_time": False}
```

## `SHIFT_RULES`

```python
SHIFT_RULES = {
    "default_break_hours": 0.5,
    "minimum_paid_shift_hours": {
        "variation": "employment_type",
        "full_time": 4,
        "part_time": 3,
        "casual": 3,
    },
}
```

- `default_break_hours` is used when a request shift omits `break_duration`.
- `minimum_paid_shift_hours` extends a shorter attendance period to its paid
  minimum before other rules run. Use `{}` to disable it.
- The current minimum-engagement evaluator supports an employment-type map:
  `variation: "employment_type"` with `full_time`, `part_time`, and `casual`
  keys. A zero value disables the minimum for that type. It also accepts a
  legacy unlabelled map keyed directly by employment type or worker type.
  Do not use `variation: "default"` or `"worker_type"` in a new grouped
  minimum-engagement record; unlike daily and period limits, those variations
  are not interpreted by the current evaluator.

## `ORDINARY_TIME_RULES`

### Span overtime

Span OT applies to `day` workers only. Each window has optional `start` and
`end` cut-offs: time before `start` and after `end` is overtime.

```python
"span_overtime": {
    "day": {
        "default": {"start": 6, "end": 18, "enabled": True},
        "Saturday": {"start": 7, "end": 12, "enabled": True},
        "Sunday": {"enabled": False},
    }
}
```

- The day-specific record overrides `default` for that calendar day.
- Omit `start` to disable before-span OT; omit `end` to disable after-span OT.
- Set `enabled: False` to disable span OT for that day.
- Use `"span_overtime": {}` to disable span OT entirely.

### Daily limits and the long-day exception

```python
"daily": {
    "variation": "employment_type",
    "full_time": 8,
    "part_time": 7.6,
    "casual": 8,
},
"long_day": {"uses_per_week": 1, "ordinary_limit_hours": 10},
```

Every limit record has exactly one variation method:

```python
{"variation": "default", "default": 8}
{"variation": "worker_type", "day": 8, "shift": 10}
{"variation": "employment_type", "full_time": 8, "part_time": 7.6, "casual": 8}
```

`long_day` is optional. `uses_per_week: 1` lets the first eligible workday in
each week use `ordinary_limit_hours` rather than the standard daily limit.
Omit `long_day` or use `{"uses_per_week": 0}` to disable it.

### Period hours and maximum worked days

```python
"period": {
    "variation": "employment_type",
    "full_time": 76,
    "part_time": 38,
    "casual": 38,
    "basis": {
        "full_time": "pay_period",
        "part_time": "weekly",
        "casual": "weekly",
    },
    "max_work_days": 10,
    "max_work_days_basis": "pay_period",
    "part_time_uses_contracted_hours": False,
},
```

- The hours threshold uses the same `variation` forms as `daily`.
- `basis` is either `"weekly"`/`"pay_period"` for every employee, or an
  employment-type map when `variation` is `"employment_type"`.
- A weekly limit is enforced independently in each week. A pay-period limit
  is one threshold across both weeks; do not supply a weekly number and
  expect it to be multiplied automatically.
- `max_work_days` is optional. Later worked days in its group have their
  remaining ordinary hours converted to overtime. Set it to `None` or omit it
  to disable the days cap.
- `max_work_days_basis` is `"weekly"` or `"pay_period"`. It defaults to
  weekly when omitted, so set it explicitly when a weekly hour limit is paired
  with a fortnight-wide days cap.
- `part_time_uses_contracted_hours: True` replaces a part-time threshold with
  the request's contracted weekly hours. It does not affect full-time or
  casual thresholds.

`ordinary_rates.casual_loading` is an optional ordinary-hours loading. It is
used only for casual ordinary hours that have no other ordinary-hours loading:

```python
"ordinary_rates": {"casual_loading": 0.25}
```

## `DAY_TREATMENT_RULES`

Define Saturday and Sunday for both worker types. Add `public_holiday` when
the award supports manually selected public holidays.

```python
DAY_TREATMENT_RULES = {
    "Saturday": {
        "day": {"base_classification": "overtime", "ordinary_loading": 0,
                "overtime_rate_key": "saturday"},
        "shift": {"base_classification": "ordinary", "ordinary_loading": 0.5,
                  "casual_rate": 0.65, "overtime_rate_key": "saturday"},
    },
    "Sunday": {...},
    "public_holiday": {
        "day": {"base_classification": "overtime", "ordinary_loading": 0,
                "overtime_rate_key": "public_holiday"},
        "shift": {"base_classification": "ordinary", "ordinary_loading": 1.5,
                  "casual_rate": 1.5, "overtime_rate_key": "public_holiday"},
    },
}
```

For each worker record:

- `base_classification` is `"ordinary"` or `"overtime"`.
- `ordinary_loading` is an additional loading on ordinary hours.
- `casual_rate`, when present, replaces `ordinary_loading` for casuals.
- `overtime_rate_key` selects an entry in `PAY_RATES["overtime"]` when the
  record makes the day overtime.

The request supplies public holidays explicitly as
`public_holidays: [{"week": 1, "day": "Monday"}]`. If a request selects a
public holiday and the ruleset has no `public_holiday` treatment, calculation
fails clearly rather than silently guessing. Public-holiday treatment replaces
normal weekday/weekend and custom penalty treatment for that logical day.

## `PAY_RATES`

```python
PAY_RATES = {
    "overtime": {
        "weekday": {"multiplier": 1.5, "casual": 1.75},
        "manual": {"multiplier": 1.5, "casual": 1.75},
        "saturday": {"multiplier": 2.0, "casual": 2.25},
        "sunday": {"multiplier": 2.0, "casual": 2.25},
        "public_holiday": {"multiplier": 2.5, "casual": 2.5},
        "extended": {"multiplier": 2.0, "casual": 2.25},
        "two_tier": {
            "enabled": True,
            "threshold": 2,
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        },
    }
}
```

- `weekday`, `saturday`, `sunday`, and `extended` should always be supplied.
- `manual` and `public_holiday` are optional but recommended when those
  classifications are used. Without a key, the calculator falls back to the
  standard day-based overtime rate.
- `casual` is a total casual OT multiplier; it does not stack with the casual
  ordinary loading.
- With `two_tier.enabled: True`, OT on listed `days` is split at `threshold`:
  first-tier OT uses `weekday`, later OT uses `extended`. Use
  `{"enabled": False, "threshold": 0, "days": []}` to disable it.

## `ORDINARY_HOUR_PENALTIES`

Use a dictionary keyed by a stable code name. `days` lets every penalty define
its own calendar-day scope, such as Monday–Friday or Monday–Saturday.

```python
ORDINARY_HOUR_PENALTIES = {
    "late_shift": {
        "type": "shift_based",
        "basis": "start",
        "start": 18,
        "end": 24,
        "rate": 0.15,
        "casual_rate": 0.25,
        "description": "Late shift loading",
        "applies_to": ["shift"],
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    },
    "night_hours": {
        "type": "time_based",
        "basis": "time",
        "start": 22,
        "end": 6,
        "rate": 0.2,
        "description": "Night-hours loading",
        "applies_to": ["day", "shift"],
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    },
}
```

Common fields:

- `type`: `"shift_based"` or `"time_based"`.
- `rate`: ordinary-hours loading; `casual_rate` optionally replaces it for
  casual employees.
- `description`: user-facing applied-rule text.
- `applies_to`: a non-empty list containing `day`, `shift`, or both.
- `days`: optional explicit day list. If omitted, the rule is weekday-style
  and is skipped on Saturday and Sunday.

For `shift_based`, `basis` is `start`, `end`, `duration`, or `start_and_end`.
`start`/`end` define the trigger range. `duration` uses them as minimum and
maximum duration. `start_and_end` additionally requires `finish_start` and
`finish_end`.

For `time_based`, use `basis: "time"`; `start` and `end` are the payable
window and may cross midnight. The engine calculates worked-hour overlap, then
only final ordinary hours remain penalty-eligible.

Use `{}` to disable all custom ordinary-hour penalties. A penalty does not
replace another matching penalty; configured loadings are additive.

## `GAP_BETWEEN_SHIFTS_RULE`

```python
GAP_BETWEEN_SHIFTS_RULE = {
    "minimum_hours": 10,
    "loading": 1.0,
    "casual_rate": 1.0,
}
```

When the gap before a shift is below `minimum_hours`, the current shift's
final ordinary hours receive `loading`. `casual_rate` optionally replaces it
for casual employees. Use `{}` or a missing/zero `minimum_hours` to disable
this rule.

## `TOP_UP_RULES`

```python
TOP_UP_RULES = {"part_time": True, "full_time": False}
```

When enabled and contracted hours are supplied, the calculator adds ordinary
top-up hours if total worked hours fall below the contracted fortnight target.
Overtime counts as worked time and does not itself create top-up.

## Manual request overrides

These are request fields, not ruleset fields:

```json
{
  "day": "Sunday",
  "week": 1,
  "start": 9,
  "end": 17,
  "break_duration": 0.5,
  "manual_overtime": false,
  "manual_ordinary": true
}
```

- `manual_overtime: true` hard-codes the logical workday as overtime.
- `manual_ordinary: true` hard-codes it as ordinary and bypasses span, daily,
  period, weekend, and public-holiday OT classification. Ordinary penalties
  can still apply.
- The UI makes the two controls mutually exclusive. API callers must also
  treat them as mutually exclusive.

## Calculation order

For each logical workday, the calculator:

1. Expands minimum paid shifts and deducts the unpaid break.
2. Applies manual ordinary or manual overtime classification.
3. Applies public-holiday and weekend base classification, then span and daily
   overtime (including the long-day exception).
4. Applies maximum-worked-days OT, then period-hours OT. Later eligible days
   are converted first.
5. Finalises ordinary-only penalties and casual ordinary loading.
6. Adds any contracted-hours top-up and calculates pay.

The result reports ordinary, overtime, top-up, and each penalty component
separately. Penalty pay is additional to base ordinary pay; it is never added
to an overtime hour.

## Unsupported legacy shapes

Flat fields such as `WEEKLY_OVERTIME_CONFIGURATION`, `WEEKEND_RULES`,
`PENALTIES`, and `STANDARD_OVERTIME_RATE` are not part of the live ruleset
contract. A custom configuration that provides only those fields fails
validation because it does not assign the seven required grouped attributes.
Migrate the full class to the grouped contract before saving or calculating
with it.
