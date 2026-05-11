# Changelog

このプロジェクトのすべての変更履歴を記録します。

バージョニング: [Semantic Versioning 2.0](https://semver.org/lang/ja/) (`MAJOR.MINOR.PATCH`)

- **MAJOR**: 大きな変更・仕様変更（後方互換なし）
- **MINOR**: 部分的な機能追加・改善（後方互換あり）
- **PATCH**: バグ修正・小さな調整（**常に 2 桁ゼロパディング表記**、例: `1.1.04`）

---

## [1.2.04] - 2026-05-11

### Removed (撤去)
- **イントロスプラッシュ実装を撤去** (v1.2.00 〜 v1.2.03 を巻き戻し)
  - 削除した CSS: `.intro-splash` / `.intro-splash .intro-ai` / `.intro-splash .intro-sub` および `@keyframes intro-life / intro-ai-life / intro-sub-life`
  - 削除した Python: `if 'intro_shown' not in st.session_state` のレンダリングブロック
  - 残置: `_build_particles_html()` および `_PARTICLES_HTML` 定数（loader が使用するため）
- **撤去の理由**:
  - Streamlit のレンダリングパイプライン（Python 経由で逐次マークダウン送信）の構造上、CSS のみで初期 UI のチラ見え (FOUC) を完全に防ぐことが困難
  - 試した手法（z-index 引き上げ、inline 重要スタイル、CSS markdown より先に DOM 投入、グラデーション遷移）でも改善せず、起動が 4.5 秒遅くなる代償の方が大きかった
  - 将来再実装する場合は `st.set_page_config` レベルでのカスタム HTML 注入や、JavaScript ベースのアプローチが必要

---

## [1.2.03] - 2026-05-11

### Fixed (重要な修正)
- **FOUC（Flash of Unstyled Content）対策**: イントロ起動時に UI が一瞬見えてから黒に変わる問題を解消
  - イントロ splash の DOM を**メイン CSS の `<style>` タグより前**に投入
  - intro 要素に **inline 重要スタイル** (`position:fixed; inset:0; background:#010519; z-index:999999`) を直接付与
  - CSS 解析より前から黒い背景が確保され、Streamlit 内部要素も完全に隠蔽される
  - 副次効果として `_build_particles_html()` / `_PARTICLES_HTML` 定数も上部に移動

### Fixed (見た目の修正)
- **AI と TAXI NIPPOU の視覚中心がずれていた問題を修正**:
  - `letter-spacing` は末尾文字の後にも空白を生むため、要素幅が視覚中心より広くなり、flex 中央寄せでも見た目の中心がずれる
  - 両テキストに `padding-left` で letter-spacing と同値（AI: 0.08em / sub: 0.4em）を加えて視覚中心 = 要素中心 = flex 中心に揃える
  - `text-align: center` を明示

---

## [1.2.02] - 2026-05-11

### Changed (演出再設計)
イントロスプラッシュの演出を 4.5 秒の 4 フェーズに再設計、自然な「立ち上がり感」に。

**新しいタイムライン:**
| 時刻 | 状態 |
|---|---|
| 0.0s | 黒画面 (#010519) + 粒子だけが動き始める |
| 0.5s | 「AI」が下からふわっと登場 (translateY 24px → 0、opacity 0 → 1) |
| 0.8s | 「TAXI NIPPOU」が続いて登場 |
| 1.5〜2.5s | 全要素揃って静止 |
| 2.5〜4.5s | 背景が下から透明になるグラデーションへ、AI が拡大しながら blur(8px) で溶ける |

**実装ポイント:**
- 各要素 (background / AI / sub) に**ライフサイクル全体を 1 つの keyframes** で表現 (intro-life / intro-ai-life / intro-sub-life)
- 退場時に `transform: scale(1.18)` + `filter: blur(8px)` で粒子と一緒に「溶ける」効果
- 背景は `linear-gradient(to top, transparent 0%, #010519 50%)` を経由して UI へ自然に繋がる

---

## [1.2.01] - 2026-05-11

### Fixed (調整)
- イントロスプラッシュ起動時に背景の UI が透けて見えていた問題を修正:
  - `z-index: 99998 → 999999`（Streamlit ヘッダー等より上に確実に配置）
  - `background: #010519 !important` で確実な不透明背景
  - フェードアウト animation の 0.3s 遅延を削除（即座にスプラッシュ表示開始）

### Changed (見た目調整)
- **AI 文字の色を白に変更**（金 `#d4af37` → 白 `#ffffff`）
- **AI 文字のグローを白に変更**（金グロー → 白グロー、3 段階の影で立体感）
- **AI 文字のサイズを拡大**: `clamp(96px, 24vw, 220px)` → `clamp(160px, 36vw, 360px)`
- **演出順序を整理**: 粒子が先に動き始め、0.5 秒後に AI 文字、0.8 秒後にサブテキストが順番に現れる（`both` fill-mode で遅延中は非表示）

---

## [1.2.00] - 2026-05-11

### Added (機能追加)
- **イントロスプラッシュ画面**: セッション初回起動時に「AI」を中央に大表示、下段に "TAXI NIPPOU" を表示する立ち上がり演出を追加。
  - 既存のパーティクル CSS (`_PARTICLES_HTML` / spiral / drift / rise) をそのまま再利用
  - 起動から約 3 秒で CSS animation により自動フェードアウト（JS 不使用）
  - `st.session_state.intro_shown` フラグで「初回のみ表示」を制御（rerun では再表示しない）
  - `pointer-events: none` により表示中もユーザー操作をブロックしない
- `_build_particles_html()` および `_PARTICLES_HTML` 定数を CSS 直後に前倒し配置（intro と loader 両方で参照するため）

---

## [1.1.04] - 2026-05-11

### Changed (表記規約)
- PATCH 番号を **常に 2 桁ゼロパディング表記**に統一（例: `v1.1.4` → `v1.1.04`）
- 過去の全バージョン (v1.0.0 / v1.1.0 〜 v1.1.3) も遡って `v1.0.00 / v1.1.00 〜 v1.1.03` に表記変更
- 影響範囲: `app.py` ヘッダーコメント・表示 span・about expander、`CHANGELOG.md`、`README.md`
- PATCH を 99 回まで重ねても視覚的に揃う

---

## [1.1.03] - 2026-05-11

### Documentation (ドキュメント)
- `README.md` を空状態から包括的な記録ドキュメントへ整備:
  - プロジェクト概要・課題意識・解決アプローチ
  - 技術スタック表
  - パイプライン全体図（Stage 1/2/3 のフロー）
  - 各 Stage の役割と入出力 JSON 形式
  - **重要な設計判断**（sequence ベースアライメント、ハイブリッド OCR 等）
  - 業務ルール詳細（通常乗車・メーター超過・障害者割引・集計方針・整合性チェック）
  - セットアップ手順（ローカル / Streamlit Cloud）
  - プロジェクト構造・バージョニング規約

---

## [1.1.02] - 2026-05-11

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

## [1.1.01] - 2026-05-11

### Changed (表示調整)
- バージョン番号のフォントサイズを 11px → 14px に拡大、不透明度を 0.55 → 0.7 に調整
- タイトルブロック下の余白を `margin-bottom: 1.5rem` → `0.5rem` に削減
- 完成バーのフォント拡大:
  - `✓ 完成` ラベル: 14px → 18px
  - 件数・人数: 22px → 28px / weight 500 → 600
  - 件・人 単位: 11px → 14px

---

## [1.1.00] - 2026-05-11

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

## [1.0.00] - 2026-05-10

### 初回リリース
- Vision API + Claude のハイブリッド OCR パイプライン
- メーターレシート + 手書き日報の 2 画像から日報自動生成
- メーター超過（から回し）対応
- 集計（件数・人数・現収・未収・総収・消費税・税抜運収）
- 整合性チェック（メーター額 vs 出力テーブル）
- 乖離チェック（メーター件数 vs 日報件数）
- パーティクルローダー演出（CSS @keyframes のみ、JS 不使用）
