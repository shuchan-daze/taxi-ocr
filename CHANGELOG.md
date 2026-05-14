# Changelog

このプロジェクトのすべての変更履歴を記録します。

バージョニング: [Semantic Versioning 2.0](https://semver.org/lang/ja/) (`MAJOR.MINOR.PATCH`)

- **MAJOR**: 大きな変更・仕様変更（後方互換なし）
- **MINOR**: 部分的な機能追加・改善（後方互換あり）
- **PATCH**: バグ修正・小さな調整（**常に 2 桁ゼロパディング表記**、例: `1.1.04`）

---

## [1.21.00] - 2026-05-15

### Added (AI 自信シグナル — unknown pattern detector)

- AI が「この行は digit OCR の自信が無い / 既知ケースに当てはまらない / memo が見慣れない」と感じた行に `needs_review: true` を返せるようにした。プロンプトに strict な使用条件を記載 (過剰に true にしないよう「年に 1-2 行レベル」と明示)
- `NIPPOU_COLUMNS` に `needs_review` (boolean) を追加。プロンプト自動生成に乗る
- `interpret_raw_rows` / `_finalize_rides` / `build_report` で needs_review を伝播
- `render_detail_table`: mismatch / missing_nippou ではない行で needs_review が立ってる時のみ「⚠ AI 確信なし、紙を確認」を状態列に表示
- 既存の state (mismatch / missing_nippou) と排他: アラインメント警告がある行ではそちらを優先

### 設計判断

- 元の案 (`case='unknown'`) は v1.9.00 以降のアーキ (AI は case を返さない、Python が判定) と合わなかったので、**「自信シグナル」フラグ** に再設計
- 自動修正はせず、ユーザーが目視確認するヒントとして機能 ([[feedback_proceed_is_confirm]] と整合)
- 過剰検出を防ぐため、プロンプトで「滅多に true にしない」を強調

---

## [1.20.00] - 2026-05-15

### Added (テスト整備)

- **Phase 1: 純ロジックの単体テスト** (`tests/`, 78 ケース、API 不要、実行 0.04 秒)
  - `tests/conftest.py`: streamlit/anthropic/google.cloud.vision を mock して app.py を import 可能に (refactor 不要のアプローチ)
  - `tests/test_helpers.py` (21): `_coerce_int`, `_parse_hhmm`, `_is_discount_memo`, `_is_overage_marker`, `_parse_overage_marker`, `_cell_to_int`
  - `tests/test_interpret.py` (16): `_interpret_raw_row` の case 分類 (normal / split / overage / karamawashi / discount / empty / invalid)、`interpret_raw_rows`、`_split_rides`
  - `tests/test_finalize.py` (15): `_finalize_rows` (メーター正規化 + issues)、`_finalize_rides` (日報正規化 + issues、where 形式が 'index N' に統一されてることを保証)
  - `tests/test_alignment.py` (16): `_align_rides_to_meter` Pass 1 (金額一致 + 時刻 tie-break) と Pass 2 (時刻最近接、20分閾値)、`build_report` の各 case (perfect / missing_nippou / mismatch / split / overage / discount)、`_add_discount_hints` の数学的検出
  - `tests/test_validate.py` (10): `validate`, `aggregate_totals` (special/discount 除外ルール)、`validate_meter_sequence`
  - `pytest.ini`: 設定ファイル
  - `requirements-dev.txt`: pytest を dev 依存として分離 (本番 Streamlit Cloud には追加しない)
- **Phase 2: E2E テストフレームワーク** (`tests/test_e2e.py`)
  - 実 Claude API を呼んで画像 → 結果のパイプラインを検証
  - デフォルト skip (`RUN_E2E_TESTS=1` + `ANTHROPIC_API_KEY` で有効化)
  - `tests/fixtures/<case_name>/meter.jpg + nippou.jpg + meta.json` でケース追加
  - 期待値: `meter_total` / `row_count` / `state_counts` を JSON で記述、書かれた項目だけ検証
  - 運用想定: Shuchan が「間違えた日報」に遭遇したら 1 ケース fixture 化、累積で網羅性向上

### 設計判断

- ([[feedback_root_cause_first]]): テストはパッチではなく構造的安全網。今後の refactor が「壊れたら自動で気付ける」状態にする
- ([[feedback_iteration_friendly]]): Phase 2 は実機運用で出た実例を 1 件ずつ積む形で、最初から完璧を目指さない
- API mock 案を採用してロジック抽出 (taxi_logic.py) を回避 — 既存コードへの侵襲を最小化、refactor リスクゼロ

### 効果

- 構造変更時の回帰検出が自動化
- 過去 14 バージョンで散発的に出たバグ (例: meter_no 死蔵、Pass 2 時刻ベース) の再発を防ぐ網ができた

---

## [1.19.00] - 2026-05-15

### Added (新機能)

- **第 2 段 OCR (mismatch 行の AI 再確認)**: build_report で `state='mismatch'` 行が検出された時、AI に「メーター額が読める可能性は?」と再質問する Phase 4.5 を追加。AI が `"confirm"` を返したら mismatch を解消 (digit OCR ミスのリカバー)。`"keep"` なら mismatch のまま (紙が実際に違う数字)。mismatch 無し時はスキップでコストゼロ。プロンプトに「自信無いなら keep」を厳守させて誤訂正を防止
- **障割 (障害者割引) の数学的検出**: メーター額 = 原運賃 × 0.9 (1割引で印字)、障割額 = 原運賃 / 10 = メーター額 / 9 の関係を利用。mismatch 行で `paper_amount ≈ meter_amount / 9 (±10円)` を満たすケースを検出し、`💡 No.X の障割の可能性 (紙 ¥Y)` ヒントを表示。自動確定はせず、ユーザー判断に委ねる

### 設計の根拠

- ([[project_correction_philosophy]]): AI は既知情報で自動補完。Shuchan の要望「いちいち確認してたら日が暮れる」に従い、第 2 段 OCR で自律的に digit OCR ミスを救う
- ([[feedback_proceed_is_confirm]]): ただし AI が判定に迷う時は `keep` で訂正しない (ユーザーが見て判断する余地を残す)
- ([[project_paper_constraints.md]]): 障割の数学的検出は memo に「障割」キーワードが無くても数値で拾える、ユーザーが書き忘れた場合の安全網

### コスト影響

- mismatch 無し: 追加コスト 0
- mismatch あり: 1 回の追加 API 呼び出し (Claude Opus 4.5)。普通は 1-3 件なので $0.01-0.05 程度

---

## [1.18.00] - 2026-05-15

### Refactor

- 大規模クリーンアップ Phase 1+2+3+6 を実施 (2938 → 2380 行, -19%):
  - **Phase 1**: 冒頭 changelog (476 行) を CHANGELOG.md に移管
  - **Phase 2**: `except: pass` を `except (AttributeError, KeyError)` に絞り込み
  - **Phase 3**: 旧形式 (`_OLD_FORMAT_KEYS`) 後方互換削除 (現プロンプトでは到達不能)
  - **Phase 6 (本丸)**: `meter_no` フィールドの完全撤去
    - v1.14.00 以降「日報には No 列が無い」前提に変わったのに、ride dict には死蔵されていた
    - `_to_user_where` の `meter_no=` 正規表現マスクは典型的なパッチ → 撲滅
    - Stage B debug display の meter_no カラム削除
    - 残存 `meter_no` シンボルは alignment 内部の「メーター行の no」のみ、意味的に正しいので残置
- 副次: 死蔵コメント整理、在アプリの更新履歴を最新 5 バージョン + CHANGELOG.md ポインタに圧縮
- Phase 4/5 (HTML 統合、金額抽出統合) は精査の結果「やる方が複雑化する」「責務が違うものを統合は誤り」と判断、見送り

---

## [1.17.02] - 2026-05-14

- 開発者デバッグ UI をデフォルトで完全に隠す形に変更。v1.17.01 で「仕切り + 注意書き」を入れたが、それでも expander 自体は画面に出てたので一般ユーザーが触ってしまう可能性があった。
- 新方式: 「🛠️ 開発者メニューを開く」トグルボタンを設置。押すまで Stage 1/2/3 expander は一切レンダリングしない (st.stop で打ち切り)。再度押すと閉じる。ボタン自体も控えめなグレー色で「これは目立たないやつだよ」と暗示。

## [1.17.00] - 2026-05-14

- **完了導線の哲学転換**: 「直して再アップロード」強制ループからの脱却。これまでの UX は「🟠 🔴 がすべて消えるまで完成じゃない」と促す形だったが、紙の物理制約 (行追加できない / 修正ペン無し / 斜線で AI が混乱) を考えると AI 読み違いケースで詰む。
- 新方針: 警告は情報として残すが、ユーザーが「次へ進む」を選んだらアプリは結果を尊重する (= 暗黙の確定)。判定 UI (per-row OK ボタン等) は足さない (UI 増えると別バグの温床)。
- 表示文言: 旧「🔄 手書き日報を直したら、もう一度写真を撮って再アップロード / 🟠 🔴 がすべて消えたら完成です」→ 新「🟠 🔴 の行を確認してください / 紙に書き漏れ・誤記があれば修正して再アップ。AI の読み違いなら、このまま完了で OK です。」
- mismatch 状態列の文言を「紙の数字」から「AI 読み」に修正。旧「🟠 紙の数字 ¥1,090 → ¥1,200」→ 新「🟠 AI 読み ¥1,090 / メーター ¥1,200」。「紙」って何だよ感を解消、AI が読み取った値だと明示。

## [1.16.05] - 2026-05-14

- missing_nippou 行の memo 文言再調整。「何が問題か」を先に説明する語順に。
- 新: この金額の記入が漏れています。新しい行を作成して現収か未収の欄に記入してください。

## [1.16.04] - 2026-05-14

- missing_nippou 行の memo 文言修正。「入金確認」だと「客が払ったか確かめろ」と誤解される（実際は「日報に書け」が本質）。Siri 流の端的なアクション指示に差し替え。
- 旧: ⚠ 自動で「現収」と仮定。実際は未収かもしれないので入金確認してください
- 新: 日報に新しい行を追加して、現収 or 未収欄に記入してください

## [1.16.03] - 2026-05-14

- revert v1.16.02: input オーバーレイで iOS Chrome の白タブを止めようとしたが実機検証で効果なし。原因は JS 間接呼び出しではなく、WebKit-on-iOS Chrome の `<input type="file">` 自体の挙動 — ピッカーを about:blank コンテキストで描く設計なので、JS 経路を変えても変わらない。CSS で解決不能なので撤去。
- 代替: ユーザーには iPhone Safari の使用を案内する (Safari では出ない)。

## [1.16.02] - 2026-05-14

- iOS Chrome 白タブ (about:blank) 対策の再投入。`<input type="file">` を dropzone セクション全体に透明オーバーレイし、ユーザーのタップがネイティブ input に直接届くようにする。Streamlit の JS 経由クリック (input.click()) を回避するので iOS Chrome の popup blocker を通過する。
- 前回 (v1.15.02) で同じアプローチを試した時は section の幅が崩れたが、当時は block-container 自体も壊れていて副作用に見えただけ。v1.15.04 で block-container を `width: 100% !important` で固定したので前提が変わった。section にも `width: 100%` + `box-sizing: border-box` を明示して再発防止。

## [1.16.01] - 2026-05-14

- 検証ロジックのゴミ削除: _finalize_rides の `missing_meter_no` チェック撤去。v1.14.00 以降、日報には No 列が存在しないと判明 → プロンプトも「行番号は与えない」設計に変更済。なのに検証側だけ「meter_no が None なら issue」と旧前提のまま動いていた。結果、全 ride で false positive な「日報の左端 No が読めず」 issue が発生。UI 側で v1.15.01 で「画面に🟠🔴が無ければパネル非表示」にして見えなくしてたが、根本のゴミは残ったままだった。発生源と labels 辞書からキーごと撤去。

## [1.16.00] - 2026-05-14

- **アライメント大改善**: build_report の Pass 2 (金額不一致 ride の救済) を「上から順番割当」から「時刻が近いメーター行への自動推定」に切替。閾値 20 分。
- これまで: 紙が 1 行書き漏れ (例: メーター No.11 ¥900) すると、後続の紙の行が全部ずれて、メーター No.11 に「紙の ¥1,090 AMEX」という機械的な嘘の mismatch が表示されてた。AMEX は実は No.13 用なのに。
- 今後: 紙の 18:09 AMEX (1090) は時刻最近接のメーター No.13 (18:08 ¥1,200) に当たって「¥1,090 → ¥1,200 の mismatch、AMEX memo は維持」と正しく表示。書き漏れた No.11 (17:14 ¥900) は誰も来ないので 🔴 missing_nippou で「¥900 を書く」と素直に教える。
- 「AI なら自動で直しつつ、ここを書けと教えてくれ」というユーザー要求への構造的対応。

## [1.15.04] - 2026-05-14

- レイアウトバグ修正: iOS Chrome で画面幅の 60〜70% しか使えず、右側に 24% も空白が出ていた問題を修正。原因は .block-container の horizontal padding を明示していなかったため、Streamlit 1.50 のデフォルト (端末/ブラウザによって非対称な計算) が残っていた。padding を `1.5rem 1rem 2rem 1rem` で全方向明示、`margin-left/right: auto` + `width: 100%` + `box-sizing: border-box` で確実にセンタリング & 全幅活用。!important で内部スタイル上書きも保証。

## [1.15.03] - 2026-05-14

- revert: v1.15.02 で試した「<input type="file"> をセクション全体に絶対配置で透明オーバーレイ」する iOS Chrome popup blocker 回避策を撤回。Streamlit の dropzone セクションは内部 flex で子要素を基準にサイズを決めているらしく、input を absolute に逃がすとセクションの幅が縮む副作用が出たため。
- iOS Chrome の初回 about:blank は「下スワイプで消せば以降は出ない」ワンタイム挙動だと判明したので、UX 影響度を考えて一旦受容する。

## [1.15.02] - 2026-05-14

- UX バグ修正（矛盾警告の撲滅）: 結果画面上部の「メーターレシートと日報の内容が大きく乖離しています」が、下の「✅ 読み取り完了」と同時に出る矛盾を解消。
- 原因: 乖離判定が raw rides の meter_no 充足率で測っていたため、AI が左端 No を読めない (missing_meter_no) と amount/time マッチで揃ってても「100% 乖離」と誤検出していた。
- 修正: 乖離判定を build_report 後の最終テーブルベースに統一。state='missing_nippou' の行数・金額で測るので、上下で同じ事実を見るように。

## [1.15.01] - 2026-05-14

- UX バグ修正: 結果画面に「🟠 🔴 がすべて消えたら完成です」の修正導線が常時出ていた問題を修正。表に 🟠 (mismatch) / 🔴 (missing_nippou) が無い かつ合計も合っている時は「✅ 読み取り完了 — このまま日報として使えます」を出す。
- UX バグ修正: 「⚠ 読み取り時に検出された問題」パネルが内部用語まみれだった (meter_no / build_report / index N) のを全部ユーザー言語に書き換え。さらに、画面上に 🟠 🔴 が出ていない時はこのパネル自体を表示しない（後段で自動補完済の AI ゆらぎを「直せ」と見せても混乱するだけ）。

## [1.15.00] - 2026-05-14

- **constraint-aware OCR**: 日報 OCR (Opus 4.5) にメーターデータを参考情報として渡す。目的: 手書きの曖昧な digit (8 vs 5、1 vs 7 等) を AI が disambiguate する時、メーター値と整合する候補を選べるようにする。auto-correct ではない: 紙に明確に書かれた数字はそのまま読む。メーター情報は「曖昧な手書きを推測する補助材料」としてのみ使う、というプロンプト指示を厳守。
- パイプライン構成変更: 旧 Phase 2 で clarity / parse_meter / classify_nippou を 3 並列 → 新 Phase 2 で clarity || parse_meter を並列、Phase 3 で classify_nippou を meter_data を文脈に渡して実行 (sequential)。並列度低下で +3〜5 秒の体感遅延、引き換えに OCR 精度向上。
- split mismatch 等での post-processing 補正は導入しない (AI 側で digit を正しく読めることを期待)。建前通り「メーター = 金額の絶対」「AI = 列位置の絶対」を維持しつつ、AI の OCR ステップを賢くする。

## [1.14.00] - 2026-05-14

- **アラインメント大改修 + 列構造のデータ宣言化**: 現実の日報レイアウト確認の結果、最左端は 時間 列で「No 列」は存在しないことが判明。v1.10.00 の「AI に最左端 No 列を読ませる」設計は前提が崩壊しており、AI は仕方なく 人数 列を meter_no として返していた → アラインメント崩壊。
- **NIPPOU_COLUMNS データ宣言を導入**: 列を 1 箇所のリストで定義し、プロンプトは `_build_nippou_prompt(NIPPOU_COLUMNS)` で自動生成。新しい列を増やす場合は COLUMNS に 1 行追加で済む。
- **alignment を amount-first に書き換え**: Pass 1: 金額完全一致で割当 (同金額複数なら時刻が近い ride を tie-break)。Pass 2: 残り meter ←→ 残り ride を出現順に強制割当 (mismatch 表示)。meter_no 概念を使わない。
- Stage A デバッグ表示の "meter_no" カラムを "順" (上から N 番目) に変更。

## [1.13.01] - 2026-05-14

- v1.13.00 で normal mismatch 行を「AI 読み取り値」表示にしたが、ユーザー指摘で方針を見直し: **メーターは絶対的に正しい（印字）から、テーブルの数値はメーター値 (正解) を表示する**。集計もメーター値で確定。アプリの役割は「紙のミスを指摘する」であって「数字を訂正する」ではない。
- 状態列の mismatch を「🟠 紙の数字 ¥X → ¥Y」形式に変更。AI が読んだ紙の違う値 ¥X とメーター正解 ¥Y を並べる → ユーザーは紙のどこを直すか一目で分かる。
- mismatch セルのピンク色塗りを撤去 (テーブルが正解値を表示してるので、セル色付けは「値がおかしい」誤解を招く)。行全体のピンク背景は維持。
- build_report に nippou_amount フィールド追加。

## [1.13.00] - 2026-05-14

- **訂正 UX を「視覚情報だけで完結」に再構築**: ユーザー本人「タップしたらすべてやり直しになっちゃう。ポップアップで直そう言われても何が間違ってるかわからない。視覚情報で導いてほしい」。ミッション: 「手書き日報を完成させるサジェスト」、デジタル編集はしない。
- detail-table のセルタップ機構を全撤去 (?edit=N アンカー / ダイアログ / edit_row_target / クエリパラメータハンドラ全部削除)。
- 状態列を具体化: 'mismatch' → 「🟠 メーター ¥1,600」(正解値が直接見える)。'missing_nippou' → 「🔴 未記載・¥1,000 を書く」(やることが直接見える)。'ok' → 空 (ノイズなし)。
- normal mismatch の gen/mi 表示を AI 読み取り値に変更。
- 問題サマリ expander の重複を削除。再アップ導線をテーブル下に金色枠で目立たせる。

## [1.12.01] - 2026-05-14

- ローダーの 2 つの UX バグを構造修正:
- **数字が戻る問題**: show_loader が prev > pct (新規パイプライン開始等で前回 100 が残った状態で新 3% 来る) を「リセット → 1, 2, 3 をアニメ」として描画していたため、画面上 100→1→2→3 で「戻った」と見えていた。修正: prev >= pct なら即時ジャンプ (アニメしない)。
- **途中で止まる問題**: _poll_until_done の creep が creep_target に追いついた後、次の future 完了まで完全停止していた。修正: drift モード追加。cur >= creep_target でも end-1 までは 250ms に 1 ずつ drift し続ける。

## [1.12.00] - 2026-05-14

- **アプリのミッションを再定義**: 「手書き日報を完成させるサジェストツール」。iterative ループ: 写真 → サジェスト → 紙を直す → 再アップ → 確認 → ...完成。
- 上記に伴いデジタル編集機構を全撤去: session_state.row_overrides / apply_overrides() / state='edited' 削除。ダイアログを read-only サジェスト表示に書き換え（編集フォーム廃止）。
- 結果: アプリが「紙を直す→再アップ」ループの advisor に純化、デジタルが「直されたフリ」をすることがなくなった。

## [1.11.00] - 2026-05-14

- **訂正 UX を「紙の日報を直す助言者」モデルに再構築**: これまでの訂正 UI は「デジタル出力を編集する」モードで、テーブル外に別パネルを設置して same item を 2 箇所に重複させていた。さらに「ユーザーが直すべきは紙の日報そのもの」というアプリの本質的価値を見失っていた。
- 訂正専用セクションを撤去。detail-table の編集可能セルを <a href="?edit=N"> で全面タップ可能に。
- ダイアログを「紙のここに何を書くか」フレームに書き換え: タイトル「📝 紙の日報を直そう」。

## [1.10.05] - 2026-05-14

- ローダーが API 待ちで止まって見える件を UX 修正: _poll_until_done に creep ロジック導入。50ms に 1 unit 進め、実 target より CREEP_LEAD だけ先行表示する。
- 表示 pct は厳密な進捗ではなく「動いてる感」を優先した演出値 (UX 系数値の位置づけ)。

## [1.10.04] - 2026-05-14

- ローダーの「1 ずつ滑らかに動く」を確実に実現するため、Python 側で fine-grained pct を 20ms 刻みで送る方式に切替。
- メーター/日報の件数乖離アラート文を「写真が正しいか…」から「手書きの日報に書かれている内容が正しいか…」に変更。

## [1.10.03] - 2026-05-14

- v1.10.02 のローダーが 3% で止まる症状を構造修正: animation を CSS transition に置き換え。transition は --to-pct の値変更で毎回自動発火するので、Streamlit の更新方式に依存しない。

## [1.10.02] - 2026-05-14

- ローダー UI 改善: % 記号を数字より小さく。数値を CSS counter + @property で前回値から滑らかにアニメ。

## [1.10.01] - 2026-05-14

- 「+N」マーカーを構造的に overage として解釈（v1.5.03 までの挙動を完全復元）: _interpret_raw_row で gen_cell が "+100" 形式なら type='overage' を返す。
- **CSS 修正**: 訂正セクション / st.dialog の文字が黒で暗背景に埋もれていた件。原因は `h1,h2,...,p,div,label {color: #010519}` が全ページに適用されていたこと。`.upload-card, .result-card` の子孫だけにスコープ限定。

## [1.10.00] - 2026-05-14

- **構造修正: AI の meter_no を一次アラインメント信号に戻す**。v1.5.03 まで AI は meter_no を直接出力していた（精度高）。v1.9.x で「no = 日報上から連番」に変えて、Python の金額一致だけでアラインしたら、似た金額が並ぶケースで「+100 が 1 行下にズレる」などの破綻が頻発。
- パッチで補正する案も検討したが、複雑化して詰むので根本から修正: NIPPOU_PROMPT で AI に meter_no を返させる。_align_rides_to_meter で 3 段階アライメント。v1.9.02 の「メーター超過セーフティネット」パッチを撤回。
- **validate 失敗時の UI 強化**: 合計タイルを赤背景 + ダーク部グレーアウトに切替。「OK っぽく見える成功状態」を絶対に表示しない。

## [1.9.02] - 2026-05-14

- 重大バグ修正: 結果表示の問題サマリ expander 内で変数 `rows` を HTML 文字列リストで上書きしていたため、後段の訂正リスト ( `rows` を辞書として参照 ) で AttributeError → Stage 2 デバッグ expander と「新しい日報を作成」ボタンが描画されない症状を解消。
- アライメントにメーター超過セーフティネット追加 (※ v1.10.00 で構造修正に置き換え)。

## [1.9.01] - 2026-05-14

- メーター超過自腹補填パターン（現収=+100, 未収=1500）の取りこぼし対策。NIPPOU_PROMPT を強化、「+100」のような追加表記を絶対に省略しないよう厳命。interpret_raw_rows に後方互換層追加。Stage 2 debug expander に Stage A (AI 抽出 raw) と Stage B (Python 解釈後) の二段表示を追加。

## [1.9.00] - 2026-05-14

- **アーキテクチャ大改革: AI と Python の役割を完全分離**
- Stage A (AI): 日報のセルを純粋抽出のみ。raw_rows = {no, time, gen_cell, mi_cell, memo, strikethrough}。case や kind の判定は一切させない。「+100」等は文字列のまま記録。
- Stage B (Python): interpret_raw_rows() が特殊ケースを 1 個ずつ別関数で判定。各ケースが独立関数 → 互いに干渉しない、テスト容易、debug 容易。

## [1.8.00] - 2026-05-14

- ユーザー訂正 UI を追加（コア機能、慎重実装）: AI が自信を持てなかった行 (missing_nippou / mismatch) と訂正済み行 (edited) を結果テーブルの下に「✎ 訂正」セクションとして並べる。
- 哲学: AI は 80% を仕上げる、ユーザーが 20% を 30秒で完成させる。OCR 再実行不要。

## [1.7.05] - 2026-05-14

- NIPPOU_PROMPT の判定順序を再構成。「分割払い」判定を最優先(STEP 2)に上げ、通常行/kind 判定より先に「現収欄と未収欄の両方を見る」を強制。
- 「から回し」と「自腹補填」の見分け方を明示。

## [1.7.04] - 2026-05-14

- アライメントを保守化: missing_nippou 判定は金額完全一致 (signal=2) を要求するように変更。
- NIPPOU_PROMPT の split 判定を強化: 「両欄に数字があれば必ず split」と明示。

## [1.7.03] - 2026-05-14

- UI 微調整: ファイルアップローダーの英語デフォルト文を隠し、カスタムテキストを短く。mismatch 行で値が入ってる側だけ薄赤に塗るよう変更。

## [1.7.02] - 2026-05-14

- 「人間が間違える前提、AI が黙って働く答えを作る」原則を build_report に実装。missing_nippou 行は kind 不明だが、メーター額は既知なので「現収」と仮定して gen 列に充填。合計が成立する状態を作る。
- aggregate_totals: missing_nippou を件数・人数に含める（1 件 1 人と仮定）。

## [1.7.01] - 2026-05-14

- アラインメントを time + amount のダブルシグナル化: NIPPOU_PROMPT に "time" (降車時刻) フィールドを追加。_ride_meter_signal_match で「金額一致 / 時刻 ±5分以内」を強い指標として評価。
- missing_nippou 行の見た目を「真っ赤背景 + 白抜き文字」に刷新。

## [1.7.00] - 2026-05-14

- build_report を v2 に再構築: メーター明細書をマスター（行数・順序・金額の絶対真実）として扱い、必ず N 行（=メーター行数）の出力を作るように変更。
- 新アルゴリズム _align_rides_to_meter: nippou_amount をヒントに greedy + 先読み（3 行先まで）で対応 ride を探す。対応が無いメーター行は state='missing_nippou'。
- CSS: missing_nippou 行は黄色ハイライト + 「日報に未記載」表記でテーブル内に明示。

## [1.6.00] - 2026-05-14

- Stage1/2 出力の堅牢化: AI 出力の欠損・null・型不正を normalize 段で吸収。_coerce_int ヘルパー / _finalize_rows と _finalize_rides の正規化処理を追加。
- 検出した問題を issues 配列として回収し、UI 上に専用パネル「⚠ 読み取り時に検出された問題」で一覧表示。

---

## [1.5.03] - 2026-05-12

### Added (新機能)
- **分割払い（現金 + チケット併用等）対応**: `case="split"` を新設
  - `NIPPOU_PROMPT` に 【分割払い行】 セクション追加
  - `build_report` に `case='split'` 分岐追加: `gen_amount` → 現収列、`mi_amount` → 未収列に両計上
  - `gen_amount + mi_amount` がメーター額と一致しなければ `state='mismatch'`
- Stage 2 デバッグ表示も split 対応（金額列で `現3000+未2400` のように表示）

### 後方互換
既存の normal / overage / discount ロジックは無変更。split 行を含まない日報は v1.5.02 と完全同等の出力。

---

## [1.5.02] - 2026-05-12

### Performance (体感速度)
- `.streamlit/config.toml` でテーマを `base="dark"` + `backgroundColor="#010519"` に設定。Streamlit のロード画面の段階から最終形と同じ濃紺背景になり、起動直後の白フラッシュ (~1〜2 秒) を撲滅。実時間は変わらないが「スパッと開いた」体感に。
- `page_icon='🚖'` を `st.set_page_config` に追加。ブラウザタブの瞬間表示で識別性向上。

---

## [1.5.01] - 2026-05-12

### Changed (コスト最適化)
- `_ocr_vision_claude` の JSON 構造化を Claude Opus 4.5 → Claude Sonnet 4.6 に変更。Vision API が読み取った clean な印字テキストを JSON 化するだけのタスクで、画像認識ではないため精度劣化なし。実測 20 行 receipt で Opus と完全同等出力、コスト 1/5。
- JSON 不正時は `_ocr_claude` (Opus 画像直叩き) にフォールバックする安全網は維持。
- 100 枚/月で約 ¥480/人 削減。

---

## [1.5.00] - 2026-05-12

### Removed (撤去)
- v1.4 の A/B 検証用コードと Gemini 経路を全撤去（本番構成確定済のため）。対象: `_ai_call_text` / `get_gemini_model` / `_ocr_gemini` / `_classify_nippou_gemini` / `OCR_PROVIDERS` / `NIPPOU_PROVIDERS` / `_is_nippou_compare_mode` / `_nippou_compare` UI / `compare_nippou.py` / `requirements.txt` の `google-generativeai`。
- `identify_image` / `check_clarity` を Claude Opus 直叩きに変更（Gemini 画像呼び出しが 10〜30s と遅くフリーズの主因だったため）。

### Performance
- `run_pipeline` を 3 並列化: `identify×2` → `clarity + parse_meter + classify_nippou`。
- `_poll_until_done` で全フェーズをポーリング型に統一し、14% / 31% / 85% で進捗が止まって見える問題を解消。

### コスト影響
1 人/100 枚/月 で約 ¥4,460 → ¥3,780（15% 削減、v1.5.01 と合わせて）。

---

## [1.4.01] - 2026-05-11

### Decision (技術検証結果と方針確定)
今日 1 日かけて 4 つの代替案を `compare_nippou.py`（アプリ独立の純粋検証スクリプト）で
8 枚の実画像に対して検証した結果、**「精度妥協ナシ」の縛りで Claude Opus 4.5 を置換
できるモデル/手法は存在しない**ことが立証された。

### 検証結果サマリ（基準: Claude Opus 4.5）

| 代替案 | 結果 | 不採用理由 |
|---|---|---|
| Gemini 2.5 Flash | 0/8 完全一致 | 致命的誤読（金額・人数・現収/未収・行数）。商用 NG |
| Claude Opus 4.7 | 0/8 完全一致 | 出力が微妙にズレる、人間検証なしでは精度差不明 |
| Claude Sonnet 4.6 | 0/8 完全一致 | Opus 4.5 より誤差大、明確に精度劣化 |
| Prompt Caching (system 化) | 0/8 完全一致 | system prompt 化で挙動変化（memo の現金省略等）。節約 $2/人で小 |

### 本番推奨構成 (secrets.toml)

```toml
[ocr]
provider = "vision_claude"   # Vision API + Claude 構造化 (既定、精度確認済み)

[nippou]
provider = "claude"          # Claude Opus 4.5 (既定、精度確認済み)
# compare_mode は削除 or false に
```

### コスト試算 (本番構成・1 人 100 枚/月の想定)
- 1 枚あたり: 約 $0.17 (identify×2 + clarity = Gemini 安、meter = Vision+Claude、nippou = Opus)
- 1 人/月: 約 $17 (≒ ¥2,550)

### 価格設計（コミット）

| プラン | 月額 | 含む処理枚数 | 想定原価 | 粗利 |
|---|---|---|---|---|
| 無料 | ¥0 | 計算機能のみ（売上・稼働時間・残時間） | ¥0 | — |
| Light | ¥3,000 | 月 10 枚 + 計算 | ¥255 | 92% |
| Standard | ¥5,000 | 月 20 枚 + 計算 | ¥510 | 90% |
| Heavy | ¥9,000 | 月 40 枚 + 計算 | ¥1,020 | 89% |
| 超過分 | ¥300/枚 | — | ¥26/枚 | 91% |

### Why (なぜ価格設計に倒すか)
- 「楽したい」のは特定層（時間価値を理解するドライバー）。全員に売る必要はない
- 計算機能のみの**無料層**でユーザーを獲得 → OCR は本気で楽したい人だけが課金
- 粗利 89%以上で運用余力確保（サーバ代・サポート・改善投資）
- ¥500 設計は実現困難（原価が物理的に到達不可）と認め、現実的な価格に切替

### Next (次にやること)
1. 無料層の計算機能を設計・実装（売上日計・稼働時間管理・残稼働可能時間・月集計）
2. 課金機構の組込み（Stripe 等、月額 + 従量）
3. 余力で人間検証ベンチマーク（Opus 4.5 vs Opus 4.7 真の精度差を測る）

---

## [1.4.00] - 2026-05-11

### Added (追加)
- **日報分類 (classify_nippou) のプロバイダ抽象化**
  - `NIPPOU_PROVIDERS` レジストリで `_classify_nippou_claude` / `_classify_nippou_gemini` を切替
  - `secrets.toml [nippou] provider = "claude" | "gemini"` で選択（既定 `"claude"`、後方互換）
  - 失敗時は `_classify_nippou_claude` に最終フォールバック
- **A/B 比較モード**: `secrets.toml [nippou] compare_mode = true`
  - 両プロバイダを `ThreadPoolExecutor` で並列実行
  - 結果と失敗理由を `st.session_state['_nippou_compare']` に保存
  - 結果画面に「🧪 Stage 2 A/B: 日報プロバイダ比較」expander を表示（ride 数メトリクス + 両者の JSON 並列表示）
  - 検証完了後は `compare_mode` を外し `provider = "gemini"` に切替する想定

### Changed (変更)
- **identify_image / check_clarity を Gemini 優先化**
  - `_ai_call_text(prompt, images, claude_client, max_tokens)` ヘルパーを新設
  - Gemini Flash で実行、未設定/失敗時のみ Claude Opus にフォールバック
  - これら 2 箇所だけで 1 枚あたり推定 ~$0.11 削減

### Performance / Cost
- 想定コスト試算（1 人 100 枚 × 1000 人 = 100,000 枚/月）:
  - **v1.3 まで**: 1 枚 ~$0.29 / 1 人 ~$29 / 月総額 ~$29,000
  - **v1.4 (本番 gemini 化後)**: 1 枚 ~$0.002 / 1 人 ~$0.20 / 月総額 ~$200
  - 約 **150 倍のコスト削減**（A/B で精度同等を確認後）

### Why (なぜ)
- 1 人あたり ¥500（≒ $3.3）の料金設計で 1000 人 / 月 100 枚を捌くには、1 枚 ≤ $0.01 が必須
- 日報は手書き + 業務ルール（から回し・障割・現収未収判定）が絡むため精度劣化リスクが大きい
  → A/B 比較ツールで実データ検証後に切替する設計に
- 他 4 箇所（identify×2 / clarity / meter）は判定が単純なため即 Gemini 化（リスク低）

### How to validate (使い方)
1. `secrets.toml` に `[nippou]\nprovider = "claude"\ncompare_mode = true` を追記
2. 過去テスト済みの日報を数枚アップ → 結果画面の 🧪 expander で claude/gemini を比較
3. ride 数・各フィールドが完全一致するなら `provider = "gemini"` に切替、`compare_mode` 削除
4. 一致しない箇所があれば claude 維持、または精度差をログ化して再評価

---

## [1.3.01] - 2026-05-11

### Performance (速度改善)
- **アップロード後の体感速度を大幅改善**
  - `st.file_uploader` 受信直後に `normalize_upload_bytes()` で正規化:
    - EXIF orientation 適用（事前に画素回転を済ませる）
    - `thumbnail((3000, 3000))` で長辺 3000px に縮小
    - JPEG quality 92 で再エンコード
  - 元 5〜8MB のスマホ写真 → 0.5〜1MB に縮小
  - 効果:
    - `session_state` メモリ削減（Streamlit Cloud 上のメモリ圧迫を緩和）
    - プレビュー描画の高速化
    - HEIC ファイル: 受信時に一度だけデコード → 以降は軽い JPEG として扱える（rerun のたびのデコードを排除）
- **API コスト・OCR 精度は不変**: 元々 `to_b64()` で 3000px 上限に縮小して API 送信していたため、Gemini / Vision / Claude への入力サイズは変わらない

### Why (なぜ)
- アップロード後の処理（プレビュー表示・rerun・OCR 起動）が体感で遅い問題が報告された
- 真因は「フルサイズの元画像（5〜8MB）が session_state に保持され、再描画ごとに再エンコード・再送信されていた」こと
- 受信時に 1 回だけ正規化することで、以降の処理全体が軽くなる

---

## [1.3.00] - 2026-05-11

### Added (追加)
- **OCR プロバイダ抽象化** — 時代ごとの最適 OCR への乗り換えを容易にする差し替え機構
  - `parse_meter()` をディスパッチャ化し、`OCR_PROVIDERS` レジストリ経由で実装を選択
  - 既存: `_ocr_vision_claude`（Google Vision + Claude ハイブリッド、従来の既定挙動）
  - 既存: `_ocr_claude`（Claude 単独、外部依存ゼロの最終フォールバック）
  - **新規**: `_ocr_gemini`（Gemini に画像を直接渡し JSON 構造化）
- **`secrets.toml` で切替可能**: `[ocr] provider = "vision_claude" | "gemini" | "claude"`
  - 既定は `"vision_claude"`（後方互換）。未知の値は既定にフォールバック。
  - Gemini モデル名は `[ocr] gemini_model` で上書き可（既定 `gemini-2.0-flash`）。
- **`google-generativeai`** を `requirements.txt` に追加（インポートは遅延・未使用なら不要）

### Changed (変更)
- `_ocr_claude` の戻り値に `total` キーを追加し、全プロバイダで `{rows, total}` 形式に統一
- 設定プロバイダが失敗した場合、自動で `_ocr_claude` に最終フォールバック（従来は Vision 失敗時のみ）

### Why (なぜ)
- Cloud Vision の単価がコスト課題。Gemini は同等性能で 5〜20 倍安いケースがあり乗り換え動機が大きい
- ただし将来の値上げ・無料枠縮小・円安リスクに備え、**プロバイダ差し替えを 1 行設定で完結**できる構造に
- 既存呼び出し側 (`app.py:930` 周辺) は無変更で済むよう、戻り値 shape を維持

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
