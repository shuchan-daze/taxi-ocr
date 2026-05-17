"""nippou_core.py の単体テスト + サンプル A/B/C の動作確認.

Shuchan + ChatGPT との議論で確定した設計を、コードで動くことを保証する.
"""
import nippou_core as nc


# ═══════════════════════════════════════════════════════════════════
# データクラスの基本テスト
# ═══════════════════════════════════════════════════════════════════

class TestDataClasses:
    def test_ocr_token_defaults(self):
        t = nc.OCRToken(text="200", x=10, y=20, w=30, h=10)
        assert t.text == "200"
        assert t.confidence is None

    def test_cell_blank_default(self):
        c = nc.Cell(cell_id="R03_GEN", row=3, col="gen")
        assert c.value == ""
        assert c.source == "blank"
        assert c.tokens == []

    def test_paper_row_blank_default(self):
        r = nc.PaperRow(paper_row=5)
        assert r.row_type == "blank"
        assert r.time == ""

    def test_meter_row(self):
        m = nc.MeterRow(meter_no=10, time="10:44", amount=2630)
        assert m.amount == 2630

    def test_adjustment_result_defaults(self):
        ar = nc.AdjustmentResult(rule_name="Test", row_index=1)
        assert ar.amount == 0
        assert ar.is_paper_only is False
        assert ar.is_meter_breakdown is False
        assert ar.reconciliation_mode == "none"
        assert ar.status == "ok"


# ═══════════════════════════════════════════════════════════════════
# Layer 1: 紙日報グリッド
# ═══════════════════════════════════════════════════════════════════

class TestBuildEmptyCellMap:
    def test_125_cells_generated(self):
        cell_map = nc.build_empty_cell_map()
        assert len(cell_map) == 125

    def test_all_blank_initially(self):
        cell_map = nc.build_empty_cell_map()
        for cell in cell_map.values():
            assert cell.value == ""
            assert cell.source == "blank"

    def test_cell_ids_pattern(self):
        cell_map = nc.build_empty_cell_map()
        assert "R01_TIME" in cell_map
        assert "R25_MEMO" in cell_map
        assert "R03_GEN" in cell_map
        assert "R26_TIME" not in cell_map


class TestFindCellByXY:
    def _token(self, x, y, w=10, h=10):
        return nc.OCRToken(text="x", x=x, y=y, w=w, h=h)

    def test_token_in_row3_gen(self):
        # R03 (y: 0.236〜0.264) 中央 ≈ 0.25, GEN (x: 0.36〜0.48) 中央 ≈ 0.42
        token = self._token(x=415, y=245)
        addr = nc.find_cell_by_xy(token, nc.PAPER_TEMPLATE, 1000, 1000)
        assert addr is not None
        assert addr.cell_id == "R03_GEN"

    def test_token_outside_returns_none(self):
        token = self._token(x=400, y=80)  # ヘッダ位置
        assert nc.find_cell_by_xy(token, nc.PAPER_TEMPLATE, 1000, 1000) is None

    def test_invalid_image_size(self):
        token = self._token(x=100, y=100)
        assert nc.find_cell_by_xy(token, nc.PAPER_TEMPLATE, 0, 0) is None


