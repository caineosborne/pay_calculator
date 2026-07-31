# Award Extractor compatibility amendments

## Unified weekday penalty configuration

Award Extractor should write weekday penalty loadings only to the `PENALTIES`
dictionary on the generated rule class. Do not generate `SHIFT_PEN_RULES` or
`HOURS_PEN_RULES`; they are legacy fallback structures and are not displayed
in the Paychecker frontend.

Each `PENALTIES` entry must include:

```python
{
    "type": "shift_based" | "time_based",
    "start": 0-24,
    "end": 0-24,
    "rate": 0.0,
    "description": "Plain-language loading description",
    "applies_to": ["day"] | ["shift"] | ["day", "shift"],
}
```

The end of every time window is exclusive. For example, `start: 13` and
`end: 16` means from 1:00 pm up to, but not including, 4:00 pm.

## Supported penalty conditions

### Shift-based penalties

Shift-based penalties pay the loading on all ordinary hours of a matching
shift. Set `basis` to one of:

| Basis | Meaning | Required fields |
| --- | --- | --- |
| `start` | Shift starts in the `start`–`end` window. | Base fields |
| `end` | Shift ends in the `start`–`end` window. | Base fields |
| `duration` | Shift length is at least `start` hours and less than `end` hours. | Base fields |
| `start_and_end` | Both the start window and finish window must match. | Base fields plus `finish_start` and `finish_end` |

For `start_and_end`, `start` and `end` define the shift-start window;
`finish_start` and `finish_end` define the shift-finish window.

```python
"afternoon_shift_loading": {
    "type": "shift_based",
    "basis": "start_and_end",
    "start": 13,
    "end": 16,
    "finish_start": 18,
    "finish_end": 24,
    "rate": 0.125,
    "description": "Afternoon shift loading",
    "applies_to": ["shift"],
}
```

This example applies a 12.5% loading to all ordinary hours only where the
shift starts from 1:00 pm and before 4:00 pm, and ends from 6:00 pm and before
midnight.

### Time-based penalties

Time-based penalties apply the loading only to worked hours that overlap the
`start`–`end` time window. Award Extractor should set `basis` to `"time"` for
new time-based entries.

```python
"evening_hours": {
    "type": "time_based",
    "basis": "time",
    "start": 19,
    "end": 24,
    "rate": 0.2,
    "description": "Evening hours loading",
    "applies_to": ["day", "shift"],
}
```

## Migration rule

When extractor output contains legacy shift-start or hourly-time penalty
definitions, convert them into equivalent `PENALTIES` entries during
generation. Existing legacy values remain supported by the backend only as a
fallback for older rule classes.

## Overtime-limit configuration

New extractor output may provide `DAILY_OVERTIME_CONFIGURATION` and
`WEEKLY_OVERTIME_CONFIGURATION`. Both use exactly one variation method:

```python
# One limit for everyone
DAILY_OVERTIME_CONFIGURATION = {"variation": "default", "default": 8}

# Or, different limits for day and shift workers
WEEKLY_OVERTIME_CONFIGURATION = {
    "variation": "worker_type",
    "day": 38,
    "shift": 40,
}

# Or, different limits for employment types
DAILY_OVERTIME_CONFIGURATION = {
    "variation": "employment_type",
    "full_time": 10,
    "part_time": 8,
    "casual": 10,
}
```

Do not combine worker-type and employment-type variations in one
configuration. If these attributes are absent, Paychecker uses the existing
ordinary-hours limits in the rule class unchanged.

## Out-of-span overtime

Out-of-span overtime applies to day workers only. Extractor can set either or
both boundaries:

```python
APPLY_SPAN_OVERTIME = True
SPAN_OVERTIME_START_HOUR = 6  # overtime before 6:00 am
SPAN_OVERTIME_HOUR = 18       # overtime after 6:00 pm
```

Omit a boundary when that side of the ordinary span does not create overtime.
