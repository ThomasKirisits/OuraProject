import unittest

from oura_project.metrics import daily_readiness_summary


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
