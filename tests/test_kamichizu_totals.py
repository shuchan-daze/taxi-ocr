import unittest

from kamichizu.models import AdoptedReport, AdoptedRow
from kamichizu.specials import make_charter_claim, make_public_discount_claim
from kamichizu.totals import compute_sales_totals


class KamichizuTotalsTest(unittest.TestCase):
    def test_rows_and_claims_are_summed_without_mutating_body_values(self):
        rows = (
            AdoptedRow(row_addr="01", values={"gen": 900, "mi": None}),
            AdoptedRow(row_addr="02", values={"gen": None, "mi": 2430}),
        )
        claims = (
            make_charter_claim(target_row_addr="05", amount=16400, payment_kind="gen"),
            make_charter_claim(target_row_addr="06", amount=10000, payment_kind="mi"),
        )
        report = AdoptedReport(rows=rows, claims=claims)

        totals = compute_sales_totals(report)

        self.assertEqual(totals.ride_gen, 900)
        self.assertEqual(totals.ride_mi, 2430)
        self.assertEqual(totals.claim_gen, 16400)
        self.assertEqual(totals.claim_mi, 10000)
        self.assertEqual(totals.gen, 17300)
        self.assertEqual(totals.mi, 12430)
        self.assertEqual(totals.sou, 29730)
        self.assertIsNone(report.rows[0].values["mi"])

    def test_public_discount_claim_is_summed_as_other_not_confirmed_mi(self):
        row = AdoptedRow(row_addr="14", values={"mi": 3620})
        discount = make_public_discount_claim(target_row_addr="14", meter_amount=3620, expected_claim_amount=380)
        report = AdoptedReport(rows=(row,), claims=(discount,))

        totals = compute_sales_totals(report)

        self.assertEqual(totals.ride_mi, 3620)
        self.assertEqual(totals.claim_mi, 0)
        self.assertEqual(totals.claim_other, 380)
        self.assertEqual(totals.mi, 3620)
        self.assertEqual(totals.sou, 4000)

    def test_empty_report_totals_are_zero(self):
        totals = compute_sales_totals(AdoptedReport(rows=()))

        self.assertEqual(totals.ride_gen, 0)
        self.assertEqual(totals.ride_mi, 0)
        self.assertEqual(totals.claim_gen, 0)
        self.assertEqual(totals.claim_mi, 0)
        self.assertEqual(totals.claim_other, 0)
        self.assertEqual(totals.sou, 0)


if __name__ == "__main__":
    unittest.main()
