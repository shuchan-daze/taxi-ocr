import unittest

import app
from kamichizu.models import HumanReport
from kamichizu.demo import build_demo_human_report


class MinimalAppTest(unittest.TestCase):
    def test_demo_human_report_exposes_only_human_report_sections(self):
        report = build_demo_human_report()

        self.assertIsInstance(report, HumanReport)
        self.assertTrue(report.summary_rows)
        self.assertTrue(report.ride_rows)
        self.assertTrue(report.claim_rows)
        self.assertTrue(report.diagnostics)

    def test_summary_contains_human_labels(self):
        report = build_demo_human_report()

        labels = [row["項目"] for row in report.summary_rows]
        self.assertEqual(labels, ["現収", "未収", "特例請求", "総売上"])


if __name__ == "__main__":
    unittest.main()