class TestAssignOCRTokensToCells:
    def test_unread_cells_stay_blank(self):
        cell_map = nc.build_empty_cell_map()
        result = nc.assign_ocr_tokens_to_cells(cell_map, [], nc.PAPER_TEMPLATE, 1000, 1000)
        assert len(result) == 125
        for cell in result.values():
            assert cell.source == "blank"

    def test_token_placed_at_correct_cell(self):
        cell_map = nc.build_empty_cell_map()
        tokens = [nc.OCRToken(text="200", x=415, y=245, w=20, h=10)]
        result = nc.assign_ocr_tokens_to_cells(cell_map, tokens, nc.PAPER_TEMPLATE, 1000, 1000)
        assert result["R03_GEN"].value == "200"
        assert result["R03_GEN"].source == "ocr"

    def test_amount_tokens_concatenated(self):
        cell_map = nc.build_empty_cell_map()
        tokens = [
            nc.OCRToken(text="2", x=540, y=245, w=5, h=10),
            nc.OCRToken(text="4", x=548, y=245, w=5, h=10),
            nc.OCRToken(text="30", x=556, y=245, w=10, h=10),
        ]
        result = nc.assign_ocr_tokens_to_cells(cell_map, tokens, nc.PAPER_TEMPLATE, 1000, 1000)
        assert result["R03_MI"].value == "2430"

    def test_ocr_token_order_does_not_matter(self):
        # OCR が逆順で返してきても、座標で配置されるので結果は同じ
        cell_map_a = nc.build_empty_cell_map()
        cell_map_b = nc.build_empty_cell_map()
        tokens_normal = [
            nc.OCRToken(text="900", x=415, y=189, w=20, h=10),  # R01_GEN
            nc.OCRToken(text="2800", x=415, y=217, w=20, h=10),  # R02_GEN
            nc.OCRToken(text="200", x=415, y=245, w=20, h=10),  # R03_GEN
        ]
        tokens_reversed = list(reversed(tokens_normal))
        result_a = nc.assign_ocr_tokens_to_cells(cell_map_a, tokens_normal, nc.PAPER_TEMPLATE, 1000, 1000)
        result_b = nc.assign_ocr_tokens_to_cells(cell_map_b, tokens_reversed, nc.PAPER_TEMPLATE, 1000, 1000)
        # 結果は同じ
        assert result_a["R01_GEN"].value == result_b["R01_GEN"].value == "900"
        assert result_a["R02_GEN"].value == result_b["R02_GEN"].value == "2800"
        assert result_a["R03_GEN"].value == result_b["R03_GEN"].value == "200"


class TestBuildPaperRowsFromCellMap:
    def test_25_rows_always(self):
        cell_map = nc.build_empty_cell_map()
        rows = nc.build_paper_rows_from_cell_map(cell_map)
        assert len(rows) == 25

    def test_middle_blank_preserved(self):
        # 中間の空行は詰めない
        cell_map = nc.build_empty_cell_map()
        cell_map["R01_GEN"].value = "900"
        cell_map["R05_GEN"].value = "1300"
        rows = nc.build_paper_rows_from_cell_map(cell_map)
        assert rows[0].gen_raw == "900"
        assert rows[1].gen_raw == ""
        assert rows[4].gen_raw == "1300"


# ═══════════════════════════════════════════════════════════════════
# AdjustmentRule 基盤
# ═══════════════════════════════════════════════════════════════════

class TestClassifyRowsWithRules:
    def test_blank_rows_classified_as_blank(self):
        rows = [nc.PaperRow(paper_row=1)]
        rules = [nc.MeterOverrunRule(), nc.DisabilityDiscountRule(), nc.CharterFareRule()]
        result, adj = nc.classify_rows_with_rules(rows, rules)
        assert result[0].row_type == "blank"
        assert adj == []

    def test_normal_row_classified_as_meter_fare(self):
        rows = [nc.PaperRow(paper_row=1, time="09:46", gen_raw="900")]
        rules = [nc.MeterOverrunRule(), nc.DisabilityDiscountRule(), nc.CharterFareRule()]
        result, adj = nc.classify_rows_with_rules(rows, rules)
        assert result[0].row_type == "meter_fare"
        assert adj == []


# ═══════════════════════════════════════════════════════════════════
# サンプル A: メーター超過 (= 二重計上しない)
# ═══════════════════════════════════════════════════════════════════

