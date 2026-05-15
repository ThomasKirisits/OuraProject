"""Streamlit dashboard for Oura API metrics."""

from __future__ import annotations

import os
from datetime import date

import streamlit as st

from oura_project.auth import auth_status, get_access_token
from oura_project.client import DateRange, OuraApiError, OuraClient
from oura_project.metrics import (
    activity_summary,
    heart_rate_summary,
    readiness_summary,
    sleep_summary,
)


DEFAULT_DAYS_BACK = int(os.getenv("OURA_DAYS_BACK", "30"))


def metric(label: str, value: object, help_text: str | None = None) -> None:
    st.metric(label, "n/a" if value is None else value, help=help_text)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_dashboard_data(token: str, days_back: int) -> dict[str, object]:
    date_range = DateRange.trailing_days(days_back, today=date.today())
    client = OuraClient(token)
    return {
        "range": date_range,
        "personal_info": client.personal_info(),
        "daily_readiness": client.daily_readiness(date_range),
        "daily_sleep": client.daily_sleep(date_range),
        "daily_activity": client.daily_activity(date_range),
        "heart_rate": client.heart_rate(date_range),
    }


def render_auth_panel() -> None:
    status = auth_status()
    with st.sidebar:
        st.header("Authentication")
        if status.configured:
            st.success(status.message)
            st.caption(f"Source: {status.source}")
        else:
            st.warning(status.message)
            st.code("export OURA_ACCESS_TOKEN=...", language="bash")
        st.divider()
        st.caption("This app runs locally. Tokens are read from your environment and are not stored by the dashboard.")


def render_dashboard(data: dict[str, object]) -> None:
    readiness = readiness_summary(data["daily_readiness"])  # type: ignore[arg-type]
    sleep = sleep_summary(data["daily_sleep"])  # type: ignore[arg-type]
    activity = activity_summary(data["daily_activity"])  # type: ignore[arg-type]
    heart = heart_rate_summary(data["heart_rate"])  # type: ignore[arg-type]
    date_range = data["range"]

    st.title("Oura Personal Health Dashboard")
    st.caption("Informational analytics only. This is not medical advice.")
    st.caption(f"Window: {date_range.start_date.isoformat()} to {date_range.end_date.isoformat()}")

    st.subheader("Today / Latest Daily Records")
    cols = st.columns(4)
    with cols[0]:
        metric("Readiness", readiness.get("score"), "Latest daily readiness score")
    with cols[1]:
        metric("Sleep", sleep.get("score"), "Latest daily sleep score")
    with cols[2]:
        metric("Activity", activity.get("score"), "Latest daily activity score")
    with cols[3]:
        metric("Latest HR", heart.get("latest_bpm"), "Most recent heart-rate sample")

    st.subheader("Recovery")
    cols = st.columns(4)
    with cols[0]:
        metric("Avg readiness", readiness.get("average_score"))
    with cols[1]:
        metric("Resting HR contributor", readiness.get("resting_heart_rate"))
    with cols[2]:
        metric("HRV balance", readiness.get("hrv_balance"))
    with cols[3]:
        metric("Temp deviation", readiness.get("temperature_deviation"))

    st.subheader("Sleep")
    cols = st.columns(4)
    with cols[0]:
        metric("Avg sleep score", sleep.get("average_score"))
    with cols[1]:
        metric("Sleep hours", sleep.get("total_sleep_hours"))
    with cols[2]:
        metric("Efficiency", sleep.get("efficiency"))
    with cols[3]:
        metric("Restless periods", sleep.get("restless_periods"))

    st.subheader("Activity")
    cols = st.columns(4)
    with cols[0]:
        metric("Avg activity score", activity.get("average_score"))
    with cols[1]:
        metric("Steps", activity.get("steps"))
    with cols[2]:
        metric("Active calories", activity.get("active_calories"))
    with cols[3]:
        metric("Walking distance", activity.get("equivalent_walking_distance"))

    st.subheader("Raw Data Preview")
    tabs = st.tabs(["Readiness", "Sleep", "Activity", "Heart rate"])
    with tabs[0]:
        st.dataframe(data["daily_readiness"], use_container_width=True)
    with tabs[1]:
        st.dataframe(data["daily_sleep"], use_container_width=True)
    with tabs[2]:
        st.dataframe(data["daily_activity"], use_container_width=True)
    with tabs[3]:
        st.dataframe(data["heart_rate"], use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Oura Dashboard", layout="wide")
    render_auth_panel()

    with st.sidebar:
        days_back = st.slider("Days back", min_value=7, max_value=180, value=DEFAULT_DAYS_BACK, step=1)
        refresh = st.button("Refresh data")
        if refresh:
            st.cache_data.clear()

    token = get_access_token()
    if not token:
        st.title("Oura Personal Health Dashboard")
        st.info("Set OURA_ACCESS_TOKEN and restart Streamlit to load live Oura data.")
        return

    try:
        with st.spinner("Loading Oura data..."):
            data = fetch_dashboard_data(token, days_back)
    except OuraApiError as exc:
        st.error(str(exc))
        return

    render_dashboard(data)


if __name__ == "__main__":
    main()
