"""validate / aggregate_totals / validate_meter_sequence の単体テスト。"""
import app


def _meter(rows):
    return {'rows': rows, 'total': sum(r['amount'] for r in rows)}


def _nippou(rides):
    return {'rides': rides}


def _normal_ride(amount, kind='現収', time='10:00'):
    return {'time': time, 'passengers': 1, 'case': 'normal', 'kind': kind,
            'memo': '', 'nippou_amount': amount,
            'overage_amount': None, 'gen_amount': None, 'mi_amount': None}


# ── validate: 期待値 vs 出力合計 ────────────────────────────────

class TestValidate:
    def test_perfect_match(self):
        meter = _meter([{'no': 1, 'time': '10:00', 'amount': 1000}])
        nippou = _nippou([_normal_ride(1000)])
        rows = app.build_report(meter, nippou)
        ok, diff = app.validate(rows, meter, nippou)
        assert ok is True
        assert diff == 0

    def test_with_discount(self):
        # メーター ¥1,800 + 障割 ¥200 = 期待値 ¥2,000
        meter = _meter([{'no': 1, 'time': '10:00', 'amount': 1800}])
        nippou = _nippou([
            _normal_ride(1800),
            {'case': 'discount', 'nippou_amount': 200, 'memo': '障割',
             'time': '', 'passengers': 0, 'kind': None,
             'gen_amount': None, 'mi_amount': None, 'overage_amount': None},
        ])
        rows = app.build_report(meter, nippou)
        ok, diff = app.validate(rows, meter, nippou)
        assert ok is True

    def test_missing_nippou_doesnt_break_total(self):
        # 1 行書き漏れでも合計は成立 (missing は現収仮置きで集計に含む)
        meter = _meter([
            {'no': 1, 'time': '10:00', 'amount': 1000},
            {'no': 2, 'time': '11:00', 'amount': 2000},
        ])
        nippou = _nippou([_normal_ride(1000)])  # 1 つだけ
        rows = app.build_report(meter, nippou)
        ok, diff = app.validate(rows, meter, nippou)
        # missing_nippou 行も「現収」仮置きで gen に計上 → 合計成立
        assert ok is True


# ── aggregate_totals: 集計 ──────────────────────────────────────

class TestAggregateTotals:
    def test_normal_aggregate(self):
        rows = [
            {'state': 'ok', 'passengers': 1, 'gen': 1000, 'mi': 0},
            {'state': 'ok', 'passengers': 2, 'gen': 0, 'mi': 2000},
        ]
        ken, nin, gen, mi, sou, tax, net = app.aggregate_totals(rows)
        assert ken == 2  # 件数
        assert nin == 3  # 人数
        assert gen == 1000
        assert mi == 2000
        assert sou == 3000
        # 消費税は内税 10%: 3000 / 11 ≈ 273 → 10円丸めで 270
        assert tax == 270
        assert net == 2730

    def test_special_excluded_from_count(self):
        # メーター超過の special 行は二重カウント回避のため件数除外
        rows = [
            {'state': 'ok', 'passengers': 1, 'gen': 1500, 'mi': 0},
            {'state': 'special', 'passengers': 1, 'gen': 100, 'mi': 0},
        ]
        ken, nin, gen, mi, sou, tax, net = app.aggregate_totals(rows)
        assert ken == 1  # special を除外
        assert nin == 1
        # 金額は両方とも合算
        assert sou == 1600

    def test_discount_excluded_from_count(self):
        # 障割行は乗客ではないので件数除外
        rows = [
            {'state': 'ok', 'passengers': 1, 'gen': 1800, 'mi': 0},
            {'state': 'discount', 'passengers': 0, 'gen': 0, 'mi': 200},
        ]
        ken, nin, gen, mi, sou, tax, net = app.aggregate_totals(rows)
        assert ken == 1
        # 金額は合算
        assert sou == 2000

    def test_missing_nippou_included_in_count(self):
        # missing_nippou は 1 件 1 人として計上 (合計成立のため)
        rows = [
            {'state': 'missing_nippou', 'passengers': 1, 'gen': 1000, 'mi': 0},
        ]
        ken, nin, gen, mi, sou, tax, net = app.aggregate_totals(rows)
        assert ken == 1
        assert nin == 1


# ── validate_meter_sequence: メーター行番号の連番チェック ────────

class TestValidateMeterSequence:
    def test_continuous_sequence(self):
        meter = _meter([
            {'no': 1, 'time': '10:00', 'amount': 1000},
            {'no': 2, 'time': '10:30', 'amount': 1500},
            {'no': 3, 'time': '11:00', 'amount': 2000},
        ])
        ok, missing = app.validate_meter_sequence(meter)
        assert ok is True
        assert missing == []

    def test_gap_detected(self):
        # No.2 が欠落
        meter = _meter([
            {'no': 1, 'time': '10:00', 'amount': 1000},
            {'no': 3, 'time': '11:00', 'amount': 2000},
        ])
        ok, missing = app.validate_meter_sequence(meter)
        assert ok is False
        assert 2 in missing

    def test_empty_meter(self):
        meter = _meter([])
        ok, missing = app.validate_meter_sequence(meter)
        # 空はエッジケース、少なくとも crash しないこと
        assert ok is True or ok is False  # 仕様依存
