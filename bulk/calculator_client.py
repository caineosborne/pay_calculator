"""CSV preparation and API client for the standalone bulk product."""

from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


WEEKDAYS = (
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
)
REQUIRED_COLUMNS = {"shift_date", "start_time", "end_time"}
EMD_COLUMNS = ("employee", "hourly_rate", "award", "worker_type", "employment_type", "contracted_hours", "pay_cycle_start_day", "pay_cycle_anchor", "rule_configuration")
AWARDS = {"fast_food", "coles_2024", "gria_2026", "woolies_2024_demo"}


class BulkImportError(ValueError):
    """A user-facing CSV or API validation error."""


def _whole_hour(value: str, field: str, row_number: int) -> int:
    """Parse the hour-only time model accepted by the existing API."""
    text = value.strip()
    try:
        if ":" in text:
            parsed = datetime.strptime(text, "%H:%M")
            if parsed.minute:
                raise ValueError
            hour = parsed.hour
        else:
            hour = int(text)
    except ValueError as error:
        raise BulkImportError(
            f"Row {row_number}: {field} must be a whole hour (e.g. 09:00 or 9)."
        ) from error
    if not 0 <= hour <= 23:
        raise BulkImportError(f"Row {row_number}: {field} must be between 00:00 and 23:00.")
    return hour


def parse_csv(contents: bytes) -> list[dict[str, Any]]:
    """Validate a shift CSV and return normalised dated attendance periods."""
    try:
        rows = list(csv.DictReader(io.StringIO(contents.decode("utf-8-sig"))))
    except UnicodeDecodeError as error:
        raise BulkImportError("CSV must be UTF-8 encoded.") from error
    if not rows:
        raise BulkImportError("The CSV has no shift rows.")
    fields = set(rows[0])
    missing = REQUIRED_COLUMNS - fields
    if missing:
        raise BulkImportError(f"Missing required column(s): {', '.join(sorted(missing))}.")

    shifts = []
    for row_number, row in enumerate(rows, start=2):
        try:
            shift_date = date.fromisoformat((row.get("shift_date") or "").strip())
        except ValueError as error:
            raise BulkImportError(f"Row {row_number}: shift_date must use YYYY-MM-DD.") from error
        start = _whole_hour(row.get("start_time") or "", "start_time", row_number)
        end = _whole_hour(row.get("end_time") or "", "end_time", row_number)
        try:
            break_duration = float((row.get("break_duration") or "0.5").strip())
        except ValueError as error:
            raise BulkImportError(f"Row {row_number}: break_duration must be a number of hours.") from error
        if not 0 <= break_duration <= 24:
            raise BulkImportError(f"Row {row_number}: break_duration must be between 0 and 24.")
        shifts.append({
            "employee": (row.get("employee") or "Employee").strip() or "Employee",
            "shift_date": shift_date,
            "start": start,
            "end": end,
            "break_duration": break_duration,
        })
    return shifts


def parse_emd_csv(contents: bytes) -> dict[str, dict[str, Any]]:
    """Read the strict employee master data (EMD) CSV contract."""
    try:
        reader = csv.DictReader(io.StringIO(contents.decode("utf-8-sig")))
        if tuple(reader.fieldnames or ()) != EMD_COLUMNS:
            raise BulkImportError(f"EMD headers must exactly be: {', '.join(EMD_COLUMNS)}.")
        rows = list(reader)
    except UnicodeDecodeError as error:
        raise BulkImportError("EMD must be UTF-8 encoded.") from error
    if not rows:
        raise BulkImportError("The EMD has no employee rows.")
    profiles = {}
    for row_number, row in enumerate(rows, start=2):
        employee = row["employee"].strip()
        if not employee or employee in profiles:
            raise BulkImportError(f"EMD row {row_number}: employee must be unique and non-empty.")
        try:
            hourly_rate = float(row["hourly_rate"])
            contracted_hours = float(row["contracted_hours"]) if row["contracted_hours"] else None
        except ValueError as error:
            raise BulkImportError(f"EMD row {row_number}: hourly_rate and contracted_hours must be numbers.") from error
        if hourly_rate <= 0 or (contracted_hours is not None and contracted_hours < 0):
            raise BulkImportError(f"EMD row {row_number}: hours and rate cannot be negative or zero.")
        if row["award"] not in AWARDS or row["worker_type"] not in {"shift", "day"} or row["employment_type"] not in {"full_time", "part_time", "casual"} or row["pay_cycle_start_day"] not in WEEKDAYS:
            raise BulkImportError(f"EMD row {row_number}: an award, employment value, or pay-cycle day is invalid.")
        profiles[employee] = {"hourly_rate": hourly_rate, "award": row["award"], "worker_type": row["worker_type"], "employment_type": row["employment_type"], "contracted_hours": contracted_hours, "pay_cycle_start_day": row["pay_cycle_start_day"], "pay_cycle_anchor": row["pay_cycle_anchor"], "rule_configuration": row["rule_configuration"]}
    return profiles