class TestSampleA_MeterOverrun:
    """紙日報:
        行10 (10:44): 現金 1,300
        行11        : +100 メーター (= ドライバー自腹)
       メーター明細:
        10 本目 (10:44): 1,400

       期待:
        - 行10 の現金は 1,300 のまま (= 1,400 に上書きされない)
        - 行11 は別行として +100 が現金扱い
        - 合計 = 1,400 (= 二重計上しない)
    """

    def _build(self):
        # 紙日報の OCR トークン (= 行10, 行11 のみ書かれている想定)
        # R10 y: 0.432〜0.460, R11 y: 0.460〜0.488
        tokens = [
            # R10_TIME, R10_GEN
            nc.OCRToken(text="10:44", x=80, y=440, w=50, h=10),
            nc.OCRToken(text="2", x=190, y=440, w=10, h=10),
            nc.OCRToken(text="1300", x=415, y=440, w=30, h=10),
            # R11_GEN, R11_MEMO
            nc.OCRToken(text="+100", x=415, y=468, w=30, h=10),
            nc.OCRToken(text="メーター", x=680, y=468, w=40, h=10),
        ]
        cell_map = nc.build_empty_cell_map()
        cell_map = nc.assign_ocr_tokens_to_cells(cell_map, tokens, nc.PAPER_TEMPLATE, 1000, 1000)
        paper_rows = nc.build_paper_rows_from_cell_map(cell_map)
        rules = [nc.MeterOverrunRule(), nc.DisabilityDiscountRule(), nc.CharterFareRule()]
        paper_rows, adjustments = nc.classify_rows_with_rules(paper_rows, rules)
        meter_rows = [nc.MeterRow(meter_no=10, time="10:44", amount=1400)]
        return paper_rows, meter_rows, adjustments

    def test_row10_not_overwritten_to_1400(self):
        paper_rows, meter_rows, adjustments = self._build()
        final_rows = nc.build_final_rows(paper_rows, meter_rows, adjustments)
        # 行10 は paper_row=10 → final_rows[9]
        assert final_rows[9]["paper_row"] == 10
        # 紙日報の 1,300 を保持 (= メーター明細 1,400 で上書きしない)
        assert final_rows[9]["gen"] == 1300
        # 超過分 100 は行11 (= final_rows[10]) に別行として計上
        assert final_rows[10]["paper_row"] == 11
        assert final_rows[10]["gen"] == 100

    def test_row11_is_overrun_breakdown(self):
        paper_rows, meter_rows, adjustments = self._build()
        # row 11 が MeterOverrunRule にマッチして adjustment 生成される
        assert any(a.rule_name == "MeterOverrunRule" for a in adjustments)
        overrun = [a for a in adjustments if a.rule_name == "MeterOverrunRule"][0]
        assert overrun.row_index == 11
        assert overrun.amount == 100
        assert overrun.is_meter_breakdown is True
        assert overrun.reconciliation_mode == "breakdown"
        # 関連行は paper_row=10
        assert overrun.related_row_index == 10

    def test_total_is_1400_not_1500(self):
        """二重計上しないことを確認: 行10 1,300 + 行11 100 = 1,400.

        旧設計だと「紙 1,300 を meter 1,400 で上書き」+「超過 100 を別行」で
        合計 1,500 になる事故が起きた. 現設計は紙の数字を保持するので
        1,300 + 100 = 1,400 (= メーター明細と一致) で正しく集計される.
        """
        paper_rows, meter_rows, adjustments = self._build()
        final_rows = nc.build_final_rows(paper_rows, meter_rows, adjustments)
        totals = nc.calculate_totals(final_rows)

        # 合計が 1,400 になることを直接確認 (= 1,500 になっていたら二重計上)
        assert totals["gen_total"] == 1400

        # 整合確認: 紙日報合計 (1,300 + 100) == メーター明細 1,400 → ok
        reconciled = nc.reconcile_meter_with_paper(paper_rows, meter_rows, adjustments)
        row10_rec = reconciled[9]
        assert row10_rec["breakdown_total"] == 1400
        assert row10_rec["matched_meter_amount"] == 1400
        assert row10_rec["reconciliation_status"] == "ok"


# ═══════════════════════════════════════════════════════════════════
# サンプル B: 貸切 (= meter_rows と照合しない)
# ═══════════════════════════════════════════════════════════════════

