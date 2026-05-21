import unittest

from kamichizu.models import AdoptedReport, AdoptedRow, EvidenceLink, ViewMap
from kamichizu.specials import make_charter_claim, make_public_discount_claim
from kamichizu.view import build_human_report


class KamichizuHumanReportTest(unittest.TestCase):
    def test_human_report_wraps_summary_rides_claims_and_diagnostics(self):
        report = AdoptedReport(
            rows=(AdoptedRow(row_addr="01", values={"time": "10:44", "mi": 2430}),),
            claims=(
                make_public_discount_claim(
                    target_row_addr="01",
                    target_global_cell_id="P01:01_AF",
                    meter_amount=2430,
                    expected_claim_amount=270,
                    evidence=(EvidenceLink("P01:01_AF", "E01:01_AB", "discount_from_target_meter_amount"),),
                ),
                make_charter_claim(
                    target_row_addr="05",
                    target_global_cell_id="P01:05_AG",
                    claim_amount=16400,
                    payment_kind="gen",
                    evidence=(EvidenceLink("P01:05_AG", "P01:05_AG", "charter_from_paper_memo"),),
                ),
            ),
            diagnostics=("P01:01_AF: paper amount differs",),
        )
        view_map = ViewMap(view_id="taxi", columns=(("time", "時刻"), ("mi", "未収"), ("status", "状態")))

        human_report = build_human_report(report, view_map)

        self.assertEqual([row["項目"] for row in human_report.summary_rows], ["現収", "未収", "総売上", "消費税", "税抜運収"])
        self.assertEqual(human_report.ride_rows, ({"時刻": "10:44", "未収": 2430, "状態": ""},))
        self.assertEqual(human_report.claim_rows[0]["種別"], "障割請求")
        self.assertEqual(human_report.claim_rows[1]["種別"], "貸切")
        self.assertEqual(human_report.diagnostics, ("P01:01_AF: paper amount differs",))


if __name__ == "__main__":
    unittest.main()
