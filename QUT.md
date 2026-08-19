# Generic Activity-Paid Calculator with QUT Sessional as the First Scheme

## Summary

Add a second calculator mode alongside the existing shift calculator:

- **Shift mode:** populated fortnight grid; attendance hours produce ordinary,
  overtime and penalty pay.
- **Activity mode:** blank dated fortnight; users add activity-paid work or
  direct-hour work.

The activity engine will be industry-neutral. It will support any arrangement
where a task, session, item or delivered hour has a published unit price that
incorporates a specified amount of working time. Only **QUT Sessional Academic
Staff** will be exposed initially.

QUT ongoing, fixed-term, teaching-intensive and QUT College educator
calculations remain out of scope.

Dates are required for activity records, but start and finish times are not.
Separate occasions on the same date are distinguished by asking whether a new
item formed part of an existing work occasion.

## Current implementation status

The generic academic engine, QUT activity catalogue, date-only fortnight,
course-specific rate basis, repeat lookback, incorporated-time comparison and
minimum-engagement review are implemented. Same-date occasion grouping is
presented as an optional “same work occasion” choice rather than an industrial
relations code or free-text group name.

The following planned items remain deliberately deferred: academic ruleset
editing, a visible/editable history manager, missing-history warnings, CSV
import and automatic monetary valuation of a minimum-engagement shortfall.
Stored browser history is currently used automatically for repeat matching.

## Implementation phases

### Phase 1 - Generic backend and QUT tutorial MVP

- Add `calculator_mode` to the award registry. Existing awards use `shift`;
  QUT Sessional uses `activity`.
- Create a separate activity calculation service and
  `POST /calculate/activity`. Leave the existing `/calculate` contract
  unchanged.
- Introduce a validated, date-effective activity-scheme configuration format.
  Each classification declares:
  - Payment basis: `composite_unit` or `direct_hour`.
  - Quantity unit: delivered hour, session, item or another configured unit.
  - Published unit rate.
  - Incorporated hours per unit.
  - Eligibility and variant rules.
  - Repeat-classification rules.
- Configure QUT normal/repeat tutorial rates, including standard and relevant
  PhD/full-coordinator variants.
- Implement repeat classification using exact
  `course + activity family + topic/teaching-week`, with the earlier delivery
  occurring within seven calendar days.
- Support fractional delivered hours and select the published rate by activity
  date.
- Return an auditable result explaining the selected classification, rate,
  quantity and calculation.

### Phase 2 - Blank QUT activity frontend

- Route the selected award to either the existing shift screen or a new
  activity screen. Retain the shared shell, tabs, disclaimers and gross/net
  summary infrastructure.
- Present a Monday-to-Sunday fortnight based on a user-selected Monday start
  date. All fourteen days start blank.
- Add course records with course code/name and higher-rate eligibility:
  - Standard.
  - Relevant doctoral qualification.
  - Full subject/unit coordination duties.
- Allow multiple date-only work items per day. Do not collect start, finish or
  break times.
- Add a teaching-activity form containing course, date, topic/teaching week,
  activity, required variant and delivered quantity.
- Show automatic normal/repeat classification, its matched earlier activity,
  incorporated hours and expected pay.
- Permit a classification override with a mandatory reason. Retain both the
  automatic and overridden result for auditability.
- Use QUT-specific result labels - activity pay, direct-hours pay, delivered
  hours, incorporated hours and actual hours - instead of
  ordinary/overtime/penalty terminology.

### Phase 3 - Full QUT sessional activity catalogue

Add all supplied Schedule Two/Five classifications:

- Lectures: basic, developed, specialised and automatically classified repeat.
- Tutorials: normal/repeat with standard and PhD/coordinator rates.
- Clinical health education: normal/little preparation and higher-rate
  variants.
- Music accompanying: standard and higher-rate variants.
- Marking: standard, standard PhD/coordinator and higher-level marking.
- Other required academic activity: standard and PhD/coordinator.
- Present workshops, practicals, non-health clinical sessions, field trips,
  performances, simulations, studios, supplementary tuition, supervision,
  meetings and consultation as descriptive subtypes of other required academic
  activity.

Apply two payment behaviours:

- **Composite activity:** expected pay is delivered quantity multiplied by the
  published unit rate. Users may enter one total actual-associated-hours figure
  for comparison with incorporated hours.
- **Direct hours:** expected pay is actual required/approved hours multiplied by
  the published hourly rate.

An excess over incorporated hours produces a review warning and does not
automatically create additional pay. Separately approved marking is entered as
a direct-hours item and must not also be counted as associated time.

### Phase 4 - History, minimum engagement and supporting surfaces

- Store QUT courses, entries and overrides in browser-local history. When
  calculating a fortnight, automatically include the preceding seven days
  solely for repeat classification.
- Make history visible, editable and clearable. Show a warning when history is
  unavailable, such as on a new browser.