class TestSampleB_Charter:
    """紙日報:
        行6 (13:40): 4 人 16,400 貸切
       メーター明細: 該当無し

       期待:
        - 紙日報から拾われる
        - meter_rows と照合されない
        - is_paper_only = True
        - 最終合計に加算
    """

    def _build(self):
        # R06 y: 0.320〜0.348
        tokens = [
            nc.OCRToken(text="13:40", x=80, y=328, w=50, h=10),
            nc.OCRToken(text="4", x=190, y=328, w=10, h=10),
            nc.OCRToken(text="16400", x=415, y=328, w=40, h=10),
            nc.OCRToken(text="貸切", x=680, y=328, w=30, h=10),
        ]
        cell_map = nc.build_empty_cell_map()
        cell_map = nc.assign_ocr_tokens_to_cells(cell_map, tokens, nc.PAPER_TEMPLATE, 1000, 1000)
        paper_rows = nc.build_paper_rows_from_cell_map(cell_map)
        rules = [nc.MeterOverrunRule(), nc.DisabilityDiscountRule(), nc.CharterFareRule()]
        paper_rows, adjustments = nc.classify_rows_with_rules(paper_rows, rules)
        meter_rows = []  # 貸切はメーターに出ない
        return paper_rows, meter_rows, adjustments

    def test_charter_classified(self):
        paper_rows, _, adjustments = self._build()
        assert paper_rows[5].row_type == "charter_fare"
        assert any(a.rule_name == "CharterFareRule" for a in adjustments)

    def test_charter_is_paper_only(self):
        _, _, adjustments = self._build()
        charter = [a for a in adjustments if a.rule_name == "CharterFareRule"][0]
        assert charter.is_paper_only is True
        assert charter.reconciliation_mode == "paper_only"
        assert charter.affects_meter_reconciliation is False

    def test_charter_amount_picked_from_paper(self):
        _, _, adjustments = self._build()
        charter = [a for a in adjustments if a.rule_name == "CharterFareRule"][0]
        assert charter.amount == 16400
        assert charter.side == "gen"

    def test_charter_counted_in_total(self):
        paper_rows, meter_rows, adjustments = self._build()
        final_rows = nc.build_final_rows(paper_rows, meter_rows, adjustments)
        totals = nc.calculate_totals(final_rows)
        assert totals["gen_total"] == 16400


# ═══════════════════════════════════════════════════════════════════
# サンプル C: 障害者割引 (= 自動計算しない、review 扱い)
# ═══════════════════════════════════════════════════════════════════

