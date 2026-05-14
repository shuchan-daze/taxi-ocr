# バージョニング規約: SemVer 2.0 (MAJOR.MINOR.PATCH)
#   MAJOR: 大きな変更・仕様変更（後方互換なし）
#   MINOR: 部分的な機能追加・改善（後方互換あり）
#   PATCH: バグ修正・小さな調整（常に 2 桁ゼロパディング表記、例: 1.1.04）
#
# v1.17.02 - 2026-05-14
#   - 開発者デバッグ UI をデフォルトで完全に隠す形に変更。
#     v1.17.01 で「仕切り + 注意書き」を入れたが、それでも expander 自体は
#     画面に出てたので一般ユーザーが触ってしまう可能性があった。
#     新方式: 「🛠️ 開発者メニューを開く」トグルボタンを設置。押すまで Stage 1/2/3
#     expander は一切レンダリングしない (st.stop で打ち切り)。再度押すと閉じる。
#     ボタン自体も控えめなグレー色で「これは目立たないやつだよ」と暗示。
# v1.17.00 - 2026-05-14
#   - **完了導線の哲学転換**: 「直して再アップロード」強制ループからの脱却。
#     これまでの UX は「🟠 🔴 がすべて消えるまで完成じゃない」と促す形だったが、
#     紙の物理制約 (行追加できない / 修正ペン無し / 斜線で AI が混乱) を考えると
#     AI 読み違いケースで詰む。
#     新方針: 警告は情報として残すが、ユーザーが「次へ進む」を選んだら
#     アプリは結果を尊重する (= 暗黙の確定)。判定 UI (per-row OK ボタン等) は
#     足さない (UI 増えると別バグの温床)。
#     表示文言:
#       旧: 🔄 手書き日報を直したら、もう一度写真を撮って再アップロード
#           🟠 🔴 がすべて消えたら完成です
#       新: 🟠 🔴 の行を確認してください
#           紙に書き漏れ・誤記があれば修正して再アップ。
#           AI の読み違いなら、このまま完了で OK です。
#   - mismatch 状態列の文言を「紙の数字」から「AI 読み」に修正。
#     旧: 🟠 紙の数字 ¥1,090 → ¥1,200
#     新: 🟠 AI 読み ¥1,090 / メーター ¥1,200
#     「紙」って何だよ感を解消、AI が読み取った値だと明示。
# v1.16.05 - 2026-05-14
#   - missing_nippou 行の memo 文言再調整。「何が問題か」を先に説明する語順に。
#     新: この金額の記入が漏れています。新しい行を作成して現収か未収の欄に記入してください。
# v1.16.04 - 2026-05-14
#   - missing_nippou 行の memo 文言修正。「入金確認」だと「客が払ったか確かめろ」
#     と誤解される（実際は「日報に書け」が本質）。Siri 流の端的なアクション指示に
#     差し替え:
#     旧: ⚠ 自動で「現収」と仮定。実際は未収かもしれないので入金確認してください
#     新: 日報に新しい行を追加して、現収 or 未収欄に記入してください
# v1.16.03 - 2026-05-14
#   - revert v1.16.02: input オーバーレイで iOS Chrome の白タブを止めようとしたが
#     実機検証で効果なし。原因は JS 間接呼び出しではなく、WebKit-on-iOS Chrome の
#     `<input type="file">` 自体の挙動 — ピッカーを about:blank コンテキストで
#     描く設計なので、JS 経路を変えても変わらない。CSS で解決不能なので撤去。
#     代替: ユーザーには iPhone Safari の使用を案内する (Safari では出ない)。
# v1.16.02 - 2026-05-14
#   - iOS Chrome 白タブ (about:blank) 対策の再投入。
#     `<input type="file">` を dropzone セクション全体に透明オーバーレイし、
#     ユーザーのタップがネイティブ input に直接届くようにする。Streamlit の
#     JS 経由クリック (input.click()) を回避するので iOS Chrome の popup blocker
#     を通過する。
#     前回 (v1.15.02) で同じアプローチを試した時は section の幅が崩れたが、
#     当時は block-container 自体も壊れていて副作用に見えただけ。v1.15.04 で
#     block-container を `width: 100% !important` で固定したので前提が変わった。
#     section にも `width: 100%` + `box-sizing: border-box` を明示して
#     再発防止。崩れたらまた剥がす。
# v1.16.01 - 2026-05-14
#   - 検証ロジックのゴミ削除: _finalize_rides の `missing_meter_no` チェック撤去。
#     v1.14.00 以降、日報には No 列が存在しないと判明 → プロンプトも「行番号は与え
#     ない」設計に変更済。なのに検証側だけ「meter_no が None なら issue」と旧前提
#     のまま動いていた。結果、全 ride で false positive な「日報の左端 No が読めず」
#     issue が発生。UI 側で v1.15.01 で「画面に🟠🔴が無ければパネル非表示」にして
#     見えなくしてたが、根本のゴミは残ったままだった。発生源と labels 辞書から
#     キーごと撤去。
# v1.16.00 - 2026-05-14
#   - **アライメント大改善**: build_report の Pass 2 (金額不一致 ride の救済) を
#     「上から順番割当」から「時刻が近いメーター行への自動推定」に切替。閾値 20 分。
#     - これまで: 紙が 1 行書き漏れ (例: メーター No.11 ¥900) すると、後続の紙の
#       行が全部ずれて、メーター No.11 に「紙の ¥1,090 AMEX」という機械的な嘘の
#       mismatch が表示されてた。AMEX は実は No.13 用なのに。
#     - 今後: 紙の 18:09 AMEX (1090) は時刻最近接のメーター No.13 (18:08 ¥1,200)
#       に当たって「¥1,090 → ¥1,200 の mismatch、AMEX memo は維持」と正しく表示。
#       書き漏れた No.11 (17:14 ¥900) は誰も来ないので 🔴 missing_nippou で
#       「¥900 を書く」と素直に教える。
#     - 「AI なら自動で直しつつ、ここを書けと教えてくれ」というユーザー要求への構造的対応。
# v1.15.04 - 2026-05-14
#   - レイアウトバグ修正: iOS Chrome で画面幅の 60〜70% しか使えず、右側に 24% も
#     空白が出ていた問題を修正。原因は .block-container の horizontal padding を
#     明示していなかったため、Streamlit 1.50 のデフォルト (端末/ブラウザによって
#     非対称な計算) が残っていた。padding を `1.5rem 1rem 2rem 1rem` で全方向
#     明示、`margin-left/right: auto` + `width: 100%` + `box-sizing: border-box`
#     で確実にセンタリング & 全幅活用。!important で内部スタイル上書きも保証。
# v1.15.03 - 2026-05-14
#   - revert: v1.15.02 で試した「<input type="file"> をセクション全体に絶対配置で
#     透明オーバーレイ」する iOS Chrome popup blocker 回避策を撤回。Streamlit の
#     dropzone セクションは内部 flex で子要素を基準にサイズを決めているらしく、
#     input を absolute に逃がすとセクションの幅が縮む副作用が出たため。
#     iOS Chrome の初回 about:blank は「下スワイプで消せば以降は出ない」ワンタイム
#     挙動だと判明したので、UX 影響度を考えて一旦受容する。
# v1.15.02 - 2026-05-14
#   - UX バグ修正（矛盾警告の撲滅）: 結果画面上部の「メーターレシートと日報の内容が
#     大きく乖離しています」が、下の「✅ 読み取り完了」と同時に出る矛盾を解消。
#     原因: 乖離判定が raw rides の meter_no 充足率で測っていたため、AI が左端 No を
#     読めない (missing_meter_no) と amount/time マッチで揃ってても「100% 乖離」と
#     誤検出していた。
#     修正: 乖離判定を build_report 後の最終テーブルベースに統一。
#     state='missing_nippou' の行数・金額で測るので、上下で同じ事実を見るように。
# v1.15.01 - 2026-05-14
#   - UX バグ修正: 結果画面に「🟠 🔴 がすべて消えたら完成です」の修正導線が常時
#     出ていた問題を修正。表に 🟠 (mismatch) / 🔴 (missing_nippou) が無い かつ
#     合計も合っている時は「✅ 読み取り完了 — このまま日報として使えます」を出す。
#   - UX バグ修正: 「⚠ 読み取り時に検出された問題」パネルが内部用語まみれだった
#     (meter_no / build_report / index N) のを全部ユーザー言語に書き換え。さらに、
#     画面上に 🟠 🔴 が出ていない時はこのパネル自体を表示しない（後段で自動補完
#     済の AI ゆらぎを「直せ」と見せても混乱するだけ）。
# v1.15.00 - 2026-05-14
#   - **constraint-aware OCR**: 日報 OCR (Opus 4.5) にメーターデータを参考情報として渡す。
#     - 目的: 手書きの曖昧な digit (8 vs 5、1 vs 7 等) を AI が disambiguate する時、
#       メーター値と整合する候補を選べるようにする。
#     - auto-correct ではない: 紙に明確に書かれた数字はそのまま読む。メーター情報は
#       「曖昧な手書きを推測する補助材料」としてのみ使う、というプロンプト指示を厳守。
#     - 例: AI が paper の 800 を 500 と誤読しがちなケース → メーター 1,800 と整合する
#       800 を選んでくれるようになる。
#   - パイプライン構成変更:
#     - 旧: Phase 2 で clarity / parse_meter / classify_nippou を 3 並列
#     - 新: Phase 2 で clarity || parse_meter を並列、Phase 3 で classify_nippou を
#           meter_data を文脈に渡して実行 (sequential)
#     - 並列度低下で +3〜5 秒の体感遅延、引き換えに OCR 精度向上
#   - split mismatch 等での post-processing 補正は導入しない (AI 側で digit を正しく
#     読めることを期待)。建前通り「メーター = 金額の絶対」「AI = 列位置の絶対」を
#     維持しつつ、AI の OCR ステップを賢くする。
# v1.14.00 - 2026-05-14
#   - **アラインメント大改修 + 列構造のデータ宣言化**:
#     現実の日報レイアウト確認の結果、最左端は 時間 列で「No 列」は存在しないことが
#     判明。v1.10.00 の「AI に最左端 No 列を読ませる」設計は前提が崩壊しており、
#     AI は仕方なく 人数 列を meter_no として返していた → アラインメント崩壊。
#   - **NIPPOU_COLUMNS データ宣言を導入**: 列を 1 箇所のリストで定義し、プロンプトは
#     `_build_nippou_prompt(NIPPOU_COLUMNS)` で自動生成。新しい列を増やす場合は
#     COLUMNS に 1 行追加で済む。プロンプト本文・出力スキーマ・例文が自動追従。
#     (フル汎用化 (業種跨ぎ) はまだ premature だが、列レベルの拡張性は早めに入れる)
#   - **alignment を amount-first に書き換え**:
#     Pass 1: 金額完全一致で割当 (同金額複数なら時刻が近い ride を tie-break)
#     Pass 2: 残り meter ←→ 残り ride を出現順に強制割当 (mismatch 表示)
#     meter_no 概念を使わない。AI は単純に「列構造を維持して上から順に抽出」するだけ。
#   - Stage A デバッグ表示の "meter_no" カラムを "順" (上から N 番目) に変更。
#   - interpret_raw_row 内の meter_no 参照は残置 (None になるだけで害なし)。
# v1.13.01 - 2026-05-14
#   - v1.13.00 で normal mismatch 行を「AI 読み取り値」表示にしたが、ユーザー指摘で
#     方針を見直し: **メーターは絶対的に正しい（印字）から、テーブルの数値は
#     メーター値 (正解) を表示する**。集計もメーター値で確定。
#     アプリの役割は「紙のミスを指摘する」であって「数字を訂正する」ではない。
#     ユーザー本人「を訂正するのではなく合うように導いていくのが君の仕事だ」
#   - 状態列の mismatch を「🟠 紙の数字 ¥X → ¥Y」形式に変更。AI が読んだ紙の
#     違う値 ¥X とメーター正解 ¥Y を並べる → ユーザーは紙のどこを直すか一目で分かる。
#   - mismatch セルのピンク色塗りを撤去 (テーブルが正解値を表示してるので、
#     セル色付けは「値がおかしい」誤解を招く)。行全体のピンク背景は維持。
#   - build_report に nippou_amount フィールド追加 (AI が紙から読んだ値を保持、
#     state 列の表示で使う)。
# v1.13.00 - 2026-05-14
#   - **訂正 UX を「視覚情報だけで完結」に再構築**:
#     ユーザー本人「タップしたらすべてやり直しになっちゃう。ポップアップで
#     直そう言われても何が間違ってるかわからない。視覚情報で導いてほしい」。
#     ミッション: 「手書き日報を完成させるサジェスト」、デジタル編集はしない。
#   - detail-table のセルタップ機構を全撤去 (?edit=N アンカー / ダイアログ /
#     edit_row_target / クエリパラメータハンドラ全部削除)。タップで状態消失
#     する不具合も同時解消。
#   - 状態列を具体化:
#     - 'mismatch' → 「🟠 メーター ¥1,600」(正解値が直接見える)
#     - 'missing_nippou' → 「🔴 未記載・¥1,000 を書く」(やることが直接見える)
#     - 'ok' → 空 (ノイズなし)
#   - normal mismatch の gen/mi 表示を AI 読み取り値に変更 (従来は meter_amount
#     を仮置きしていたため、視覚的にズレが分からなかった)。これで「行に AI が
#     読んだ違う値、状態列に正解」のペアで一目で理解できる。
#   - 問題サマリ expander の重複を削除: missing_nippou_row / count_short の項目
#     は detail-table の状態列で全部見えるので、別パネルに重複表示しない。
#   - 再アップ導線をテーブル下に金色枠で目立たせる:「直したら撮り直して再アップ。
#     🟠🔴 が全部消えたら完成」が唯一のアクション。脳の選択肢 1 つだけ。
#   - build_report の row dict に meter_amount フィールドを追加 (render_detail_table
#     から正解値にアクセスできるように)。
# v1.12.01 - 2026-05-14
#   - ローダーの 2 つの UX バグを構造修正:
#     1. **数字が戻る問題**: show_loader が prev > pct (新規パイプライン開始等で
#        前回 100 が残った状態で新 3% 来る) を「リセット → 1, 2, 3 をアニメ」
#        として描画していたため、画面上 100→1→2→3 で「戻った」と見えていた。
#        修正: prev >= pct なら即時ジャンプ (アニメしない)。さらに「日報を完成
#        させる」ボタン押下時に _loader_prev_pct を 0 にリセットして、開始時の
#        ステイル値を確実に破棄。
#     2. **途中で止まる問題**: _poll_until_done の creep が creep_target に
#        追いついた後、次の future 完了まで完全停止していた = 「動いてはピタッ
#        と止まる」リズム。
#        修正: drift モード追加。cur >= creep_target でも end-1 までは 250ms に
#        1 ずつ drift し続ける。future 完了で real_target が上がれば 50ms に 1 ずつ
#        の fast advance に戻る。「絶対に止まらない」体感を実現。
# v1.12.00 - 2026-05-14
#   - **アプリのミッションを再定義**: 「手書き日報を完成させるサジェストツール」。
#     iterative ループ: 写真 → サジェスト → 紙を直す → 再アップ → 確認 → ...完成
#     [[project-mission]] / [[project-correction-philosophy]] に反映済み。
#   - 上記に伴いデジタル編集機構を全撤去:
#     - session_state.row_overrides / apply_overrides() / state='edited' 削除
#     - ダイアログを read-only サジェスト表示に書き換え（編集フォーム廃止）
#     - ダイアログ内容: メーター額(正解) / AI 読み取り結果 / 「紙のここを直して」サジェスト /
#       「もう一度写真撮って再アップを」案内 / 閉じるボタンのみ
#     - mismatch / missing_nippou の理由別に「桁違い / 現収未収取り違え / +100 自腹漏れ」等の
#       具体的なヒントも表示
#   - tr.edited 用 CSS, _RESULT_KEYS の row_overrides 除去
#   - 結果: アプリが「紙を直す→再アップ」ループの advisor に純化、デジタルが
#     「直されたフリ」をすることがなくなった
# v1.11.00 - 2026-05-14
#   - **訂正 UX を「紙の日報を直す助言者」モデルに再構築** (ミッション再定義):
#     これまでの訂正 UI は「デジタル出力を編集する」モードで、テーブル外に別パネルを
#     設置して same item を 2 箇所に重複させていた ([[feedback-one-entry-point]] 違反)。
#     さらに「ユーザーが直すべきは紙の日報そのもの」というアプリの本質的価値を
#     見失っていた ([[project-mission]] の「手書き日報の苦しみ解消」)。
#     - 訂正専用セクションを撤去
#     - detail-table の編集可能セル (missing_nippou / mismatch / edited) を
#       <a href="?edit=N"> で全面タップ可能に。状態セルに ✏️ アイコンで誘導
#     - クエリパラメータ ?edit を session_state.edit_row_target に転写してダイアログを開く
#     - ダイアログを「紙のここに何を書くか」フレームに書き換え:
#       - タイトル: 「📝 紙の日報を直そう」
#       - メーター額を「印字なので正解」と明示
#       - 入力後に「✏️ 手書き日報の Row N に書いてください: 現収欄 / 未収欄 / 摘要」を
#         金色枠で表示し、紙への転記を主役にする
#       - 保存ボタンも「✓ 紙を直した」に
# v1.10.05 - 2026-05-14
#   - ローダーが API 待ちで止まって見える件を UX 修正:
#     _poll_until_done に creep ロジック導入。50ms に 1 unit 進め、実 target より
#     CREEP_LEAD だけ先行表示する。実 future 完了で target が上がれば cur も追従。
#     フェーズ end の 1 手前で頭打ちにして「勝手に完了表示」は防ぐ。
#     これで「処理してるのに数字が止まる → フリーズに見える」が解消。
#     表示 pct は厳密な進捗ではなく「動いてる感」を優先した演出値 (UX 系数値の
#     位置づけ)。金額等の判断材料数値は引き続き嘘つかない。
# v1.10.04 - 2026-05-14
#   - ローダーの「1 ずつ滑らかに動く」を確実に実現するため、Python 側で fine-grained
#     pct を 20ms 刻みで送る方式に切替:
#     - これまで試した CSS @keyframes / transition + @property + counter 案は、
#       iOS Safari の counter() が整数アニメ中の中間値を反映してくれない実装で
#       実機が動かなかった。markdown 内の <script> は Streamlit が無効化、
#       components.html は iframe で重い → Python 送信が一番確実
#     - show_loader は前回値を session_state に保持し、新値との差を 1 ずつ刻んで送る
#     - 数値は <span class="num-value">、% は <span class="num-pct"> で別要素化、
#       % は 0.28em + baseline 配置（底辺合わせ）
#   - メーター/日報の件数乖離アラート文を「写真が正しいか…」から
#     「手書きの日報に書かれている内容が正しいか…」に変更（写真ではなく中身が
#     問題のニュアンスへ）。
# v1.10.03 - 2026-05-14
#   - v1.10.02 のローダーが 3% で止まる症状を構造修正:
#     - 原因: @keyframes animation は要素新規作成時にしか発火しない仕様。
#       Streamlit は markdown 更新を inline-style の差分更新で済ませるため、
#       要素が再作成されず animation が再発火しなかった。
#     - 修正: animation を CSS transition に置き換え。transition は --to-pct の
#       値変更で毎回自動発火するので、Streamlit の更新方式に依存しない。
#     - 副次効果: show_loader から from_pct と session_state 管理を撤去できて
#       コードがシンプル化（transition は現在値から自動補間するので、from を
#       管理する必要が無い）。
#   - % 記号を vertical-align: baseline に変更（数値の底辺合わせ）、0.28em に微縮小。
# v1.10.02 - 2026-05-14
#   - ローダー UI 改善:
#     - % 記号を数字より小さく
#     - 数値を CSS counter + @property で前回値から滑らかにアニメ
# v1.10.01 - 2026-05-14
#   - 「+N」マーカーを構造的に overage として解釈（v1.5.03 までの挙動を完全復元）:
#     _interpret_raw_row で gen_cell が "+100" 形式なら type='overage' を返す。
#     これまで _cell_to_int で +100 を普通の数字 100 と同等扱いし split として
#     処理していたのを廃止。+ 記号の semantic を最後まで保つ。
#   - 結果: Row 16 (+100 自腹 / 1500 Visa) は
#     「Row 16: 1500 未収 Visa」+「Row 16+: 100 現収 メーター超過 (special)」
#     の 2 行に展開されるように。これは build_report が既に case='overage' を
#     2 行展開する仕組みを持っていたので、interpret 段の構造修正だけで完結。
#   - **CSS 修正**: 訂正セクション / st.dialog の文字が黒で暗背景に埋もれていた件。
#     原因は `h1,h2,...,p,div,label {color: #010519}` が全ページに適用されていた
#     こと。`.upload-card, .result-card` の子孫だけにスコープ限定。これでカード外
#     （暗背景）は Streamlit dark theme のデフォルト明色文字が効くように。
# v1.10.00 - 2026-05-14
#   - **構造修正: AI の meter_no を一次アラインメント信号に戻す**
#     v1.5.03 まで AI は meter_no を直接出力していた（精度高）。v1.9.x で「no = 日報上から
#     連番」に変えて、Python の金額一致だけでアラインしたら、似た金額が並ぶケースで
#     「+100 が 1 行下にズレる」「ライドが 1 行ズレる」などの破綻が頻発。
#     パッチで補正する案も検討したが、複雑化して詰むので根本から修正:
#     - NIPPOU_PROMPT: AI に「日報最左端 No 列の手書き行番号」を meter_no として返させる
#     - _align_rides_to_meter: Pass 1 で ride.meter_no を直接 meter に当てる（最優先）。
#       Pass 2 で meter_no 無し ride を金額一致で補完。Pass 3 で残りを順番割当（保険）
#     - v1.9.02 の「メーター超過セーフティネット」パッチを撤回（構造で解決済み）
#   - **validate 失敗時の UI 強化**: 合計タイルを赤背景 + ダーク部グレーアウトに切替。
#     「OK っぽく見える成功状態」を絶対に表示しない。yellow warning ではなく red error。
# v1.9.02 - 2026-05-14
#   - 重大バグ修正: 結果表示の問題サマリ expander 内で変数 `rows` を HTML 文字列リストで
#     上書きしていたため、後段の訂正リスト ( `rows` を辞書として参照 ) で AttributeError
#     → Stage 2 デバッグ expander と「新しい日報を作成」ボタンが描画されない症状を解消。
#     ローカル変数を `_issue_html` に改名して衝突回避。
#   - アライメントにメーター超過セーフティネット追加: 現 meter 額が ride 額より少しだけ
#     大きく、差が 50〜500円の 50円刻みなら、AI が「+100」マーカーを取りこぼした可能性が
#     高いと判定し、lookahead より先に現位置に assign（mismatch として表示）。
#     これで Row 16 (¥1600 メーター / ¥1500 ride) が誤って missing_nippou になり
#     後続の Row 17 (¥1500) と入れ違いになる症状を防ぐ。
#     - v1.5.03 で動いていた挙動の復元（AI が overage を直接出力できた頃の動作と
#       同等の結果を Python 側で担保）。
# v1.9.01 - 2026-05-14
#   - メーター超過自腹補填パターン（現収=+100, 未収=1500）の取りこぼし対策:
#     1) NIPPOU_PROMPT を強化、「+100」のような追加表記を絶対に省略しないよう厳命
#     2) interpret_raw_rows に後方互換層追加。AI が万一 case/kind を含む旧形式で
#        返してきても rides としてそのまま通す（空行扱いで捨てない）
#     3) 空 raw_row でも meter_no があれば nippou_amount=None の placeholder ride
#        を残し、alignment ずれを防止
#     4) Stage 2 debug expander に Stage A (AI 抽出 raw) と Stage B (Python 解釈後)
#        の二段表示を追加。赤色で「+N」を強調し、両欄が捕捉できたか即確認可能。
# v1.9.00 - 2026-05-14
#   - **アーキテクチャ大改革: AI と Python の役割を完全分離**
#     Stage A (AI): 日報のセルを純粋抽出のみ。raw_rows = {no, time, gen_cell, mi_cell, memo,
#       strikethrough}。case や kind の判定は一切させない。「+100」等は文字列のまま記録。
#     Stage B (Python): interpret_raw_rows() が特殊ケースを 1 個ずつ別関数で判定。
#       - _interpret_raw_row: からまわし / 障害者割引 / 分割 / 通常 / 空 を排他的に分類
#       - 各ケースが独立関数 → 互いに干渉しない、テスト容易、debug 容易
#       - 「現金+たこ焼」のような AI 幻覚や、split 検出漏れ が構造的に起こせない設計
#   - NIPPOU_PROMPT は短くシンプルに（読み取りに集中させる）。
#   - 後段の _finalize_rides / build_report は無変更（interpret 結果がそのまま流れる）。
# v1.8.00 - 2026-05-14
#   - ユーザー訂正 UI を追加（コア機能、慎重実装）:
#     AI が自信を持てなかった行 (missing_nippou / mismatch) と訂正済み行 (edited) を
#     結果テーブルの下に「✎ 訂正」セクションとして並べる。各行に「編集」ボタンを置き、
#     タップで st.dialog が開く。
#   - ダイアログ: 種別 (通常/分割) を選び、現収/未収 or gen/mi 金額・人数・摘要を編集可能。
#     メーター額は印字なので変更不可、参考表示のみ。
#   - 訂正は session_state.row_overrides に保存。レンダリング時に apply_overrides() で
#     上書き反映、合計・validate も再計算。state='edited' で黄色ハイライト。
#   - 「新しい日報を作成」リセットボタンで訂正履歴もクリア (_RESULT_KEYS 拡張)。
#   - 哲学: AI は 80% を仕上げる、ユーザーが 20% を 30秒で完成させる。OCR 再実行不要。
# v1.7.05 - 2026-05-14
#   - NIPPOU_PROMPT の判定順序を再構成。「分割払い」判定を最優先(STEP 2)に上げ、
#     通常行/kind 判定より先に「現収欄と未収欄の両方を見る」を強制。
#     これまで AI が通常行ルールを先に当てて split を見落としていたケースを解消。
#   - 「から回し」と「自腹補填」の見分け方を明示。取り消し線**あり**ならから回し、
#     取り消し線**なし**で現収"+100"+未収金額 なら split (自腹補填) と判定。
#     これでメーター回し過ぎでドライバーが自腹補填した行が split として正しく出る。
#   - 出力例にも自腹補填パターンを追加。
# v1.7.04 - 2026-05-14
#   - アライメントを保守化: missing_nippou 判定は金額完全一致 (signal=2) を要求するように
#     変更。時刻一致だけ (signal=1) では missing 確定せず、強制 assign (mismatch 警告)
#     に倒す。これで「日報に書いてあるのに missing 扱い」される誤検出を抑制。
#   - NIPPOU_PROMPT の split 判定を強化: 「両欄に数字があれば必ず split」と明示。
#     頻出パターンを列挙 (現金+カード/電子マネー/配車アプリ)。
#     メーター回し過ぎでドライバー自腹補填するケース（現収¥100+未収¥1,500 等）も
#     split として扱う旨を明示。
#   - 障害者割引（障割）ロジックは現状維持で健全に動作（case='discount'）。
# v1.7.03 - 2026-05-14
#   - UI 微調整:
#     - ファイルアップローダーの英語デフォルト文（Drag and drop / Limit / 拡張子）を
#       しっかり隠し、カスタムテキスト「📷 写真をアップ」を短くして折り返しを防止。
#       padding も増やしてスッキリ感アップ。
#     - mismatch 行で現収・未収 両方のセルが薄赤になってたのを、値が入ってる側
#       (gen > 0 か mi > 0) だけ塗るように変更。間違っていない列が無駄に色付かない。
# v1.7.02 - 2026-05-14
#   - 「人間が間違える前提、AI が黙って働く答えを作る」原則を build_report に実装。
#     missing_nippou 行は kind 不明だが、メーター額は既知なので「現収」と仮定して
#     gen 列に充填。合計が成立する状態を作り、ユーザーの「計算したくない」要求に応える。
#     視覚的には引き続き真っ赤背景 + 白文字で「要確認」を強調、後から訂正できる。
#   - aggregate_totals: missing_nippou を件数・人数に含める（1 件 1 人と仮定）。
#   - validate: missing_nippou も合計貢献として期待値に算入。
# v1.7.01 - 2026-05-14
#   - アラインメントを time + amount のダブルシグナル化:
#     NIPPOU_PROMPT に "time" (降車時刻) フィールドを追加し、AI が日報の時刻も拾う。
#     _ride_meter_signal_match で「金額一致 / 時刻 ±5分以内」を強い指標として評価。
#     どちらか一方でも信頼できる signal があれば確実に揃え、両方ズレた時だけ
#     missing_nippou 判定 + 先読み再評価する。1 行抜けの検出精度が大幅向上。
#   - missing_nippou 行の見た目を「真っ赤背景 + 白抜き文字」に刷新。一目で気付ける。
# v1.7.00 - 2026-05-14
#   - build_report を v2 に再構築: メーター明細書をマスター（行数・順序・金額の絶対真実）
#     として扱い、必ず N 行（=メーター行数）の出力を作るように変更。
#     これまでは日報の rides 数に依存していたため「日報 17件 / メーター 18件」のように
#     1 行抜けてるとアラインメントが連鎖崩壊して mismatch が大量に出ていた。
#   - 新アルゴリズム _align_rides_to_meter: nippou_amount をヒントに greedy + 先読み
#     （3 行先まで）で対応 ride を探す。対応が無いメーター行は state='missing_nippou'。
#   - 問題パネルに「件数不足」と「メーター Row X に対応する日報記載が無い」を具体的に
#     追加。ユーザーは「どの行を追記すれば直るか」が一目で分かるように。
#   - validate / aggregate_totals も meter-master に合わせて期待値を再計算
#     （missing_nippou 行は集計対象外）。
#   - CSS: missing_nippou 行は黄色ハイライト + 「日報に未記載」表記でテーブル内に明示。
# v1.6.00 - 2026-05-14
#   - Stage1/2 出力の堅牢化: AI 出力の欠損・null・型不正を normalize 段で吸収。
#     _coerce_int ヘルパー / _finalize_rows と _finalize_rides の正規化処理を追加。
#     行番号が読めない・金額が null・case 値不正 等が来てもパイプラインが破綻しなくなった。
#   - 検出した問題を issues 配列として回収し、UI 上に専用パネル
#     「⚠ 読み取り時に検出された問題」で一覧表示。
#     どの行で何が起きたか（時刻欠損 / 金額0 / kind不明 / split金額欠損 等）が一目で分かる。
#   - 下流ロジック (build_report / validate / aggregate_totals) は無変更で、後方互換 100%。
#     既存の happy path 出力は v1.5.03 と完全同等。
# v1.5.03 - 2026-05-12
#   - 分割払い（現金 + チケット併用等）に対応。NIPPOU_PROMPT に case="split" の判定ルールを追加し、
#     1 乗車で「現収」「未収」両方の欄に金額が書かれているケースを正しく検出。
#   - build_report に case='split' 分岐を追加: gen_amount → gen 列、mi_amount → mi 列に
#     両方計上する。gen_amount + mi_amount がメーター額と一致しなければ state='mismatch'。
#   - データモデルに後方互換あり（既存の normal/overage/discount は影響なし）。
# v1.5.02 - 2026-05-12
#   - 立ち上がり体感を改善: .streamlit/config.toml でテーマを dark + 濃紺
#     (backgroundColor="#010519") に設定。Streamlit のロード画面の段階から
#     最終形と同じ背景色になり、起動直後の白フラッシュ (~1-2s) を撲滅。
#     実時間は変わらないが「アプリが起動してる」と即座に伝わる。
#   - page_icon に 🚖 を追加（ブラウザタブの瞬間表示で識別性向上）。
# v1.5.01 - 2026-05-12
#   - _ocr_vision_claude の Claude 構造化部分を Opus 4.5 → Sonnet 4.6 に変更。
#     Vision API が読んだ clean な印字テキストを JSON 化するだけのタスクで、
#     Opus と完全同等の出力（20行 receipt 実測で完全一致）かつコスト 1/5。
#     画像認識ではないので Sonnet で精度は落ちない。JSON 不正時は parse_meter が
#     _ocr_claude (Opus 画像直叩き) にフォールバックする安全網は維持。
#   - 1枚あたり OCR 構造化部分のコスト: $0.04 → $0.008 (-80%)。
#     100枚/月で約 ¥480/人 削減。
# v1.5.00 - 2026-05-12
#   - v1.4 で残った A/B 検証用コードと Gemini 経路を全撤去（本番構成確定済のため）。
#     対象: _ai_call_text / get_gemini_model / _ocr_gemini / _classify_nippou_gemini /
#     OCR_PROVIDERS / NIPPOU_PROVIDERS / _is_nippou_compare_mode / _nippou_compare UI /
#     compare_nippou.py / requirements の google-generativeai。
#   - 体感フリーズ対策: ローダーを全フェーズでポーリング型に統一。さらに pipeline を
#     identify×2 並列 → clarity + parse_meter + classify_nippou の 3 並列 に再構成し、
#     14% / 31% / 85% で進捗が止まって見える問題を解消。
#   - identify / clarity を Gemini ファースト → Claude 直叩きに変更（Gemini 画像呼出が
#     10〜30s と遅く、フリーズの主因だったため）。コスト増は v1.4.01 の価格設計で吸収。
# v1.4.01 - 2026-05-11
#   - 精度検証完了 → 本番構成を確定: 日報は **Claude Opus 4.5 を維持**。
#     Gemini 2.5 Flash は致命的誤読で商用 NG、Opus 4.7 / Sonnet 4.6 も精度劣化。
#   - 価格設計で吸収する方針に切替（¥5,000/月 × 月 20 枚 等）。
# v1.4.00 - 2026-05-11
#   - 日報分類 (classify_nippou) もプロバイダ抽象化: secrets.toml [nippou] provider で
#     "claude" | "gemini" を切替可能に。既定は "claude"（精度優先・後方互換）。
#   - A/B 比較モード追加: [nippou] compare_mode = true で両プロバイダを並列実行し、
#     UI 上で rides の差分を可視化できる（精度検証用）。一致確認後に gemini へ移行する流れ。
#   - identify_image / check_clarity を Gemini Flash 優先・Claude フォールバック化
#     (_ai_call_text ヘルパー経由)。これら 2 箇所だけで 1 枚あたり ~$0.11 削減。
#   - 全箇所 Gemini 化想定の総コスト試算: 1 枚 $0.30 → $0.002（約 150 倍削減）。
#     ただし日報は A/B で精度検証してから本番切替する設計。
# v1.3.01 - 2026-05-11
#   - アップロード後の体感速度を大幅改善: st.file_uploader 受信直後に normalize_upload_bytes()
#     で EXIF orientation 適用 → 3000px 上限 → JPEG q=92 に正規化してから session_state 保持。
#     元 5〜8MB → 0.5〜1MB に縮小され、プレビュー描画・HEIC 再デコード・再 rerun の負荷を削減。
#   - OCR 送信サイズは元々 to_b64() で 3000px 上限に縮小されているため、API コスト・精度は不変。
# v1.3.00 - 2026-05-11
#   - OCR プロバイダ抽象化: parse_meter をディスパッチャ化し、_ocr_vision_claude /
#     _ocr_claude / _ocr_gemini をプラガブルに切替可能に（OCR_PROVIDERS 経由）。
#     secrets.toml の [ocr] provider = "vision_claude" | "gemini" | "claude" で選択。
#     失敗時は常に Claude 単独に最終フォールバック。コスト最適 OCR への乗り換えを容易化。
#   - Gemini 対応追加: GEMINI_API_KEY が secrets/env にあれば gemini-2.0-flash で動作
#     （[ocr] gemini_model でモデル名上書き可）。google-generativeai を requirements に追加。
# v1.2.04 - 2026-05-11
#   - イントロスプラッシュ実装を撤去（v1.2.00〜v1.2.03 を巻き戻し）。
#     理由: Streamlit のレンダリングパイプライン上、CSS のみで完全な FOUC 防止が困難で、
#     起動が遅くなる代償の方が大きかった。粒子インフラ (_PARTICLES_HTML) は loader 用に残す。
# v1.2.03 - 2026-05-11
#   - FOUC (UI 一瞬見え) 対策: イントロを CSS markdown より先にレンダリング、
#     inline 重要スタイル (position:fixed; inset:0; background:#010519; z-index:999999)
#     で CSS 解析前から黒画面を確保。
#   - AI と TAXI NIPPOU の視覚中心のズレを修正: letter-spacing 分の末尾空白を
#     padding-left で相殺して、両テキストの視覚中心を flex 中心に揃える。
# v1.2.02 - 2026-05-11
#   - イントロ演出を 3.5s → 4.5s に拡張、4 フェーズの滑らかな遷移に再設計:
#     ① 黒+粒子のみ → ② AI 登場 → ③ 静止 → ④ グラデーション的にフェードアウト
#   - 背景: 不透明 #010519 → 下から透明グラデーション → 完全透明（UI へ自然に繋がる）
#   - AI 文字: 退場時に scale(1.18) + blur(8px) で溶けるように消える
#   - 各要素を 1 本のアニメーションに統合（intro-life / intro-ai-life / intro-sub-life）
# v1.2.01 - 2026-05-11
#   - イントロスプラッシュの調整:
#     • z-index: 99998 → 999999（背景の UI が透けて見える問題を解消）
#     • AI 文字を白に変更（金グロー → 白グロー）
#     • AI 文字サイズを clamp(160px, 36vw, 360px) に拡大
#     • 演出順序を調整: 粒子が先に動き、0.5s 後に AI 文字が現れる
# v1.2.00 - 2026-05-11
#   - イントロスプラッシュ追加: セッション初回起動時に「AI / TAXI NIPPOU」を
#     中央に大表示、既存パーティクルがダイナミックに動き、3 秒で自動フェードアウト。
#     CSS のみで実装（JS 不使用）。intro_shown フラグで初回のみ表示。
# v1.1.04 - 2026-05-11
#   - PATCH 番号を 2 桁ゼロパディングに統一（例: v1.1.4 → v1.1.04）。
#     これにより PATCH 99 まで視覚的に揃った表記が可能になる。
# v1.1.03 - 2026-05-11
#   - 包括的な README.md を整備（プロジェクト概要・アーキテクチャ・業務ルール・セットアップ）
# v1.1.02 - 2026-05-11
#   - 速度改善: to_b64() の per-image キャッシュ化（JPEG エンコード重複排除）
#   - dead code 削除: 未使用 HTML 属性 (data-metric / data-value / data-rowidx)
#   - dead code 削除: 旧 dblclick 編集 UI の名残 (cursor:pointer / .cell-edit クラス)
# v1.1.01 - 2026-05-11
#   - バージョン番号表示を 14px / opacity 0.7 に拡大
#   - タイトル下の余白を 1.5rem → 0.5rem に削減
#   - 完成バーのフォント拡大（✓完成:18px / 件数・人数:28px / 単位:14px）
# v1.1.00 - 2026-05-11
#   - 障害者割引（障割）対応の本格実装
#   - sequence ベースアライメント（meter_no が連番でない場合も正しく動作）
#   - 障割を日報順に '6+' 形式で挿入
#   - +α 要素（passengers=NULL の orphan ride）の救済
#   - 整合性チェックの誤検知修正、税抜運収の小数表示修正、ほか
# v1.0.00 - 2026-05-10 初回リリース
import streamlit as st
import streamlit.components.v1 as components
import anthropic
import base64
from PIL import Image, ExifTags
from pillow_heif import register_heif_opener
from google.cloud import vision
from google.oauth2 import service_account
import io
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