- Give every work item a unique occasion by default. Let users group same-date
  items into one occasion without entering times.
- For each occasion, compare direct paid hours plus configured incorporated
  hours with QUT's two-hour minimum and report any shortfall.
- Initially report a minimum-engagement shortfall as a review item, not a
  monetary adjustment, because the valuation of a fractional composite
  activity top-up requires a confirmed QUT payroll example.
- Extend bulk CSV import with dated activity records only after the web workflow
  is stable.
- Update the ruleset documentation to distinguish shift rules from the new
  activity-scheme contract and document the QUT-only public scope.

## Public interfaces

### Award metadata

```json
{
  "key": "qut_sessional",
  "label": "QUT Sessional Academic Staff",
  "calculator_mode": "activity",
  "activity_scheme": "qut_sessional"
}
```

### Activity calculation request

```json
{
  "scheme": "qut_sessional",
  "period_start": "2026-08-17",
  "courses": [
    {
      "id": "course-1",
      "code": "LLB101",
      "eligibility": "relevant_phd"
    }
  ],
  "work_items": [
    {
      "id": "item-1",
      "kind": "activity",
      "date": "2026-08-18",
      "occasion_id": "occasion-1",
      "course_id": "course-1",
      "topic": "Week 3 - Negligence",
      "activity": "tutorial",
      "delivered_quantity": 1.5,
      "actual_associated_hours": 2.5
    },
    {
      "id": "item-2",
      "kind": "direct_hours",
      "date": "2026-08-19",
      "occasion_id": "occasion-2",
      "course_id": "course-1",
      "activity": "standard_marking",
      "actual_hours": 3.5,
      "required_or_approved": true
    }
  ],
  "lookback_items": []
}
```

### Activity calculation response

Return:

- Per-item automatic and final classification.
- Repeat match and explanation.
- Effective published rate and rate date.
- Delivered quantity or actual paid hours.
- Incorporated, actual and variance hours.
- Expected item pay.
- Occasion-level minimum-engagement status.
- Activity-pay, direct-hours-pay and gross-pay totals.
- Review warnings and override reasons.

## Validation and behaviour

- Dates must fall within the selected fortnight. Lookback entries must be
  earlier and are never added to current-period pay.
- Topic/teaching week is required for repeat-eligible activities.
- Course is required for teaching and marking, but optional for general
  meetings or institutional activities.
- Coordinator eligibility belongs to a course. Relevant-PhD eligibility may
  default across courses but remains stored per course.
- Lecture users select basic, developed or specialised for an original
  delivery. A qualifying later delivery uses the repeat lecture
  classification.
- Different courses, topics or activity families never match as repeats.
- Exactly seven calendar days qualifies; more than seven does not.
- Weekend dates do not change QUT sessional activity rates in this scheme.
- Same-date items remain separate occasions unless the user explicitly groups
  them.
- Published composite rates are stored directly and are never reconstructed by
  multiplying a generic base hourly rate.
- Existing shift requests, custom shift rulesets and results remain backward
  compatible.

## Test plan

- Existing backend and frontend shift-calculator suites continue unchanged.
- Verify normal and repeat tutorials for standard, PhD and coordinator
  eligibility.
- Verify same topic within seven days, exactly seven days, outside seven days,
  different topic/course and prior-fortnight lookback.
- Verify user overrides retain the automatic classification and require a
  reason.
- Verify basic/developed/specialised lectures become repeat when eligible.
- Verify clinical, music, marking and other-activity rate selection.
- Verify fractional quantities, rate-effective dates and currency rounding.
- Verify actual-associated-hours comparisons never automatically increase pay.
- Verify direct approved marking is paid once and is not incorporated into a
  teaching activity.
- Verify occasion grouping and two-hour shortfall reporting without times.
- Verify Saturday/Sunday entries use the same QUT sessional rates.
- Frontend tests cover mode routing, blank fortnight creation, dynamic
  activity/direct-hours forms, course eligibility, local lookback history and
  QUT-specific summaries.
- End-to-end acceptance scenario: enter an original tutorial, a same-topic
  repeat, direct marking and a grouped same-date occasion; confirm
  classifications, warnings and gross total.

## Assumptions

- The generic engine is reusable, but QUT Sessional is the only public activity
  scheme in the initial release.
- Dates are mandatory; clock times are not collected.
- Actual associated work is a single total on its paid activity, not a dated
  sub-log.
- Repeat history is browser-local with an explicit override, not account-backed.
- The initial authoritative sources are the
  [QUT Academic Enterprise Agreement 2022-2025](https://cms.qut.edu.au/__data/assets/pdf_file/0010/974026/2022-2025-QUT-Enterprise-Agreement-Academic-2022-2025.pdf)
  and the
  [QUT Sessional Academic Staff salary schedule](https://cms.qut.edu.au/__data/assets/pdf_file/0007/974023/Salary-Scales-Sessional-Academic-Staff_2025.12.13.pdf).
