# Changelog

このプロジェクトのすべての変更履歴を記録します。

バージョニング: [Semantic Versioning 2.0](https://semver.org/lang/ja/) (`MAJOR.MINOR.PATCH`)

- **MAJOR**: 大きな変更・仕様変更（後方互換なし）
- **MINOR**: 部分的な機能追加・改善（後方互換あり）
- **PATCH**: バグ修正・小さな調整

---

## [1.1.2] - 2026-05-11

### Performance (速度改善)
- `to_b64()` に per-image キャッシュ機構を追加。pipeline 中 identify_image / check_clarity / parse_meter / classify_nippou で同じ画像が複数回 JPEG エンコードされていた問題を解消。1 画像あたり 3 回 → 1 回。

### Removed (dead code 削除)
- HTML 未使用属性を削除:
  - `data-metric="..."` 計 5 箇所（render_summary）
  - `data-value="..."` 計 2 箇所（render_detail_table）
  - `data-rowidx="..."` 1 箇所（render_detail_table、enumerate も削除）
- 旧 dblclick 編集 UI の名残 CSS を削除:
  - `cursor: pointer` および `:hover` outline（クリック編集 JS が無いため誤誘導になっていた）
  - `.detail-table td input.cell-edit` クラス

---

## [1.1.1] - 2026-05-11

### Changed (表示調整)
- バージョン番号のフォントサイズを 11px → 14px に拡大、不透明度を 0.55 → 0.7 に調整
- タイトルブロック下の余白を `margin-bottom: 1.5rem` → `0.5rem` に削減
- 完成バーのフォント拡大:
  - `✓ 完成` ラベル: 14px → 18px
  - 件数・人数: 22px → 28px / weight 500 → 600
  - 件・人 単位: 11px → 14px

---

## [1.1.0] - 2026-05-11

### Added (機能追加)
- 障害者割引（障割）対応の本格実装
  - `case='discount'` を classify_nippou のプロンプトに追加
  - kind の入力に関わらず必ず未収に計上
  - 日報の手書き割引額（`nippou_amount`）を真値として扱う
- **sequence ベースアライメント**: `meter_no` がメーター明細書の行番号と一致しない場合（空回し非実施時）でも正しく動作
- 障割行を日報順の正しい位置に `'6+'` 形式で挿入
- **+α 要素の救済**: `passengers=NULL` の orphan ride を会計調整として救済

### Fixed (バグ修正)
- 整合性チェックで障割の `'6+'` ラベルが overage 用パスに誤検出される問題を修正
- 税抜運収が `34550.0` のように小数を含めて表示される問題を修正
- バージョン番号が背景色と同色で見えなかった問題を修正
- 結果表示時のスクロール位置の改善

### Refactored (コード整理)
- `_particles_html()` をモジュール定数化（パイプライン中の重複生成を排除）
- charter / extras 関連の dead code を削除（CSS、state マップ、UI 表示）
- レイアウトを if/else 構造に整理、`result_slot = st.empty()` で結果ブロックを安定配置

---

## [1.0.0] - 2026-05-10

### 初回リリース
- Vision API + Claude のハイブリッド OCR パイプライン
- メーターレシート + 手書き日報の 2 画像から日報自動生成
- メーター超過（から回し）対応
- 集計（件数・人数・現収・未収・総収・消費税・税抜運収）
- 整合性チェック（メーター額 vs 出力テーブル）
- 乖離チェック（メーター件数 vs 日報件数）
- パーティクルローダー演出（CSS @keyframes のみ、JS 不使用）
