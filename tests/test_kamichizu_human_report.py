import unittest

from kamichizu.models import AdoptedReport, AdoptedRow, ViewMap
from kamichizu.specials import make_charter_claim, make_public_discount_claim
from kamichizu.view import build_human_report


class KamichizuHumanReportTest(unittest.TestCase):
    def test_human_report_wraps_summary_rides_claims_and_diagnostics(self):
        report = AdoptedReport(
            rows=(AdoptedRow(row_addr="01", values={"time": "10:44", "mi": 2430}),),
            claims=(
                make_public_discount_claim(target_row_addr="01", meter_amount=2430, expected_claim_amount=270),
                make_charter_claim(target_row_addr="05", amount=16400, payment_kind="gen"),
            ),
            diagnostics=("P01:01_AF: paper amount differs",),
        )
        view_map = ViewMap(view_id="taxi", columns=(("time", "時刻"), ("mi", "未収"), ("status", "状態")))

        human_report = build_human_report(report, view_map)

        self.assertEqual(human_report.summary_rows[-1]["項目"], "総売上")
        self.assertEqual(human_report.ride_rows, ({"時刻": "10:44", "未収": 2430, "状態": ""},))
        self.assertEqual(human_report.claim_rows[0]["種別"], "障割請求")
        self.assertEqual(human_report.claim_rows[1]["種別"], "貸切")
        self.assertEqual(human_report.diagnostics, ("P01:01_AF: paper amount differs",))


if __name__ == "__main__":
    unittest.main()
