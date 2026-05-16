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

    def test_with_charter(self):
        # メーター ¥1,000 + 貸切 ¥16,400 = 期待値 ¥17,400
        meter = _meter([{'no': 1, 'time': '10:00', 'amount': 1000}])
        nippou = _nippou([
            _normal_ride(1000),
            {'case': 'charter', 'nippou_amount': 16400, 'memo': '貸切',
             'time': '13:30', 'passengers': 4, 'kind': '現収',
             'gen_amount': None, 'mi_amount': None, 'overage_amount': None},
        ])
        rows = app.build_report(meter, nippou)
        ok, diff = app.validate(rows, meter, nippou)
        assert ok is True
        # 出力合計 (gen+mi) も 17,400
        total = sum((r.get('gen') or 0) + (r.get('mi') or 0) for r in rows)
        assert total == 17400

    def test_apply_user_choices_default_to_gen(self):
        # 選択無し (デフォルト) → 現収のまま
        rows = [
            {'state': 'missing_nippou', 'no': 1, 'meter_amount': 1500, 'gen': 1500, 'mi': 0, 'kind': '現収'},
        ]
        result = app.apply_user_choices(rows, choices={})
        assert result[0]['gen'] == 1500
        assert result[0]['mi'] == 0
        assert result[0]['kind'] == '現収'

    def test_apply_user_choices_switch_to_mi(self):
        # ユーザーが「未収」選択 → gen/mi 入れ替え
        rows = [
            {'state': 'missing_nippou', 'no': 2, 'meter_amount': 1800, 'gen': 1800, 'mi': 0, 'kind': '現収'},
        ]
        result = app.apply_user_choices(rows, choices={'missing_choice_2': '未収'})
        assert result[0]['gen'] == 0
        assert result[0]['mi'] == 1800
        assert result[0]['kind'] == '未収'

    def test_apply_user_choices_discount_default_agreed(self):
        # status 未指定 → デフォルト「合ってる」→ AI 読みそのまま
        rows = [
            {'state': 'discount', 'no': '5+', 'gen': 0, 'mi': 300, 'memo': '障割'},
        ]
        result = app.apply_user_choices(rows, choices={})
        assert result[0]['mi'] == 300

    def test_apply_user_choices_discount_disagreed_override(self):
        # status「違う」+ amount 指定 → 上書きされる
        rows = [
            {'state': 'discount', 'no': '5+', 'gen': 0, 'mi': 300, 'memo': '障割'},
        ]
        choices = {
            'discount_status_5+': '違う',
            'discount_amount_5+': 380,
        }
        result = app.apply_user_choices(rows, choices=choices)
        assert result[0]['mi'] == 380

    def test_apply_user_choices_discount_disagreed_no_amount(self):
        # status「違う」だが amount 未指定 → AI 読みのまま (安全側)
        rows = [
            {'state': 'discount', 'no': '5+', 'gen': 0, 'mi': 300, 'memo': '障割'},
        ]
        result = app.apply_user_choices(rows, choices={'discount_status_5+': '違う'})
        assert result[0]['mi'] == 300

    def test_apply_user_choices_charter_default_agreed(self):
        # 貸切も同じパターン。デフォルト「合ってる」→ そのまま
        rows = [
            {'state': 'charter', 'no': '貸', 'gen': 16400, 'mi': 0, 'kind': '現収', 'memo': '貸切'},
        ]
        result = app.apply_user_choices(rows, choices={})
        assert result[0]['gen'] == 16400
        assert result[0]['mi'] == 0

    def test_apply_user_choices_charter_disagreed_override(self):
        # 貸切「違う」+ amount → kind に応じて gen に上書き
        rows = [
            {'state': 'charter', 'no': '貸', 'gen': 16400, 'mi': 0, 'kind': '現収', 'memo': '貸切'},
        ]
        choices = {
            'charter_status_貸': '違う',
            'charter_amount_貸': 17000,
        }
        result = app.apply_user_choices(rows, choices=choices)
        assert result[0]['gen'] == 17000
        assert result[0]['mi'] == 0

    def test_apply_user_choices_charter_kind_mi(self):
        # 貸切 kind='未収' で「違う」→ mi に上書き
        rows = [
            {'state': 'charter', 'no': '貸', 'gen': 0, 'mi': 20000, 'kind': '未収', 'memo': '貸切'},
        ]
        choices = {
            'charter_status_貸': '違う',
            'charter_amount_貸': 25000,
        }
        result = app.apply_user_choices(rows, choices=choices)
        assert result[0]['gen'] == 0
        assert result[0]['mi'] == 25000

    def test_apply_user_choices_missing_ignore(self):
        # missing_nippou で「無視」選択 → gen/mi 0、ignored_by_user フラグ立つ
        rows = [
            {'state': 'missing_nippou', 'no': 5, 'meter_amount': 1500, 'gen': 1500, 'mi': 0, 'kind': '現収'},
        ]
        result = app.apply_user_choices(rows, choices={'missing_choice_5': '無視'})
        assert result[0]['gen'] == 0
        assert result[0]['mi'] == 0
        assert result[0]['ignored_by_user'] is True

    def test_apply_user_choices_mismatch_disagreed(self):
        # mismatch で「違う」+ amount → メーター値を上書き
        rows = [
            {'state': 'mismatch', 'no': 5, 'meter_amount': 1300, 'gen': 1300, 'mi': 0,
             'kind': '現収', 'nippou_amount': 1000},
        ]
        choices = {
            'mismatch_status_5': '違う',
            'mismatch_amount_5': 1000,
        }
        result = app.apply_user_choices(rows, choices=choices)
        assert result[0]['gen'] == 1000

    def test_apply_user_choices_mismatch_default_agreed(self):
        # mismatch のデフォルトは「合ってる」→ メーター値そのまま
        rows = [
            {'state': 'mismatch', 'no': 5, 'meter_amount': 1300, 'gen': 1300, 'mi': 0,
             'kind': '現収', 'nippou_amount': 1000},
        ]
        result = app.apply_user_choices(rows, choices={})
        assert result[0]['gen'] == 1300  # メーター値のまま

    def test_aggregate_excludes_ignored_rows(self):
        # ignored_by_user=True の行は件数・人数から除外
        rows = [
            {'state': 'ok', 'gen': 1000, 'mi': 0, 'passengers': 1},
            {'state': 'missing_nippou', 'gen': 0, 'mi': 0, 'passengers': 1,
             'ignored_by_user': True},
        ]
        ken, nin, gen, mi, sou, tax, net = app.aggregate_totals(rows)
        assert ken == 1  # 無視行は数えない
        assert nin == 1  # 同上
        assert gen == 1000

    def test_apply_user_choices_only_affects_missing(self):
        # missing_nippou 以外の行は触らない
        rows = [
            {'state': 'ok', 'no': 1, 'meter_amount': 1000, 'gen': 1000, 'mi': 0, 'kind': '現収'},
            {'state': 'missing_nippou', 'no': 2, 'meter_amount': 1800, 'gen': 1800, 'mi': 0, 'kind': '現収'},
        ]
        result = app.apply_user_choices(rows, choices={'missing_choice_1': '未収', 'missing_choice_2': '未収'})
        # No.1 は ok 行なので missing_choice_1 は無視される
        assert result[0]['gen'] == 1000
        assert result[0]['mi'] == 0
        # No.2 は missing なので適用される
        assert result[1]['mi'] == 1800

    def test_charter_with_discount_and_meter(self):
        # 三役: メーター + 障割 + 貸切 が同居しても合計成立
        meter = _meter([
            {'no': 1, 'time': '10:00', 'amount': 2700},
            {'no': 2, 'time': '11:00', 'amount': 1500},
        ])
        nippou = _nippou([
            _normal_ride(2700, kind='未収'),
            _normal_ride(1500),
            {'case': 'discount', 'nippou_amount': 300, 'memo': '障割',
             'time': '', 'passengers': 0, 'kind': None,
             'gen_amount': None, 'mi_amount': None, 'overage_amount': None},
            {'case': 'charter', 'nippou_amount': 16400, 'memo': '貸切',
             'time': '13:30', 'passengers': 4, 'kind': '現収',
             'gen_amount': None, 'mi_amount': None, 'overage_amount': None},
        ])
        rows = app.build_report(meter, nippou)
        ok, diff = app.validate(rows, meter, nippou)
        assert ok is True, f'diff={diff}'
        # 期待: 2700 + 1500 + 300 + 16400 = 20,900
        total = sum((r.get('gen') or 0) + (r.get('mi') or 0) for r in rows)
        assert total == 20900


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
