import unittest

from datetime import date
from unittest.mock import patch

from oura_project.auth import auth_status, get_access_token
from oura_project.client import DateRange
from oura_project.metrics import (
    activity_summary,
    daily_readiness_summary,
    heart_rate_summary,
    readiness_summary,
    sleep_summary,
)


class DailyReadinessSummaryTest(unittest.TestCase):
    def test_extracts_core_fields(self):
        payload = {
            "day": "2026-05-15",
            "score": 82,
            "temperature_deviation": -0.1,
            "contributors": {
                "resting_heart_rate": 91,
                "hrv_balance": 74,
                "sleep_balance": 88,
            },
        }

        self.assertEqual(
            daily_readiness_summary(payload),
            {
                "date": "2026-05-15",
                "score": 82,
                "temperature_deviation": -0.1,
                "resting_heart_rate": 91,
                "hrv_balance": 74,
                "sleep_balance": 88,
            },
        )

    def test_handles_missing_contributors(self):
        payload = {
            "day": "2026-05-15",
            "score": 70,
            "contributors": None,
        }

        self.assertEqual(
            daily_readiness_summary(payload),
            {
                "date": "2026-05-15",
                "score": 70,
                "temperature_deviation": None,
                "resting_heart_rate": None,
                "hrv_balance": None,
                "sleep_balance": None,
            },
        )


if __name__ == "__main__":
    unittest.main()


class DashboardSupportTest(unittest.TestCase):
    def test_date_range_trailing_days(self):
        range_ = DateRange.trailing_days(7, today=date(2026, 5, 15))

        self.assertEqual(range_.query(), {"start_date": "2026-05-09", "end_date": "2026-05-15"})
        self.assertEqual(
            range_.datetime_query(),
            {
                "start_datetime": "2026-05-09T00:00:00",
                "end_datetime": "2026-05-15T23:59:59",
            },
        )

    def test_auth_status_uses_environment_token(self):
        with patch.dict("os.environ", {"OURA_ACCESS_TOKEN": "secret"}, clear=False):
            self.assertEqual(get_access_token(), "secret")
            self.assertTrue(auth_status().configured)

    def test_readiness_summary_adds_average(self):
        records = [
            {"day": "2026-05-14", "score": 80, "contributors": {"hrv_balance": 70}},
            {"day": "2026-05-15", "score": 90, "contributors": {"hrv_balance": 80}},
        ]

        self.assertEqual(readiness_summary(records)["average_score"], 85.0)
        self.assertEqual(readiness_summary(records)["date"], "2026-05-15")

    def test_sleep_activity_and_heart_summaries(self):
        sleep = sleep_summary(
            [{"day": "2026-05-15", "score": 88, "total_sleep_duration": 28800, "efficiency": 91}]
        )
        activity = activity_summary(
            [{"day": "2026-05-15", "score": 77, "steps": 10000, "active_calories": 550}]
        )
        heart = heart_rate_summary(
            [{"timestamp": "2026-05-15T10:00:00Z", "bpm": 60}, {"timestamp": "2026-05-15T11:00:00Z", "bpm": 70}]
        )

        self.assertEqual(sleep["total_sleep_hours"], 8.0)
        self.assertEqual(activity["steps"], 10000)
        self.assertEqual(heart["average_bpm"], 65.0)
