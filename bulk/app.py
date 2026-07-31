"""Streamlit entry point for the bulk pay-checking product."""

import os

import streamlit as st

from calculator_client import BulkImportError, WEEKDAYS, calculate_upload, parse_csv, rows_to_csv


st.set_page_config(page_title="Pay Checker Bulk", layout="wide")
st.title("Pay Checker Bulk")
st.caption("Upload dated shifts, calculate through the existing Pay Checker API, and review each workday or fortnight.")

with st.sidebar:
    st.header("Employment profile")
    api_url = st.text_input("Calculator API URL", value=os.getenv("PAY_CHECKER_API_URL", "http://localhost:8000"))
    hourly_rate = st.number_input("Hourly rate ($)", min_value=0.01, value=30.00, step=0.01)
    award = st.selectbox("Award", ["aged_care", "hospitality", "child_care", "nurses", "clerks_private_sector", "MA000018", "MA000120", "eb11"])
    worker_type = st.selectbox("Worker type", ["shift", "day"])
    employment_type = st.selectbox("Employment type", ["full_time", "part_time", "casual"])
    contracted_hours = st.number_input("Contracted hours per week", min_value=0.0, value=38.0) if employment_type in {"full_time", "part_time"} else None
    pay_cycle_start_day = st.selectbox("Fortnight starts on", WEEKDAYS, index=0)
    pay_cycle_anchor = st.text_input("First Week 1 start (optional, YYYY-MM-DD)")
    rule_configuration = st.text_input("Custom rule configuration (optional)")

st.subheader("Shift CSV")
st.code("employee,shift_date,start_time,end_time,break_duration\nAlex,2026-07-06,09:00,17:00,0.5", language="csv")
st.caption("Required columns: shift_date, start_time, end_time. Optional: employee, break_duration. Times must be whole hours because the current API uses hour-based shifts.")
uploaded = st.file_uploader("Choose a CSV", type="csv")

if uploaded and st.button("Calculate bulk upload", type="primary"):
    try:
        shifts = parse_csv(uploaded.getvalue())
        profile = {
            "hourly_rate": hourly_rate, "award": award, "worker_type": worker_type,
            "employment_type": employment_type, "contracted_hours": contracted_hours,
            "pay_cycle_start_day": pay_cycle_start_day, "pay_cycle_anchor": pay_cycle_anchor,
            "rule_configuration": rule_configuration,
        }
        with st.spinner("Calculating each employee and fortnight through the API…"):
            shift_rows, fortnight_rows = calculate_upload(shifts, profile, api_url)
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
