import unittest

from kamichizu.models import AdoptedReport, AdoptedRow
from kamichizu.specials import claim_total, make_public_discount_claim, public_discount_candidates
from kamichizu.view import build_human_rows
from kamichizu.models import ViewMap


class KamichizuSpecialsTest(unittest.TestCase):
    def test_public_discount_without_pickup_fee(self):
        candidates = public_discount_candidates(2430)

        self.assertEqual([candidate.claim_amount for candidate in candidates], [270])
        self.assertEqual(candidates[0].pickup_fee_used, 0)
        self.assertEqual(candidates[0].original_fare, 2700)

    def test_public_discount_with_pickup_fee_excluded(self):
        candidates = public_discount_candidates(3620)

        matching = [candidate for candidate in candidates if candidate.pickup_fee_used == 200]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].claim_amount, 380)
        self.assertEqual(matching[0].discounted_fare, 3420)

    def test_public_discount_claim_is_not_mixed_into_mi(self):
        row = AdoptedRow(row_addr="14", values={"mi": 3620})
        claim = make_public_discount_claim(target_row_addr="14", meter_amount=3620, expected_claim_amount=380)
        self.assertIsNotNone(claim)
        report = AdoptedReport(rows=(row,), claims=(claim,))

        self.assertEqual(report.rows[0].values["mi"], 3620)
        self.assertEqual(claim_total(report.claims), 380)

    def test_human_rows_show_body_sales_without_claims(self):
        row = AdoptedRow(row_addr="14", values={"time": "15:37", "mi": 3620})
        claim = make_public_discount_claim(target_row_addr="14", meter_amount=3620, expected_claim_amount=380)
        report = AdoptedReport(rows=(row,), claims=(claim,))
        view = ViewMap(view_id="taxi", columns=(("time", "時刻"), ("mi", "未収"), ("status", "状態")))

        self.assertEqual(build_human_rows(report, view), [{"時刻": "15:37", "未収": 3620, "状態": ""}])
        self.assertEqual(claim_total(report.claims), 380)

    def test_ambiguous_or_unmatched_discount_claim_is_not_created(self):
        self.assertIsNone(make_public_discount_claim(target_row_addr="14", meter_amount=3620, expected_claim_amount=300))


if __name__ == "__main__":
    unittest.main()
