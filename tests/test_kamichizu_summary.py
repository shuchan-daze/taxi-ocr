import unittest

from kamichizu.models import AdoptedReport, AdoptedRow, EvidenceLink
from kamichizu.specials import make_charter_claim, make_public_discount_claim
from kamichizu.view import build_summary_rows


def evidence(row_addr: str, field: str = "AG") -> tuple[EvidenceLink, ...]:
    return (EvidenceLink(f"P01:{row_addr}_{field}", f"P01:{row_addr}_{field}", "claim_from_paper"),)


class KamichizuSummaryTest(unittest.TestCase):
    def test_summary_shows_ride_and_special_components(self):
        report = AdoptedReport(
            rows=(
                AdoptedRow(row_addr="01", values={"gen": 900}),
                AdoptedRow(row_addr="02", values={"mi": 2430}),
            ),
            claims=(
                make_charter_claim(
                    target_row_addr="05",
                    target_global_cell_id="P01:05_AG",
                    claim_amount=16400,
                    payment_kind="gen",
                    evidence=evidence("05"),
                ),
                make_charter_claim(
                    target_row_addr="06",
                    target_global_cell_id="P01:06_AG",
                    claim_amount=10000,
                    payment_kind="mi",
                    evidence=evidence("06"),
                ),
                make_public_discount_claim(
                    target_row_addr="14",
                    target_global_cell_id="P01:14_AF",
                    meter_amount=3620,
                    expected_claim_amount=380,
                    evidence=evidence("14", "AF"),
                ),
            ),
        )

        summary = build_summary_rows(report)

        self.assertEqual(summary[0], {"項目": "現収", "金額": 17300, "内訳": "通常 900 + 特例 16400"})
        self.assertEqual(summary[1], {"項目": "未収", "金額": 12810, "内訳": "通常 2430 + 特例 10380"})
        self.assertEqual(summary[2], {"項目": "総売上", "金額": 30110, "内訳": "現収 + 未収"})
        self.assertEqual(summary[3], {"項目": "消費税", "金額": 2740, "内訳": "総売上に含まれる税額"})
        self.assertEqual(summary[4], {"項目": "税抜運収", "金額": 27370, "内訳": "総売上 - 消費税"})

    def test_summary_empty_report_is_zero(self):
        summary = build_summary_rows(AdoptedReport(rows=()))

        self.assertEqual([row["金額"] for row in summary], [0, 0, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()
