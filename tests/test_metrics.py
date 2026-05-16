import unittest

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from oura_project.auth import OAuthConfig, auth_status, authorization_url, get_access_token, save_token, token_expired
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

    def test_auth_status_uses_saved_oauth_token(self):
        with TemporaryDirectory() as directory:
            token_file = Path(directory) / "token.json"
            save_token({"access_token": "secret", "expires_in": 3600}, token_file)

            self.assertTrue(auth_status(token_file).configured)
            self.assertEqual(get_access_token(token_file), "secret")

    def test_authorization_url_contains_expected_oauth_parameters(self):
        config = OAuthConfig(
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://127.0.0.1:8765/callback",
            scopes="personal daily",
        )

        url = authorization_url(config, "state-value")

        self.assertIn("response_type=code", url)
        self.assertIn("client_id=client-id", url)
        self.assertIn("scope=personal+daily", url)
        self.assertIn("state=state-value", url)

    def test_token_expired_respects_missing_or_expired_tokens(self):
        self.assertTrue(token_expired(None))
        self.assertTrue(token_expired({"access_token": "secret", "expires_at": 1}))
        self.assertFalse(token_expired({"access_token": "secret"}))

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
