import unittest
from pathlib import Path

import app
from kamichizu.demo import build_demo_human_report
from kamichizu.openai_ocr import OcrImage
from kamichizu.models import HumanReport


class FakeUpload:
    def __init__(self, name="paper.jpg", mime_type="image/jpeg", data=b"image"):
        self.name = name
        self.type = mime_type
        self._data = data

    def getvalue(self):
        return self._data


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

    def test_uploaded_files_become_ocr_images_without_interpretation(self):
        images = app.build_ocr_images([FakeUpload(name="a.png", mime_type="image/png", data=b"abc")])

        self.assertEqual(images, [OcrImage(name="a.png", mime_type="image/png", data=b"abc")])

    def test_unmatched_evidence_prevents_complete_success(self):
        report = HumanReport(
            summary_rows=(),
            ride_rows=({"No": 7, "状態": "要確認"},),
            claim_rows=(),
            diagnostics=("unmatched evidence E01:08",),
        )

        issues = app.build_completion_issues(report)

        self.assertEqual(issues, ["メーター明細に未照合が1件残っています。", "No.7 が要確認です。"])

    def test_all_mi_large_report_prevents_complete_success(self):
        report = HumanReport(
            summary_rows=(
                {"項目": "現収", "金額": 0, "内訳": "通常 0 + 特例 0"},
                {"項目": "未収", "金額": 41500, "内訳": "通常 41500 + 特例 0"},
            ),
            ride_rows=tuple({"No": index, "時刻": "10:10", "現収": "", "未収": 1000, "摘要": "Visa", "状態": ""} for index in range(1, 13)),
            claim_rows=(),
            diagnostics=(),
        )

        issues = app.build_completion_issues(report)

        self.assertEqual(issues, ["現収が0円です。紙日報の現収欄・未収欄のOCR位置を確認してください。"])

    def test_unmatched_evidence_message_is_human_readable(self):
        message = app._human_diagnostic_message("unmatched evidence E01:08")

        self.assertEqual(message, "メーター明細に未照合が残っています（E01:08）")

    def test_unmatched_evidence_message_explains_missing_paper_row(self):
        message = app._human_diagnostic_message(
            "unmatched evidence E01:08 reason=no_paper_time_within_9_minutes time=17:08 amount=1200"
        )

        self.assertIn("17:08 / 1,200円", message)
        self.assertIn("対応する紙日報行が見つかりません", message)

    def test_unmatched_evidence_message_explains_missing_payment_destination(self):
        message = app._human_diagnostic_message(
            "unmatched evidence E01:05 reason=paper_time_match_without_payment_destination time=10:46 amount=2430 near_paper=03@2m"
        )

        self.assertIn("10:46 / 2,430円", message)
        self.assertIn("現収・未収・摘要の判断材料が不足", message)

    def test_app_uses_ocr_observation_route_without_adopted_report_shortcut(self):
        app_source = Path("app.py").read_text(encoding="utf-8")

        self.assertIn("build_observations_from_images", app_source)
        self.assertIn("build_human_report_from_observations", app_source)
        self.assertIn("file_uploader", app_source)
        self.assertNotIn("AdoptedReport", app_source)
        self.assertNotIn("AdoptedRow", app_source)

    def test_demo_does_not_hand_build_adopted_report(self):
        demo_source = Path("kamichizu/demo.py").read_text(encoding="utf-8")

        self.assertNotIn("AdoptedReport", demo_source)
        self.assertNotIn("AdoptedRow", demo_source)
        self.assertIn("build_human_report_from_sources", demo_source)


if __name__ == "__main__":
    unittest.main()
