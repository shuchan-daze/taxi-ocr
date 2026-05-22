import unittest
from pathlib import Path

import app
from kamichizu.demo import build_demo_human_report
from kamichizu.models import HumanReport


class MinimalAppTest(unittest.TestCase):
    def test_demo_human_report_uses_formal_pipeline_sections(self):
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

    def test_report_table_keeps_human_columns_and_places_claims_after_target(self):
        report = build_demo_human_report()

        rows = app.build_report_table_rows(report)

        self.assertEqual(list(rows[0]), ["No", "人数", "時刻", "現収", "未収", "摘要", "状態"])
        self.assertEqual(rows[0]["現収"], "900")
        self.assertEqual(rows[1]["未収"], "2,430")
        self.assertEqual(rows[2]["No"], "△2")
        self.assertEqual(rows[2]["未収"], "270")
        self.assertEqual(rows[2]["摘要"], "障割請求")
        self.assertEqual(rows[4]["No"], "△4")
        self.assertEqual(rows[4]["現収"], "16,400")
        self.assertEqual(rows[4]["摘要"], "貸切")

    def test_app_does_not_wire_photo_ocr_to_final_report(self):
        app_source = Path("app.py").read_text(encoding="utf-8")

        self.assertNotIn("build_observations_from_images", app_source)
        self.assertNotIn("OPENAI_API_KEY", app_source)
        self.assertNotIn("file_uploader", app_source)
        self.assertNotIn("写真から日報を作成", app_source)

    def test_demo_does_not_hand_build_adopted_report(self):
        demo_source = Path("kamichizu/demo.py").read_text(encoding="utf-8")

        self.assertNotIn("AdoptedReport", demo_source)
        self.assertNotIn("AdoptedRow", demo_source)
        self.assertIn("build_human_report_from_sources", demo_source)


if __name__ == "__main__":
    unittest.main()
