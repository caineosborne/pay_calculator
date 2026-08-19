# Academic Activity Ruleset Contract

This document defines the configuration contract for date-based academic
activity pay. It is separate from the shift ruleset in `ruleset.md` because an
academic activity may be paid by a delivered unit that incorporates other work,
rather than by attendance hours on that date.

QUT Sessional Academic Staff is the first implementation. The format is
intended to support additional universities without adding university-specific
branches to the calculation engine.

## Registration and loading

Register an academic calculator in `backend/config/awards.json`:

```json
{
  "key": "example_university_sessional",
  "label": "Example University Sessional Staff",
  "module": "example_university_sessional",
  "class_name": "ExampleUniversitySessionalRules",
  "calculator_mode": "academic_activity",
  "academic_scheme": "example_university_sessional",
  "public_tab": "Example University"
}
```

Place the Python ruleset in `backend/services/academic_rules/`. Academic
rulesets are read-only in the current product and are not included in the
custom shift-rules editor.

Every academic ruleset class supplies four attributes:

```python
class ExampleUniversitySessionalRules:
    SCHEME = {...}
    ELIGIBILITY = {...}
    RATE_SCHEDULES = [...]
    ACTIVITIES = {...}
```

## `SCHEME`

```python
SCHEME = {
    "key": "example_university_sessional",
    "label": "Example University Sessional Staff",
    "minimum_engagement_hours": 2,
    "repeat_window_days": 7,
    "sources": [
        {"label": "Enterprise agreement", "url": "https://example.edu/ea.pdf"}
    ],
}
```

- `key` must match the award registry key and API `scheme` value.
- `minimum_engagement_hours` is used to report an occasion-level shortfall. A
  shortfall is not automatically added to pay.
- `repeat_window_days` controls automatic repeat classification for activities
  with `repeatable: True`.
- `sources` are displayed or retained for auditability and maintenance.

## `ELIGIBILITY`

`ELIGIBILITY` maps stable codes to user-facing course eligibility choices:

```python
ELIGIBILITY = {
    "standard": "Standard",
    "relevant_phd": "Relevant doctoral qualification",
    "full_coordinator": "Full subject/unit coordination duties",
}
```

The generic engine currently treats `relevant_phd` and `full_coordinator` as
the `higher` classification branch. A future university requiring different
rates for those conditions should extend the eligibility selector in the
engine rather than encode the distinction in user-entered activity names.

## `RATE_SCHEDULES`

Store every published rate directly in a date-effective schedule:

```python
RATE_SCHEDULES = [
    {
        "effective_from": "2025-12-13",
        "rates": {
            "TUTORIAL_NORMAL": 165.64,
            "TUTORIAL_REPEAT": 110.32,
            "MARKING_STANDARD": 55.11,
        },
    }
]
```

The calculator selects the latest schedule whose `effective_from` is on or
before the work date. Composite rates must not be reconstructed from a generic
hourly rate: store the published unit amount even where the agreement explains
it as a multiple of an underlying rate.

Add a new schedule for a pay increase. Do not overwrite an existing schedule
when historical calculations need to remain reproducible.

## `ACTIVITIES`

Activities are keyed by a stable, institution-independent code where practical:

```python
ACTIVITIES = {
    "tutorial": {
        "label": "Tutorial",
        "payment_basis": "composite_unit",
        "quantity_label": "Delivered hours",
        "course_required": True,
        "topic_required": True,
        "repeatable": True,
        "variants": {"normal": "Normal tutorial"},
        "default_variant": "normal",
        "classifications": {
            "normal:standard": {
                "rate_code": "TUTORIAL_NORMAL",
                "incorporated_hours": 2,
                "label": "Normal tutorial",
            },
            "repeat:standard": {
                "rate_code": "TUTORIAL_REPEAT",
                "incorporated_hours": 1,
                "label": "Repeat tutorial",
            },
        },
    }
}
```

### Payment bases

`payment_basis` is one of:

- `composite_unit`: pay equals delivered quantity multiplied by the published
  unit rate. `incorporated_hours` is also multiplied by delivered quantity.
- `direct_hour`: pay equals actual required or approved hours multiplied by the
  published hourly rate.

The quantity unit is not hard-coded. `quantity_label` tells the UI whether the
number represents delivered hours, sessions, items or another configured unit.

### Activity fields

- `course_required`: requires a valid course reference on the work item.
- `topic_required`: requires a topic/teaching-week value. Repeat matching uses
  its normalized value.
- `quantity_help`: optional plain-language guidance shown beside the quantity
  input, such as clarifying that only delivered teaching time is entered.
- `repeatable`: enables automatic original/repeat classification.
- `requires_approval`: requires the work item to confirm that direct hours were
  required or approved.
- `variants`: stable variant codes and their labels.
- `default_variant`: used when the request does not supply a variant.
- `classifications`: maps `variant:eligibility` to a published rate code,
  incorporated hours per unit and an auditable label.
- `variant_uses_default_classification`: allows descriptive variants such as
  workshop, field trip and meeting to share one payment classification.

For a repeat result, the engine uses the `repeat:standard` or `repeat:higher`
classification key. Non-repeat activities use their selected variant.

## Request behavior

Academic calculations use `POST /calculate/academic`. A request contains:

- A Monday `period_start` for the 14-day result period.
- Course records with eligibility.
- Current-period work items.
- Optional work items from the preceding seven days used only for repeat
  classification.

Work items have a date but no clock times. Every item has an `occasion_id`.
Items on the same date and with the same occasion ID are combined solely for
the minimum-engagement review.

Repeat matching requires the same:

1. Course ID.
2. Activity key.
3. Normalized topic/teaching-week text.
4. Delivery within the configured calendar-day window.

The first matching item is original and later qualifying items are repeat.
Users may override original/repeat classification only with a recorded reason.

## Result and calculation boundaries

The response reports each published rate, classification, repeat match,
quantity, incorporated hours, actual-associated-hours variance and pay amount.
It also reports activity-pay and direct-hours-pay totals separately.

Actual associated time is an audit comparison. It does not increase pay.
Minimum-engagement shortfalls are review warnings and are not monetized. Rules
about overtime, penalties, leave, tax and superannuation are outside this
academic activity contract unless a future version adds an explicit group for
them.

## Authoring checklist

Before adding another university:

1. Register it with `calculator_mode: "academic_activity"`.
2. Add all published rates as date-effective, direct values.
3. Map every payable activity to `composite_unit` or `direct_hour`.
4. Record incorporated hours per delivered unit.
5. Identify which activities require course, topic, repeat logic or approval.
6. Add backend tests for every classification, eligibility branch and rate
   period.
7. Add institution-specific scope, assumptions and exclusions to
   `backend/config/disclaimers.json`.