class TestSampleC_DisabilityDiscount:
    """紙日報:
        行3 (10:44): 客払い 2,430 (mi 欄、memo: 障割で割引後)
        行4        : 障害者割引補填 270 (mi 欄、memo: 障割)
       メーター明細: 3 本目 2,700  (仮例、実際の丸めルールは未確定)

       期待:
        - 紙の数字をそのまま拾う (= 1/9 等の自動計算はしない)
        - status = "review"
        - reconciliation_mode = "review"
        - side は紙の記入欄から (mi 固定にしない)
        - 整合確認: 客払い 2,430 + 補填 270 = メーター 2,700 で OK (注: 仮例)
    """

    def _build(self):
        # R03 y: 0.236〜0.264, R04 y: 0.264〜0.292
        # 行3: 客払い 2,430 (mi 欄), memo "障割 現金+チケット" (= 障害者割引)
        # 行4: 補填 270 (mi 欄), memo "障割"
        tokens = [
            # 行3
            nc.OCRToken(text="10:44", x=80, y=245, w=50, h=10),
            nc.OCRToken(text="2", x=190, y=245, w=10, h=10),
            nc.OCRToken(text="2430", x=540, y=245, w=30, h=10),
            nc.OCRToken(text="障割", x=680, y=245, w=30, h=10),
            # 行4
            nc.OCRToken(text="270", x=540, y=273, w=20, h=10),
            nc.OCRToken(text="障割", x=680, y=273, w=30, h=10),
        ]
        cell_map = nc.build_empty_cell_map()
        cell_map = nc.assign_ocr_tokens_to_cells(cell_map, tokens, nc.PAPER_TEMPLATE, 1000, 1000)
        paper_rows = nc.build_paper_rows_from_cell_map(cell_map)
        rules = [nc.MeterOverrunRule(), nc.DisabilityDiscountRule(), nc.CharterFareRule()]
        paper_rows, adjustments = nc.classify_rows_with_rules(paper_rows, rules)
        meter_rows = [nc.MeterRow(meter_no=3, time="10:44", amount=2700)]  # 仮例
        return paper_rows, meter_rows, adjustments

    def test_both_rows_classified_as_disability_discount(self):
        paper_rows, _, adjustments = self._build()
        # memo に「障割」を含む両方の行が DisabilityDiscountRule にマッチ
        disability_adjs = [a for a in adjustments if a.rule_name == "DisabilityDiscountRule"]
        assert len(disability_adjs) == 2

    def test_amount_not_auto_calculated(self):
        """1/9 等の自動計算をしない. 紙の数字をそのまま拾う."""
        _, _, adjustments = self._build()
        disability_adjs = [a for a in adjustments if a.rule_name == "DisabilityDiscountRule"]
        amounts = sorted([a.amount for a in disability_adjs])
        assert amounts == [270, 2430]  # 紙の数字そのまま

    def test_status_is_review(self):
        """status = review (= 人間判断に委ねる)."""
        _, _, adjustments = self._build()
        for a in adjustments:
            if a.rule_name == "DisabilityDiscountRule":
                assert a.status == "review"
                assert a.reconciliation_mode == "review"

    def test_side_not_fixed_to_mi(self):
        """side は紙の記入欄から判定 (mi 固定じゃない). 今回は両方とも mi 欄なので mi になるはず."""
        _, _, adjustments = self._build()
        disability_adjs = [a for a in adjustments if a.rule_name == "DisabilityDiscountRule"]
        # 紙の mi 欄に書かれてるので side = "mi"
        for a in disability_adjs:
            assert a.side == "mi"

    def test_side_gen_if_paper_has_gen(self):
        """gen 欄に書かれてる障割なら side = "gen" になる (= 固定じゃない確認)."""
        row = nc.PaperRow(paper_row=5, gen_raw="270", memo="障割")
        rule = nc.DisabilityDiscountRule()
        context = {"all_rows": [row], "row_index": 0}
        assert rule.match(row, context) is True
        result = rule.apply(row, context)
        assert result.side == "gen"
        assert result.affects_cash_total is True
        assert result.affects_mi_total is False

    def test_side_review_if_both_filled(self):
        """両方に金額あり → status = review (= 人間判断)."""
        row = nc.PaperRow(paper_row=5, gen_raw="100", mi_raw="270", memo="障割")
        rule = nc.DisabilityDiscountRule()
        context = {"all_rows": [row], "row_index": 0}
        result = rule.apply(row, context)
        assert result.status == "review"
        assert result.side == ""


# ═══════════════════════════════════════════════════════════════════
# プラグイン拡張性 (= 将来ルール追加が容易な構造)
# ═══════════════════════════════════════════════════════════════════

class TestPluginExtensibility:
    """新しい AdjustmentRule を継承して登録するだけで動作することを保証.
    Shuchan の哲学「将来例外が増えてもコア処理を触らない」."""

    def test_new_rule_recognized_without_core_change(self):
        class DummyTipRule(nc.AdjustmentRule):
            name = "DummyTipRule"
            priority = 5  # 他より先に評価

            def match(self, row, context):
                return "チップ" in (row.memo or "")

            def apply(self, row, context):
                return nc.AdjustmentResult(
                    rule_name=self.name,
                    row_index=row.paper_row,
                    amount=nc._extract_amount(row.gen_raw or row.mi_raw),
                    side="gen",
                    is_paper_only=True,
                    reconciliation_mode="paper_only",
                    note="チップ (= 新ルールのダミー)",
                )

        # コア関数は触らず、rules リストに追加するだけで動く
        rows = [nc.PaperRow(paper_row=1, gen_raw="500", memo="チップ")]
        rules = [
            DummyTipRule(),
            nc.MeterOverrunRule(),
            nc.DisabilityDiscountRule(),
            nc.CharterFareRule(),
        ]
        _, adjustments = nc.classify_rows_with_rules(rows, rules)
        assert len(adjustments) == 1
        assert adjustments[0].rule_name == "DummyTipRule"
        assert adjustments[0].amount == 500


# ═══════════════════════════════════════════════════════════════════
# 空欄保持 + review 分類 (= ChatGPT v2 レビュー指摘)
# ═══════════════════════════════════════════════════════════════════

