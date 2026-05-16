"""_interpret_raw_row / interpret_raw_rows の単体テスト。
AI が抽出した raw cell を Python で case 分類する層。"""
import app


def _raw(time='14:30', passengers=1, gen_cell=None, mi_cell=None, memo='', strikethrough=False):
    """raw_row フィクスチャ。デフォルト値で省略可能。"""
    return {
        'time': time, 'passengers': passengers,
        'gen_cell': gen_cell, 'mi_cell': mi_cell,
        'memo': memo, 'strikethrough': strikethrough,
    }


# ── _interpret_raw_row: 各 case 分類 ────────────────────────────

class TestInterpretRawRow:
    def test_empty_row(self):
        result = app._interpret_raw_row(_raw())
        assert result['type'] == 'empty'

    def test_normal_gen_only(self):
        result = app._interpret_raw_row(_raw(gen_cell=1500, memo='現金'))
        assert result['type'] == 'normal'
        assert result['kind'] == '現収'
        assert result['amount'] == 1500
        assert result['memo'] == '現金'

    def test_normal_mi_only(self):
        result = app._interpret_raw_row(_raw(mi_cell=2000, memo='Visa'))
        assert result['type'] == 'normal'
        assert result['kind'] == '未収'
        assert result['amount'] == 2000

    def test_split_both_columns(self):
        # 現収・未収両方に数字 → split 判定
        result = app._interpret_raw_row(_raw(gen_cell=1000, mi_cell=800, memo='現金+チケット'))
        assert result['type'] == 'split'
        assert result['gen'] == 1000
        assert result['mi'] == 800

    def test_overage_marker_plus_mi(self):
        # 現収に "+100" マーカー + 未収に客払い額 → overage
        result = app._interpret_raw_row(_raw(gen_cell='+100', mi_cell=1500, memo='Visa'))
        assert result['type'] == 'overage'
        assert result['overage_amount'] == 100
        assert result['customer_amount'] == 1500
        assert result['kind'] == '未収'

    def test_overage_marker_only(self):
        # 現収 "+100" のみ、未収空 → overage で kind 仮置き
        result = app._interpret_raw_row(_raw(gen_cell='+100'))
        assert result['type'] == 'overage'
        assert result['overage_amount'] == 100

    def test_karamawashi_strikethrough_plus_overage(self):
        # 取り消し線 + 現収に "+N" のみ → からまわし
        result = app._interpret_raw_row(_raw(gen_cell='+200', strikethrough=True))
        assert result['type'] == 'karamawashi'
        assert result['overage_amount'] == 200

    def test_meter_overage_standalone_with_plus(self):
        # 推奨書式: 現収 "+100" + memo "メーター" → 自腹補填行
        result = app._interpret_raw_row(_raw(gen_cell='+100', memo='メーター'))
        assert result['type'] == 'meter_overage_standalone'
        assert result['overage_amount'] == 100

    def test_meter_overage_standalone_without_plus(self):
        # 推奨書式の「+」忘れケース: 現収 100 + memo "メーター" でも検出
        result = app._interpret_raw_row(_raw(gen_cell=100, memo='メーター'))
        assert result['type'] == 'meter_overage_standalone'
        assert result['overage_amount'] == 100

    def test_meter_overage_standalone_requires_memo(self):
        # memo に「メーター」が無いと自腹補填行と認識しない (通常行扱い)
        result = app._interpret_raw_row(_raw(gen_cell=100, memo=''))
        assert result['type'] == 'normal'  # 通常の ¥100 現収行として扱う

    def test_discount_memo_mi(self):
        # memo に「障割」+ 未収に額 → discount
        result = app._interpret_raw_row(_raw(mi_cell=200, memo='障割'))
        assert result['type'] == 'discount'
        assert result['amount'] == 200

    def test_discount_memo_keyword_alt(self):
        # 「障害者割引」表記もOK
        result = app._interpret_raw_row(_raw(mi_cell=180, memo='障害者割引'))
        assert result['type'] == 'discount'
        assert result['amount'] == 180

    def test_invalid_input(self):
        # dict 以外は invalid
        result = app._interpret_raw_row('not a dict')
        assert result['type'] == 'invalid'


# ── interpret_raw_rows: 配列処理 ────────────────────────────────

