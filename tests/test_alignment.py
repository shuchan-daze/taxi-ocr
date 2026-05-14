"""_align_rides_to_meter / build_report の単体テスト。
タクシー日報 OCR の心臓部であるアライメントロジックを保護する。
v1.16.00 で Pass 2 を時刻ベースに切替たので、書き漏れケースのテストが特に重要。"""
import app


def _meter_row(no, time, amount):
    return {'no': no, 'time': time, 'amount': amount}


def _ride(time, amount, case='normal', kind='現収', memo='', passengers=1):
    return {
        'time': time, 'passengers': passengers, 'case': case, 'kind': kind,
        'memo': memo, 'nippou_amount': amount,
        'overage_amount': None, 'gen_amount': None, 'mi_amount': None,
    }


# ── _align_rides_to_meter: Pass 1 + Pass 2 ─────────────────────

class TestAlignmentPass1:
    """Pass 1: 金額完全一致 (同金額複数なら時刻 tie-break)"""

    def test_perfect_amount_match(self):
        meter = [_meter_row(1, '10:00', 1000), _meter_row(2, '11:00', 2000)]
        rides = [_ride('10:00', 1000), _ride('11:00', 2000)]
        aligned = app._align_rides_to_meter(rides, meter)
        assert len(aligned) == 2
        # ride が meter[0] と meter[1] にそれぞれ対応
        assert aligned[0][0] is not None  # ride 1 → meter 1
        assert aligned[0][0]['nippou_amount'] == 1000
        assert aligned[1][0]['nippou_amount'] == 2000

    def test_duplicate_amount_time_tiebreak(self):
        # 同じ ¥1,000 のメーター行が 2 つ → 時刻近い ride を割当
        meter = [_meter_row(1, '10:00', 1000), _meter_row(2, '15:00', 1000)]
        rides = [_ride('14:50', 1000), _ride('10:10', 1000)]
        aligned = app._align_rides_to_meter(rides, meter)
        # meter 1 (10:00) には ride 2 (10:10) が、meter 2 (15:00) には ride 1 (14:50) が
        assert aligned[0][0]['time'] == '10:10'
        assert aligned[1][0]['time'] == '14:50'


class TestAlignmentPass2:
    """Pass 2: 金額不一致 ride を時刻最近接で救済 (v1.16.00、20分閾値)"""

    def test_missing_paper_row_creates_orphan_meter(self):
        # 紙が 1 行書き漏れ: メーター 3 行、紙 2 行
        meter = [
            _meter_row(1, '10:00', 1000),
            _meter_row(2, '11:00', 2000),
            _meter_row(3, '12:00', 1500),  # この行に対応する紙なし
        ]
        rides = [_ride('10:00', 1000), _ride('11:00', 2000)]
        aligned = app._align_rides_to_meter(rides, meter)
        # meter 3 には ride 無し (missing_nippou になる予定)
        assert aligned[2][0] is None

    def test_mismatch_amount_aligned_by_time(self):
        # 紙が 1 行で金額誤記 (¥1000 のはずが ¥1090 と書いた)
        # Pass 1 で当たらず、Pass 2 で時刻最近接へ
        meter = [_meter_row(1, '10:00', 1000), _meter_row(2, '11:00', 2000)]
        rides = [_ride('10:05', 1090), _ride('11:00', 2000)]  # ride 1 が金額違い
        aligned = app._align_rides_to_meter(rides, meter)
        # 時刻近い meter 1 に ¥1,090 ride が当たる (mismatch として)
        assert aligned[0][0] is not None
        assert aligned[0][0]['nippou_amount'] == 1090

    def test_time_threshold_prevents_far_match(self):
        # v1.16.00 の真髄: 時刻が遠すぎたら無理に当てない
        # 紙にメーター No.1 がそもそも書かれてない時、後段の紙の行を強制マッチさせない
        meter = [
            _meter_row(1, '10:00', 1000),  # 紙に対応無し、書き漏れ
            _meter_row(2, '15:00', 1500),
        ]
        rides = [_ride('14:55', 1700)]  # 金額違い (¥1700 vs ¥1500)、時刻は 15:00 に近い
        aligned = app._align_rides_to_meter(rides, meter)
        # meter 1 (10:00) には来ない (15:00 とは 5 時間離れてる、閾値 20 分超え)
        # meter 2 (15:00) に時刻近い ride が来る (mismatch)
        assert aligned[0][0] is None  # meter 1 = ride 無し
        assert aligned[1][0] is not None  # meter 2 = mismatch
        assert aligned[1][0]['nippou_amount'] == 1700

    def test_ride_without_time_skipped_in_pass2(self):
        # 時刻無しの ride は Pass 2 で当たらない (orphan として捨てる)
        meter = [_meter_row(1, '10:00', 1000)]
        rides = [_ride('', 999)]
        aligned = app._align_rides_to_meter(rides, meter)
        assert aligned[0][0] is None


# ── build_report: 統合出力 (state 判定込み) ────────────────────