register_heif_opener()
st.set_page_config(page_title='タクシー日報', page_icon='🚖', layout='centered', initial_sidebar_state='collapsed')

# (intro より先に必要なため、CSS markdown より前に配置)
# パーティクル HTML を先に構築（intro と loader の両方で再利用）
def _build_particles_html():
    """40 個の白いパーティクル HTML を構築（決定論的、毎回同じ出力）。
    3 種類の動き(spiral/drift/rise)を index で割り当て、サイズ 15〜40px / duration 1.5〜5s /
    delay 0〜4s をすべて分散（JS 不使用、ちらつかない）。"""
    patterns = ['p-spiral', 'p-drift', 'p-rise']
    parts = []
    for i in range(40):
        pat = patterns[i % 3]
        size = 15 + (i * 13) % 26
        delay = (i * 0.17) % 4
        duration = 1.5 + (i * 0.23) % 3.5
        if pat == 'p-spiral':
            pos_style = ''
        elif pat == 'p-drift':
            x_pct = (i * 73 + 5) % 95
            y_pct = (i * 41 + 10) % 90
            pos_style = f'left:{x_pct}%;top:{y_pct}%;'
        else:  # p-rise
            x_pct = (i * 83 + 7) % 100
            dx = ((i * 31) % 400) - 200
            pos_style = f'left:{x_pct}%;top:100vh;--dx:{dx}px;'
        parts.append(
            f'<span class="particle {pat}" style="'
            f'{pos_style}'
            f'width:{size}px;height:{size}px;'
            f'animation-delay:-{delay:.2f}s;'
            f'animation-duration:{duration:.2f}s;'
            f'"></span>'
        )
    return ''.join(parts)


