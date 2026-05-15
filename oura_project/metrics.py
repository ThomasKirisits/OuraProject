"""Small metric helpers for Oura API payloads."""

from __future__ import annotations

from collections.abc import Mapping


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