class TestBuildReport:
    def _make_data(self, meter_rows, rides):
        return (
            {'rows': meter_rows, 'total': sum(r['amount'] for r in meter_rows)},
            {'rides': rides},
        )

    def test_perfect_alignment_no_issues(self):
        meter, nippou = self._make_data(
            [_meter_row(1, '10:00', 1000), _meter_row(2, '11:00', 2000)],
            [_ride('10:00', 1000), _ride('11:00', 2000)],
        )
        output = app.build_report(meter, nippou)
        assert len(output) == 2
        # state が 'ok' or 空 (mismatch でも missing でもない)
        for row in output:
            assert row.get('state') in ('ok', '', None)

    def test_missing_nippou_detected(self):
        # 1 行書き漏れ
        meter, nippou = self._make_data(
            [_meter_row(1, '10:00', 1000),
             _meter_row(2, '11:00', 2000),
             _meter_row(3, '12:00', 1500)],
            [_ride('10:00', 1000), _ride('11:00', 2000)],
        )
        output = app.build_report(meter, nippou)
        assert len(output) == 3  # メーター行数 = 必ず N 行
        states = [r.get('state') for r in output]
        assert 'missing_nippou' in states

    def test_mismatch_amount(self):
        meter, nippou = self._make_data(
            [_meter_row(1, '10:00', 1000)],
            [_ride('10:00', 1090)],  # 金額違い
        )
        output = app.build_report(meter, nippou)
        assert output[0]['state'] == 'mismatch'
        assert output[0]['nippou_amount'] == 1090
        # 出力金額はメーター値 (正解) を採用
        assert output[0]['gen'] + output[0]['mi'] == 1000

    def test_split_payment(self):
        # 分割払い: 現金 + チケット = メーター額
        meter, nippou = self._make_data(
            [_meter_row(1, '10:00', 1800)],
            [{'time': '10:00', 'passengers': 1, 'case': 'split',
              'gen_amount': 1000, 'mi_amount': 800, 'memo': '現金+チケット',
              'kind': None, 'nippou_amount': None, 'overage_amount': None}],
        )
        output = app.build_report(meter, nippou)
        assert output[0]['gen'] == 1000
        assert output[0]['mi'] == 800

    def test_overage_creates_special_row(self):
        # メーター超過: 客分行 + 超過分 (special) の 2 行出力
        meter, nippou = self._make_data(
            [_meter_row(1, '10:00', 1600)],
            [{'time': '10:00', 'passengers': 1, 'case': 'overage',
              'kind': '未収', 'nippou_amount': 1500, 'overage_amount': 100,
              'gen_amount': None, 'mi_amount': None, 'memo': 'Visa'}],
        )
        output = app.build_report(meter, nippou)
        assert len(output) == 2  # 客分 + 超過分
        special = [r for r in output if r.get('state') == 'special']
        assert len(special) == 1
        assert special[0]['gen'] + special[0]['mi'] == 100  # 超過分

    def test_discount_appended_after_meter_rows(self):
        # 障割: メーター行とは独立、別行として追加
        meter, nippou = self._make_data(
            [_meter_row(1, '10:00', 1800)],
            [_ride('10:00', 1800, kind='現収'),
             {'case': 'discount', 'nippou_amount': 200, 'memo': '障割',
              'time': '', 'passengers': 0, 'kind': None,
              'gen_amount': None, 'mi_amount': None, 'overage_amount': None}],
        )
        output = app.build_report(meter, nippou)
        # 通常行 + 障割行
        assert len(output) == 2
        discount_rows = [r for r in output if r.get('state') == 'discount']
        assert len(discount_rows) == 1
        assert discount_rows[0]['mi'] == 200


# ── _add_discount_hints: 数学的検出 (v1.19.00) ─────────────────

class TestAddDiscountHints:
    def test_no_hint_when_no_mismatch(self):
        rows = [
            {'state': 'ok', 'no': 1, 'meter_amount': 1800, 'nippou_amount': 1800},
        ]
        app._add_discount_hints(rows, [{'no': 1, 'amount': 1800}])
        assert not rows[0].get('discount_hint')

    def test_hint_when_paper_is_meter_div_9(self):
        # メーター ¥1,800 / 紙 ¥200 → 1800/9 = 200 → 障割候補
        rows = [
            {'state': 'mismatch', 'no': 1, 'meter_amount': 1000,
             'nippou_amount': 200, 'gen': 1000, 'mi': 0},
        ]
        meter_rows = [{'no': 1, 'amount': 1000}, {'no': 2, 'amount': 1800}]
        app._add_discount_hints(rows, meter_rows)
        assert rows[0].get('discount_hint') is True
        assert rows[0]['discount_hint_meter_amount'] == 1800  # 1800 / 9 = 200

    def test_no_hint_when_amount_too_large(self):
        # 紙の額 ¥1,000 は障割 (通常 100-500 円) としては大きすぎる
        rows = [
            {'state': 'mismatch', 'no': 1, 'meter_amount': 1000,
             'nippou_amount': 1000},
        ]
        meter_rows = [{'no': 1, 'amount': 9000}]  # 9000 / 9 = 1000
        app._add_discount_hints(rows, meter_rows)
        # 額が大きすぎるので障割候補としない
        assert not rows[0].get('discount_hint')

    def test_tolerance_allows_rounding(self):
        # メーター ¥1,000 / 紙 ¥110 → 1000/9 ≈ 111.11 → 許容 (10円丸め)
        rows = [
            {'state': 'mismatch', 'no': 1, 'meter_amount': 1000,
             'nippou_amount': 110},
        ]
        meter_rows = [{'no': 1, 'amount': 1000}]
        app._add_discount_hints(rows, meter_rows)
        assert rows[0].get('discount_hint') is True