# モジュール起動時に 1 回だけ構築してキャッシュ（intro / loader から共有）
_PARTICLES_HTML = _build_particles_html()



st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stApp {background: #010519;}
/* Streamlit 1.50 のレイアウト階層を全部 100% 幅に揃える。
   親 (stMain / stAppViewContainer) に padding が残ると block-container が
   全幅にならないので、上から下まで明示的にリセット。 */
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    width: 100% !important;
    max-width: 100% !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}
.block-container,
[data-testid="stMainBlockContainer"] {
    padding: 1.5rem 1rem 2rem 1rem !important;
    max-width: 600px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    width: 100% !important;
    box-sizing: border-box !important;
}
/* 白背景カード内は濃紺文字。カード外（暗背景）は Streamlit テーマ既定の明色文字に任せる。
   こうすると訂正セクション・ダイアログ等のカード外要素も読める。 */
.upload-card, .upload-card *, .result-card, .result-card * {color: #010519;}
.stApp > header {background: transparent;}
.title-block {margin-bottom: 0.5rem;}
.result-card h1, .result-card h2, .result-card h3, .result-card h4 {color: #010519 !important;}
.title-block h1 {color: #d4af37 !important; font-size: 32px !important; font-weight: 600 !important; margin: 0 0 6px !important;}
.title-block h1 * {color: #d4af37 !important;}
.title-block .subtitle {color: #d4af37; font-size: 11px; letter-spacing: 0.15em; margin: 0 0 8px;}
.title-block .divider {height: 1px; background: linear-gradient(90deg, #d4af37, transparent);}
.upload-card, .result-card {background: white; border-radius: 16px; padding: 1.25rem; margin-bottom: 1rem;}
[data-testid="stFileUploader"] section {
    background: #fafafa !important;
    border: 2px dashed #ddd !important;
    border-radius: 14px !important;
    padding: 1rem 0.85rem !important;
}
/* Streamlit デフォルトのドラッグ&ドロップ説明文・サイズ制限文を全部隠す */
[data-testid="stFileUploaderDropzoneInstructions"] > div > span,
[data-testid="stFileUploaderDropzoneInstructions"] > div > small,
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] small {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    overflow: hidden !important;
}
/* カスタムテキスト: 英字を上、日本語を下、左寄せ */
[data-testid="stFileUploaderDropzoneInstructions"] > div {
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    text-align: left !important;
    min-height: 1.5rem !important;
}
/* 上: 薄い英字キャプション（ブランドの "DAILY REPORT · OCR ASSIST" と同系）*/
[data-testid="stFileUploaderDropzoneInstructions"] > div::before {
    content: "DAILY REPORT + METER RECEIPT";
    color: #aaa !important;
    font-size: 9px !important;
    font-weight: 500 !important;
    letter-spacing: 0.2em !important;
    display: block !important;
    margin-bottom: 4px !important;
}
/* 下: 日本語の指示 */
[data-testid="stFileUploaderDropzoneInstructions"] > div::after {
    content: "📷 日報と明細の写真をアップしてください";
    color: #010519 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em !important;
    line-height: 1.35 !important;
    display: block !important;
}
[data-testid="stFileUploader"] label {color: #010519 !important; font-weight: 500 !important;}
[data-testid="stFileUploaderDropzoneInstructions"] {color: #010519 !important; padding: 0 !important; margin: 0 !important;}
[data-testid="stFileUploaderDropzoneInstructions"] * {color: #010519 !important;}

.stButton button {
    background: #d4af37 !important;
    color: #010519 !important;
    border: none !important;
    border-radius: 16px !important;
    padding: 1rem !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    box-shadow: 0 4px 14px rgba(212,175,55,0.17) !important;
    letter-spacing: 0.05em !important;
    width: 100% !important;
}
.stButton button:hover {background: #c89f2e !important; transform: translateY(-1px);}
/* 開発者メニューボタンは控えめに（一般ユーザーが押したくならない見た目）。
   key=dev_menu_toggle に対応する Streamlit のクラス名で targeting。 */
.st-key-dev_menu_toggle .stButton > button,
.st-key-dev_menu_toggle button {
    background: rgba(255,255,255,0.06) !important;
    color: rgba(255,255,255,0.5) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    box-shadow: none !important;
    font-size: 12px !important;
    letter-spacing: 0.05em !important;
    padding: 8px 12px !important;
}
.st-key-dev_menu_toggle .stButton > button:hover,
.st-key-dev_menu_toggle button:hover {
    background: rgba(255,255,255,0.10) !important;
    transform: none !important;
}
.stImage img {border-radius: 12px;}
.complete-bar {background: #f5f5f7; border-radius: 12px; padding: 14px 16px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; border-left: 3px solid #d4af37; scroll-margin-top: 80px;}
.result-card {animation: slideInFromAbove 0.55s cubic-bezier(0.4, 0, 0.2, 1) forwards;}
@keyframes slideInFromAbove {
    from {opacity: 0; transform: translateY(-20px);}
    to {opacity: 1; transform: translateY(0);}
}
.complete-bar .label {font-size: 18px; font-weight: 500; color: #010519; margin: 0;}
.complete-bar .stats {font-size: 28px; font-weight: 600; color: #010519; margin: 0;}
.complete-bar .stats small {font-size: 14px; color: #888;}
.metric-grid-3 {display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 8px;}
.metric-grid-2 {display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 14px;}
.metric {background: #f5f5f7; border-radius: 10px; padding: 10px 12px; min-width: 0;}
.metric.dark {background: #d4af37;}
.metric.dark .label {color: #010519 !important;}
.metric.dark .value {color: #010519 !important;}
.metric .label {font-size: clamp(13px, 3vw, 15px); color: #888; margin: 0; letter-spacing: 0.05em;}

.metric .value {font-size: clamp(24px, 6vw, 34px); font-weight: 700; margin: 2px 0 0; color: #010519; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}

/* validate 失敗時: 合計タイルを警告状態に。OK っぽい見た目を絶対に出さない */
.result-card.invalid .metric {background: #fff0f0 !important; border: 1px solid #f5b0b0;}
.result-card.invalid .metric.dark {background: #e8e8eb !important; opacity: 0.55;}
.result-card.invalid .metric .value {color: #b71c1c !important;}
.result-card.invalid .metric.dark .value {color: #666 !important;}
.result-card.invalid .metric .label {color: #b71c1c !important;}
.result-card.invalid .metric.dark .label {color: #666 !important;}

table {width: 100%; font-size: 12px; border-collapse: collapse; border-radius: 12px; overflow: hidden; border: 0.5px solid #eee;}
thead tr {background: #010519 !important; color: white !important;}
thead tr th {padding: 8px 6px !important; font-weight: 500 !important; color: white !important;}
tbody tr td {padding: 6px !important; color: #010519 !important; background: white !important;}
tbody tr:nth-child(even) td {background: #d8d8dc !important;}
.stAlert {border-radius: 12px !important;}
.stSpinner > div {border-top-color: #d4af37 !important;}

[data-testid="stFileUploaderDropzoneInstructions"] span {
    font-size: 9px !important;
    color: #888 !important;
    line-height: 1 !important;
}
[data-testid="stFileUploader"] button {
    background: #010519 !important;
    color: white !important;
    border: none !important;
}
[data-testid="stFileUploader"] button:hover {
    background: #0a1845 !important;
}

[data-testid="stFileUploader"] button,
[data-testid="stFileUploader"] button * {
    color: white !important;
}
[data-testid="stFileUploader"] button p,
[data-testid="stFileUploader"] button div,
[data-testid="stFileUploader"] button span {
    color: white !important;
}

[data-testid="stVerticalBlock"] > div:empty {display: none !important;}
.result-card:empty {display: none !important;}
.upload-card:empty {display: none !important;}

[data-testid="stProgress"] > div > div > div > div {
    background-color: #d4af37 !important;
}
[data-testid="stProgress"] > div > div > div {
    background-color: #e8e8e8 !important;
    height: 12px !important;
}
[data-testid="stProgress"] {
    height: 12px !important;
}

.big-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(1, 5, 25, 0.92);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    z-index: 99999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    pointer-events: none;
}
.big-overlay.entering {
    animation: overlayFadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}
.big-overlay.entering::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.55), rgba(212,175,55,0.55));
    animation: goldFlash 0.6s ease-out forwards;
    pointer-events: none;
    z-index: 5;
    mix-blend-mode: screen;
}
.big-overlay.exiting {
    animation: overlayFadeOut 0.3s cubic-bezier(0.4, 0, 1, 1) forwards;
}
@keyframes overlayFadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes overlayFadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}
@keyframes goldFlash {
    0% { opacity: 0; }
    30% { opacity: 0.85; }
    100% { opacity: 0; }
}
/* 数値は span で大きく、% も span で小さく底辺合わせ。アニメは Python 側で 1 ずつ送る。 */
.big-num {
    font-weight: 700 !important;
    color: rgba(255, 255, 255, 0.15) !important;
    letter-spacing: -0.05em;
    line-height: 1;
    margin-bottom: 16px;
    font-size: 140px;
}
.big-num .num-value {
    font-size: inherit;
}
.big-num .num-pct {
    font-size: 0.28em;
    font-weight: 500;
    opacity: 0.55;
    margin-left: 6px;
    vertical-align: baseline;
    letter-spacing: 0;
}
.big-label {
    font-size: 14px !important;
    color: #d4af37 !important;
    letter-spacing: 0.2em;
    font-weight: 400 !important;
}
/* === CSS 純正パーティクルアニメーション (JS 不使用) === */
.particles-container {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    z-index: 99999;
    overflow: hidden;
}
.particle {
    position: fixed;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.25);
    box-shadow: 0 0 8px 3px rgba(255, 255, 255, 0.2), 0 0 16px 6px rgba(255, 255, 255, 0.1);
    animation-iteration-count: infinite;
    animation-timing-function: linear;
    will-change: transform, opacity;
}
/* パターン1: 中心から螺旋を描いて外側へ */
.particle.p-spiral {
    top: 50%;
    left: 50%;
    transform-origin: 0 0;
    animation-name: p-spiral;
}
@keyframes p-spiral {
    0%   { transform: rotate(0deg) translateX(0px) scale(0.5); opacity: 0; }
    20%  { opacity: 1; }
    100% { transform: rotate(720deg) translateX(440px) scale(1.5); opacity: 0; }
}
/* パターン2: 画面全体を sin 波でゆらゆら漂う */
.particle.p-drift {
    animation-name: p-drift;
}
@keyframes p-drift {
    0%   { transform: translate(0, 0) scale(0.8); opacity: 0; }
    20%  { opacity: 1; }
    25%  { transform: translate(80px, -60px) scale(1); }
    50%  { transform: translate(-60px, -120px) scale(1.2); }
    75%  { transform: translate(100px, -180px) scale(1); }
    100% { transform: translate(-40px, -240px) scale(0.7); opacity: 0; }
}
/* パターン3: 下から上へ舞い上がる */
.particle.p-rise {
    animation-name: p-rise;
}
@keyframes p-rise {
    0%   { transform: translateY(0) translateX(0) scale(0.6); opacity: 0; }
    20%  { opacity: 1; }
    100% { transform: translateY(-110vh) translateX(var(--dx, 0)) scale(1.4); opacity: 0; }
}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] *,
[data-testid="stExpander"] p,
[data-testid="stExpander"] li,
[data-testid="stExpander"] strong,
[data-testid="stExpander"] b,
[data-testid="stExpander"] h1,
[data-testid="stExpander"] h2,
[data-testid="stExpander"] h3 {color: white !important;}
[data-testid="stExpander"] summary p {color: #d4af37 !important;}
[data-testid="stExpander"] {background: rgba(255,255,255,0.05); border: 1px solid rgba(212,175,55,0.3); border-radius: 12px;}
[data-testid="stExpander"] pre {background: #f5f5f5 !important; color: #1a1a1a !important; padding: 10px !important; border-radius: 6px !important;}
[data-testid="stExpander"] pre * {color: #1a1a1a !important; background-color: transparent !important;}
[data-testid="stExpander"] code {color: #1a1a1a !important; background: #f5f5f5 !important;}
[data-testid="stExpander"] [data-testid="stCodeBlock"] {background: #f5f5f5 !important;}
[data-testid="stExpander"] [data-testid="stCodeBlock"] * {color: #1a1a1a !important;}
[data-testid="stColumn"]:has([class*="st-key-del_"]) {position: relative;}
[class*="st-key-del_"] {position: absolute !important; bottom: 12px; right: 12px; width: auto !important; z-index: 10;}
[class*="st-key-del_"] button {background: rgba(0,0,0,0.6) !important; color: white !important; border: 1px solid rgba(255,255,255,0.3) !important; border-radius: 6px !important; padding: 4px 10px !important; min-height: auto !important; line-height: 1.2 !important; backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);}
[class*="st-key-del_"] button:hover {background: rgba(220,38,38,0.85) !important; border-color: rgba(255,255,255,0.5) !important;}
[class*="st-key-del_"] button p {font-size: 12px !important; margin: 0 !important; color: white !important;}
.detail-table {width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 14px;}
.detail-table th, .detail-table td {padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,0.15); text-align: left; color: white;}
.detail-table th {background: rgba(255,255,255,0.06); font-weight: 600;}
[data-testid="stExpander"] .detail-table tbody tr td {
    color: white !important;
    background: transparent !important;
}
[data-testid="stExpander"] .detail-table tbody tr:nth-child(even) td {
    background: rgba(255,255,255,0.08) !important;
}
/* mismatch: 値が入ってる方の現収 or 未収 セルだけ薄赤（両方は塗らない）*/
.detail-table td.mismatch-cell {background: #fee2e2 !important; color: #7f1d1d !important; font-weight: 600;}
.detail-table tr.mismatch td {background: #fee2e2 !important; color: #7f1d1d !important;}
.detail-table tr.mismatch:nth-child(even) td {background: #fecaca !important;}
.detail-table tr.mismatch td:first-child {border-left: 4px solid #dc2626 !important;}
.detail-table tr.special td {background: #fef3c7 !important; color: #78350f !important;}
.detail-table tr.special td:first-child {border-left: 4px solid #d97706 !important;}
/* missing_nippou: 日報に未記載のメーター行。真っ赤背景＋白抜き文字でインパクト最大 */
.detail-table tr.missing_nippou td {
    background: #dc2626 !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}
.detail-table tr.missing_nippou td:first-child {border-left: 4px solid #fff !important;}
.detail-table tr.missing_nippou:nth-child(even) td {background: #b91c1c !important;}
</style>
""", unsafe_allow_html=True)

# タイトルブロック（ページ最上部、常時表示。結果の有無に関わらず常に最上段）
st.markdown("""
<div class="title-block">
  <h1>AIタクシー日報<span style="font-size: 13px; color: #d4af37; font-weight: 400; margin-left: 8px;">by 怒りの山本</span></h1>
  <p class="subtitle">DAILY REPORT · OCR ASSIST</p>
  <div class="divider"></div>
  <p style="color: rgba(255,255,255,0.7); font-size: 14px; letter-spacing: 0.08em; margin: 4px 0 0; text-align: right;">v1.15.00</p>
</div>
""", unsafe_allow_html=True)

# 結果表示用スロット（タイトルの直下）。結果がある時に container() で埋める。
result_slot = st.empty()


# Loader タイミング定数
LOADER_STEP_SLEEP = 0.15   # loader_steps の各ステップ間隔（デフォルト、callerが上書きする）
LOADER_POLL_SLEEP = 0.1    # parse_meter / classify_nippou 並列実行中のポーリング間隔
                            # 1% 刻みで滑らかに進捗を出すため短めに設定


# 画像準備

def fix_orientation(img):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = img.getexif()
        if exif is not None:
            o = exif.get(orientation)
            if o == 3: img = img.rotate(180, expand=True)
            elif o == 6: img = img.rotate(270, expand=True)
            elif o == 8: img = img.rotate(90, expand=True)
    except: pass
    return img

def normalize_upload_bytes(raw_bytes):
    """アップロード受信バイト列を正規化: EXIF orientation 適用 → 3000px 上限 → JPEG q=92。
    元 5〜8MB のスマホ写真を 0.5〜1MB 程度に縮め、session_state 保持・プレビュー描画・
    HEIC 再デコード等のサーバ負荷を削減する。OCR 入力サイズは to_b64() で同じ 3000px 上限
    に既に縮小されているため、API への送信サイズと OCR 精度には影響しない。"""
    img = fix_orientation(Image.open(io.BytesIO(raw_bytes)))
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')  # JPEG は alpha 非対応
    img.thumbnail((3000, 3000))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=92)
    return buf.getvalue()


def to_b64(img):
    """画像を base64 JPEG にエンコード。同一 img オブジェクトには結果をキャッシュ
    (pipeline 中 identify_image / check_clarity / parse_meter / classify_nippou で
    同じ画像が複数回エンコードされるのを排除し、5-10 % の速度改善)。"""
    cached = getattr(img, '_taxi_b64', None)
    if cached is not None:
        return cached
    img.thumbnail((3000, 3000))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=95)
    b64 = base64.standard_b64encode(buf.getvalue()).decode()
    try:
        img._taxi_b64 = b64  # PIL Image にキャッシュをアタッチ
    except Exception:
        pass  # __slots__ などで失敗してもキャッシュなしで動作続行
    return b64


# 画像識別

def identify_image(client, img):
    """画像を判定して 'meter' / 'nippou' / 'unclear' を返す。"""
    prompt = '''この画像を判定してください。

- メーター明細書（営業明細書）：機械印字、時刻と金額の2列構造、ヘッダに「営業明細書」または「明細」表記
- 日報：手書き、複数列（人数・時刻・現収・未収・摘要等）
- どちらでもない／判別不能：unclear

回答は以下のいずれか1単語のみで（前後に余計な語なし）：
meter
nippou
unclear'''
    res = client.messages.create(
        model='claude-opus-4-5', max_tokens=20, temperature=0,
        messages=[{'role': 'user', 'content': [
            {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': to_b64(img)}},
            {'type': 'text', 'text': prompt},
        ]}]
    )
    answer = res.content[0].text.strip().lower()
    if 'meter' in answer:
        return 'meter'
    if 'nippou' in answer or '日報' in answer:
        return 'nippou'
    return 'unclear'


# 鮮明度チェック

def check_clarity(client, meter_img, nippou_img):
    """両画像が読み取り可能な品質か判定。返値: (ok: bool, reason: str)。"""
    prompt = '''1枚目はメーター明細書、2枚目は日報です。

各画像が読み取り可能な品質か確認してください：
- メーター明細書：時刻と金額の桁が一つひとつはっきり判別できるか
- 日報：手書き数字、現収/未収欄、摘要が判読できるか

結果は以下のいずれかの形式のみで出力（前後に余計な文字なし）：
clarity: ok
または
clarity: ng
reason: <NGの場合の具体的な理由（どの画像のどこが不鮮明か）>'''
    res = client.messages.create(
        model='claude-opus-4-5', max_tokens=200, temperature=0,
        messages=[{'role': 'user', 'content': [
            {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': to_b64(meter_img)}},
            {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': to_b64(nippou_img)}},
            {'type': 'text', 'text': prompt},
        ]}]
    )
    text = res.content[0].text.strip()
    if 'clarity: ok' in text.lower() or 'clarity:ok' in text.lower():
        return True, ''
    m = re.search(r'reason:\s*(.+)', text, re.DOTALL)
    return False, (m.group(1).strip() if m else '画像が不鮮明です')


# ============================================================
# Stage 1: メーター明細書 OCR
# ============================================================
# 出力金額は build_report で「真実」として使用される。
# 既定経路: Vision API + Claude 構造化 (_ocr_vision_claude)
# Vision 未認証 / 失敗時は _ocr_claude (Claude 単体) にフォールバック。

JSON_PROMPT_DIRECT = """このタクシーメーターのレシート画像から全乗車明細を読み取り、
以下のJSON形式のみで返答せよ。説明文は不要。

{"rows": [
  {"no": 1, "time": "10:32", "amount": 4100},
  {"no": 2, "time": "10:50", "amount": 1000}
]}

・noはレシートの行番号
・timeは降車時刻（HH:MM形式）
・amountは¥の金額（数値のみ）
・JSON以外出力しない"""


def _coerce_int(v, default=None):
    """値を int に変換、失敗時は default。None/空文字/文字列数字/float すべてに対応。"""
    if v is None or v == '':
        return default
    if isinstance(v, bool):  # bool は int の派生だが、誤って True=1 にしないため除外
        return default
    if isinstance(v, (int, float)):
        try:
            return int(v)
        except (ValueError, OverflowError):
            return default
    if isinstance(v, str):
        try:
            return int(v.replace(',', '').replace('¥', '').strip())
        except ValueError:
            return default
    return default


def _finalize_rows(rows):
    """rows -> {rows, total, issues} に正規化。
    AI 出力の欠損・null・型不正をここで吸収して下流に渡さない。
    issues: 検出された問題のリスト（後で UI 表示・自己検証に使う）。
    """
    rows = rows or []
    normalized = []
    issues = []
    for idx, r in enumerate(rows):
        if not isinstance(r, dict):
            issues.append({'stage': 'meter', 'type': 'invalid_row', 'where': f'index {idx}',
                           'detail': f'行データが dict ではない: {type(r).__name__}'})
            continue
        no = _coerce_int(r.get('no'))
        if no is None:
            issues.append({'stage': 'meter', 'type': 'missing_no', 'where': f'index {idx}',
                           'detail': '行番号 (no) が読み取れない、スキップ'})
            continue
        time = str(r.get('time') or '').strip()
        if not time:
            issues.append({'stage': 'meter', 'type': 'missing_time', 'where': f'No.{no}',
                           'detail': '時刻が欠損', 'row_no': no})
        amount = _coerce_int(r.get('amount'), default=0)
        if amount == 0:
            issues.append({'stage': 'meter', 'type': 'zero_amount', 'where': f'No.{no}',
                           'detail': '金額が 0 円 (読み取り失敗の可能性)', 'row_no': no})
        normalized.append({'no': no, 'time': time, 'amount': amount})

    # 行番号の昇順ソート & 重複検出
    seen_nos = {}
    for r in normalized:
        seen_nos.setdefault(r['no'], 0)
        seen_nos[r['no']] += 1
    for n, count in seen_nos.items():
        if count > 1:
            issues.append({'stage': 'meter', 'type': 'duplicate_no', 'where': f'No.{n}',
                           'detail': f'同じ行番号が {count} 回出現', 'row_no': n})
    normalized.sort(key=lambda r: r['no'])

    return {'rows': normalized, 'total': sum(r['amount'] for r in normalized), 'issues': issues}


def _extract_json_rows(text):
    """応答テキストから {...} を取り出し rows を返す。見つからなければ None。"""
    m = re.search(r'\{.*\}', text or '', re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    rows = data.get('rows')
    return rows if rows else None


def _ocr_claude(meter_img, claude_client):
    """Claude に画像を直接渡して JSON 構造化。外部依存なしで動く最終フォールバック。"""
    res = claude_client.messages.create(
        model='claude-opus-4-5', max_tokens=4000, temperature=0,
        messages=[{'role': 'user', 'content': [
            {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': to_b64(meter_img)}},
            {'type': 'text', 'text': JSON_PROMPT_DIRECT},
        ]}]
    )
    text = res.content[0].text.strip()
    rows = _extract_json_rows(text)
    if rows is None:
        raise ValueError(f'メーター明細のJSONが見つかりません。応答: {text[:300]}')
    return _finalize_rows(rows)


@st.cache_resource
def get_vision_client():
    """Google Vision API クライアント取得。secrets / key.json から認証。失敗時 None。"""
    try:
        if 'gcp_service_account' in st.secrets:
            info = dict(st.secrets['gcp_service_account'])
            credentials = service_account.Credentials.from_service_account_info(info)
            return vision.ImageAnnotatorClient(credentials=credentials)
    except Exception:
        pass
    if os.path.exists('key.json'):
        try:
            credentials = service_account.Credentials.from_service_account_file('key.json')
            return vision.ImageAnnotatorClient(credentials=credentials)
        except Exception:
            return None
    return None


def _ocr_vision_claude(meter_img, claude_client):
    """ハイブリッド: Vision API で OCR した生テキストを Claude に渡して JSON 構造化。"""
    client_vision = get_vision_client()
    if client_vision is None:
        return None
    buf = io.BytesIO()
    meter_img.save(buf, format='JPEG', quality=95)
    image = vision.Image(content=buf.getvalue())
    image_context = vision.ImageContext(language_hints=['ja'])
    response = client_vision.document_text_detection(
        image=image,
        image_context=image_context,
    )
    if response.error.message:
        return None
    annotation = response.full_text_annotation
    full_text = annotation.text if annotation else ''
    if not full_text.strip():
        return None

    prompt = f"""以下はタクシーメーターのレシートをOCRで読み取った生テキストです。
全乗車明細を読み取り、以下のJSON形式のみで返答せよ。説明文は不要。

{full_text}

{{"rows": [{{"no": 1, "time": "10:32", "amount": 4100}}]}}

・noはレシートの行番号（整数）・timeは降車時刻（HH:MM形式）・amountは¥の金額（数値のみ）・JSON以外出力しない"""
    # OCR 後の clean な印字テキストを JSON 化するだけのタスクのため Sonnet で十分。
    # 実測 (20行 receipt): Opus と完全一致、コスト 1/5。JSON 不正時は parse_meter が
    # _ocr_claude (画像直渡し Opus) にフォールバックする安全網あり。
    res = claude_client.messages.create(
        model='claude-sonnet-4-6', max_tokens=4000, temperature=0,
        messages=[{'role': 'user', 'content': prompt}]
    )
    rows = _extract_json_rows(res.content[0].text.strip())
    return _finalize_rows(rows) if rows else None


def parse_meter(client, meter_img):
    """Stage 1: Vision API + Claude 構造化 → 失敗時は Claude 単独にフォールバック。"""
    try:
        result = _ocr_vision_claude(meter_img, client)
        if result is not None:
            return result
    except Exception:
        pass
    return _ocr_claude(meter_img, client)


# ============================================================
# Stage 2: 日報分類（Claude Opus 4.5）
# ============================================================
# 日報のみから乗客行を分類 → {'rides': [...]}
# meter_data に依存せず、meter_no は日報の上から 1 始まり連番で割当。
# 金額の主要値は読まないが、mismatch 検出のため nippou_amount として
# 日報の手書き金額を任意で記録する（読めない場合は null）。

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 日報の列構造をデータ宣言として持つ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 新しい列を追加する時はここに 1 行足せばプロンプトと出力スキーマが自動追従。
# 別業種の日報を扱う時は別の COLUMNS 定数を用意して切替（ただし interpret 層の
# 業種固有ロジック (overage マーカー検出等) は別途差し替え必要）。
#
# type は AI への型ガイダンスとプロンプト文言生成に使う。
NIPPOU_COLUMNS = [
    {'name': 'time',          'label': '時間 (降車時刻)',         'type': 'time'},
    {'name': 'passengers',    'label': '人数',                  'type': 'int'},
    {'name': 'gen_cell',      'label': '現収欄',                'type': 'amount_or_marker'},
    {'name': 'mi_cell',       'label': '未収欄',                'type': 'amount_or_marker'},
    {'name': 'memo',          'label': '摘要',                  'type': 'string'},
    {'name': 'strikethrough', 'label': '乗車区間の取り消し線', 'type': 'boolean'},
]


def _build_nippou_prompt(columns):
    """COLUMNS 宣言からプロンプトを自動生成。

    新規列を増やす時はこの関数ではなく COLUMNS リストを編集するだけで済む。
    """
    type_guide = {
        'time': '"HH:MM" 文字列。読めない場合は null',
        'int': '整数。不明なら null',
        'amount_or_marker': '数字だけなら数値 (例: 1500)、'
                            '「+100」のような追加表記は文字列 (例: "+100")、'
                            '空欄や「-」だけなら null',
        'string': '文字列。何も書かれてない / 読めない場合は ""',
        'boolean': 'true / false',
    }
    field_lines = '\n'.join(
        f'  "{c["name"]}": {c["label"]} — {type_guide.get(c["type"], "")}'
        for c in columns
    )
    example_values = {
        'time': '"19:19"',
        'int': '1',
        'amount_or_marker': '1000',
        'string': '""',
        'boolean': 'false',
    }
    example_a = '{' + ', '.join(
        f'"{c["name"]}": {example_values.get(c["type"], "null")}'
        for c in columns
    ) + '}'
    # 典型ケースの例: メーター超過自腹補填 (gen=+100, mi=客払い)
    overage_example = {}
    for c in columns:
        if c['name'] == 'gen_cell':
            overage_example[c['name']] = '"+100"'
        elif c['name'] == 'mi_cell':
            overage_example[c['name']] = '1500'
        elif c['name'] == 'memo':
            overage_example[c['name']] = '"Visa"'
        elif c['name'] == 'time':
            overage_example[c['name']] = '"20:06"'
        elif c['name'] == 'passengers':
            overage_example[c['name']] = '1'
        elif c['name'] == 'strikethrough':
            overage_example[c['name']] = 'false'
        else:
            overage_example[c['name']] = 'null'
    example_b = '{' + ', '.join(f'"{k}": {v}' for k, v in overage_example.items()) + '}'

    return f"""これはタクシー乗務員の手書き日報の写真です。
あなたの仕事は **「日報のテーブル構造をそのまま JSON 配列にする」** だけ。
種別の判定（現収か未収か、split か、からまわしか等）は一切しないでください。
判定は後段の Python プログラムが行います。AI は読み取りに集中。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【日報の列構造 (固定)】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

日報は表形式で、左から右に以下の列が並んでいます:

{field_lines}

各行はこの列構造を **必ず維持** したまま読み取ります。空欄はそのまま空 (null / "" / false)
として記録し、列を詰めたり順序を変えたりしないこと。

【行の順番】
- 日報に書かれている順序 (上から下) でそのまま配列に並べる
- 行番号は与えない (上からの順序が暗黙の番号)
- 乗務員が間にブランク行を入れていても、その行は飛ばさず空オブジェクトとして記録する

【amount_or_marker の書き方 - 最重要】
- 「+100」「+200」のような追加表記は **そのまま文字列** で（例: "+100"）。「+」記号は
  乗務員が自腹でメーター超過を補填した重要情報。絶対に省略しない
- 通常の金額は数値で（例: 1500）
- 空欄 / 「-」だけ は null

【memo】
- 摘要欄に書かれた文字をそのまま (Visa / Uber / 現金 / 障割 / AMEX 等)
- 読めない文字は推測せず ""（空文字）。「たこ焼」のような幻覚は禁止

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【出力例】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[
  {example_a},
  {example_b}
]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【厳守事項】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- JSON 配列のみ返す。前後に余計なテキスト・コードブロック記号・思考過程は付けない
- 判定 (case, kind 等) は出力に含めない。生のセルの内容だけ
- 列ごとに必ず両方確認。片方しか読まないと split / overage が落ちる
- 読めない数字を推測で埋めない。null のままにする
"""


NIPPOU_PROMPT = _build_nippou_prompt(NIPPOU_COLUMNS)


def _extract_nippou_rides(text):
    """応答テキストから JSON 配列を取り出して rides を返す。失敗時 None。
    新設計では AI は raw_rows を返す。下流で interpret_raw_rows() に通して rides へ変換。"""
    m = re.search(r'\[.*\]', text or '', re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Stage B: 解釈ロジック（特殊ケースを 1 個ずつ別関数で判定）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI から来る raw_rows を、ピュア Python で解釈して既存形式の rides に変換する。
# 各特殊ケースが独立関数として書かれており、互いに干渉しない。
# テスト容易、debug 容易、新ケース追加も「関数を 1 個足すだけ」。


def _is_overage_marker(value):
    """+100 / +200 のような追加表記か判定。文字列 "+数字" の形式を検出。"""
    if not isinstance(value, str):
        return False
    s = value.strip().replace(',', '')
    return len(s) >= 2 and s[0] == '+' and s[1:].isdigit()


def _parse_overage_marker(value):
    """'+100' → 100 (int)。失敗時 None。"""
    if not _is_overage_marker(value):
        return None
    return int(value.strip().replace(',', '')[1:])


def _cell_to_int(value):
    """raw cell の値を int に変換。数値ならそのまま、"+100" 形式なら 100、null や数字以外なら None。"""
    if isinstance(value, (int, float)):
        return int(value)
    if _is_overage_marker(value):
        return _parse_overage_marker(value)
    return None


def _is_discount_memo(memo):
    """memo に障割の記載があるか。"""
    if not memo:
        return False
    return '障割' in memo or '障害者' in memo


def _interpret_raw_row(raw_row):
    """1 行の raw データを「中間表現」に変換。

    返値: dict with 'type' key:
      - 'karamawashi': 取り消し線あり + "+N" → 直前の通常行に overage を足す
      - 'overage':     「+N」マーカー + 客の支払いあり → メーター超過の自腹補填
      - 'discount':    memo に障割
      - 'split':       両欄に **通常の数字** がある → 現金 + カード等の併用
      - 'normal':      片方の欄のみ
      - 'empty':       何も無い行（スキップ）

    重要: gen_cell に "+N" 形式の文字列があれば overage マーカーとして扱う
    （v1.5.03 までの挙動。split と overage は意味が違うので構造的に分ける）。
    """
    if not isinstance(raw_row, dict):
        return {'type': 'invalid', 'raw': raw_row}

    gen_cell = raw_row.get('gen_cell')
    mi_cell = raw_row.get('mi_cell')
    memo = (raw_row.get('memo') or '').strip()
    strikethrough = bool(raw_row.get('strikethrough'))
    gen_is_overage_marker = _is_overage_marker(gen_cell)

    # Step 1: からまわし（取り消し線 + 現収に "+N" のみ、未収は空）
    if strikethrough and gen_is_overage_marker and mi_cell is None:
        return {
            'type': 'karamawashi',
            'overage_amount': _parse_overage_marker(gen_cell),
        }

    # Step 2: 障害者割引
    if _is_discount_memo(memo):
        amt = _cell_to_int(mi_cell)
        if amt is None:
            amt = _cell_to_int(gen_cell)
        return {
            'type': 'discount',
            'meter_no': raw_row.get('meter_no'),
            'amount': amt,
            'memo': memo,
        }

    # Step 3: メーター超過（"+N" マーカー + 客の支払い）
    # 乗務員が回し過ぎたメーター額を自腹補填するケース。
    # 現収欄に「+100」等のマーカー、未収欄に客の支払額（または現収欄に "+N" + 現収側に客の支払い）。
    if gen_is_overage_marker:
        overage_amt = _parse_overage_marker(gen_cell)
        mi_int = _cell_to_int(mi_cell)
        if mi_int is not None:
            # 客は未収側（カード等）で支払い
            return {
                'type': 'overage',
                'meter_no': raw_row.get('meter_no'),
                'time': raw_row.get('time'),
                'passengers': raw_row.get('passengers'),
                'kind': '未収',
                'customer_amount': mi_int,
                'overage_amount': overage_amt,
                'memo': memo,
            }
        # mi も空: 客の支払額不明だが超過マーカーだけある（稀）。後段でメーター額から推測。
        return {
            'type': 'overage',
            'meter_no': raw_row.get('meter_no'),
            'time': raw_row.get('time'),
            'passengers': raw_row.get('passengers'),
            'kind': '現収',  # 仮置き
            'customer_amount': None,
            'overage_amount': overage_amt,
            'memo': memo,
        }

    # Step 4: 分割払い（両欄に **通常の数字** がある場合）
    gen_int = _cell_to_int(gen_cell)
    mi_int = _cell_to_int(mi_cell)

    if gen_int is not None and mi_int is not None:
        return {
            'type': 'split',
            'meter_no': raw_row.get('meter_no'),
            'time': raw_row.get('time'),
            'passengers': raw_row.get('passengers'),
            'gen': gen_int,
            'mi': mi_int,
            'memo': memo,
        }

    # Step 5: 単一支払
    if gen_int is not None:
        return {
            'type': 'normal',
            'meter_no': raw_row.get('meter_no'),
            'time': raw_row.get('time'),
            'passengers': raw_row.get('passengers'),
            'kind': '現収',
            'amount': gen_int,
            'memo': memo,
        }
    if mi_int is not None:
        return {
            'type': 'normal',
            'meter_no': raw_row.get('meter_no'),
            'time': raw_row.get('time'),
            'passengers': raw_row.get('passengers'),
            'kind': '未収',
            'amount': mi_int,
            'memo': memo,
        }

    # Step 6: 空
    return {'type': 'empty'}


_OLD_FORMAT_KEYS = {'case', 'kind', 'nippou_amount', 'gen_amount', 'mi_amount', 'overage_amount'}
_NEW_FORMAT_KEYS = {'gen_cell', 'mi_cell', 'strikethrough'}


def interpret_raw_rows(raw_rows):
    """raw_rows → 既存形式の rides リストに変換。

    AI 出力の形式に応じて挙動を分岐:
    - 新形式 (gen_cell/mi_cell 等): _interpret_raw_row で特殊ケース判定して ride 化
    - 旧形式 (case/kind 等): そのまま ride として通す（後方互換）
    - 形式が混在していても両方処理可能

    新形式の interp 結果:
      - 'karamawashi': 直前の通常行に overage_amount を付ける
      - 'discount':   障害者割引行を独立で追加
      - 'split':       分割払い行を追加
      - 'normal':      通常行を追加
      - 'empty':       何も書かれていない（スキップ、ただし meter_no があれば
                       「読み取り失敗」プレースホルダーとして alignment 維持）
    """
    rides = []
    raw_rows = raw_rows or []
    for raw in raw_rows:
        if not isinstance(raw, dict):
            continue

        # 形式判定
        keys = set(raw.keys())
        has_old = bool(keys & _OLD_FORMAT_KEYS)
        has_new = bool(keys & _NEW_FORMAT_KEYS)

        # 旧形式 (新形式のキーがなく case/kind 等を持つ) はそのまま ride として通す
        if has_old and not has_new:
            rides.append(raw)
            continue

        # 新形式を解釈
        interp = _interpret_raw_row(raw)
        t = interp.get('type')

        if t == 'invalid':
            continue

        if t == 'empty':
            # 何も書かれていない: meter_no があれば alignment 維持のため空 ride を残す
            meter_no = raw.get('meter_no')
            if isinstance(meter_no, int):
                rides.append({
                    'meter_no': meter_no,
                    'time': raw.get('time') or '',
                    'passengers': raw.get('passengers'),
                    'case': 'normal',
                    'kind': '現収',  # 仮置き
                    'nippou_amount': None,  # 読み取れていない印
                    'memo': '',
                })
            continue

        if t == 'karamawashi':
            # 直前の通常行/分割行に overage_amount を足す
            if rides and rides[-1].get('case') in ('normal', 'split'):
                rides[-1]['case'] = 'overage'
                rides[-1]['overage_amount'] = interp.get('overage_amount') or 0
            continue

        if t == 'overage':
            # メーター超過: 客が支払った額を nippou_amount に、自腹補填額を overage_amount に
            # build_report が 2 行に分けて出力する（客分 + 超過分）
            rides.append({
                'meter_no': interp.get('meter_no'),
                'time': interp.get('time') or '',
                'passengers': interp.get('passengers'),
                'case': 'overage',
                'kind': interp.get('kind') or '未収',
                'nippou_amount': interp.get('customer_amount'),
                'overage_amount': interp.get('overage_amount') or 0,
                'memo': interp.get('memo') or '',
            })
            continue

        if t == 'discount':
            rides.append({
                'meter_no': interp.get('meter_no'),
                'case': 'discount',
                'nippou_amount': interp.get('amount'),
                'memo': interp.get('memo'),
            })
            continue

        if t == 'split':
            rides.append({
                'meter_no': interp.get('meter_no'),
                'time': interp.get('time') or '',
                'passengers': interp.get('passengers'),
                'case': 'split',
                'gen_amount': interp.get('gen'),
                'mi_amount': interp.get('mi'),
                'memo': interp.get('memo') or '',
            })
            continue

        if t == 'normal':
            rides.append({
                'meter_no': interp.get('meter_no'),
                'time': interp.get('time') or '',
                'passengers': interp.get('passengers'),
                'kind': interp.get('kind'),
                'case': 'normal',
                'nippou_amount': interp.get('amount'),
                'memo': interp.get('memo') or '',
            })
    return rides


_VALID_CASES = {'normal', 'overage', 'discount', 'split'}


def _finalize_rides(rides):
    """rides -> {rides, issues} に正規化。
    AI 出力の欠損・null・型不正をここで吸収。下流の build_report が安全に動く保証を作る。
    """
    rides = rides or []
    normalized = []
    issues = []
    for idx, r in enumerate(rides):
        if not isinstance(r, dict):
            issues.append({'stage': 'nippou', 'type': 'invalid_row', 'where': f'index {idx}',
                           'detail': f'行データが dict ではない: {type(r).__name__}'})
            continue
        mn = _coerce_int(r.get('meter_no'))
        case = r.get('case') or 'normal'
        if case not in _VALID_CASES:
            issues.append({'stage': 'nippou', 'type': 'invalid_case',
                           'where': f'index {idx} (meter_no={mn})',
                           'detail': f'未知の case 値「{case}」→ normal として扱う', 'row_no': mn})
            case = 'normal'
        # 注: missing_meter_no チェックは v1.16.01 で削除。
        # 現プロンプト (NIPPOU_PROMPT) は日報の No 列を読ませない設計 (実物の日報に
        # No 列が存在しないため、v1.14.00 で AI に「行番号は与えない」と明示)。
        # アライメントは _align_rides_to_meter が amount/time で実施するため
        # meter_no が None でも正常。にもかかわらず旧 check が残っていて、
        # 全 ride について「meter_no 読めず」という嘘 issue を発生させていた。
        passengers = _coerce_int(r.get('passengers'), default=1) or 1
        if passengers < 0:
            passengers = 1
        kind = r.get('kind') or '現収'
        if case in ('normal', 'overage') and kind not in ('現収', '未収'):
            issues.append({'stage': 'nippou', 'type': 'invalid_kind',
                           'where': f'meter_no={mn}',
                           'detail': f'kind 値が不正「{kind}」→ 現収 として扱う', 'row_no': mn})
            kind = '現収'
        memo = str(r.get('memo') or '').strip()
        time_str = str(r.get('time') or '').strip()  # 降車時刻、無ければ空文字
        nippou_amount = _coerce_int(r.get('nippou_amount'))
        overage_amount = _coerce_int(r.get('overage_amount'))
        gen_amount = _coerce_int(r.get('gen_amount'))
        mi_amount = _coerce_int(r.get('mi_amount'))

        # 各 case 固有の妥当性
        if case == 'split':
            if gen_amount is None and mi_amount is None:
                issues.append({'stage': 'nippou', 'type': 'split_missing_amounts',
                               'where': f'meter_no={mn}',
                               'detail': 'split なのに gen_amount/mi_amount 両方欠損', 'row_no': mn})
        elif case == 'overage':
            if overage_amount is None or overage_amount <= 0:
                issues.append({'stage': 'nippou', 'type': 'overage_missing_amount',
                               'where': f'meter_no={mn}',
                               'detail': 'overage なのに overage_amount が無効', 'row_no': mn})
        elif case == 'discount':
            if nippou_amount is None or nippou_amount <= 0:
                issues.append({'stage': 'nippou', 'type': 'discount_missing_amount',
                               'where': f'meter_no={mn}',
                               'detail': 'discount なのに nippou_amount が無効、行スキップ',
                               'row_no': mn})
                continue  # 金額が無い障割は集計不能、データ破棄

        normalized.append({
            'meter_no': mn, 'time': time_str,
            'passengers': passengers, 'kind': kind,
            'memo': memo, 'case': case,
            'nippou_amount': nippou_amount, 'overage_amount': overage_amount,
            'gen_amount': gen_amount, 'mi_amount': mi_amount,
        })

    return {'rides': normalized, 'issues': issues}


def _build_meter_context(meter_data):
    """日報 OCR プロンプトに添える「メーター参考情報」セクションを作る。

    メーターは印字なので絶対的に正しい。AI はこれを digit ambiguity
    (8 と 5、1 と 7 の取り違え等) の解消に使ってよい。ただし auto-correct
    はせず、紙に明確に書かれた値はそのまま読む。
    """
    rows = (meter_data or {}).get('rows') or []
    if not rows:
        return ''
    lines = []
    for r in rows:
        no = r.get('no')
        t = r.get('time') or ''
        amt = r.get('amount')
        if isinstance(amt, (int, float)):
            lines.append(f'  Row {no}: {t}  ¥{int(amt):,}')
    return f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【メーターレシートの内容 (参考情報、印字なので絶対的に正しい)】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{chr(10).join(lines)}

【このメーター情報の使い方】
- 日報を読むとき、これを **digit ambiguity の解消** に使ってよい
  - 例: 手書きの数字が 8 か 5 か判別困難 → メーター額と整合する候補を選ぶ
  - 例: 1 か 7 か曖昧 → メーター側で 7 が自然なら 7 を選ぶ
- ただし auto-correct はしない:
  - 紙に **明確に書かれた数字** はそのまま出力 (メーターと違っても)
  - 紙には書いてない数字を補完しない (null のまま)
  - 紙の値とメーターが大きく違う (倍以上ズレ等) なら、迷わず紙の値を出力
- メーター情報はあくまで「曖昧な手書きを推測する補助材料」。紙の真実を覆い隠す道具ではない
"""


def classify_nippou(client, nippou_img, meter_data=None):
    """Stage 2: 2 段階処理 + メーター文脈による digit disambiguation。

    A) AI に「raw cells を抽出するだけ」を依頼（判定はさせない）
       + メーターデータを参考情報として渡し、曖昧な数字の disambiguation に使わせる
    B) Python の interpret_raw_rows で特殊ケースを 1 個ずつ判定して rides に変換
    C) _finalize_rides で型・null 整理 + issues 収集

    constraint-aware OCR: AI は曖昧な手書き数字 (8 vs 5 等) でメーターと整合する
    候補を選んでよい。だが auto-correct はしない (明確に書かれた値はそのまま読む)。
    """
    prompt = NIPPOU_PROMPT + _build_meter_context(meter_data)
    res = client.messages.create(
        model='claude-opus-4-5', max_tokens=4000, temperature=0,
        messages=[{'role': 'user', 'content': [
            {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': to_b64(nippou_img)}},
            {'type': 'text', 'text': prompt},
        ]}]
    )
    text = res.content[0].text.strip()
    raw_rows = _extract_nippou_rides(text)
    if raw_rows is None:
        raise ValueError(f'日報のJSON配列が見つかりません。応答: {text[:300]}')
    rides = interpret_raw_rows(raw_rows)
    result = _finalize_rides(rides)
    result['raw_rows'] = raw_rows
    return result


# Stage 3: 純 Python でメーター×日報を統合（AIは関与しない）
# 通常行は meter_amount をそのまま gen/mi に振り分け。
# overage 行は客分 (meter - overage) と超過分 (overage) の 2 行に分割。

def _split_rides(rides):
    """rides を「通常乗車（normal/overage/split）」と「障割（discount）」に分離。
    split（分割払い）はメーター 1 行に対応するので real 側に含める。"""
    real = [r for r in rides if r.get('case') != 'discount']
    adjustments = [r for r in rides if r.get('case') == 'discount']
    return real, adjustments


def _parse_hhmm(s):
    """HH:MM 形式の文字列を「その日の通算分」に変換。失敗時 None。"""
    if not s:
        return None
    s = str(s).strip().replace('：', ':')
    if ':' not in s:
        return None
    try:
        h, m = s.split(':', 1)
        return int(h) * 60 + int(m)
    except (ValueError, IndexError):
        return None


def _ride_effective_amount(ride):
    """ride から「メーター額相当」の見立て金額を返す（アラインメント比較用）。
    - split: gen_amount + mi_amount の合計（=メーター額のはず）
    - overage: nippou_amount + overage_amount（メーター額のはず）
    - normal: nippou_amount そのまま
    どれも欠損なら None を返す（マッチング不可）。
    """
    case = ride.get('case') or 'normal'
    if case == 'split':
        g = ride.get('gen_amount')
        m = ride.get('mi_amount')
        if g is None and m is None:
            return None
        return (g or 0) + (m or 0)
    if case == 'overage':
        n = ride.get('nippou_amount')
        o = ride.get('overage_amount')
        if n is None and o is None:
            return None
        return (n or 0) + (o or 0)
    # normal / その他
    n = ride.get('nippou_amount')
    return int(n) if isinstance(n, (int, float)) else None


def _ride_meter_signal_match(ride, meter_row):
    """ride と meter_row が「同じ乗車」と言えるかの強い指標を返す。

    判定:
      - 金額 が一致 (eff_amount == meter.amount): score 2 (確信)
      - 時刻 が ±5 分以内: score 1 (一致の可能性高)
      - 上記がいずれも不明: score 0 (情報不足、形だけのアライン)
      - 金額がズレ かつ 時刻もズレ: score -1 (明確に違う)
    """
    eff = _ride_effective_amount(ride)
    m_amt = int(meter_row['amount'])
    amt_known = eff is not None
    amt_match = amt_known and eff == m_amt
    amt_diff = amt_known and not amt_match

    rt = _parse_hhmm(ride.get('time'))
    mt = _parse_hhmm(meter_row.get('time'))
    time_known = rt is not None and mt is not None
    time_close = time_known and abs(rt - mt) <= 5
    time_diff = time_known and not time_close

    if amt_match:
        return 2
    if time_close and not amt_diff:
        return 1
    if amt_diff and time_diff:
        return -1
    if amt_diff or time_diff:
        return -1
    return 0  # 情報不足


def _align_rides_to_meter(real_rides, meter_rows_list):
    """メーター行をマスターに、各 meter 行に対応する ride を金額一致で割り当てる。

    日報には行番号列が無い前提。AI は上から順にライドを抽出するだけで、
    メーター行とのマッピングは下流（この関数）で実施する。

    シグナルの優先順位:
      Pass 1: **金額完全一致**で割当 (最も信頼できる: メーター = 印字、AI は金額をほぼ正確に読む)。
              同じ金額が複数あれば「時刻が近い ride」を tie-break で選ぶ。
      Pass 2: 残り meter 行 ←→ 残り ride を、上から順番に強制割当 (mismatch として表示される)。

    設計理由:
      - 「最左端の No 列」を前提にすると、その列が存在しない日報レイアウトで破綻する (v1.10.x)
      - 金額はメーターと日報の両方に書かれるので普遍的に使えるシグナル
      - 同じ金額が並ぶ場合のみ時刻で補完すれば、ほぼ全てのケースで安定
    """
    assigned_ride_idx = set()
    rides_by_meter_no = {}

    # Pass 1: 金額一致で割当。同金額複数なら時刻が近い ride を選ぶ。
    for m in meter_rows_list:
        m_amt = int(m.get('amount') or 0)
        m_time = _parse_hhmm(m.get('time'))
        candidates = []
        for i, ride in enumerate(real_rides):
            if i in assigned_ride_idx:
                continue
            eff = _ride_effective_amount(ride)
            if eff is None or eff != m_amt:
                continue
            r_time = _parse_hhmm(ride.get('time'))
            if r_time is not None and m_time is not None:
                time_diff = abs(r_time - m_time)
            else:
                time_diff = 9999  # 情報不足は後ろに
            candidates.append((time_diff, i, ride))
        if candidates:
            candidates.sort(key=lambda x: x[0])
            _, i, ride = candidates[0]
            rides_by_meter_no[m['no']] = ride
            assigned_ride_idx.add(i)

    # Pass 2: 金額不一致 (Pass 1 で当たらなかった) ride を「時刻が最も近い」未割当
    # メーター行に当てる。ただし時刻差が閾値超なら無理に当てない (false mismatch を防ぐ)。
    #
    # 設計の根拠:
    #   旧 Pass 2 は「余り物を上から順番に当てる」だったが、紙に 1 行書き漏れが
    #   あると、後続の paper 行が全部 1 つずれて存在しない場所に強制マッチされ、
    #   「メーター ¥900 なのに紙の ¥1,090 AMEX」みたいな機械的に作られた嘘の
    #   mismatch が並んでしまう (実例: 紙が No.11 ¥900 を書き漏れ → 紙の順12
    #   18:09 AMEX がメーター No.11 17:14 に強制割当)。
    #
    #   時刻ベース + 閾値で当てれば、書き漏れ位置は missing_nippou で残り、
    #   紙にある行は時刻が一致するメーター行に正しく付く。AMEX のような memo も
    #   正しい行に乗る。
    TIME_PROXIMITY_THRESHOLD = 20  # 分。これより離れてたら別の乗車として扱う
    unassigned_ride_idx = [i for i in range(len(real_rides)) if i not in assigned_ride_idx]
    for ride_idx in unassigned_ride_idx:
        ride = real_rides[ride_idx]
        r_time = _parse_hhmm(ride.get('time'))
        if r_time is None:
            continue  # 時刻無しは推定不能、orphan として捨てる
        # 未割当メーター行の中で最も時刻が近いものを探す
        best_no = None
        best_diff = float('inf')
        for m in meter_rows_list:
            if m['no'] in rides_by_meter_no:
                continue
            m_time = _parse_hhmm(m.get('time'))
            if m_time is None:
                continue
            diff = abs(r_time - m_time)
            if diff < best_diff:
                best_diff = diff
                best_no = m['no']
        if best_no is not None and best_diff <= TIME_PROXIMITY_THRESHOLD:
            rides_by_meter_no[best_no] = ride
            assigned_ride_idx.add(ride_idx)

    # メーター順で aligned を組み立て (残ったメーター行は ride=None → missing_nippou)
    aligned = [(rides_by_meter_no.get(m['no']), m) for m in meter_rows_list]
    return aligned


def build_report(meter_data, nippou_data):
    """Stage 3 (v2): メーター行をマスターとして必ず N 行の出力を作る。

    設計原則:
      - メーター明細書 = 行数・順序・金額の絶対真実（印字なので誤読の確率も極小）
      - 日報 = annotation（kind, 人数, memo 等の付加情報のソース）
      - 出力は必ずメーター行数と同じ件数
      - 対応 ride が見つからない meter 行は state='missing_nippou' で出力し、
        UI 側で「日報に未記載」として明示する

    case の扱い:
      - 'overage': 客分行 + 超過分(state='special') の 2 行に分割
      - 'split':   現金 + チケット等の併用。gen_amount/mi_amount を両方計上
      - 'discount': 別ループで nippou_amount を mi に計上、state='discount'
      - 'normal'/不明: kind に従って gen/mi に振り分け 1 行出力

    アライメントは _align_rides_to_meter による nippou_amount ベースの greedy + 先読み。
    日報金額 (nippou_amount) がメーター額と異なる場合は state='mismatch' で警告
    （金額はメーター値を採用、ハイライトのみ）。"""
    meter_rows_list = sorted(meter_data.get('rows', []), key=lambda r: r['no'])
    rides = nippou_data.get('rides', [])
    real_rides, adjustments = _split_rides(rides)
    aligned = _align_rides_to_meter(real_rides, meter_rows_list)

    output = []
    last_real_meter_no = None
    for ride, m in aligned:
        meter_no = m['no']
        meter_amount = int(m['amount'])
        time_str = m['time']

        if ride is None:
            # 対応 ride 無し: 「現収」と仮定して合計に貢献させる。
            # 哲学: ユーザーは計算したくない。kind 不明でも合計が成立する状態を作る。
            # 後で「実は未収だった」と気付いたら訂正できるよう赤背景で強く明示。
            output.append({
                'no': meter_no, 'passengers': 1, 'time': time_str,
                'gen': meter_amount, 'mi': 0,  # 現収と仮定
                'memo': 'この金額の記入が漏れています。新しい行を作成して現収か未収の欄に記入してください。',
                'state': 'missing_nippou',
                'meter_amount': meter_amount,
            })
            continue

        last_real_meter_no = meter_no
        case = ride.get('case') or 'normal'
        passengers = int(ride.get('passengers') or 1)
        kind = ride.get('kind') or '現収'
        memo = ride.get('memo') or ''
        nippou_amt = ride.get('nippou_amount')
        nippou_amt = int(nippou_amt) if isinstance(nippou_amt, (int, float)) else None

        if case == 'overage':
            overage = int(ride.get('overage_amount') or 0)
            client_amount = meter_amount - overage
            client_state = 'mismatch' if (nippou_amt is not None and nippou_amt != client_amount) else 'ok'
            output.append({
                'no': meter_no, 'passengers': passengers, 'time': time_str,
                'gen': client_amount if kind == '現収' else 0,
                'mi': client_amount if kind == '未収' else 0,
                'memo': memo, 'state': client_state,
                'meter_amount': client_amount,
            })
            output.append({
                'no': f'{meter_no}+', 'passengers': passengers, 'time': time_str,
                'gen': overage, 'mi': 0,
                'memo': 'メーター超過', 'state': 'special',
            })
        elif case == 'split':
            gen_amt = int(ride.get('gen_amount') or 0)
            mi_amt = int(ride.get('mi_amount') or 0)
            split_state = 'ok' if (gen_amt + mi_amt) == meter_amount else 'mismatch'
            output.append({
                'no': meter_no, 'passengers': passengers, 'time': time_str,
                'gen': gen_amt, 'mi': mi_amt,
                'memo': memo or '現金+チケット',
                'state': split_state,
                'meter_amount': meter_amount,
            })
        else:  # normal or 不明
            row_state = 'mismatch' if (nippou_amt is not None and nippou_amt != meter_amount) else 'ok'
            # メーターが絶対的に正しい (印字なので)。テーブルの数値はメーター値を表示し、
            # AI が読んだ違う値は state 列で「紙のここを直して」サジェストとして見せる。
            # → 集計はメーター値で確定、ユーザーは紙のミスだけ直せばよい。
            output.append({
                'no': meter_no, 'passengers': passengers, 'time': time_str,
                'gen': meter_amount if kind == '現収' else 0,
                'mi': meter_amount if kind == '未収' else 0,
                'memo': memo, 'state': row_state,
                'meter_amount': meter_amount,
                'nippou_amount': nippou_amt,  # AI が紙から読んだ値（mismatch 時に表示）
            })

    # discount 行: meter 行とは独立、別途追加（最後に対応した通常行の no + '+' をラベルに）
    for r in adjustments:
        n_amt = r.get('nippou_amount')
        if not isinstance(n_amt, (int, float)) or int(n_amt) <= 0:
            continue
        label = f'{last_real_meter_no}+' if last_real_meter_no is not None else '*'
        output.append({
            'no': label,
            'passengers': 0, 'time': '',
            'gen': 0, 'mi': int(n_amt),
            'memo': r.get('memo') or '障割',
            'state': 'discount',
        })

    return output


# 整合性チェック

def validate(report_rows, meter_data, nippou_data):
    """出力合計と期待値の整合性チェック (v2: meter-master 設計に対応)。

    返値:
        (ok: bool, diff: int)
        - ok: True なら期待値と出力合計が完全一致
        - diff: 出力合計 − 期待値（正なら出力過多、負なら出力不足）

    期待値の算出:
      - メーター行合計 (全行)
      - + 障割の nippou_amount 合計
      missing_nippou 行も「現収と仮定」で合計に貢献しているので、期待値から引かない。
    """
    output_total = sum((r.get('gen') or 0) + (r.get('mi') or 0) for r in report_rows)
    meter_rows_list = sorted(meter_data.get('rows', []), key=lambda r: r['no'])
    rides = nippou_data.get('rides', [])
    _, adjustments = _split_rides(rides)

    meter_total = sum(int(r['amount']) for r in meter_rows_list)
    discount_total = sum(
        int(d['nippou_amount']) for d in adjustments
        if isinstance(d.get('nippou_amount'), (int, float)) and int(d['nippou_amount']) > 0
    )
    expected = meter_total + discount_total
    diff = output_total - expected
    return diff == 0, diff


def validate_meter_sequence(meter_data):
    """メーター明細の行番号が連番か検証（欠番検出）。

    例: nos=[1,2,4,5] → (False, [3])
        nos=[1,2,3,4,5] → (True, [])
        nos=[] → (True, [])

    返値:
        (ok: bool, missing: list[int])
        - ok: True なら最小〜最大の間に欠番なし
        - missing: 欠番の昇順リスト
    """
    rows = meter_data.get('rows', [])
    nos = sorted(int(r.get('no', 0)) for r in rows if r.get('no') is not None)
    if not nos:
        return True, []
    expected = set(range(nos[0], nos[-1] + 1))
    missing = sorted(expected - set(nos))
    return len(missing) == 0, missing


# Loader 演出ヘルパー（CSS のみ: %数値 + ラベル + パーティクル）
# 注: _PARTICLES_HTML はイントロスプラッシュでも使うため、ファイル冒頭側に前倒しで定義済み。


def _render_loader_frame(loader, pct, label, anim_class):
    cls = f'big-overlay {anim_class}'.strip()
    loader.markdown(
        f'<div class="{cls}" data-pct="{pct}">'
        f'<div class="particles-container">{_PARTICLES_HTML}</div>'
        f'<div class="big-num">'
        f'<span class="num-value">{pct}</span><span class="num-pct">%</span>'
        f'</div>'
        f'<div class="big-label">{label}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def show_loader(loader, pct, label, anim_class=''):
    """進捗ローダー。前回値 → 新 pct を 1 ずつ刻んで送り、体感的に動いて見せる。

    重要: pct < prev (新規パイプライン等で値が戻る) の場合、アニメで降りずに
    新しい pct に **直接ジャンプ** する。前回 100 で完了したセッションが残った
    状態で新パイプラインが 3 から始まる時、100→1→2→3 と描画してしまうと
    視覚的に「戻ってる」と感じる（実際はリセット → 上昇）。これを避ける。
    """
    prev = st.session_state.get('_loader_prev_pct', 0)
    if prev >= pct:
        # 同じ値 or 戻る方向 → 直接描画 (アニメしない)
        _render_loader_frame(loader, pct, label, anim_class)
    else:
        # 上昇方向 → 1 ずつアニメ
        for v in range(prev + 1, pct + 1):
            _render_loader_frame(loader, v, label, anim_class if v == prev + 1 else '')
            if v != pct:
                time.sleep(0.02)
    st.session_state['_loader_prev_pct'] = pct

def loader_steps(loader, pcts, label, sleep=LOADER_STEP_SLEEP, anim_class=''):
    for pct in pcts:
        show_loader(loader, pct, label, anim_class=anim_class)
        time.sleep(sleep)
        anim_class = ''  # 最初のステップだけアニメーション、以降は静的に


# 表示ヘルパー

def render_summary(ken, nin, gen, mi, sou, tax, net):
    """表示順: 1.完成バー(件数/人数) → 2.現収/未収/総収 → 3.消費税/税抜。
    その後の render_detail_table で詳細テーブル。"""
    fmt = lambda x: f'¥{int(x):,}'
    st.markdown(f"""
<div class="complete-bar">
  <p class="label">✓ 完成</p>
  <p class="stats">{ken}<small> 件 </small>{nin}<small> 人</small></p>
</div>
<div class="metric-grid-3">
  <div class="metric"><p class="label">現収</p><p class="value">{fmt(gen)}</p></div>
  <div class="metric"><p class="label">未収</p><p class="value">{fmt(mi)}</p></div>
  <div class="metric dark"><p class="label">総収</p><p class="value">{fmt(sou)}</p></div>
</div>
<div class="metric-grid-2">
  <div class="metric"><p class="label">消費税</p><p class="value">{fmt(tax)}</p></div>
  <div class="metric"><p class="label">税抜運収</p><p class="value">{fmt(net)}</p></div>
</div>
""", unsafe_allow_html=True)


def render_detail_table(rows):
    """テーブルは read-only。タップ機構なし。状態列で「メーター額」「次に何をすべきか」
    を一目で分かるようにする。同じ情報を別パネルに重複表示しない。"""
    headers = ['No', '人数', '時刻', '現収', '未収', '摘要', '状態']
    parts = ['<table class="detail-table"><thead><tr>']
    parts.extend(f'<th>{h}</th>' for h in headers)
    parts.append('</tr></thead><tbody>')
    state_class_map = {'mismatch': 'mismatch', 'special': 'special', 'missing_nippou': 'missing_nippou'}
    for r in rows:
        state = r.get('state', '')
        cls = state_class_map.get(state, '')
        row_class = f' class="{cls}"' if cls else ''
        gen_v = int(r.get('gen') or 0)
        mi_v = int(r.get('mi') or 0)
        gen = f"{gen_v:,}" if gen_v else ''
        mi = f"{mi_v:,}" if mi_v else ''
        # mismatch のセル色付けは廃止: 今のテーブルはメーター(正解)を表示しているので、
        # セルを「値がおかしい」と塗ると逆に誤解を生む。行全体のピンク背景で注意喚起する。
        gen_cell_cls = ''
        mi_cell_cls = ''

        # 状態列: テーブルの数値はメーター (正解) を表示してる前提で、
        # mismatch 行は「紙の方が違う」を AI 読み取り値で具体的に示す。
        meter_amt = r.get('meter_amount')
        nippou_amt = r.get('nippou_amount')
        if state == 'mismatch':
            if isinstance(nippou_amt, int) and isinstance(meter_amt, int):
                state_display = f'🟠 AI 読み ¥{nippou_amt:,} / メーター ¥{meter_amt:,}'
            elif isinstance(meter_amt, int):
                state_display = f'🟠 メーター ¥{meter_amt:,}（日報の数字を確認）'
            else:
                state_display = '🟠 日報の数字を確認'
        elif state == 'missing_nippou' and isinstance(meter_amt, int):
            state_display = f'🔴 未記載・¥{meter_amt:,} を書く'
        elif state == 'special':
            state_display = 'メーター超過'
        elif state == 'discount':
            state_display = '障割'
        elif state == 'ok':
            state_display = ''
        else:
            state_display = state

        parts.append(f'<tr{row_class}>')
        parts.append(f'<td>{r["no"]}</td>')
        parts.append(f'<td>{r["passengers"] if r["passengers"] else ""}</td>')
        parts.append(f'<td>{r["time"]}</td>')
        parts.append(f'<td data-col="gen"{gen_cell_cls}>{gen}</td>')
        parts.append(f'<td data-col="mi"{mi_cell_cls}>{mi}</td>')
        parts.append(f'<td>{r["memo"]}</td>')
        parts.append(f'<td>{state_display}</td>')
        parts.append('</tr>')
    parts.append('</tbody></table>')
    st.markdown(''.join(parts), unsafe_allow_html=True)


def aggregate_totals(rows):
    """件数・人数・現収・未収・総収・消費税・税抜運収を集計。

    state ごとの件数(ken)・人数(nin)カウント方針【業務ルール】:
      - 'special'（メーター超過）: 除外。同一乗客の超過分のため二重計上回避。
      - 'discount'（障割）: 除外。割引額の独立行は会計調整であり「乗客」ではないため。
      - 'missing_nippou'（日報未記載・現収仮定）: 含める。1 件 1 人の乗車として計上
        （合計を成立させる仮置き。ユーザーが訂正したらそれに従う）。
      - 'normal' / 'mismatch' / 'edited' 等: 含める。通常の乗車。

    金額(gen/mi/sou/tax/net)は state を問わず合算するため、
    消費税・税抜運収は gen+mi の合計から自動的に正しく計算される。
    """
    gen = sum((r.get('gen') or 0) for r in rows)
    mi = sum((r.get('mi') or 0) for r in rows)
    excluded_states = {'special', 'discount'}
    ken = sum(1 for r in rows if r.get('state') not in excluded_states)
    nin = sum((r.get('passengers') or 0) for r in rows if r.get('state') not in excluded_states)
    sou = gen + mi
    tax = int(round(sou / 11, -1))
    net = sou - tax
    return ken, nin, gen, mi, sou, tax, net


# パイプライン本体

def _poll_until_done(loader, futures, pct_range, label):
    """futures が全て完了するまで pct を進めながらローダーを更新。

    UX 重視: **絶対に止まらない**。
    - 通常時 (cur < creep_target): 50ms に 1 ずつ進む（fast advance）
    - creep に追いついた時 (cur >= creep_target, cur < end-1): 250ms に 1 ずつ進む（drift）
    - end-1 に達したら future 完了を待つ（ここで止まるのは仕方ない）
    - future 完了で real_target が上がれば fast advance で追従

    フェーズ末尾 (end-1) で頭打ちにして「勝手に完了表示」を防ぐ。
    """
    start, end = pct_range
    span = max(1, end - start)
    cur = start
    show_loader(loader, cur, label)

    TICK = 0.05         # 50ms ごとに 1 tick
    POLL_EVERY = 10     # 500ms ごとに future 完了確認
    DRIFT_EVERY = 5     # 250ms ごとに drift で 1 進める
    CREEP_LEAD = max(2, span // 6)  # 実 target からの先行幅

    tick_count = 0
    done = 0
    while done < len(futures):
        if tick_count % POLL_EVERY == 0:
            done = sum(1 for f in futures if f.done())
        real_target = start + int(span * done / max(1, len(futures)))
        creep_target = min(end - 1, real_target + CREEP_LEAD)
        if cur < creep_target:
            # 通常前進: 50ms ごとに 1 ずつ
            cur += 1
            show_loader(loader, cur, label)
        elif cur < end - 1 and tick_count % DRIFT_EVERY == 0:
            # creep に追いついて停滞しそうなら drift で末尾に向かう
            cur += 1
            show_loader(loader, cur, label)
        time.sleep(TICK)
        tick_count += 1

    # 完了: end まで一気に詰める（show_loader 側が 1 ずつ animate してくれる）
    show_loader(loader, end, label)


def run_pipeline(client, imgs, loader):
    """End-to-end pipeline. 失敗時は RuntimeError。返値: (rows, valid, diff, meter_data, nippou_data)

    並列構成:
      Phase 1 (3-25%):  identify×2 (どちらがメーター/日報か特定)
      Phase 2 (25-60%): clarity || parse_meter を 2 並列
                        (clarity NG なら中断)
      Phase 3 (60-92%): classify_nippou (meter context 付き、constraint-aware OCR)
                        メーター完了後に日報を読む = digit ambiguity 解消の精度向上
      Phase 4 (92-100%): build + validate (純 Python、瞬時)
    """
    # フェードイン演出（1% 刻み × 短sleep）
    loader_steps(loader, list(range(3, 10)), '画像を判別中', sleep=0.04, anim_class='entering')

    # Phase 1: 2 枚の判別を並列実行
    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(identify_image, client, imgs[0])
        f2 = executor.submit(identify_image, client, imgs[1])
        _poll_until_done(loader, [f1, f2], (10, 25), '画像を判別中')
        kind1 = f1.result()
        kind2 = f2.result()

    if kind1 == 'unclear' or kind2 == 'unclear':
        idx = 1 if kind1 == 'unclear' else 2
        raise RuntimeError(f'{idx}枚目が日報・メーター明細書のどちらか判別できません。正しい画像を選択してください。')
    if kind1 == kind2:
        kind_jp = 'メーター明細書' if kind1 == 'meter' else '日報'
        raise RuntimeError(f'同じ種類の画像が2枚アップされています（両方とも{kind_jp}）。日報1枚＋メーター明細書1枚をアップしてください。')

    if kind1 == 'meter':
        meter_img, nippou_img = imgs[0], imgs[1]
    else:
        meter_img, nippou_img = imgs[1], imgs[0]

    # Phase 2: 鮮明度 + メーター OCR を 2 並列 (clarity NG なら中断)
    with ThreadPoolExecutor(max_workers=2) as executor:
        clarity_future = executor.submit(check_clarity, client, meter_img, nippou_img)
        meter_future = executor.submit(parse_meter, client, meter_img)
        _poll_until_done(
            loader,
            [clarity_future, meter_future],
            (25, 60),
            'メーター明細を読み取り中',
        )
        ok, reason = clarity_future.result()
        if not ok:
            raise RuntimeError(f'画像の鮮明度が不足しています：{reason}\n撮り直して再アップしてください。')
        meter_data = meter_future.result()

    # Phase 3: 日報 OCR を constraint-aware で実行 (meter_data を文脈として渡す)
    # メーター情報を AI に渡すと、曖昧な手書き数字 (8 vs 5 等) でメーターと整合する
    # 候補を選んでくれる = digit ambiguity の解消。auto-correct ではなく OCR の
    # 補助情報として使う。
    with ThreadPoolExecutor(max_workers=1) as executor:
        nippou_future = executor.submit(classify_nippou, client, nippou_img, meter_data)
        _poll_until_done(loader, [nippou_future], (60, 92), '日報を読み取り中 (メーター照合)')
        nippou_data = nippou_future.result()

    loader_steps(loader, list(range(92, 101)), '統合中', sleep=0.03)
    report_rows = build_report(meter_data, nippou_data)
    valid, diff = validate(report_rows, meter_data, nippou_data)
    return report_rows, valid, diff, meter_data, nippou_data


# Reset / state

_RESULT_KEYS = ('result_rows', 'result_valid', 'result_diff', 'result_meter', 'result_nippou')


def _clear_results():
    """結果系の session_state を全削除"""
    for k in _RESULT_KEYS:
        st.session_state.pop(k, None)


def reset_app():
    st.session_state.uploader_counter = st.session_state.get('uploader_counter', 0) + 1
    st.session_state.kept_files = []
    _clear_results()

if 'uploader_counter' not in st.session_state:
    st.session_state.uploader_counter = 0
if 'kept_files' not in st.session_state:
    st.session_state.kept_files = []

if st.session_state.get('result_rows'):
    with result_slot.container():
        # 処理完了後にページ最上部へ強制スクロール。
        # Streamlit は st.rerun() でスクロール位置を保持してしまうため、
        # 完成ボタンを押した位置（ページ下部）から動かないバグへの対策。
        # 複数のスクロール API（scrollTo / scrollTop / scrollIntoView）を併用し、
        # Streamlit の遅延レンダリングに追従するよう 50ms / 200ms / 500ms / 1200ms で
        # 連打する。height=1 + body height:1px で iframe を完全に不可視化。
        components.html("""
<style>html, body { margin:0; padding:0; overflow:hidden; height:1px; }</style>
<script>
(function() {
  function doScroll() {
    try {
      var w = window.parent;
      var d = w.document;
      w.scrollTo(0, 0);
      if (d.documentElement) d.documentElement.scrollTop = 0;
      if (d.body) d.body.scrollTop = 0;
      var t = d.querySelector('.title-block');
      if (t && t.scrollIntoView) t.scrollIntoView({block: 'start'});
    } catch(e) {}
  }
  doScroll();
  setTimeout(doScroll, 50);
  setTimeout(doScroll, 200);
  setTimeout(doScroll, 500);
  setTimeout(doScroll, 1200);
})();
</script>
""", height=1)

        # 結果本体（summary / detail-table / reset button / debug expander）
        # アプリは「紙の日報を完成させるためのサジェスト」が責務。
        # デジタル編集はしない — AI が読んだままを表示し、ユーザーは紙を直して再アップする。
        rows = st.session_state.result_rows
        meter_data = st.session_state.get('result_meter', {'rows': [], 'total': 0})
        nippou_data = st.session_state.get('result_nippou', {'rides': []})
        valid = st.session_state.result_valid
        diff = st.session_state.result_diff

        # メーターレシート品質チェック
        _meter_rows = meter_data.get('rows', [])
        _meter_no_list = [int(r.get('no', 0)) for r in _meter_rows]

        # ① 先頭5行の行番号が [1,2,3,4,5] と一致するか
        _first_5 = _meter_no_list[:5]
        _expected_head = [1, 2, 3, 4, 5]
        _top5_mismatch_count = sum(
            1 for i, n in enumerate(_first_5)
            if i < len(_expected_head) and n != _expected_head[i]
        )
        # 先頭5行のうち2件以上が連番からズレていれば異常（5件未満ならスキップ）
        _top5_invalid = len(_first_5) >= 5 and _top5_mismatch_count >= 2

        # ② 総件数と最終行番号の乖離
        _meter_total_count = len(_meter_no_list)
        _meter_last_no = _meter_no_list[-1] if _meter_no_list else 0
        _no_count_gap = abs(_meter_total_count - _meter_last_no) if _meter_no_list else 0
        _count_diverged = _meter_no_list and _no_count_gap >= 3

        if _meter_rows and (_top5_invalid or _count_diverged):
            _reasons = []
            if _top5_invalid:
                _reasons.append(
                    f'先頭5行の行番号が連番になっていません（読み取り: {_first_5}、期待: [1,2,3,4,5]）'
                )
            if _count_diverged:
                _reasons.append(
                    f'抽出行数（{_meter_total_count}件）と最終行番号（No.{_meter_last_no}）が乖離しています（差 {_no_count_gap}）'
                )
            _bullets = '\n'.join('- ' + r for r in _reasons)
            st.error(
                f'### ⚠️ メーターレシートの読み取りに問題があります\n\n'
                f'{_bullets}\n\n'
                f'正しいメーターレシートの写真か確認して再アップしてください。'
            )
            st.button('🔄 写真を再アップする', on_click=reset_app, key='reupload_meter_btn', use_container_width=True)

        # 行番号連番チェック（内部欠番の検出: 例 1,2,4,5 で 3 が抜けるケース）
        _seq_ok, _missing_nos = validate_meter_sequence(meter_data)
        if not _seq_ok:
            st.warning(
                f'メーター明細の行番号に欠番があります（欠番: {_missing_nos}）。'
                f'写真の途中行が読み取れていない可能性があります。'
            )

        # 乖離チェック（写真誤り検知）
        # 最終テーブル (build_report 後) で本当に未カバーだったメーター行だけを数える。
        # AI が meter_no を読めなくても amount/time マッチで揃ったケースを
        # 「100% 乖離」と誤判定して下の「✅ 読み取り完了」と矛盾する事故を防ぐ。
        _missing_rows = [r for r in rows if r.get('state') == 'missing_nippou']
        _missing_count = len(_missing_rows)
        _missing_amount = sum(int(r.get('meter_amount') or 0) for r in _missing_rows)
        _meter_count = len(_meter_rows)
        _meter_total = int(meter_data.get('total') or sum(int(r.get('amount', 0)) for r in _meter_rows))
        _gap_rate = (_missing_amount / _meter_total) if _meter_total > 0 else 0.0

        if _missing_count >= 3 or _gap_rate >= 0.30:
            st.error(
                f'### ⚠️ メーターレシートと日報の内容が大きく乖離しています\n\n'
                f'- メーター {_meter_count} 件中、日報に未記載が **{_missing_count} 件**\n'
                f'- 未カバー金額: **¥{_missing_amount:,}**（メーター合計の {_gap_rate*100:.0f}%）\n\n'
                f'手書きの日報に書かれている内容が正しいか確認して、必要であれば修正して再アップしてください。'
            )
            st.button('🔄 写真を再アップする', on_click=reset_app, key='reupload_btn', use_container_width=True)
        elif _missing_count == 2:
            st.warning(
                f'日報に未記載のメーター行が 2 件あります（赤い 🔴 行）。書き漏れがないか確認してください。'
            )

        _result_class = 'result-card invalid' if not valid else 'result-card'
        st.markdown(f'<div class="{_result_class}">', unsafe_allow_html=True)

        if not valid:
            diff_abs = abs(diff)
            # 差額のパターンからヒントを推定
            hints = []
            if diff > 0:
                hints.append(f'出力合計が ¥{diff_abs:,} **多い** → 余分な金額が混入（+100 等の超過マーカーが二重計上された可能性）')
            else:
                hints.append(f'出力合計が ¥{diff_abs:,} **少ない** → 行の取りこぼし、または金額の桁を少なく読んだ可能性')
            # 似た数字ペアの差額パターン
            digit_swap_patterns = {
                300: '（例: 1,800 ↔ 1,500、3,000 ↔ 2,700 などの「3 と 2」「8 と 5」の取り違え）',
                500: '（例: 1,000 ↔ 1,500、2,500 ↔ 2,000 などの「0 と 5」の取り違え）',
                600: '（例: 1,800 ↔ 1,200 などの「8 と 2」の取り違え）',
                900: '（例: 1,000 ↔ 1,900 などの「0 と 9」の取り違え）',
                4000: '（例: 1,100 ↔ 5,100 などの千の位「1 と 5」の取り違え）',
            }
            for delta, hint in digit_swap_patterns.items():
                if diff_abs == delta:
                    hints.append(f'¥{delta:,} は典型的な誤読パターン {hint}')
                    break
            # 構造的失敗。yellow warning ではなく red error で「結果不整合」を強く表示
            st.error(
                f'### 🚨 この日報は完成していません — メーター額と合計が ¥{diff_abs:,} ズレています\n\n'
                + '\n'.join('- ' + h for h in hints)
                + '\n\n下の表で 🟠 mismatch / 🔴 未記載 の行を確認し、'
                + '「✎ 訂正」セクションから修正してください。'
                + '訂正すると合計が自動で再計算されます。'
            )

        # 表示順序を厳守:
        #   1. render_summary（件数・現収・未収・総収・消費税・税抜）
        #   2. render_detail_table（日報の行一覧）
        #   この後: 整合性チェック → デバッグ expander → リセットボタン
        ken, nin, gen, mi, sou, tax, net = aggregate_totals(rows)
        render_summary(ken, nin, gen, mi, sou, tax, net)
        render_detail_table(rows)
        # テーブルが長い場合に下スクロール後でも集計が見えるよう、テーブル直後にも再表示
        st.markdown(f"""
    <div class="metric-grid-3" style="margin-top:12px;">
      <div class="metric"><p class="label">現収</p><p class="value">¥{gen:,}</p></div>
      <div class="metric"><p class="label">未収</p><p class="value">¥{mi:,}</p></div>
      <div class="metric dark"><p class="label">総収</p><p class="value">¥{sou:,}</p></div>
    </div>
    <div class="metric-grid-2">
      <div class="metric"><p class="label">消費税</p><p class="value">¥{tax:,}</p></div>
      <div class="metric"><p class="label">税抜運収</p><p class="value">¥{net:,}</p></div>
    </div>
    """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # 値の破壊検出（Stage1 vs 最終出力の整合性）
        # 各 meter_no について、メーター額とテーブル出力 (gen+mi) の合計が一致するか検証。
        # 障割（state='discount'）は nippou_amount を真値とする独立調整行のため、
        # メーター行の合算からは除外する（同じ '6+' ラベルでも overage と別扱い）。
        meter_amounts = {r['no']: int(r['amount']) for r in meter_data.get('rows', [])}
        sum_by_no = {}
        for r in rows:
            if r.get('state') == 'discount':
                continue  # 障割は独立した調整行、メーター額検証の対象外
            no = r.get('no')
            # メーター超過の "22+" のような string は元の meter_no に正規化して合算
            if isinstance(no, str) and no.endswith('+'):
                try:
                    no = int(no.rstrip('+'))
                except ValueError:
                    continue
            if no in meter_amounts:
                sum_by_no[no] = sum_by_no.get(no, 0) + int(r.get('gen') or 0) + int(r.get('mi') or 0)
        integrity_issues = []
        for no, meter_amt in sorted(meter_amounts.items()):
            actual = sum_by_no.get(no, 0)
            if meter_amt != actual:
                integrity_issues.append({
                    'no': no, 'meter': meter_amt, 'actual': actual,
                })

        if integrity_issues:
            st.error(f'🚨 値の破壊を検出（{len(integrity_issues)}件）: Stage 1 で読み取った金額とテーブル出力が一致していません')
            parts = ['<table class="detail-table"><thead><tr><th>No</th><th>Stage1メーター額</th><th>テーブル合計</th><th>差</th></tr></thead><tbody>']
            for it in integrity_issues:
                diff_v = it['actual'] - it['meter']
                parts.append(
                    f'<tr class="mismatch"><td>{it["no"]}</td>'
                    f'<td>¥{it["meter"]:,}</td>'
                    f'<td>¥{it["actual"]:,}</td>'
                    f'<td>{diff_v:+,}</td></tr>'
                )
            parts.append('</tbody></table>')
            st.markdown(''.join(parts), unsafe_allow_html=True)
            st.caption('差が出ている No について、下のデバッグセクションで Stage 1 の値と最終出力の値を照合してください。')

        # 「ユーザーが画面で見える問題」があるかどうかで導線を出し分ける。
        # 🟠/🔴 が出ていない＝後段の補完で揃ってる、ということなので
        # AI 内部のゆらぎ (meter_no 欠損等) を見せると「直せって言われても何のこっちゃ」になる。
        _visible_alerts = any(r.get('state') in ('mismatch', 'missing_nippou') for r in rows)
        _has_actionable = _visible_alerts or (not valid)

        _meter_issues = meter_data.get('issues', []) or []
        _nippou_issues = nippou_data.get('issues', []) or []
        _all_issues = _meter_issues + _nippou_issues

        if _all_issues and _has_actionable:
            # 内部用語 (meter_no / case / kind / build_report / index) は使わない。
            # ユーザーは「日報のどの行で何が起きたか」だけ分かればよい。
            # 注: 'missing_meter_no' は v1.16.01 で発生源を削除済（日報に No 列が
            # 存在しない前提なので、そもそも「読めず」という指摘自体が筋違いだった）。
            _ISSUE_LABELS = {
                'invalid_row': '行データが壊れていた',
                'missing_no': 'メーターの行番号が読めず',
                'missing_time': '時刻が読めず',
                'zero_amount': '金額が 0 円',
                'duplicate_no': '行番号が重複',
                'invalid_case': '入力区分が判別できず',
                'invalid_kind': '現/未の区別が判別できず',
                'split_missing_amounts': '分割払いの金額が空',
                'overage_missing_amount': '超過金額が空',
                'discount_missing_amount': '障割金額が空',
            }
            _USER_DETAILS = {
                'invalid_row': '行データが壊れていたため、その行はスキップしました。',
                'missing_no': '行番号が読み取れずスキップしました。',
                'missing_time': '時刻欄が空でした。',
                'zero_amount': '金額が 0 円でした（読み取り失敗の可能性）。',
                'duplicate_no': '同じ行番号が複数回出ています。',
                'invalid_case': '入力区分が分からず、通常として扱いました。',
                'invalid_kind': '現/未の区別が分からず、現収として扱いました。',
                'split_missing_amounts': '分割払いの内訳金額が両方とも空でした。',
                'overage_missing_amount': '超過金額が空でした。',
                'discount_missing_amount': '障割金額が空のため、この行を集計から除外しました。',
            }
            _STAGE_LABEL = {'meter': '🚕 メーター', 'nippou': '📝 日報'}

            def _to_user_where(where_str):
                """'index 0' / 'meter_no=5' / 'No.3' をユーザー表現に。"""
                s = where_str or ''
                m = re.match(r'^index (\d+)(.*)$', s)
                if m:
                    base = f'{int(m.group(1)) + 1} 行目'
                    tail = re.sub(r'\s*\(meter_no=[^)]*\)\s*', '', m.group(2) or '')
                    return base + tail
                m = re.match(r'^meter_no=(\S+)', s)
                if m:
                    v = m.group(1)
                    return f'No.{v}' if v.lower() != 'none' else '行未特定'
                return s

            with st.expander(f'⚠ 読み取りで気になった箇所（{len(_all_issues)} 件）', expanded=False):
                st.caption('AI が読み取り切れず、自動で補完した部分です。表で 🟠 🔴 を直せば一緒に解消します。')
                _issue_html = ['<table class="detail-table"><thead><tr><th>箇所</th><th>内容</th><th>処理</th></tr></thead><tbody>']
                for iss in _all_issues:
                    stage = _STAGE_LABEL.get(iss.get('stage'), iss.get('stage', ''))
                    type_lbl = _ISSUE_LABELS.get(iss.get('type'), iss.get('type', ''))
                    where = _to_user_where(iss.get('where', ''))
                    detail = _USER_DETAILS.get(iss.get('type'), '')
                    _issue_html.append(
                        f'<tr><td>{stage} / {where}</td>'
                        f'<td>{type_lbl}</td>'
                        f'<td>{detail}</td></tr>'
                    )
                _issue_html.append('</tbody></table>')
                st.markdown(''.join(_issue_html), unsafe_allow_html=True)

        # 完了導線:
        #   原則「次へ進む = 確定」。ユーザーが「次へ」を押したらアプリは結果を尊重する。
        #   紙の物理制約 (行追加不可・修正ペン無し・斜線で AI が混乱する) を考えると、
        #   AI 読み違いの場合まで再アップロードを強制するのは詰みパターン。
        #   気になる行 (🟠/🔴) は情報として表に残すが、行動は強制しない。
        if _has_actionable:
            st.markdown(
                '<div style="background:rgba(212,175,55,0.10);'
                'border:1px solid #d4af37;border-radius:8px;padding:14px 16px;'
                'margin:16px 0 8px;text-align:center;">'
                '<b>🟠 🔴 の行を確認してください</b><br>'
                '<small style="opacity:0.85">'
                '紙に書き漏れ・誤記があれば修正して再アップ。'
                '<br>AI の読み違いなら、このまま完了で OK です。'
                '</small>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background:rgba(212,175,55,0.10);'
                'border:1px solid #d4af37;border-radius:8px;padding:14px 16px;'
                'margin:16px 0 8px;text-align:center;">'
                '<b>✅ 読み取り完了 — このまま日報として使えます</b>'
                '</div>',
                unsafe_allow_html=True,
            )
        st.button('🔄 新しい日報を作成', on_click=reset_app, key='reset_btn', use_container_width=True)

        # 一般ユーザー向け UI はここで終わり。以下は開発者デバッグ用なので
        # デフォルトでは完全に隠す。「開発者メニュー」トグルを押した時だけ展開。
        if 'show_dev_menu' not in st.session_state:
            st.session_state.show_dev_menu = False

        def _toggle_dev_menu():
            st.session_state.show_dev_menu = not st.session_state.show_dev_menu

        _dev_label = (
            '🛠️ 開発者メニューを閉じる' if st.session_state.show_dev_menu
            else '🛠️ 開発者メニューを開く'
        )
        st.markdown('<div style="margin-top:32px;"></div>', unsafe_allow_html=True)
        st.button(
            _dev_label, on_click=_toggle_dev_menu, key='dev_menu_toggle',
            use_container_width=True,
        )

        if not st.session_state.show_dev_menu:
            st.stop()

        # ─── ここから下は開発者メニューが開いている時だけ表示 ───

        # Stage 1: メーター明細生データ
        with st.expander('🔧 Stage 1: メーター明細生データ'):
            meter_rows_disp = meter_data.get('rows', [])
            if meter_rows_disp:
                parts = ['<table class="detail-table"><thead><tr><th>No</th><th>時刻</th><th>金額</th></tr></thead><tbody>']
                for r in meter_rows_disp:
                    parts.append(f'<tr><td>{r["no"]}</td><td>{r["time"]}</td><td>¥{r["amount"]:,}</td></tr>')
                parts.append('</tbody></table>')
                st.markdown(''.join(parts), unsafe_allow_html=True)
                st.markdown(f'**合計**: ¥{sum(int(r.get("amount", 0)) for r in meter_rows_disp):,}（{len(meter_rows_disp)}行）')
            else:
                st.info('メーター明細データなし')
            compact = '  '.join(f'**{r["no"]}**:{r["amount"]:,}' for r in meter_rows_disp)
            st.markdown(f'📋 **OCR数値一覧:** {compact}')
            st.markdown('**生 JSON:**')
            st.json(meter_data)

        # Stage 2: 日報分類生データ
        with st.expander('🔧 Stage 2: 日報分類生データ'):
            rides = nippou_data.get('rides', [])

            def _ride_amount_cell(r):
                """case ごとに表示する金額情報を組み立てる。"""
                c = r.get('case') or 'normal'
                if c == 'split':
                    g = r.get('gen_amount') or 0
                    m = r.get('mi_amount') or 0
                    return f'現{g:,}+未{m:,}'
                if c == 'overage':
                    o = r.get('overage_amount') or 0
                    n = r.get('nippou_amount')
                    base = f'¥{n:,}' if isinstance(n, (int, float)) else '?'
                    return f'{base} (+{o})'
                # normal / discount
                n = r.get('nippou_amount')
                return f'¥{n:,}' if isinstance(n, (int, float)) else ''

            def _ride_compact(r):
                """1 行コンパクト表示。"""
                no = r.get('meter_no')
                c = r.get('case') or 'normal'
                if c == 'split':
                    return f'**{no}**:{r.get("gen_amount", 0)}+{r.get("mi_amount", 0)}(分割)'
                amt = r.get('nippou_amount')
                kind_initial = (r.get('kind') or '?')[0]
                return f'**{no}**:{amt if amt is not None else "?"}({kind_initial})'

            # Stage A: AI が抽出した raw_rows（両欄が捕捉できているか確認）
            raw_rows_disp = nippou_data.get('raw_rows') or []
            if raw_rows_disp:
                st.markdown('**📥 Stage A: AI 抽出 raw（列構造を保ったまま上から順）:**')
                parts = ['<table class="detail-table"><thead><tr><th>順</th><th>time</th><th>人数</th><th>現収欄</th><th>未収欄</th><th>memo</th><th>消線</th></tr></thead><tbody>']
                for idx, raw in enumerate(raw_rows_disp, start=1):
                    gc = raw.get('gen_cell')
                    mc = raw.get('mi_cell')
                    gc_disp = '<span style="color:#c33">{}</span>'.format(gc) if isinstance(gc, str) and gc.startswith('+') else (str(gc) if gc is not None else '<span style="color:#999">—</span>')
                    mc_disp = str(mc) if mc is not None else '<span style="color:#999">—</span>'
                    st_mark = '✓' if raw.get('strikethrough') else ''
                    parts.append(
                        f'<tr><td>{idx}</td>'
                        f'<td>{raw.get("time") or ""}</td>'
                        f'<td>{raw.get("passengers", "")}</td>'
                        f'<td>{gc_disp}</td>'
                        f'<td>{mc_disp}</td>'
                        f'<td>{raw.get("memo", "")}</td>'
                        f'<td>{st_mark}</td></tr>'
                    )
                parts.append('</tbody></table>')
                st.markdown(''.join(parts), unsafe_allow_html=True)
                st.caption('赤い "+N" は メーター超過の自腹補填マーカー。両欄に値があれば自動で split 判定されます。')

            # Stage B: Python が解釈した rides
            if rides:
                st.markdown('**🧠 Stage B: Python 解釈後 rides:**')
                parts = ['<table class="detail-table"><thead><tr><th>meter_no</th><th>人数</th><th>kind</th><th>memo</th><th>case</th><th>金額</th></tr></thead><tbody>']
                for r in rides:
                    parts.append(
                        f'<tr><td>{r.get("meter_no", "")}</td>'
                        f'<td>{r.get("passengers", "")}</td>'
                        f'<td>{r.get("kind", "")}</td>'
                        f'<td>{r.get("memo", "")}</td>'
                        f'<td>{r.get("case", "")}</td>'
                        f'<td>{_ride_amount_cell(r)}</td></tr>'
                    )
                parts.append('</tbody></table>')
                st.markdown(''.join(parts), unsafe_allow_html=True)
            else:
                st.info('日報の分類データなし')

            st.markdown('**生 JSON:**')
            compact2 = '  '.join(_ride_compact(r) for r in rides)
            st.markdown(f'📋 **日報数値一覧:** {compact2}')
            st.json(nippou_data)

        # Stage 3: build_report 入出力
        with st.expander('🔧 Stage 3: build_report 入出力'):
            st.markdown('**No ごとの突き合わせ（Stage1金額 vs テーブル出力）:**')
            parts = ['<table class="detail-table"><thead><tr><th>No</th><th>Stage1金額</th><th>出力 gen</th><th>出力 mi</th><th>出力合計</th><th>state</th><th>memo</th></tr></thead><tbody>']
            for r in rows:
                no = r.get('no')
                meter_amt = meter_amounts.get(no)
                meter_amt_disp = f'¥{meter_amt:,}' if isinstance(meter_amt, int) else '-'
                gen_v = int(r.get('gen') or 0)
                mi_v = int(r.get('mi') or 0)
                total = gen_v + mi_v
                cls = ''
                if r.get('state') == 'mismatch':
                    cls = ' class="mismatch"'
                elif r.get('state') == 'special':
                    cls = ' class="special"'
                parts.append(
                    f'<tr{cls}><td>{no}</td>'
                    f'<td>{meter_amt_disp}</td>'
                    f'<td>¥{gen_v:,}</td>'
                    f'<td>¥{mi_v:,}</td>'
                    f'<td>¥{total:,}</td>'
                    f'<td>{r.get("state", "")}</td>'
                    f'<td>{r.get("memo", "")}</td></tr>'
                )
            parts.append('</tbody></table>')
            st.markdown(''.join(parts), unsafe_allow_html=True)

            st.markdown('**report_rows 生 JSON:**')
            st.json(rows)

    st.stop()

new_files = st.file_uploader('日報と営業明細書をアップしてください', type=['jpg','jpeg','png','heic'], accept_multiple_files=True, key=f"uploader_{st.session_state.uploader_counter}")

if new_files:
    # size は重複検出用に元アップロードサイズを保持（bytes は正規化済みなので size と一致しない）
    existing_keys = {(kf['name'], kf['size']) for kf in st.session_state.kept_files}
    added = False
    for f in new_files:
        key = (f.name, f.size)
        if key not in existing_keys:
            normalized = normalize_upload_bytes(f.getvalue())
            st.session_state.kept_files.append({'name': f.name, 'size': f.size, 'bytes': normalized})
            added = True
    if added:
        st.session_state.uploader_counter += 1
        st.rerun()

imgs = []
if st.session_state.kept_files:
    cols = st.columns(len(st.session_state.kept_files))
    for i, kf in enumerate(st.session_state.kept_files):
        # 受信時に fix_orientation 済みなのでここでは不要、Image.open のみで OK
        img = Image.open(io.BytesIO(kf['bytes']))
        imgs.append(img)
        with cols[i]:
            st.image(img, use_container_width=True)
            if st.button('✕ 削除', key=f'del_{i}'):
                st.session_state.kept_files.pop(i)
                st.rerun()

if len(imgs) == 2:
    if st.button('🔍 日報を完成させる', use_container_width=True, type='primary'):
        loader = st.empty()
        # 新パイプライン開始 → ローダー前回値をリセット
        # (前回完了で 100 が残ってると、新規 3% との差分アニメで戻る挙動になる)
        st.session_state['_loader_prev_pct'] = 0
        try:
            api_key = os.environ.get('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY')
            client = anthropic.Anthropic(api_key=api_key)
            report_rows, valid, diff, meter_data, nippou_data = run_pipeline(client, imgs, loader)
            show_loader(loader, 100, '完成しました', anim_class='exiting')
            time.sleep(0.3)
            loader.empty()
            st.session_state.result_rows = report_rows
            st.session_state.result_valid = valid
            st.session_state.result_diff = diff
            st.session_state.result_meter = meter_data
            st.session_state.result_nippou = nippou_data
            st.rerun()  # if/else 分岐を再評価し、結果ブロックを即時表示（2回押し回避）
        except Exception as e:
            loader.empty()
            _clear_results()
            if isinstance(e, RuntimeError):
                st.error(str(e))
            elif isinstance(e, (json.JSONDecodeError, ValueError)):
                # JSON 抽出失敗または JSON が見つからない (_ocr_claude / classify_nippou が raise)
                st.error(f'AI応答のJSON解析に失敗しました: {e}\nもう一度お試しください。')
            else:
                st.error(f'処理中にエラーが発生しました: {type(e).__name__}: {e}')
elif st.session_state.kept_files and len(st.session_state.kept_files) != 2:
    st.warning(f'2枚選択してください（現在{len(st.session_state.kept_files)}枚）')

with st.expander('？ このアプリについて・使い方'):
    st.markdown('''
### 1. 日報の書き方ルール
このアプリを正しく使うには、手書き日報の書き方にルールがあります。

- **通常の乗車（現金）**：現収欄に金額を記入。未収欄は空欄のまま。
- **通常の乗車（カード・電子マネー等）**：未収欄に金額を記入。現収欄は空欄。
- **使用しない欄（現収・未収）**：空欄のまま、または横線（―）を引く。
  どちらでも正しく読み取ります。
- **障害者割引（障割）**：
  - 1行目：割引後の乗客支払い額を現収または未収欄に記入（支払い方法による）
  - 2行目（別段）：割引額を未収欄に記入。摘要欄に「障割」と明記。
- **メーター超過（消し忘れ）**：超過分を現収で別行追加（自己負担で会社納金）。

### 2. 使い方
1. 写真2枚をアップ（手書き日報＋営業明細書）
2. 「日報を完成させる」を押す
3. 待つ。完成。

### 3. このアプリについて
- **なぜ生まれたか**：日報入力に毎日10分、年間60時間以上の単純作業
- **AIが代わりにやること**：手書き文字解読、画像照合、業務ルール判断、自動計算
- **何がすごいか**：OCRではなくAIが画像を「理解」、数年前まで研究段階だった技術

### 4. プライバシー
写真はこのアプリのサーバーに保存されません。AI処理元（Anthropic社）に一時送信されますが、学習には使われず、30日以内に自動削除されます。

### 5. 更新履歴
- **v1.15.00** (2026-05-14): constraint-aware OCR を導入。日報 OCR に メーター情報を参考として渡し、AI が曖昧な手書き数字 (8 vs 5 等) でメーター値と整合する候補を選べるように。auto-correct ではなく digit disambiguation のための補助情報。パイプラインは parse_meter → classify_nippou の sequential 構成に変更 (+3〜5 秒遅延の引き換えに OCR 精度向上)
- **v1.14.00** (2026-05-14): アラインメント大改修 + 列構造のデータ宣言化。日報には「No 列」が無いという前提を反映し、v1.10.00 の「AI に No 列を読ませる」設計を撤去（AI が 人数 列を meter_no と誤読してたのが mismatch 多発の原因）。NIPPOU_COLUMNS リストで列を一元管理、プロンプトは自動生成。アラインメントは「金額一致 → 時刻 tie-break → 順番 fallback」の amount-first 方式に。新しい列を足す時は COLUMNS に 1 行追加で済む構造に
- **v1.13.01** (2026-05-14): 「テーブルの数値はメーター（正解）を表示する」原則に再修正。v1.13.00 で mismatch 行に AI 読み取り値を出していたのを撤回。アプリの役割は「数字を訂正する」ではなく「紙のミスを指摘する」なので、集計はメーター値で確定し、状態列に「🟠 紙の数字 ¥X → ¥Y」形式で「紙の違う値 → メーター正解」を併記する形に
- **v1.13.00** (2026-05-14): 訂正 UX を「視覚情報だけで完結」に再構築。セルタップ機構を全撤去（タップで状態消失する不具合も同時解消）、ダイアログ廃止。状態列を「🟠 メーター ¥1,600」「🔴 未記載・¥1,000 を書く」のように具体化して、行を一目見れば「何が間違ってるか」「紙に何を書くか」が分かるように。同じ情報を別パネルに重複させず、再アップ導線を金色枠で唯一のアクションに
- **v1.12.01** (2026-05-14): ローダーの体感修正。「数字が戻る」「途中で止まる」の 2 つを構造修正。前回完了値が残った状態の新パイプラインで戻るアニメが起きていたのを即時ジャンプに変更 + 新パイプライン開始時にリセット。creep に追いついて停滞する問題を drift モード（250ms に 1）で解消、「絶対に止まらない」体感に
- **v1.12.00** (2026-05-14): アプリのミッションを「手書き日報を完成させるサジェストツール」に純化。iterative ループ（写真 → サジェスト → 手書き日報を直す → 再アップ → 確認）が本質。デジタル編集機構を全撤去し、ダイアログを read-only のサジェスト表示に。mismatch / missing_nippou の理由別に「桁違い」「現収未収取り違え」「+100 自腹漏れ」等の具体的ヒントを表示。アプリが「直されたフリ」をしなくなった
- **v1.11.00** (2026-05-14): 訂正 UX を「手書き日報を直す助言者」モデルに再構築。テーブル下の訂正専用セクションを撤去、編集可能セル（missing_nippou / mismatch / edited）をテーブル内で直接タップ可能に（同じ項目が 2 箇所に出る冗長性を解消）。ダイアログも「デジタル編集」から「手書き日報のここに何を書くか」フレームへ書き換え。アプリの本質「手書き日報の苦しみ解消」を UI に反映
- **v1.10.05** (2026-05-14): ローダーが API 待ちで止まって見える問題を UX 修正。`_poll_until_done` に creep ロジック導入し、50ms に 1 ずつ進めて実 target より少し先行表示するように。実 future 完了で追従、フェーズ末尾 1 手前で頭打ち。「処理中なのに数字が止まる」体感を解消
- **v1.10.04** (2026-05-14): ローダーを「1 ずつ滑らかに動く」に確実対応。iOS Safari の counter() アニメ実装が中間値を表示しない制限が判明したため、CSS アニメではなく Python 側で 20ms 刻みに pct を送る方式に切替（前回値は session_state で管理、再パイプライン時は自動リセット）。アラート文「写真が正しいか…」を「手書きの日報に書かれている内容が正しいか…」に変更
- **v1.10.03** (2026-05-14): v1.10.02 のローダーが 3% で止まる症状を構造修正。原因は CSS @keyframes が要素新規作成時しか発火しないこと（Streamlit は属性更新で済ませるので発火せず）。CSS transition に置換することで値変更ごとに自動再発火するように。% は数字の底辺合わせに変更。show_loader から状態管理コードも撤去でシンプル化
- **v1.10.02** (2026-05-14): ローダー UI 改善試作（@keyframes 版、3% で止まるバグあり、v1.10.03 で構造修正）
- **v1.10.01** (2026-05-14): 「+100」マーカーを構造的に「メーター超過」として解釈するよう修正。これまで「+100」を普通の数字と同等扱いして split になっていた行（例: Row 16）が、v1.5.03 までと同じく「客の支払い（未収 1500 Uber）」+「メーター超過（現収 100 special、Row 16+）」の 2 行に正しく分解されるように。さらに訂正セクションとダイアログ内の文字が暗背景に埋もれて見えなかった CSS バグも修正
- **v1.10.00** (2026-05-14): 構造修正。AI の `meter_no` を一次アラインメント信号に戻す（v1.5.03 までの挙動）。v1.9.x で金額一致だけで推測する設計が破綻し「+100 が 1 行下にズレる」現象が再発していたのを根本から解決。AI に日報最左端「No」列の手書き行番号を読ませ、Python は直接対応 meter 行に割当てる。さらに validate 失敗時は合計タイルを赤背景に切替えて「OK っぽい見た目」を絶対に出さないようにした
- **v1.9.02** (2026-05-14): 重大バグ修正。問題サマリ表示の内部変数衝突で Stage 2 デバッグ expander と「新しい日報を作成」ボタンが描画されない症状を解消。さらに、AI が「+100」マーカーを取りこぼしてもメーター額との差が典型的な超過幅なら現位置に割り当てるセーフティネットを追加（v1.10.00 で構造修正に置き換え）
- **v1.9.01** (2026-05-14): メーター超過の自腹補填パターン（現収=+100, 未収=1500）の取りこぼし対策。プロンプトで「+N」を絶対に省略しないよう強化、AI が旧形式を返してきても受け止める後方互換層を追加、空 raw でも meter_no があれば alignment 維持。デバッグ画面に AI が両欄を捕捉できたか即確認できる Stage A/B 二段表示を追加
- **v1.9.00** (2026-05-14): AI と Python の役割を完全分離。AI は日報のセルを純粋抽出するだけ、判定（分割払い、障害者割引、からまわし等）は Python の独立関数群が行う。これで AI の幻覚や判定漏れが構造的に起こせない設計に
- **v1.8.00** (2026-05-14): ユーザー訂正 UI を追加。AI が自信を持てなかった行をテーブル下に並べ、タップでダイアログを開いて種別 (通常/分割)・金額・人数・摘要を 30 秒で訂正できる。OCR を再実行せずに完成形にできる
- **v1.7.05** (2026-05-14): AI プロンプトの判定順序を再構成。「分割払い」(現収・未収両方に数字) の判定を最優先に。メーター回し過ぎでドライバー自腹補填のケースも明示し、「から回し」(空乗車) との区別を明確化
- **v1.7.04** (2026-05-14): アライメント精度向上。missing_nippou 判定を金額完全一致のみに厳格化して誤検出を抑制。日報に書いてあるのに「未記載扱い」されるケースを解消。split 判定も強化し、メーター回し過ぎでドライバー自腹補填のケース（現金+未収）も split として正しく分類
- **v1.7.03** (2026-05-14): UI 微調整。ファイルアップロード欄の英語デフォルト文を隠してテキストを短くし、行折り返しを解消。mismatch 行では現収・未収両方じゃなく値が入っている側のセルだけピンクで強調
- **v1.7.02** (2026-05-14): 日報に未記載の行も「現収」と自動で仮置きして合計が成立するように。kind 不明でも合計が狂わない。後で実際は未収だったら訂正可能。「計算したくない」を最優先
- **v1.7.01** (2026-05-14): アラインメントを「時刻 + 金額」のダブルシグナル化。AI が日報の降車時刻も拾うようにし、片方が欠けてももう一方で揃えられる。日報に未記載の行は真っ赤背景 + 白文字で目立つ表示に
- **v1.7.00** (2026-05-14): build_report をメーターマスター設計に再構築。日報の rides 数に依存せず必ずメーター行数と同じ件数を出力。日報に対応がない行は黄色で「日報に未記載」表示。問題パネルに「Row X に記載が無い」と具体的に提示
- **v1.6.00** (2026-05-14): Stage1/2 出力を堅牢化。AI 出力に欠損や型不正があってもパイプラインが破綻せず、検出した問題を「⚠ 読み取り時に検出された問題」パネルに一覧表示
- **v1.5.03** (2026-05-12): 分割払い（現金+チケット併用等）に対応。1乗車で現収・未収両方に金額が書かれている場合を case="split" として正しく集計。合計がメーター額と一致すれば OK、ズレれば mismatch ハイライト
- **v1.5.02** (2026-05-12): 立ち上がり体感の改善。Streamlit テーマを濃紺＋ダーク基調に設定し、ロード画面の段階から最終形と同じ背景色になるようにした（白フラッシュ撲滅）。実時間は変わらないが「スパッと開いた」感じに
- **v1.5.01** (2026-05-12): メーター明細 OCR の JSON 構造化を Opus 4.5 → Sonnet 4.6 に変更（実測で完全同等の出力、コスト 1/5）。Vision API が読み取った印字テキストを JSON 化するだけのタスクで精度は落ちない設計
- **v1.5.00** (2026-05-12): A/B 検証用コードと Gemini 経路を撤去（本番構成確定済）。パイプラインを 3 並列化（鮮明度＋OCR＋日報を同時処理）+ ローダーを全段ポーリング型に統一して「途中で固まって見える」問題を解消
- **v1.4.01** (2026-05-11): 精度検証の結果、日報は Claude Opus 4.5 維持で確定（Gemini/Sonnet/Opus 4.7 / Caching すべて出力ズレあり）。コスト削減は価格設計で吸収する方針へ
- **v1.4.00** (2026-05-11): 日報分類もプロバイダ抽象化（`[nippou] provider` で claude/gemini 切替、`compare_mode` で A/B 比較）。identify/clarity を Gemini 優先化。1 枚 $0.30 → $0.002 想定（要 A/B 検証）
- **v1.3.01** (2026-05-11): アップロード後の体感速度を改善（受信時に 3000px JPEG に正規化、5〜8MB → 0.5〜1MB 化）。API コスト・OCR 精度は不変。
- **v1.3.00** (2026-05-11): OCR プロバイダ抽象化（Vision+Claude / Gemini / Claude を `[ocr] provider` で切替、失敗時は Claude 単独に自動フォールバック）
- **v1.2.04** (2026-05-11): イントロスプラッシュ撤去（v1.2.00〜v1.2.03 を巻き戻し）
- **v1.2.03** (2026-05-11): FOUC 対策（UI 一瞬見え解消）・AI / TAXI NIPPOU の視覚中心揃え
- **v1.2.02** (2026-05-11): イントロ演出を 4 フェーズの滑らかな遷移に再設計（粒子先行 → AI登場 → 静止 → グラデーション溶解）
- **v1.2.01** (2026-05-11): イントロ調整（背景完全カバー・AI 白グロー・文字拡大・粒子先行）
- **v1.2.00** (2026-05-11): イントロスプラッシュ追加（AI / TAXI NIPPOU と粒子の演出、3秒で自動フェード）
- **v1.1.04** (2026-05-11): バージョン表記を 2 桁ゼロパディングに統一（例: 1.1.4 → 1.1.04）
- **v1.1.03** (2026-05-11): README.md 整備（プロジェクトの全記録ドキュメント）
- **v1.1.02** (2026-05-11): 速度改善（画像エンコードのキャッシュ化）、dead code 削除
- **v1.1.01** (2026-05-11): 表示の微調整（バージョン番号拡大・タイトル下余白削減・完成バー拡大）
- **v1.1.00** (2026-05-11): 障害者割引（障割）対応の本格実装、整合性チェック修正、税抜運収の表示修正など
- **v1.0.00** (2026-05-10): 初回リリース

作者＞怒りの山本
''')
