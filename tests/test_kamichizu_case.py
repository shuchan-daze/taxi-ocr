import unittest

from kamichizu.case import build_human_report_from_case
from kamichizu.demo import build_demo_case
from kamichizu.models import HumanReport


class KamichizuCaseTest(unittest.TestCase):
    def test_formal_case_builds_human_report(self):
        report = build_human_report_from_case(build_demo_case())

        self.assertIsInstance(report, HumanReport)
        self.assertEqual([row["項目"] for row in report.summary_rows], ["現収", "未収", "総売上", "消費税", "税抜運収"])
        self.assertEqual(report.ride_rows[0]["未収"], 2430)
        self.assertEqual(report.claim_rows[0]["種別"], "障割請求")
        self.assertEqual(report.claim_rows[1]["種別"], "貸切")

    def test_case_requires_physical_cells(self):
        case_data = build_demo_case()
        case_data["paper"]["cells"] = {"01_MI": {"raw": "2400", "value": 2400}}

        with self.assertRaises(ValueError):
            build_human_report_from_case(case_data)

    def test_case_rejects_unknown_claim_type(self):
        case_data = build_demo_case()
        case_data["claims"] = [{"type": "unknown", "target_row_addr": "01", "amount": 1}]

        with self.assertRaises(ValueError):
            build_human_report_from_case(case_data)

    def test_case_rejects_charter_amount_alias(self):
        case_data = build_demo_case()
        case_data["claims"][1]["amount"] = case_data["claims"][1].pop("claim_amount")

        with self.assertRaises(ValueError):
            build_human_report_from_case(case_data)


if __name__ == "__main__":
    unittest.main()