class TestInterpretRawRows:
    def test_empty_list(self):
        assert app.interpret_raw_rows([]) == []
        assert app.interpret_raw_rows(None) == []

    def test_mix_of_cases(self):
        rows = [
            _raw(gen_cell=1500, memo='現金'),
            _raw(mi_cell=2000, memo='Visa'),
            _raw(gen_cell=1000, mi_cell=800, memo='現金+チケット'),
        ]
        rides = app.interpret_raw_rows(rows)
        assert len(rides) == 3
        assert rides[0]['case'] == 'normal'
        assert rides[1]['case'] == 'normal'
        assert rides[2]['case'] == 'split'

    def test_karamawashi_attaches_to_previous(self):
        # karamawashi 行は単独 ride にならず、直前の normal 行に overage_amount を足す
        rows = [
            _raw(gen_cell=1500, memo='現金'),  # 普通
            _raw(gen_cell='+200', strikethrough=True),  # からまわし → 上に付く
        ]
        rides = app.interpret_raw_rows(rows)
        assert len(rides) == 1
        assert rides[0]['case'] == 'overage'
        assert rides[0]['overage_amount'] == 200

    def test_empty_rows_skipped(self):
        # 空行はスキップされる (No 列が無い設計なので placeholder も不要)
        rows = [
            _raw(gen_cell=1500),
            _raw(),  # empty
            _raw(mi_cell=2000),
        ]
        rides = app.interpret_raw_rows(rows)
        assert len(rides) == 2
        assert rides[0]['nippou_amount'] == 1500
        assert rides[1]['nippou_amount'] == 2000

    def test_non_dict_skipped(self):
        rows = [
            _raw(gen_cell=1500),
            'invalid',  # 非 dict は invalid type → skip
            None,
        ]
        rides = app.interpret_raw_rows(rows)
        assert len(rides) == 1


# ── 貸切 (charter) ───────────────────────────────────────────────

class TestCharter:
    def test_charter_gen(self):
        # 現収欄に金額 + 摘要「貸切」→ case=charter, kind=現収
        result = app._interpret_raw_row(_raw(time='13:30', passengers=4, gen_cell=16400, memo='貸切'))
        assert result['type'] == 'charter'
        assert result['kind'] == '現収'
        assert result['amount'] == 16400

    def test_charter_mi(self):
        # 未収欄に金額 + 摘要「貸切」→ case=charter, kind=未収
        result = app._interpret_raw_row(_raw(mi_cell=20000, memo='貸切'))
        assert result['type'] == 'charter'
        assert result['kind'] == '未収'
        assert result['amount'] == 20000

    def test_charter_in_rides(self):
        rows = [
            _raw(gen_cell=900, memo='現金'),
            _raw(time='13:30', passengers=4, gen_cell=16400, memo='貸切'),
        ]
        rides = app.interpret_raw_rows(rows)
        assert len(rides) == 2
        assert rides[1]['case'] == 'charter'
        assert rides[1]['nippou_amount'] == 16400
        assert rides[1]['passengers'] == 4


# ── プラグイン性の実証: 新ハンドラ追加だけで識別できる ──────────

class TestPluginExtensibility:
    """RowHandler を継承して ROW_HANDLERS に追加するだけで
    新イレギュラーケースが認識されることを保証 (= Shuchan の 3 レイヤー設計図の
    「いくらでも加えることができる状態」)."""

    def test_register_custom_handler(self):
        # ダミー: memo に「テスト印」が入った行を独自 case='test_marker' で識別
        class TestMarkerHandler(app.RowHandler):
            name = 'test_marker'

            def detect(self, r):
                return 'テスト印' in (r.get('memo') or '')

            def interpret(self, r):
                return {'type': 'test_marker', 'memo': r.get('memo')}

        original = list(app.ROW_HANDLERS)
        try:
            # 既存ハンドラより先に評価されるよう先頭に挿入
            app.ROW_HANDLERS.insert(0, TestMarkerHandler())
            result = app._interpret_raw_row(_raw(gen_cell=1000, memo='テスト印'))
            assert result['type'] == 'test_marker'
            assert result['memo'] == 'テスト印'
        finally:
            # 副作用が他テストに漏れないよう必ず元に戻す
            app.ROW_HANDLERS[:] = original


# ── _split_rides: discount を分離 ───────────────────────────────


# ── _split_rides: discount を分離 ───────────────────────────────

class TestSplitRides:
    def test_separates_discount(self):
        rides = [
            {'case': 'normal', 'nippou_amount': 1000},
            {'case': 'discount', 'nippou_amount': 200},
            {'case': 'split', 'gen_amount': 500, 'mi_amount': 500},
        ]
        real, by_layer3 = app._split_rides(rides)
        assert len(real) == 2
        assert len(by_layer3['discount']) == 1
        assert by_layer3['discount'][0]['case'] == 'discount'
        assert by_layer3.get('charter', []) == []

    def test_separates_charter(self):
        rides = [
            {'case': 'normal', 'nippou_amount': 1000},
            {'case': 'charter', 'nippou_amount': 16400, 'kind': '現収', 'memo': '貸切'},
            {'case': 'discount', 'nippou_amount': 200},
        ]
        real, by_layer3 = app._split_rides(rides)
        assert len(real) == 1
        assert len(by_layer3['discount']) == 1
        assert len(by_layer3['charter']) == 1
        assert by_layer3['charter'][0]['nippou_amount'] == 16400
