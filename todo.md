# Todo

# Split / Extended Overtime - currently only applies Monday to Friday


## Clerks Private Sector Award

- Extend `extended_overtime_rate` so it can apply on weekends for the Clerks Private Sector award only.
- Confirm the precedence between weekend overtime, span overtime, and the second overtime tier so the award behaves correctly on Saturday/Sunday.
- Add a focused test case for a weekend shift that crosses the overtime threshold and verify the correct multiplier is used.

## MA120

- Confirm that split/extended overtime can apply on any day of the week, including Saturday and Sunday, even though the award is usually worked Monday to Friday.
- Add a test case for a weekend MA120 shift that exceeds the first overtime tier and verify the second tier still applies.
