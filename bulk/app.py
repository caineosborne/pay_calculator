"""Streamlit entry point for the bulk pay-checking product."""

import os

import streamlit as st

from calculator_client import AWARDS, BulkImportError, EMD_COLUMNS, WEEKDAYS, calculate_upload, parse_csv, parse_emd_csv, rows_to_csv


st.set_page_config(page_title="payguide.au Bulk", layout="wide")
st.title("payguide.au Bulk")
st.caption("Upload dated shifts, calculate through the payguide.au API, and review each workday or pay period.")

with st.sidebar:
    st.header("Connection")
    api_url = st.text_input("Calculator API URL", value=os.getenv("PAY_CHECKER_API_URL", "http://localhost:8000"))

st.subheader("Shift CSV")
st.code("employee,shift_date,start_time,end_time,break_duration\nAlex,2026-07-06,09:00,17:00,0.5", language="csv")
st.caption("Required columns: shift_date, start_time, end_time. Optional: employee, break_duration. Times must be whole hours because the current API uses hour-based shifts.")
uploaded = st.file_uploader("Choose a CSV", type="csv")
emd_upload = st.file_uploader("Employee master data (EMD, optional CSV)", type="csv")
st.download_button("Download EMD template", ",".join(EMD_COLUMNS) + "\n", "employee-master-data-template.csv", "text/csv")

if uploaded:
    try:
        shifts = parse_csv(uploaded.getvalue())
        employees = sorted({shift["employee"] for shift in shifts})
        st.subheader("Employee configurations")
        st.caption("Each employee can have a different rate, award and employment settings. The same profile applies to all of that employee's uploaded shifts.")
        profile_rows = [{
            "Employee": employee, "Hourly rate": 30.0, "Award": "fast_food", "Worker type": "shift",
            "Employment type": "full_time", "Contracted hours": 38.0, "Fortnight starts": "Monday",
            "First Week 1 start": "", "Custom configuration": "",
        } for employee in employees]
        if emd_upload:
            profiles = parse_emd_csv(emd_upload.getvalue())
            if set(profiles) != set(employees):
                raise BulkImportError("EMD employees must exactly match the employee names in the shifts CSV.")
            st.success("Using employee configurations from the EMD upload.")
        else:
            configured_rows = st.data_editor(profile_rows, key="employee_profiles", hide_index=True, disabled=["Employee"], use_container_width=True, column_config={"Hourly rate": st.column_config.NumberColumn(min_value=0.01, format="$%.2f"), "Award": st.column_config.SelectboxColumn(options=sorted(AWARDS)), "Worker type": st.column_config.SelectboxColumn(options=["shift", "day"]), "Employment type": st.column_config.SelectboxColumn(options=["full_time", "part_time", "casual"]), "Fortnight starts": st.column_config.SelectboxColumn(options=WEEKDAYS)})
            profiles = {row["Employee"]: {"hourly_rate": row["Hourly rate"], "award": row["Award"], "worker_type": row["Worker type"], "employment_type": row["Employment type"], "contracted_hours": row["Contracted hours"], "pay_cycle_start_day": row["Fortnight starts"], "pay_cycle_anchor": row["First Week 1 start"], "rule_configuration": row["Custom configuration"]} for row in configured_rows}
        if st.button("Calculate bulk upload", type="primary"):
            with st.spinner("Calculating each employee and fortnight through the API…"):
                shift_rows, fortnight_rows = calculate_upload(shifts, profiles, api_url)
            st.session_state["bulk_results"] = (shift_rows, fortnight_rows)
    except BulkImportError as error:
        st.error(str(error))

if "bulk_results" in st.session_state:
    shift_rows, fortnight_rows = st.session_state["bulk_results"]
    shift_tab, fortnight_tab = st.tabs(["Shift breakdown", "Fortnight breakdown"])
    with shift_tab:
        st.dataframe(shift_rows, use_container_width=True, hide_index=True)
        st.download_button("Download shift breakdown CSV", rows_to_csv(shift_rows), "shift-breakdown.csv", "text/csv")
    with fortnight_tab:
        st.dataframe(fortnight_rows, use_container_width=True, hide_index=True)
        st.download_button("Download fortnight breakdown CSV", rows_to_csv(fortnight_rows), "fortnight-breakdown.csv", "text/csv")