class TestBlankCellsAndReviewClassification:
    """最終表の空欄は "" のまま (= 0 にしない).
    金額のない不完全 OCR 行は meter_fare ではなく review にして、
    meter_rows を勝手に消費しないようにする.
    """

    def _rules(self):
        return [nc.MeterOverrunRule(), nc.DisabilityDiscountRule(), nc.CharterFareRule()]

    def test_blank_rows_have_empty_string_not_zero(self):
        """完全空欄行の gen / mi は 0 ではなく ""."""
        rows = [nc.PaperRow(paper_row=i) for i in range(1, 26)]
        rows, adjustments = nc.classify_rows_with_rules(rows, self._rules())
        final_rows = nc.build_final_rows(rows, [], adjustments)
        assert final_rows[0]["gen"] == ""
        assert final_rows[0]["mi"] == ""
        assert final_rows[24]["gen"] == ""
        assert final_rows[24]["mi"] == ""

    def test_mi_only_row_keeps_gen_empty(self):
        """未収だけの行は gen='', mi=int."""
        rows = [nc.PaperRow(paper_row=1, time="10:00", mi_raw="2800")]
        rows, adjustments = nc.classify_rows_with_rules(rows, self._rules())
        meter_rows = [nc.MeterRow(meter_no=1, time="10:00", amount=2800)]
        final_rows = nc.build_final_rows(rows, meter_rows, adjustments)
        assert final_rows[0]["gen"] == ""
        assert final_rows[0]["mi"] == 2800

    def test_gen_only_row_keeps_mi_empty(self):
        """現金だけの行は gen=int, mi=''."""
        rows = [nc.PaperRow(paper_row=1, time="10:00", gen_raw="1300")]
        rows, adjustments = nc.classify_rows_with_rules(rows, self._rules())
        meter_rows = [nc.MeterRow(meter_no=1, time="10:00", amount=1300)]
        final_rows = nc.build_final_rows(rows, meter_rows, adjustments)
        assert final_rows[0]["gen"] == 1300
        assert final_rows[0]["mi"] == ""

    def test_time_only_row_is_review(self):
        """時刻だけ読めた行は meter_fare ではなく review."""
        rows = [nc.PaperRow(paper_row=1, time="09:46")]
        rows, _ = nc.classify_rows_with_rules(rows, self._rules())
        assert rows[0].row_type == "review"

    def test_memo_only_row_is_review(self):
        """メモだけ読めた行は meter_fare ではなく review."""
        rows = [nc.PaperRow(paper_row=1, memo="不明メモ")]
        rows, _ = nc.classify_rows_with_rules(rows, self._rules())
        assert rows[0].row_type == "review"

    def test_passengers_only_row_is_review(self):
        """人数だけ読めた行は meter_fare ではなく review."""
        rows = [nc.PaperRow(paper_row=1, passengers="2")]
        rows, _ = nc.classify_rows_with_rules(rows, self._rules())
        assert rows[0].row_type == "review"

    def test_review_does_not_consume_meter_rows(self):
        """金額のない review 行が meter_rows を消費しない.
        後続の通常営業行が正しい meter_row と照合されるか."""
        rows = [
            nc.PaperRow(paper_row=1, time="09:46"),                  # → review
            nc.PaperRow(paper_row=2, time="10:00", gen_raw="1300"),  # → meter_fare
        ]
        rows, adjustments = nc.classify_rows_with_rules(rows, self._rules())
        assert rows[0].row_type == "review"
        assert rows[1].row_type == "meter_fare"

        meter_rows = [nc.MeterRow(meter_no=1, time="10:00", amount=1300)]
        reconciled = nc.reconcile_meter_with_paper(rows, meter_rows, adjustments)
        # 行1 (review) は meter_rows を消費しない
        assert reconciled[0]["matched_meter_no"] is None
        # 行2 (meter_fare) が meter_rows[0] と正しく一致
        assert reconciled[1]["matched_meter_no"] == 1
        assert reconciled[1]["matched_meter_amount"] == 1300
        assert reconciled[1]["reconciliation_status"] == "ok"
