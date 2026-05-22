import unittest

from kamichizu.demo import build_demo_human_report, build_demo_observations, build_demo_view
from kamichizu.input import build_human_report_from_observations
from kamichizu.models import HumanReport


class KamichizuInputTest(unittest.TestCase):
    def test_observations_build_human_report(self):
        report = build_human_report_from_observations(build_demo_observations(), build_demo_view())

        self.assertIsInstance(report, HumanReport)
        self.assertEqual([row["項目"] for row in report.summary_rows], ["現収", "未収", "総売上", "消費税", "税抜運収"])
        self.assertEqual(report.ride_rows[0]["未収"], 2430)

    def test_input_requires_physical_cells(self):
        observation_data = build_demo_observations()
        observation_data["paper"]["cells"] = {"01_MI": {"raw": "2400", "value": 2400}}

        with self.assertRaises(ValueError):
            build_human_report_from_observations(observation_data, build_demo_view())

    def test_input_rejects_claims(self):
        observation_data = build_demo_observations()
        observation_data["claims"] = [
            {
                "type": "charter_sale",
                "target_global_cell_id": "P01:02_AG",
                "claim_amount": 16400,
            }
        ]

        with self.assertRaisesRegex(ValueError, r"observation\.claims is not part"):
            build_human_report_from_observations(observation_data, build_demo_view())

    def test_input_rejects_view(self):
        observation_data = build_demo_observations()
        observation_data["view"] = {"view_id": "table", "columns": []}

        with self.assertRaisesRegex(ValueError, r"observation\.view is not part"):
            build_human_report_from_observations(observation_data, build_demo_view())

    def test_input_rejects_paper_rows(self):
        observation_data = build_demo_observations()
        observation_data["paper"]["rows"] = []

        with self.assertRaisesRegex(ValueError, r"paper\.rows is not part"):
            build_human_report_from_observations(observation_data, build_demo_view())

    def test_demo_uses_formal_source_pipeline(self):
        report = build_demo_human_report()

        self.assertTrue(report.ride_rows)
        self.assertTrue(report.claim_rows)


if __name__ == "__main__":
    unittest.main()
