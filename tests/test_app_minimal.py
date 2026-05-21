import unittest
from pathlib import Path

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
        self.assertEqual(labels, ["現収", "未収", "総売上", "消費税", "税抜運収"])

    def test_report_table_places_claims_in_payment_columns(self):
        report = build_demo_human_report()

        rows = app.build_report_table_rows(report)

        self.assertEqual(rows[0]["未収"], 2430)
        self.assertEqual(rows[1]["No"], "△1")
        self.assertEqual(rows[1]["未収"], 270)
        self.assertEqual(rows[1]["摘要"], "障割請求")
        self.assertEqual(rows[3]["No"], "△2")
        self.assertEqual(rows[3]["現収"], 16400)
        self.assertEqual(rows[3]["摘要"], "貸切")

    def test_demo_does_not_hand_build_adopted_report(self):
        demo_source = Path("kamichizu/demo.py").read_text(encoding="utf-8")

        self.assertNotIn("AdoptedReport", demo_source)
        self.assertNotIn("AdoptedRow", demo_source)
        self.assertIn("build_human_report_from_case", demo_source)


if __name__ == "__main__":
    unittest.main()
