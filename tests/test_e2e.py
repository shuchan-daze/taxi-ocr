"""End-to-end OCR テスト (Phase 2)。

実際の Claude API を呼んで、画像 → 結果 のパイプライン全体を検証する。
デフォルトでは skip。実行する場合は環境変数で明示的に有効化:

    RUN_E2E_TESTS=1 ANTHROPIC_API_KEY=sk-... pytest tests/test_e2e.py

テストケース追加方法:
    tests/fixtures/<case_name>/
        meter.jpg      ← メーター明細書の写真 (gitignore 済の test_data/ にあるものをコピー or symlink)
        nippou.jpg     ← 手書き日報の写真
        meta.json      ← 期待出力 (下記フォーマット)

    meta.json の例:
        {
            "description": "通常 17 行、書き漏れ無し",
            "meter_total": 30300,
            "row_count": 17,
            "state_counts": {
                "ok": 16,
                "missing_nippou": 1
            }
        }

設計判断:
    - run_pipeline をフルで呼ばず、parse_meter / classify_nippou / build_report を
      個別呼ぶスタイル。pipeline 全体のローダー UI 依存を避ける。
    - 1 ケース ≈ $0.10-0.20 の API コスト (Claude Opus 4.5)
    - 大量に走らせるとお金かかるので、CI 自動実行はしない設計
    - Shuchan が「あ、これ間違ってた」と思った日報を 1 ケース追加するパターンで運用
"""
import json
import os
from pathlib import Path

import pytest

import app


pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_E2E_TESTS'),
    reason='E2E tests require RUN_E2E_TESTS=1 and ANTHROPIC_API_KEY',
)


FIXTURES_DIR = Path(__file__).parent / 'fixtures'


def _discover_test_cases():
    """fixtures/ 配下のディレクトリを列挙し、meta.json があるものをテストケース化。"""
    cases = []
    if not FIXTURES_DIR.exists():
        return cases
    for case_dir in sorted(FIXTURES_DIR.iterdir()):
        if not case_dir.is_dir():
            continue
        meta_path = case_dir / 'meta.json'
        if not meta_path.exists():
            continue
        with open(meta_path) as f:
            meta = json.load(f)
        cases.append({
            'id': case_dir.name,
            'dir': case_dir,
            'meta': meta,
        })
    return cases


TEST_CASES = _discover_test_cases()


def _load_pil_image(path):
    from PIL import Image
    return Image.open(path)


def _build_real_client():
    """実 Anthropic クライアントを構築。テスト中は本物の API キーが必要。"""
    import anthropic
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        pytest.skip('ANTHROPIC_API_KEY not set')
    return anthropic.Anthropic(api_key=api_key)


@pytest.mark.skipif(not TEST_CASES, reason='No test cases in tests/fixtures/')
@pytest.mark.parametrize('case', TEST_CASES, ids=lambda c: c['id'])
def test_pipeline_e2e(case):
    """各 fixture ケースについて、OCR → 統合 → 期待値比較。"""
    client = _build_real_client()
    case_dir = case['dir']
    meta = case['meta']

    # 画像読み込み (拡張子は jpg/png/heic のいずれか自動検出)
    meter_path = _find_image(case_dir, 'meter')
    nippou_path = _find_image(case_dir, 'nippou')
    meter_img = _load_pil_image(meter_path)
    nippou_img = _load_pil_image(nippou_path)

    # Stage 1-2-3 を直接実行 (run_pipeline ではなく個別呼び出し、UI 依存を避ける)
    meter_data = app.parse_meter(client, meter_img)
    nippou_data = app.classify_nippou(client, nippou_img, meter_data)
    report_rows = app.build_report(meter_data, nippou_data)

    # 期待値の各項目を検証 (meta.json に記載のものだけ)
    if 'meter_total' in meta:
        actual = sum(int(r.get('amount') or 0) for r in meter_data.get('rows', []))
        assert actual == meta['meter_total'], (
            f"meter_total mismatch: expected {meta['meter_total']}, got {actual}"
        )

    if 'row_count' in meta:
        assert len(report_rows) == meta['row_count'], (
            f"row_count mismatch: expected {meta['row_count']}, got {len(report_rows)}"
        )

    if 'state_counts' in meta:
        actual_counts = {}
        for r in report_rows:
            s = r.get('state') or 'ok'
            actual_counts[s] = actual_counts.get(s, 0) + 1
        for state, expected_n in meta['state_counts'].items():
            assert actual_counts.get(state, 0) == expected_n, (
                f"state_counts['{state}'] mismatch: "
                f"expected {expected_n}, got {actual_counts.get(state, 0)}"
            )


def _find_image(case_dir, basename):
    """case_dir 配下の basename.{jpg,jpeg,png,heic} を探す。"""
    for ext in ('jpg', 'jpeg', 'png', 'heic', 'JPG', 'JPEG', 'PNG', 'HEIC'):
        candidate = case_dir / f'{basename}.{ext}'
        if candidate.exists():
            return candidate
    pytest.skip(f'No {basename} image in {case_dir}')
