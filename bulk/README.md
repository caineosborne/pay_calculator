# Pay Checker Bulk

This is a separate Streamlit product. It does not change the calculator API or duplicate award logic: it turns dated CSV rows into the existing `POST /calculate` payload, once per employee and fortnight. Each employee has an independent award, rate, employment type, contracted hours and pay-cycle settings.

## Run locally

Start the existing API from `backend`:

```bash
uvicorn main:app --reload
```

In a second terminal, install the bulk UI dependency and run it:

```bash
pip install -r bulk/requirements.txt
streamlit run bulk/app.py
```

Set `PAY_CHECKER_API_URL` if the API is not at `http://localhost:8000`.

## CSV format

Required columns: `shift_date` (`YYYY-MM-DD`), `start_time`, `end_time`.

Optional columns: `employee` (defaults to `Employee`) and `break_duration` (defaults to `0.5`). Times currently need to be whole hours, matching the existing calculator API.

Choose the weekday that starts Week 1. Optionally provide the date of a known Week 1 start to align the results to an organisation's established pay calendar; otherwise the first uploaded shift determines the first fortnight's Week 1.

Multiple periods on one date are submitted together so existing daily overtime and gap-rule behaviour is preserved. The shift screen therefore shows one calculated workday, with its source periods combined in the `Periods` column.

## Employee master data (EMD)

Optionally upload a strict EMD CSV to configure employees instead of using the Streamlit table. Headers must be exactly:

```text
employee,hourly_rate,award,worker_type,employment_type,contracted_hours,pay_cycle_start_day,pay_cycle_anchor,rule_configuration
```

The employee names must exactly match the `employee` values in the shifts CSV. `contracted_hours`, `pay_cycle_anchor`, and `rule_configuration` may be blank.
