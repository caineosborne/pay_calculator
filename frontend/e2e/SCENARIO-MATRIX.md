# Payroll E2E scenario matrix

All calculations use an independently written test-side reference calculator at `payroll-reference.js`; it does not import the application rule engine.

| Scenario | Award/configuration | Timesheet | Expected result |
| --- | --- | --- | --- |
| Weekday roster | Built-in Hospitality, shift worker | Mon–Fri 09:00–17:00, 0.5h unpaid break | 37.50 ordinary hours, $1,125.00 gross |
| Daily boundary | Built-in Hospitality | 2.5h short shift plus 10.5h long shift | 12.50 total, 0.50 daily OT, $397.50 gross |
| Fortnight boundary | Built-in Hospitality | Ten 8h weekday shifts across two weeks | 76 ordinary, 4 period OT, $2,460.00 gross |
| Weekend/evening | Built-in Hospitality | Fri 18:00–22:00, Sat 09:00–17:00, Sun 09:00–17:00 | 20 ordinary, $138 penalty loading, $738 gross |
| Split shift | Built-in Hospitality | Mon 09:00–12:00 and 17:00–22:00 | 8 ordinary, 3 loaded evening hours, $258 gross |
| Part-time amendment | Built-in Hospitality, part-time 20h/week | Two 8h shifts; amend second to 10h | 24h then 22h top-up; $1,200 gross in both cases |
| Full-time top-up toggle | Custom Hospitality copied in UI | Mon 09:00–17:00 | Disable entitlement: 0 top-up/$240; re-enable: 68h top-up/$2,280 |
| Config mutation | Custom Hospitality copied in UI | Mon 08:00–17:00 | Daily cap 8 => 8 ordinary/1 OT/$285; change cap 10 => 9 ordinary/$270 |
| Invalid overlap | Built-in Hospitality | Mon 09:00–14:00 plus 13:00–17:00 | Calculation error, no silent result |

## Current-product limits

The current UI/API does not model employee identities, dates/public holidays, classifications, multiple base rates, paid breaks, meal/rest-break compliance, minimum engagements, allowances, sleepovers, general rule enable/disable flags, stacking/substitution controls, or export/download. Shift start/end entry is integer hours only (although breaks accept decimals), so one-minute/15-minute boundary tests cannot be expressed through the frontend. The suite intentionally does not claim coverage for those unsupported capabilities. The specific full-time and part-time top-up entitlements are configurable and covered.
