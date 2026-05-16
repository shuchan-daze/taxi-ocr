"""paper_grid.py の単体テスト.

Shuchan の哲学 (座標ベース設計) を実装した最小ゴール 4 関数の動作確認.
"""
import paper_grid as pg


# =========================
# build_empty_cell_map
# =========================

class TestBuildEmptyCellMap:
    def test_default_25_rows_5_cols(self):
        # デフォルトテンプレートで 25 行 × 5 列 = 125 セル
        cell_map = pg.build_empty_cell_map()
        assert len(cell_map) == 125

    def test_all_cells_blank_initially(self):
        cell_map = pg.build_empty_cell_map()
        for cell in cell_map.values():
            assert cell.value == ""
            assert cell.source == "blank"
            assert cell.tokens == []
            assert cell.confidence is None

    def test_cell_ids_follow_pattern(self):
        cell_map = pg.build_empty_cell_map()
        # R01_TIME, R01_PASSENGERS, R01_GEN, R01_MI, R01_MEMO ... R25_MEMO
        assert "R01_TIME" in cell_map
        assert "R01_GEN" in cell_map
        assert "R01_MI" in cell_map
        assert "R25_MEMO" in cell_map
        assert "R03_GEN" in cell_map
        # 存在しないラベルは含まない
        assert "R26_TIME" not in cell_map
        assert "R00_TIME" not in cell_map

    def test_row_col_attributes(self):
        cell_map = pg.build_empty_cell_map()
        r03_gen = cell_map["R03_GEN"]
        assert r03_gen.row == 3
        assert r03_gen.col == "gen"


# =========================
# find_cell_by_xy
# =========================

class TestFindCellByXY:
    def _token(self, x, y, w=10, h=10, text="x"):
        return pg.OCRToken(text=text, x=x, y=y, w=w, h=h)

    def test_token_in_row3_gen_column(self):
        # R03 の y 範囲 (0.236〜0.264) の中央 = 0.25
        # GEN 列の x 範囲 (0.36〜0.48) の中央 = 0.42
        # 画像 1000 × 1000 なら、中心 (420, 250) のトークン
        token = self._token(x=415, y=245, w=10, h=10)
        addr = pg.find_cell_by_xy(token, pg.PAPER_TEMPLATE, 1000, 1000)
        assert addr is not None
        assert addr.cell_id == "R03_GEN"
        assert addr.row == 3
        assert addr.col == "gen"

    def test_token_in_row10_mi_column(self):
        # R10 (0.432〜0.460) 中央 0.446, MI (0.49〜0.61) 中央 0.55
        token = self._token(x=545, y=441, w=10, h=10)
        addr = pg.find_cell_by_xy(token, pg.PAPER_TEMPLATE, 1000, 1000)
        assert addr is not None
        assert addr.cell_id == "R10_MI"

    def test_token_outside_returns_none(self):
        # ヘッダ位置 (y=0.1) はテンプレート外
        token = self._token(x=400, y=80, w=10, h=10)
        addr = pg.find_cell_by_xy(token, pg.PAPER_TEMPLATE, 1000, 1000)
        assert addr is None

    def test_invalid_image_size_returns_none(self):
        token = self._token(x=100, y=100)
        assert pg.find_cell_by_xy(token, pg.PAPER_TEMPLATE, 0, 0) is None
        assert pg.find_cell_by_xy(token, pg.PAPER_TEMPLATE, -100, 100) is None


# =========================
# assign_ocr_tokens_to_cells
# =========================

class TestAssignOCRTokensToCells:
    def _token(self, text, x, y, w=10, h=10, conf=None):
        return pg.OCRToken(text=text, x=x, y=y, w=w, h=h, confidence=conf)

    def test_unread_cells_stay_blank(self):
        # OCR が何も返さなくても、全セルは空状態で残る
        cell_map = pg.build_empty_cell_map()
        result = pg.assign_ocr_tokens_to_cells(cell_map, [], pg.PAPER_TEMPLATE, 1000, 1000)
        assert len(result) == 125
        for cell in result.values():
            assert cell.source == "blank"
            assert cell.value == ""

    def test_token_placed_at_correct_cell(self):
        cell_map = pg.build_empty_cell_map()
        # R03_GEN の範囲に "200" のトークンを配置
        tokens = [self._token("200", x=415, y=245)]
        result = pg.assign_ocr_tokens_to_cells(cell_map, tokens, pg.PAPER_TEMPLATE, 1000, 1000)
        assert result["R03_GEN"].value == "200"
        assert result["R03_GEN"].source == "ocr"

    def test_multiple_tokens_concatenated_in_amount_cell(self):
        # 数字セルではトークンを区切り無し連結 (例: '2' + '4' + '30' → '2430')
        cell_map = pg.build_empty_cell_map()
        tokens = [
            self._token("2", x=540, y=245, w=5),
            self._token("4", x=548, y=245, w=5),
            self._token("30", x=556, y=245, w=10),
        ]
        result = pg.assign_ocr_tokens_to_cells(cell_map, tokens, pg.PAPER_TEMPLATE, 1000, 1000)
        assert result["R03_MI"].value == "2430"

    def test_memo_tokens_joined_with_space(self):
        # memo はスペース区切り
        cell_map = pg.build_empty_cell_map()
        tokens = [
            self._token("現金", x=650, y=245),
            self._token("チケット", x=700, y=245),
        ]
        result = pg.assign_ocr_tokens_to_cells(cell_map, tokens, pg.PAPER_TEMPLATE, 1000, 1000)
        assert result["R03_MEMO"].value == "現金 チケット"

    def test_tokens_outside_grid_ignored(self):
        cell_map = pg.build_empty_cell_map()
        tokens = [
            self._token("ヘッダ", x=400, y=80),   # テンプレート外
            self._token("OK", x=415, y=245),     # R03_GEN
        ]
        result = pg.assign_ocr_tokens_to_cells(cell_map, tokens, pg.PAPER_TEMPLATE, 1000, 1000)
        assert result["R03_GEN"].value == "OK"
        # 範囲外トークンはどのセルにも入らない
        non_blank = [c for c in result.values() if c.source == "ocr"]
        assert len(non_blank) == 1

    def test_confidence_averaged(self):
        cell_map = pg.build_empty_cell_map()
        tokens = [
            self._token("1", x=540, y=245, w=5, conf=0.8),
            self._token("2", x=548, y=245, w=5, conf=0.6),
        ]
        result = pg.assign_ocr_tokens_to_cells(cell_map, tokens, pg.PAPER_TEMPLATE, 1000, 1000)
        assert result["R03_MI"].confidence == 0.7