def cycle_start(shift_date: date, cycle_anchor: date) -> date:
    """Return the 14-day cycle start relative to a known Week 1 start."""
    period_offset = (shift_date - cycle_anchor).days // 14
    return cycle_anchor + timedelta(days=period_offset * 14)


def create_requests(shifts: list[dict[str, Any]], profiles: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Create one unchanged `/calculate` payload per employee/fortnight."""
    grouped: dict[tuple[str, date], list[dict[str, Any]]] = defaultdict(list)
    for employee in {shift["employee"] for shift in shifts}:
        if employee not in profiles:
            raise BulkImportError(f"No employment profile was supplied for {employee}.")
        profile = profiles[employee]
        cycle_day = profile["pay_cycle_start_day"]
        employee_shifts = [shift for shift in shifts if shift["employee"] == employee]
        configured_anchor = profile.get("pay_cycle_anchor")
        if configured_anchor:
            try:
                cycle_anchor = date.fromisoformat(configured_anchor)
            except ValueError as error:
                raise BulkImportError(f"{employee}: First Week 1 start must use YYYY-MM-DD.") from error
            if cycle_anchor.strftime("%A") != cycle_day:
                raise BulkImportError(f"{employee}: First Week 1 start must be a {cycle_day}.")
        else:
            earliest_shift = min(shift["shift_date"] for shift in employee_shifts)
            start_day = WEEKDAYS.index(cycle_day)
            cycle_anchor = earliest_shift - timedelta(days=(earliest_shift.weekday() - start_day) % 7)
        for shift in employee_shifts:
            grouped[(employee, cycle_start(shift["shift_date"], cycle_anchor))].append(shift)

    requests = []
    for (employee, period_start), periods in sorted(grouped.items()):
        profile = profiles[employee]
        cycle_day = profile["pay_cycle_start_day"]
        api_shifts = []
        dates_by_key: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
        for shift in periods:
            offset = (shift["shift_date"] - period_start).days
            weekday = shift["shift_date"].weekday()
            day = WEEKDAYS[weekday]
            # The core calculator sorts each week Monday-to-Sunday.  When a
            # pay cycle starts later in the week, putting its Monday/Tuesday
            # tail in week two keeps its workdays chronologically ordered.
            week = 1 if offset < 7 and weekday >= WEEKDAYS.index(cycle_day) else 2
            api_shifts.append({
                "week": week, "day": day, "start": shift["start"], "end": shift["end"],
                "break_duration": shift["break_duration"],
            })
            dates_by_key[(week, day)].append(shift)
        requests.append({
            "employee": employee,
            "period_start": period_start,
            "period_end": period_start + timedelta(days=13),
            "dates_by_key": dates_by_key,
            "payload": {
                "hourly_rate": profile["hourly_rate"],
                "worker_type": profile["worker_type"],
                "award": profile["award"],
                "employment_type": profile["employment_type"],
                "contracted_hours": profile.get("contracted_hours"),
                "rule_configuration": profile.get("rule_configuration") or None,
                "shifts": api_shifts,
            },
        })
    return requests


def call_api(api_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        f"{api_url.rstrip('/')}/calculate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode())
    except HTTPError as error:
        detail = error.read().decode() or error.reason
        raise BulkImportError(f"API rejected this fortnight: {detail}") from error
    except URLError as error:
        raise BulkImportError(f"Could not reach the calculator API: {error.reason}") from error


def calculate_upload(shifts: list[dict[str, Any]], profiles: dict[str, dict[str, Any]], api_url: str) -> tuple[list[dict], list[dict]]:
    """Call the existing API and shape its results for the two UI screens."""
    shift_rows, fortnight_rows = [], []
    for job in create_requests(shifts, profiles):
        result = call_api(api_url, job["payload"])
        fortnight_rows.append({
            "Employee": job["employee"], "Period start": job["period_start"].isoformat(),
            "Period end": job["period_end"].isoformat(),
            "Worked hours": round(result["total_hours"] - result.get("topup_hours", 0), 2),
            "Ordinary hours": result["ordinary_hours"], "Overtime hours": result["overtime_hours"],
            "Paid hours": result["total_hours"], "Gross pay": result["total_pay"],
        })
        for (week, day), source_periods in job["dates_by_key"].items():
            breakdown = result["daily_breakdown"][f"Week {week} - {day}"]
            shift_rows.append({
                "Employee": job["employee"], "Date": source_periods[0]["shift_date"].isoformat(),
                "Periods": "; ".join(f"{item['start']:02d}:00–{item['end']:02d}:00" for item in source_periods),
                "Worked hours": round(breakdown["total"], 2), "Ordinary hours": round(breakdown["ordinary"], 2),
                "Overtime hours": round(breakdown["overtime"], 2),
                "Applied rules": "; ".join(breakdown["applied_rules"]),
            })
    return shift_rows, fortnight_rows


def rows_to_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
