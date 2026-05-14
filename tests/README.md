# テスト

タクシー日報 OCR アプリのテスト群。Phase 1 (純ロジック単体テスト) + Phase 2 (実画像 E2E テスト) の 2 段構成。

## 実行方法

```bash
# 仮想環境を有効化
source venv/bin/activate

# Phase 1 (純ロジック、API 不要、コストゼロ、数秒で完了)
pytest tests/ --ignore=tests/test_e2e.py

# 全テスト (Phase 2 は skip される)
pytest tests/

# Phase 2 も実行 (実 API 呼び出し、コスト発生)
RUN_E2E_TESTS=1 ANTHROPIC_API_KEY=sk-... pytest tests/test_e2e.py
```

## ファイル構成

```
tests/
├── conftest.py             # streamlit/anthropic を mock して app.py を import 可能に
├── test_helpers.py         # _coerce_int / _parse_hhmm / _is_*_marker 等
├── test_interpret.py       # _interpret_raw_row / interpret_raw_rows
├── test_finalize.py        # _finalize_rows / _finalize_rides
├── test_alignment.py       # _align_rides_to_meter / build_report / _add_discount_hints
├── test_validate.py        # validate / aggregate_totals / validate_meter_sequence
├── test_e2e.py             # 実画像 → 全パイプライン → 期待値比較 (デフォルト skip)
└── fixtures/               # E2E テスト用の画像 + 期待値 JSON
    └── <case_name>/
        ├── meter.jpg
        ├── nippou.jpg
        └── meta.json
```

## Phase 1: 純ロジックテスト

API 呼び出しなし、純粋な Python ロジックの単体テスト。コストゼロ、実行 0.1 秒程度。
構造変更や refactoring の際の安全網になる。

現在のカバー範囲 (約 78 ケース):
- ヘルパー関数: `_coerce_int`, `_parse_hhmm`, `_is_discount_memo`, `_is_overage_marker`,
  `_parse_overage_marker`, `_cell_to_int`
- 解釈層: `_interpret_raw_row`, `interpret_raw_rows`, `_split_rides`
- 正規化層: `_finalize_rows`, `_finalize_rides`
- アライメント: `_align_rides_to_meter` (Pass 1: 金額一致 / Pass 2: 時刻最近接)
- 統合: `build_report`, `_add_discount_hints`
- 検証: `validate`, `aggregate_totals`, `validate_meter_sequence`

## Phase 2: E2E テスト (実画像)

実際の Claude API を呼んで画像 → 結果のパイプライン全体を検証。

### コスト感

- 1 ケース ≈ $0.10〜$0.20 (Claude Opus 4.5)
- 10 ケース × 月 5 回実行 = 月 $5〜$10
- CI で自動実行はしない (お金かかるので)

### テストケースの追加方法

実機で「あ、これ間違えた」という日報に遭遇したら、そのケースを fixture 化:

```bash
# 1. ケース用のディレクトリを作る
mkdir -p tests/fixtures/case_001_handwritten_missing_row

# 2. 画像を置く
cp /path/to/meter.jpg tests/fixtures/case_001_handwritten_missing_row/meter.jpg
cp /path/to/nippou.jpg tests/fixtures/case_001_handwritten_missing_row/nippou.jpg

# 3. 期待値を書く
cat > tests/fixtures/case_001_handwritten_missing_row/meta.json <<EOF
{
    "description": "メーター 17 行、紙が No.11 を書き漏れ",
    "meter_total": 30300,
    "row_count": 17,
    "state_counts": {
        "ok": 16,
        "missing_nippou": 1
    }
}
EOF
```

### meta.json のフィールド

すべて optional。書かれた項目だけ検証される。

| キー | 型 | 意味 |
|------|------|------|
| `description` | string | 人間用のメモ (テストは無視) |
| `meter_total` | int | メーター行の金額合計 |
| `row_count` | int | build_report 後の行数 |
| `state_counts` | dict | state ごとの件数 (例: `{"ok": 16, "missing_nippou": 1}`) |

### プライバシー

`tests/fixtures/` 配下の画像は実画像なので、コミット前に注意:
- 個人情報 (顧客名・乗務員名等) が写ってないか確認
- 必要なら `tests/fixtures/.gitignore` で個別管理
