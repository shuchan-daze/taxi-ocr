"""_finalize_rows / _finalize_rides の単体テスト。
AI 出力の欠損・型不正を吸収し、issues を収集する正規化層。"""
import app


# ── _finalize_rows: メーター明細の正規化 ────────────────────────

class TestFinalizeRows:
    def test_normal_rows(self):
        rows = [
            {'no': 1, 'time': '10:00', 'amount': 1500},
            {'no': 2, 'time': '10:30', 'amount': 2000},
        ]
        result = app._finalize_rows(rows)
        assert len(result['rows']) == 2
        assert result['total'] == 3500
        assert result['issues'] == []

    def test_missing_no_skipped(self):
        rows = [
            {'no': 1, 'time': '10:00', 'amount': 1500},
            {'no': None, 'time': '10:30', 'amount': 2000},  # no 欠損
        ]
        result = app._finalize_rows(rows)
        assert len(result['rows']) == 1
        assert len(result['issues']) == 1
        assert result['issues'][0]['type'] == 'missing_no'

    def test_zero_amount_kept_with_issue(self):
        rows = [
            {'no': 1, 'time': '10:00', 'amount': 0},
        ]
        result = app._finalize_rows(rows)
        # 0円行は集計に含まれるが issue として記録
        assert len(result['rows']) == 1
        issue_types = [i['type'] for i in result['issues']]
        assert 'zero_amount' in issue_types

    def test_duplicate_no_detected(self):
        rows = [
            {'no': 1, 'time': '10:00', 'amount': 1500},
            {'no': 1, 'time': '11:00', 'amount': 2000},  # No 重複
        ]
        result = app._finalize_rows(rows)
        issue_types = [i['type'] for i in result['issues']]
        assert 'duplicate_no' in issue_types

    def test_missing_time_detected(self):
        rows = [
            {'no': 1, 'time': '', 'amount': 1500},
        ]
        result = app._finalize_rows(rows)
        issue_types = [i['type'] for i in result['issues']]
        assert 'missing_time' in issue_types

    def test_non_dict_invalid(self):
        rows = [
            {'no': 1, 'time': '10:00', 'amount': 1500},
            'not a dict',
        ]
        result = app._finalize_rows(rows)
        assert len(result['rows']) == 1
        assert any(i['type'] == 'invalid_row' for i in result['issues'])

    def test_empty_input(self):
        assert app._finalize_rows([])['rows'] == []
        assert app._finalize_rows(None)['rows'] == []


# ── _finalize_rides: 日報行の正規化 ─────────────────────────────

class TestFinalizeRides:
    def test_normal_ride(self):
        rides = [
            {'case': 'normal', 'kind': '現収', 'nippou_amount': 1500,
             'memo': '現金', 'time': '14:30', 'passengers': 1},
        ]
        result = app._finalize_rides(rides)
        assert len(result['rides']) == 1
        assert result['issues'] == []
        assert result['rides'][0]['kind'] == '現収'
        assert result['rides'][0]['nippou_amount'] == 1500

    def test_invalid_case_normalized(self):
        rides = [
            {'case': 'mystery', 'kind': '現収', 'nippou_amount': 1500},
        ]
        result = app._finalize_rides(rides)
        # 不正 case は 'normal' に補正
        assert result['rides'][0]['case'] == 'normal'
        assert any(i['type'] == 'invalid_case' for i in result['issues'])

    def test_invalid_kind_normalized(self):
        rides = [
            {'case': 'normal', 'kind': '謎', 'nippou_amount': 1500},
        ]
        result = app._finalize_rides(rides)
        assert result['rides'][0]['kind'] == '現収'
        assert any(i['type'] == 'invalid_kind' for i in result['issues'])

    def test_discount_without_amount_dropped(self):
        rides = [
            {'case': 'discount', 'nippou_amount': None},
        ]
        result = app._finalize_rides(rides)
        # 金額無い discount は集計不能、データ破棄
        assert len(result['rides']) == 0
        assert any(i['type'] == 'discount_missing_amount' for i in result['issues'])

    def test_split_both_amounts_missing_issue(self):
        rides = [
            {'case': 'split', 'gen_amount': None, 'mi_amount': None},
        ]
        result = app._finalize_rides(rides)
        assert any(i['type'] == 'split_missing_amounts' for i in result['issues'])

    def test_overage_invalid_amount_issue(self):
        rides = [
            {'case': 'overage', 'kind': '未収', 'nippou_amount': 1500,
             'overage_amount': 0},
        ]
        result = app._finalize_rides(rides)
        assert any(i['type'] == 'overage_missing_amount' for i in result['issues'])

    def test_passengers_default_when_invalid(self):
        rides = [
            {'case': 'normal', 'kind': '現収', 'nippou_amount': 1500,
             'passengers': None},
        ]
        result = app._finalize_rides(rides)
        assert result['rides'][0]['passengers'] == 1  # default

    def test_where_format_is_index_based(self):
        """v1.18.00 で全 where 文字列を 'index N' 形式に統一済"""
        rides = [
            {'case': 'mystery'},  # invalid_case
        ]
        result = app._finalize_rides(rides)
        for issue in result['issues']:
            # where が 'index 0' で始まる (meter_no= を含まない)
            assert issue['where'].startswith('index ') or issue['where'] == 'index 0'
            assert 'meter_no' not in issue['where']
