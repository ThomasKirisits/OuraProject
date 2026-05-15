"""Minimal Oura API v2 client.

The client intentionally uses the Python standard library so tests and basic
usage do not depend on a heavyweight HTTP stack.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://api.ouraring.com/v2"


class OuraApiError(RuntimeError):
    """Raised when the Oura API request fails."""


@dataclass(frozen=True)
class DateRange:
    start_date: date
    end_date: date

    @classmethod
    def trailing_days(cls, days: int, today: date | None = None) -> "DateRange":
        if days < 1:
            raise ValueError("days must be >= 1")
        end = today or date.today()
        return cls(start_date=end - timedelta(days=days - 1), end_date=end)

    def query(self) -> dict[str, str]:
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
        }

    def datetime_query(self) -> dict[str, str]:
        return {
            "start_datetime": f"{self.start_date.isoformat()}T00:00:00",
            "end_datetime": f"{self.end_date.isoformat()}T23:59:59",
        }


class OuraClient:
    """Small Oura API v2 wrapper for dashboard data."""

    def __init__(self, access_token: str, base_url: str = BASE_URL, timeout: int = 30):
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_json(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urlencode(params)}"
        request = Request(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
                "User-Agent": "OuraProject/0.1",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OuraApiError(f"Oura API returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise OuraApiError(f"Oura API request failed: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise OuraApiError("Oura API returned invalid JSON") from exc

    def personal_info(self) -> dict[str, Any]:
        return self.get_json("usercollection/personal_info")

    def daily_sleep(self, range_: DateRange) -> list[dict[str, Any]]:
        return self.get_json("usercollection/daily_sleep", range_.query()).get("data", [])

    def daily_activity(self, range_: DateRange) -> list[dict[str, Any]]:
        return self.get_json("usercollection/daily_activity", range_.query()).get("data", [])

    def daily_readiness(self, range_: DateRange) -> list[dict[str, Any]]:
        return self.get_json("usercollection/daily_readiness", range_.query()).get("data", [])

    def heart_rate(self, range_: DateRange) -> list[dict[str, Any]]:
        return self.get_json("usercollection/heartrate", range_.datetime_query()).get("data", [])