# =========================
# build_paper_rows_from_cell_map
# =========================

class TestBuildPaperRowsFromCellMap:
    def test_all_25_rows_generated_even_when_empty(self):
        # OCR で何も読めなくても 25 行全部が生成される (= 行を詰めない)
        cell_map = pg.build_empty_cell_map()
        rows = pg.build_paper_rows_from_cell_map(cell_map)
        assert len(rows) == 25
        assert rows[0].paper_row == 1
        assert rows[24].paper_row == 25
        for row in rows:
            assert row.time == ""
            assert row.gen_raw == ""

    def test_cell_values_propagated_to_rows(self):
        cell_map = pg.build_empty_cell_map()
        cell_map["R03_TIME"].value = "10:44"
        cell_map["R03_GEN"].value = "200"
        cell_map["R03_MI"].value = "2430"
        cell_map["R03_MEMO"].value = "現金+チケット"
        rows = pg.build_paper_rows_from_cell_map(cell_map)
        assert rows[2].paper_row == 3
        assert rows[2].time == "10:44"
        assert rows[2].gen_raw == "200"
        assert rows[2].mi_raw == "2430"
        assert rows[2].memo == "現金+チケット"

    def test_middle_row_blank_preserved(self):
        # 中間の空行も詰めない
        cell_map = pg.build_empty_cell_map()
        cell_map["R01_GEN"].value = "900"
        cell_map["R05_GEN"].value = "1300"
        rows = pg.build_paper_rows_from_cell_map(cell_map)
        assert rows[0].gen_raw == "900"
        assert rows[1].gen_raw == ""  # R02 は空
        assert rows[2].gen_raw == ""  # R03 は空
        assert rows[3].gen_raw == ""  # R04 は空
        assert rows[4].gen_raw == "1300"  # R05


# =========================
# 結合: 4 関数を通した最小フロー
# =========================

class TestIntegratedMinimalFlow:
    """4 関数を組み合わせた最小フロー: OCR トークン → cell_map → paper_rows."""

    def test_realistic_flow(self):
        # 紙日報の 3 行目に「10:44, 2 人, 現収 200, 未収 2430, 現金+チケット」と書いてある想定
        cell_map = pg.build_empty_cell_map()
        tokens = [
            pg.OCRToken(text="10:44", x=80, y=245, w=50, h=10),    # R03_TIME
            pg.OCRToken(text="2",      x=190, y=245, w=10, h=10),   # R03_PASSENGERS
            pg.OCRToken(text="200",    x=415, y=245, w=20, h=10),   # R03_GEN
            pg.OCRToken(text="2430",   x=540, y=245, w=30, h=10),   # R03_MI
            pg.OCRToken(text="現金+チケット", x=680, y=245, w=80, h=10),  # R03_MEMO
        ]
        cell_map = pg.assign_ocr_tokens_to_cells(cell_map, tokens, pg.PAPER_TEMPLATE, 1000, 1000)
        rows = pg.build_paper_rows_from_cell_map(cell_map)

        # 3 行目の各セルに値が入ってる、他は空
        assert rows[2].time == "10:44"
        assert rows[2].passengers == "2"
        assert rows[2].gen_raw == "200"
        assert rows[2].mi_raw == "2430"
        assert rows[2].memo == "現金+チケット"
        # 1, 2, 4, 5 行目は全部空 (= 詰められない)
        assert rows[0].time == ""
        assert rows[1].time == ""
        assert rows[3].time == ""
        assert rows[4].time == ""
        # 全 25 行存在
        assert len(rows) == 25
