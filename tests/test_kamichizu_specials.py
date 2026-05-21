import unittest

from kamichizu.models import AdoptedReport, AdoptedRow
from kamichizu.specials import claim_total, make_charter_claim, make_public_discount_claim, public_discount_candidates
from kamichizu.view import build_claim_rows, build_human_rows
from kamichizu.models import EvidenceLink, ViewMap


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

    def test_build_claim_rows_shows_claims_separately_for_humans(self):
        evidence = (EvidenceLink("P01:14_AF", "E01:10_AC", "discount_from_meter_amount"),)
        claim = make_public_discount_claim(
            target_row_addr="14",
            meter_amount=3620,
            expected_claim_amount=380,
            evidence=evidence,
        )
        report = AdoptedReport(rows=(), claims=(claim,))

        self.assertEqual(
            build_claim_rows(report),
            [
                {
                    "種別": "障割請求",
                    "対象行": "14",
                    "区分": "未収",
                    "金額": 380,
                    "根拠": "P01:14_AF ← E01:10_AC",
                }
            ],
        )

    def test_charter_claim_is_special_sale_not_ride_row(self):
        row = AdoptedRow(row_addr="05", values={"time": "13:40", "gen": None, "mi": None})
        charter = make_charter_claim(target_row_addr="05", amount=16400, payment_kind="gen")
        report = AdoptedReport(rows=(row,), claims=(charter,))

        self.assertIsNone(report.rows[0].values["gen"])
        self.assertIsNone(report.rows[0].values["mi"])
        self.assertEqual(claim_total(report.claims, "charter_sale"), 16400)

    def test_charter_payment_kind_distinguishes_gen_and_mi(self):
        gen_charter = make_charter_claim(target_row_addr="05", amount=16400, payment_kind="gen")
        mi_charter = make_charter_claim(target_row_addr="06", amount=10000, payment_kind="mi")

        self.assertEqual(gen_charter.payment_kind, "gen")
        self.assertEqual(mi_charter.payment_kind, "mi")

    def test_build_claim_rows_shows_charter_separately_from_discount(self):
        discount = make_public_discount_claim(target_row_addr="14", meter_amount=3620, expected_claim_amount=380)
        charter = make_charter_claim(target_row_addr="05", amount=16400, payment_kind="gen")
        report = AdoptedReport(rows=(), claims=(discount, charter))

        rows = build_claim_rows(report)

        self.assertEqual(rows[0]["種別"], "障割請求")
        self.assertEqual(rows[0]["区分"], "未収")
        self.assertEqual(rows[1]["種別"], "貸切")
        self.assertEqual(rows[1]["区分"], "現収")
        self.assertEqual(rows[1]["金額"], 16400)
        self.assertNotIn("調整", str(rows))
        self.assertNotIn("global_cell_id", str(rows))
        self.assertNotIn("rule_id", str(rows))

    def test_ambiguous_or_unmatched_discount_claim_is_not_created(self):
        self.assertIsNone(make_public_discount_claim(target_row_addr="14", meter_amount=3620, expected_claim_amount=300))


if __name__ == "__main__":
    unittest.main()
