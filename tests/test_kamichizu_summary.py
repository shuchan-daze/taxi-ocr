import unittest

from kamichizu.models import AdoptedReport, AdoptedRow
from kamichizu.specials import make_charter_claim, make_public_discount_claim
from kamichizu.view import build_summary_rows


class KamichizuSummaryTest(unittest.TestCase):
    def test_summary_shows_ride_and_special_components(self):
        report = AdoptedReport(
            rows=(
                AdoptedRow(row_addr="01", values={"gen": 900}),
                AdoptedRow(row_addr="02", values={"mi": 2430}),
            ),
            claims=(
                make_charter_claim(target_row_addr="05", amount=16400, payment_kind="gen"),
                make_charter_claim(target_row_addr="06", amount=10000, payment_kind="mi"),
                make_public_discount_claim(target_row_addr="14", meter_amount=3620, expected_claim_amount=380),
            ),
        )

        summary = build_summary_rows(report)

        self.assertEqual(summary[0], {"項目": "現収", "金額": 17300, "内訳": "通常 900 + 特例 16400"})
        self.assertEqual(summary[1], {"項目": "未収", "金額": 12430, "内訳": "通常 2430 + 特例 10000"})
        self.assertEqual(summary[2], {"項目": "特例請求", "金額": 380, "内訳": "障割請求など"})
        self.assertEqual(summary[3], {"項目": "総売上", "金額": 30110, "内訳": "現収 + 未収 + 特例請求"})

    def test_summary_empty_report_is_zero(self):
        summary = build_summary_rows(AdoptedReport(rows=()))

        self.assertEqual([row["金額"] for row in summary], [0, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()
