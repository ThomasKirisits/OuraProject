"""Small metric helpers for Oura API payloads."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from statistics import mean
from typing import Any


def daily_readiness_summary(day: Mapping[str, object]) -> dict[str, object]:
    """Return a compact summary for one Oura daily readiness record.

    The Oura API commonly represents daily readiness with a top-level score and
    a nested contributors object. This helper keeps the raw payload handling
    narrow so dashboard code can consume a predictable shape.
    """

    contributors = day.get("contributors")
    if not isinstance(contributors, Mapping):
        contributors = {}

    return {
        "date": day.get("day"),
        "score": day.get("score"),
        "temperature_deviation": day.get("temperature_deviation"),
        "resting_heart_rate": contributors.get("resting_heart_rate"),
        "hrv_balance": contributors.get("hrv_balance"),
        "sleep_balance": contributors.get("sleep_balance"),
    }


def latest_by_day(records: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """Return the newest daily Oura record by its day field."""

    dated = [record for record in records if record.get("day")]
    if not dated:
        return None
    return max(dated, key=lambda record: str(record.get("day")))


def minutes_to_hours(minutes: int | float | None) -> float | None:
    if minutes is None:
        return None
    return round(float(minutes) / 60.0, 2)


def seconds_to_hours(seconds: int | float | None) -> float | None:
    if seconds is None:
        return None
    return round(float(seconds) / 3600.0, 2)


def average_numeric(records: list[Mapping[str, Any]], key: str) -> float | None:
    values = [record.get(key) for record in records]
    numbers = [float(value) for value in values if isinstance(value, int | float)]
    if not numbers:
        return None
    return round(mean(numbers), 2)


def readiness_summary(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    latest = latest_by_day(records)
    if not latest:
        return {}
    summary = daily_readiness_summary(latest)
    summary["average_score"] = average_numeric(records, "score")
    return summary


def sleep_summary(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    latest = latest_by_day(records)
    if not latest:
        return {}
    return {
        "date": latest.get("day"),
        "score": latest.get("score"),
        "average_score": average_numeric(records, "score"),
        "total_sleep_hours": seconds_to_hours(latest.get("total_sleep_duration")),
        "efficiency": latest.get("efficiency"),
        "restless_periods": latest.get("restless_periods"),
    }


def activity_summary(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    latest = latest_by_day(records)
    if not latest:
        return {}
    return {
        "date": latest.get("day"),
        "score": latest.get("score"),
        "average_score": average_numeric(records, "score"),
        "steps": latest.get("steps"),
        "active_calories": latest.get("active_calories"),
        "equivalent_walking_distance": latest.get("equivalent_walking_distance"),
    }


def heart_rate_summary(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    values = [record.get("bpm") for record in records]
    bpms = [float(value) for value in values if isinstance(value, int | float)]
    latest = max(records, key=lambda record: str(record.get("timestamp", ""))) if records else None
    return {
        "latest_bpm": latest.get("bpm") if latest else None,
        "latest_timestamp": latest.get("timestamp") if latest else None,
        "average_bpm": round(mean(bpms), 2) if bpms else None,
        "samples": len(records),
    }


def parse_iso_date(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
