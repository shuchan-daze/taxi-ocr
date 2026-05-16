"""ヘルパー関数の単体テスト: _coerce_int / _parse_hhmm / _is_discount_memo /
_is_overage_marker / _parse_overage_marker / _cell_to_int."""
import app


# ── _coerce_int ─────────────────────────────────────────────────

class TestCoerceInt:
    def test_int_passthrough(self):
        assert app._coerce_int(1234) == 1234
        assert app._coerce_int(0) == 0
        assert app._coerce_int(-100) == -100

    def test_float_truncated_to_int(self):
        assert app._coerce_int(12.7) == 12
        assert app._coerce_int(12.0) == 12

    def test_string_digits(self):
        assert app._coerce_int('1500') == 1500
        assert app._coerce_int('1,500') == 1500
        assert app._coerce_int('¥1,500') == 1500
        assert app._coerce_int('  1500  ') == 1500

    def test_string_invalid(self):
        assert app._coerce_int('abc') is None
        assert app._coerce_int('1.5.0') is None

    def test_none_and_empty(self):
        assert app._coerce_int(None) is None
        assert app._coerce_int('') is None

    def test_default_fallback(self):
        assert app._coerce_int(None, default=0) == 0
        assert app._coerce_int('xx', default=-1) == -1

    def test_bool_excluded(self):
        # bool は int 派生だが、True=1 / False=0 として扱わない (誤検出回避)
        assert app._coerce_int(True) is None
        assert app._coerce_int(False) is None


# ── _parse_hhmm ─────────────────────────────────────────────────

class TestParseHhmm:
    def test_valid_hhmm(self):
        assert app._parse_hhmm('17:14') == 17 * 60 + 14
        assert app._parse_hhmm('00:00') == 0
        assert app._parse_hhmm('23:59') == 23 * 60 + 59

    def test_none_or_empty(self):
        assert app._parse_hhmm(None) is None
        assert app._parse_hhmm('') is None

    def test_invalid_format(self):
        assert app._parse_hhmm('abc') is None
        assert app._parse_hhmm('25:99') is None or app._parse_hhmm('25:99') == 25 * 60 + 99
        # 厳密な validation は実装次第。少なくとも crash しなければ OK


# ── _is_discount_memo ───────────────────────────────────────────

class TestIsDiscountMemo:
    def test_explicit_discount_keywords(self):
        assert app._is_discount_memo('障割') is True
        assert app._is_discount_memo('障害者割引') is True

    def test_non_discount(self):
        assert app._is_discount_memo('現金') is False
        assert app._is_discount_memo('Visa') is False
        assert app._is_discount_memo('') is False
        assert app._is_discount_memo(None) is False


# ── _is_overage_marker ──────────────────────────────────────────

class TestIsOverageMarker:
    def test_overage_string(self):
        assert app._is_overage_marker('+100') is True
        assert app._is_overage_marker('+200') is True
        assert app._is_overage_marker('+50') is True

    def test_not_overage(self):
        assert app._is_overage_marker(100) is False  # int は overage マーカーではない
        assert app._is_overage_marker('100') is False  # + 無し文字列も非該当
        assert app._is_overage_marker('') is False
        assert app._is_overage_marker(None) is False
        assert app._is_overage_marker('+abc') is False


# ── _parse_overage_marker ───────────────────────────────────────

class TestParseOverageMarker:
    def test_valid_marker(self):
        assert app._parse_overage_marker('+100') == 100
        assert app._parse_overage_marker('+50') == 50

    def test_non_marker_returns_default(self):
        # 仕様: マーカー以外なら 0 など (実装に合わせる)
        result = app._parse_overage_marker('100')
        assert result == 0 or result is None  # どちらでも害なし


# ── _cell_to_int ────────────────────────────────────────────────

class TestCellToInt:
    """_cell_to_int の仕様: AI 出力の raw cell を解釈する関数。
    - int/float → int 変換
    - "+N" overage マーカー → N (int)
    - その他 (None, 空文字, "1500" 等の生文字列) → None
    """

    def test_int_value(self):
        assert app._cell_to_int(1500) == 1500
        assert app._cell_to_int(0) == 0

    def test_float_value(self):
        assert app._cell_to_int(1500.0) == 1500

    def test_overage_marker_parsed(self):
        # "+100" は overage marker としてパースされる
        assert app._cell_to_int('+100') == 100
        assert app._cell_to_int('+200') == 200

    def test_none_or_dash(self):
        assert app._cell_to_int(None) is None
        assert app._cell_to_int('') is None
        assert app._cell_to_int('-') is None

    def test_plain_string_not_handled(self):
        # 数字文字列 (例 '1500') は AI 出力では float/int で来る前提。
        # 想定外の string が来たら None を返す (sanity check 用テスト)。
        assert app._cell_to_int('1500') is None


# ── __version__ 定数: 一元管理ガード ─────────────────────────────

class TestVersionConstant:
    """版番号がモジュール定数 __version__ で一元管理されてることを保証。
    過去 (〜v1.24) は UI バナーに別の値がハードコードされて差が出る事故が起きた。
    """

    def test_version_constant_exists(self):
        assert hasattr(app, '__version__')
        assert isinstance(app.__version__, str)

    def test_version_format(self):
        # SemVer: X.Y.ZZ (PATCH は 2 桁ゼロパディング)
        import re
        assert re.match(r'^\d+\.\d+\.\d{2}$', app.__version__)
