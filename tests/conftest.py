"""pytest 共通フィクスチャ & app.py を import 可能にするための mock 設定。

app.py は import 時に streamlit などの UI 依存を持つ。
テストではそれらを直接呼ばないので、import 時にだけ mock を当てて pure logic を
取り出せるようにする。
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock


# プロジェクトルートを sys.path に追加 (tests/ から app をインポート可能に)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _AttrDict(dict):
    """st.session_state 模倣: dict 属性アクセスと get() の両方をサポート。"""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)
    def __setattr__(self, key, value):
        self[key] = value


def _install_mocks():
    """app.py が import 時に呼ぶ重い依存をすべて MagicMock に差し替える。"""
    # streamlit
    mock_st = MagicMock()
    mock_st.session_state = _AttrDict()
    mock_st.secrets = {}
    sys.modules.setdefault('streamlit', mock_st)
    sys.modules.setdefault('streamlit.components', MagicMock())
    # Anthropic SDK is imported lazily in OCR code, but keeping a mock here prevents
    # optional dependency issues in focused unit tests.
    sys.modules.setdefault('anthropic', MagicMock())
    # PIL extras
    sys.modules.setdefault('pillow_heif', MagicMock())


_install_mocks()
