# Backend Summary

## Runtime flow

The backend runtime path is:

`main.py` -> `models/request_models.py` -> `services/pay_calculator.py` -> `services/rule_engine.py` -> `services/rules/*.py` -> `models/response_models.py`

The frontend posts a JSON payload to `POST /calculate`, and the backend returns a deterministic calculation result.

## Main backend files

### `main.py`
- Defines the FastAPI app.
- Configures CORS.
- Exposes `POST /calculate`.
- Instantiates `PayCalculator` and returns its `PayResponse`.

### `models/request_models.py`
- Defines the input schema with Pydantic.
- Main types:
  - `Shift`
  - `PayRequest`
  - `WorkerType`
  - `AwardType`
  - `EmploymentType`

### `models/response_models.py`
- Defines the output schema with Pydantic.
- Main types:
  - `RulesetSummary`
  - `PayResponse`

### `services/pay_calculator.py`
- Main calculation orchestrator.
- Processes each shift.
- Splits hours into ordinary, overtime, penalty, gap-penalty, shift-penalty, hourly-penalty, and top-up buckets.
- Applies weekly overtime after daily processing.
- Applies contracted-hours top-up after overtime processing.
- Builds the final response and rule summary.

### `services/rule_engine.py`
- Common adapter over award-specific rule classes.
- Knows how to:
  - select the active award
  - read daily and weekly limits
  - decide weekend overtime vs weekend penalties
  - apply span overtime
  - calculate unified penalties
  - calculate gap penalties

## Rule/config files

### `services/rules/rule_factory.py`
- Maps award strings to rule classes.
- Current supported awards:
  - `aged_care`
  - `hospitality`
  - `child_care`
  - `nurses_award`
  - `eb11`

### `services/rules/aged_care_rules.py`
- Aged Care rule constants.
- Uses span overtime for day workers.
- Uses shift-based weekday penalties.
- Uses gap penalties.

### `services/rules/hospitality_rules.py`
- Hospitality rule constants.
- Does not use span overtime.
- Uses time-based weekday penalties.
- No real gap penalty.

### `services/rules/child_care_rules.py`
- Child Care rule constants.
- Does not use span overtime.
- Uses a shift-based afternoon penalty.
- Uses two-tier overtime.
- Weekend rules are modeled as overtime.

### `services/rules/nurses_award_rules.py`
- Nurses Award rule constants.
- Does not use span overtime.
- Uses time-based night loading.
- Uses two-tier overtime.
- Weekend rules are modeled as penalties, not automatic overtime.

### `services/rules/eb11_rules.py`
- EB11 rule constants.
- Does not use span overtime.
- Uses time-based night loading.
- Overtime is effectively always double time.

### `services/rules/Nurses_rules.py`
- Backward-compatibility re-export only.
- Does not define separate runtime logic.

### `services/rules/__init__.py`
- Re-exports `get_rules_for_award`.

## Config approach

There are no YAML rule files in the current repo.

All active rule/config data is defined in Python class attributes inside `services/rules/*.py`.

Typical config fields in those classes include:
- ordinary hour limits
- overtime multipliers
- weekend rules
- `APPLY_SPAN_OVERTIME`
- `SPAN_OVERTIME_HOUR`
- `PENALTIES`
- gap-penalty settings
- contracted-hours top-up flags

## Penalties vs overtime

Penalty handling is optional per award.

If an award has no weekday penalties:
- `PENALTIES` can be empty
- weekend penalty rates can be zero
- gap penalty can be zero or omitted

In that case the calculator still works and only overtime or ordinary-time logic will contribute to pay.

`APPLY_SPAN_OVERTIME` is only applied to day workers in `rule_engine.py`. Shift workers never use span overtime in the current code.

## LLM / AI usage

There are no LLM, AI, or external inference calls in this repo.

The backend is deterministic:
- input payload in
- rule selection
- fixed calculations
- structured response out

The frontend only sends HTTP requests to the backend `/calculate` endpoint.
