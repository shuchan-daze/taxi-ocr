# AI タクシー日報 OCR
# バージョンは下の __version__ 定数で一元管理 (UI 表示・コメント・CHANGELOG リンクすべてこれを参照)
# 変更履歴: CHANGELOG.md を参照
# バージョニング: SemVer 2.0 (MAJOR.MINOR.PATCH、PATCH は 2 桁ゼロパディング)
# テスト: tests/README.md を参照 (pytest で純ロジック 78 件、E2E は環境変数で有効化)
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

# バージョン定数 (一元管理、ここを更新するだけで UI バナー・コメント・CHANGELOG リンクが追従)
__version__ = '1.26.05'

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
    /* 視覚的中心調整: 大きな数字 + 小さい % だと、% の幅 (0.28em) 分だけ
       数値が左に偏って見える。translateX で右へ 0.06em (= 140px 換算で約 8px)
       ずらして光学的中心を合わせる。em 単位なので画面/フォントサイズに自動追従。 */
    transform: translateX(0.06em);
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
/* charter: 貸切行。メーター明細に対応行が無い独立案件。ブランド金で視認性確保 */
.detail-table tr.charter td {background: rgba(212,175,55,0.18) !important; color: #f5e9c2 !important;}
.detail-table tr.charter:nth-child(even) td {background: rgba(212,175,55,0.26) !important;}
.detail-table tr.charter td:first-child {border-left: 4px solid #d4af37 !important;}

/* === AI エンジン八咫烏バッジ ===
   タイトルバー的に存在感を出す、半透明金背景 + 金細線 + ホバー時に微発光。
   バッジ全体がクリック可能で、押すと dialog が開く。
   実装: 視覚的にはバッジ HTML、クリック判定は直後に置く透明な Streamlit
   button を負マージンで重ねて拾う (negative-margin overlay trick)。 */
.yata-badge {
    margin-top: 32px;
    margin-bottom: 0;
    padding: 14px 18px;
    background: rgba(212, 175, 55, 0.08);
    border: 1px solid #d4af37;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 16px;
    transition: box-shadow 0.4s ease, background 0.4s ease;
    pointer-events: none;  /* クリック判定は overlay button に委ねる */
}
.yata-badge .yata-icon-img {
    width: 56px;
    height: auto;
    flex-shrink: 0;
    filter: drop-shadow(0 0 6px rgba(212, 175, 55, 0.4));
}
.yata-badge .yata-text {
    display: flex;
    flex-direction: column;
    flex: 1;
    line-height: 1.2;
}
.yata-badge .yata-text .label-small {
    color: rgba(212, 175, 55, 0.7);
    font-size: 9px;
    letter-spacing: 0.3em;
    font-weight: 500;
    margin-bottom: 4px;
}
.yata-badge .yata-text .label-main {
    color: #d4af37;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.05em;
}
.yata-badge .yata-text .label-en {
    color: rgba(212, 175, 55, 0.6);
    font-size: 9px;
    letter-spacing: 0.35em;
    margin-top: 3px;
    font-weight: 400;
}
/* バッジ全体をクリック可能にする透明 overlay (Streamlit ボタンの上に乗る) */
.st-key-yata_dialog_btn {
    margin-top: -94px !important;  /* バッジ上に乗せる */
    position: relative;
    z-index: 5;
    pointer-events: auto;
}
.st-key-yata_dialog_btn .stButton,
.st-key-yata_dialog_btn .stButton > button,
.st-key-yata_dialog_btn button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    min-height: 94px !important;
    height: 94px !important;
    padding: 0 !important;
    color: transparent !important;
    cursor: pointer !important;
}
.st-key-yata_dialog_btn .stButton > button:hover,
.st-key-yata_dialog_btn button:hover {
    background: rgba(212, 175, 55, 0.05) !important;
    box-shadow: 0 0 16px rgba(212, 175, 55, 0.3) !important;
    transform: none !important;
}
</style>
""", unsafe_allow_html=True)

# タイトルブロック（ページ最上部、常時表示。結果の有無に関わらず常に最上段）
# 版番号は __version__ 定数を参照 (上の import 群直下で定義)
st.markdown(f"""
<div class="title-block">
  <h1>AIタクシー日報<span style="font-size: 13px; color: #d4af37; font-weight: 400; margin-left: 8px;">by 怒りの山本</span></h1>
  <p class="subtitle">DAILY REPORT · OCR ASSIST</p>
  <div class="divider"></div>
  <p style="color: rgba(255,255,255,0.7); font-size: 14px; letter-spacing: 0.08em; margin: 4px 0 0; text-align: right;">v{__version__}</p>
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
    except (AttributeError, KeyError):
        # EXIF タグ未対応の画像形式 / 該当キー無し → 回転スキップで元画像返す
        pass
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
# AI には行番号は読ませない (実物の日報に No 列が無いため)。
# 各 ride はメーター行への紐付け属性を持たず、_align_rides_to_meter が
# 金額 + 時刻で対応 meter 行を判定する。
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
    {'name': 'paper_row',     'label': '紙日報の行番号 (1 始まり、紙の罫線で区切られた区画を上から数えた番号)', 'type': 'int'},
    {'name': 'time',          'label': '時間 (降車時刻)',         'type': 'time'},
    {'name': 'passengers',    'label': '人数',                  'type': 'int'},
    {'name': 'gen_cell',      'label': '現収欄',                'type': 'amount_or_marker'},
    {'name': 'mi_cell',       'label': '未収欄',                'type': 'amount_or_marker'},
    {'name': 'memo',          'label': '摘要',                  'type': 'string'},
    {'name': 'strikethrough', 'label': '乗車区間の取り消し線', 'type': 'boolean'},
    {'name': 'needs_review',  'label': 'AI の確信度 (この行に digit OCR の自信が無い・既知ケースに当てはまらない・memo が見慣れない時のみ true、それ以外は false)', 'type': 'boolean'},
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
        if c['name'] == 'paper_row':
            overage_example[c['name']] = '2'
        elif c['name'] == 'gen_cell':
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
【最重要: 日報は罫線で区切られた 2D グリッド (= データシート)】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

日報は **文字列の流れではなく、罫線で区切られた絶対座標のグリッド** です。
以下の前提を絶対に崩さないでください:

- **行数は紙の罫線の数で機械的に決まる**。あなたが「空白だから飛ばす」「数字が
  小さいから無視」と判断する権限はありません
- **罫線で区切られた区画は 1 つでも見逃さず、全て JSON の 1 オブジェクトとして
  出力する**。全セルが空欄でも、その区画は存在するので空オブジェクトを残す
- 数字が薄い・小さい・滲んでも、罫線内に何か書かれていればその行は値ありとして読む
- 行の見落としは致命的な失敗。罫線をスキャンする時は、上から下まで全ての横線間を
  漏らさず認識すること

各オブジェクトには `paper_row` フィールドを付け、紙の罫線で区切られた区画の
上からの番号 (1 始まり、空区画も含めて連番) を入れてください。
これは紙の物理的座標で、後段の Python プログラムが行の漏れを検出するのに使います。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【日報の列構造 (固定)】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

日報は表形式で、左から右に以下の列が並んでいます:

{field_lines}

各行はこの列構造を **必ず維持** したまま読み取ります。空欄はそのまま空 (null / "" / false)
として記録し、列を詰めたり順序を変えたりしないこと。

【行の順番】
- 日報に書かれている順序 (上から下) でそのまま配列に並べる
- `paper_row` フィールドは紙の罫線で区切られた区画番号 (1 始まり、連番)
- 乗務員が間にブランク行を入れていても、その行は飛ばさず空オブジェクトとして記録する
  (paper_row は連番のまま付与する)

【amount_or_marker の書き方 - 最重要】
- 「+100」「+200」のような追加表記は **そのまま文字列** で（例: "+100"）。「+」記号は
  乗務員が自腹でメーター超過を補填した重要情報。絶対に省略しない
- 通常の金額は数値で（例: 1500）
- 空欄 / 「-」だけ は null

【memo】
- 摘要欄に書かれた文字をそのまま (Visa / Uber / 現金 / 障割 / AMEX 等)
- 読めない文字は推測せず ""（空文字）。「たこ焼」のような幻覚は禁止

【needs_review — 自信シグナル】
- デフォルト false。**本当に自信が無い行だけ true**。
- true にする条件 (どれか):
  - digit が滲んで読めず推測で埋めた (例: 1090 か 1000 か明らかに分からない)
  - 既知の支払い種別・カテゴリ (現金/カード/Uber/Visa/JCB/AMEX/Suica/PASMO/PayPay/QP/障割/貸切 等) に該当しない見慣れない memo
  - セルに見慣れない文字 / 記号がある
  - 現収欄・未収欄の数字が部分的にしか読めない
- false にする条件:
  - 普通に読めた行 (大多数はこれ)
  - 何も書かれていない empty 行
- **過剰に true を付けない**。全行 true になると人間が確認できない。年に 1-2 行レベルの精度で。

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


# ─────────────────────────────────────────────────────────────────
# Layer 1: 行ハンドラのレジストリ
# ─────────────────────────────────────────────────────────────────
# 1 行の raw データを「中間表現 (interp dict)」に変換する責務。
# 新しいイレギュラーケースを増やす時は RowHandler を継承して
# ROW_HANDLERS リストに追加するだけ。中央の if-elif チェーンに
# 手を入れる必要は無い (= モジュール化、Shuchan の 3 レイヤー設計図に沿う)。

class RowHandler:
    """1 行の解釈を担当する基底クラス.

    サブクラスは name (識別子) と 2 メソッドを実装する:
      - detect(raw_row): このケースに該当する？ → bool
      - interpret(raw_row): 中間表現 (interp dict) を返す

    ROW_HANDLERS リストの上から順に detect が呼ばれ、最初に True を返した
    ハンドラの interpret 結果が採用される。優先順位を変えたい時はリストの
    並び順を変えるだけ。
    """
    name = None

    def detect(self, raw_row):
        return False

    def interpret(self, raw_row):
        raise NotImplementedError


class KaramawashiHandler(RowHandler):
    """からまわし: 取り消し線 + 現収に "+N" のみ、未収は空.
    → 直前の通常行に overage_amount を足す (interpret_raw_rows で処理)."""
    name = 'karamawashi'

    def detect(self, r):
        return (bool(r.get('strikethrough'))
                and _is_overage_marker(r.get('gen_cell'))
                and r.get('mi_cell') is None)

    def interpret(self, r):
        return {
            'type': 'karamawashi',
            'overage_amount': _parse_overage_marker(r.get('gen_cell')),
        }


class MeterOverageStandaloneHandler(RowHandler):
    """メーター超過 (新書式): memo に「メーター」キーワード、取り消し線なし、
    現収欄に数字、未収欄空 → 直前ライドの自腹補填分."""
    name = 'meter_overage_standalone'

    def detect(self, r):
        memo = (r.get('memo') or '').strip()
        if r.get('strikethrough') or 'メーター' not in memo:
            return False
        if r.get('mi_cell') is not None or r.get('gen_cell') is None:
            return False
        gen_int = _cell_to_int(r.get('gen_cell'))
        return gen_int is not None and gen_int > 0

    def interpret(self, r):
        return {
            'type': 'meter_overage_standalone',
            'overage_amount': _cell_to_int(r.get('gen_cell')),
        }


class CharterHandler(RowHandler):
    """貸切: 摘要に「貸切」を含む独立案件 (メーター不使用).
    現収/未収どちらに金額が入ってても拾う. ([[project-charter-rules]])"""
    name = 'charter'

    def detect(self, r):
        memo = (r.get('memo') or '').strip()
        return '貸切' in memo

    def interpret(self, r):
        memo = (r.get('memo') or '').strip()
        gen_int = _cell_to_int(r.get('gen_cell'))
        mi_int = _cell_to_int(r.get('mi_cell'))
        if gen_int is not None:
            kind, amount = '現収', gen_int
        elif mi_int is not None:
            kind, amount = '未収', mi_int
        else:
            kind, amount = '現収', None
        return {
            'type': 'charter',
            'time': r.get('time'),
            'passengers': r.get('passengers'),
            'kind': kind,
            'amount': amount,
            'memo': memo,
        }


class DiscountHandler(RowHandler):
    """障害者割引: memo に「障割」or「障害者」.
    1/9 リインバース行を独立行として扱う."""
    name = 'discount'

    def detect(self, r):
        return _is_discount_memo((r.get('memo') or '').strip())

    def interpret(self, r):
        memo = (r.get('memo') or '').strip()
        amt = _cell_to_int(r.get('mi_cell'))
        if amt is None:
            amt = _cell_to_int(r.get('gen_cell'))
        return {'type': 'discount', 'amount': amt, 'memo': memo}


class OverageHandler(RowHandler):
    """メーター超過: 現収欄に "+N" マーカー + (任意で) 未収に客払い額."""
    name = 'overage'

    def detect(self, r):
        return _is_overage_marker(r.get('gen_cell'))

    def interpret(self, r):
        memo = (r.get('memo') or '').strip()
        overage_amt = _parse_overage_marker(r.get('gen_cell'))
        mi_int = _cell_to_int(r.get('mi_cell'))
        if mi_int is not None:
            return {
                'type': 'overage',
                'time': r.get('time'),
                'passengers': r.get('passengers'),
                'kind': '未収',
                'customer_amount': mi_int,
                'overage_amount': overage_amt,
                'memo': memo,
            }
        # mi も空: 客の支払額不明、後段で推測
        return {
            'type': 'overage',
            'time': r.get('time'),
            'passengers': r.get('passengers'),
            'kind': '現収',
            'customer_amount': None,
            'overage_amount': overage_amt,
            'memo': memo,
        }


class SplitHandler(RowHandler):
    """分割払い: 現収・未収両欄に通常の数字 → 現金+カード等の併用."""
    name = 'split'

    def detect(self, r):
        return (_cell_to_int(r.get('gen_cell')) is not None
                and _cell_to_int(r.get('mi_cell')) is not None)

    def interpret(self, r):
        memo = (r.get('memo') or '').strip()
        return {
            'type': 'split',
            'time': r.get('time'),
            'passengers': r.get('passengers'),
            'gen': _cell_to_int(r.get('gen_cell')),
            'mi': _cell_to_int(r.get('mi_cell')),
            'memo': memo,
        }


class NormalHandler(RowHandler):
    """通常乗車 (フォールバック): 現収 or 未収の片方にだけ数字.
    現収欄に書いてあれば現収、未収欄なら未収. 摘要が空でも判定可能."""
    name = 'normal'

    def detect(self, r):
        return (_cell_to_int(r.get('gen_cell')) is not None
                or _cell_to_int(r.get('mi_cell')) is not None)

    def interpret(self, r):
        memo = (r.get('memo') or '').strip()
        gen_int = _cell_to_int(r.get('gen_cell'))
        mi_int = _cell_to_int(r.get('mi_cell'))
        if gen_int is not None:
            kind, amount = '現収', gen_int
        else:
            kind, amount = '未収', mi_int
        return {
            'type': 'normal',
            'time': r.get('time'),
            'passengers': r.get('passengers'),
            'kind': kind,
            'amount': amount,
            'memo': memo,
        }


# レジストリ (順序付き、上から順に評価).
# 新ケースはここに 1 行追加するだけ. NormalHandler は最後 (フォールバック).
ROW_HANDLERS = [
    KaramawashiHandler(),
    MeterOverageStandaloneHandler(),
    CharterHandler(),
    DiscountHandler(),
    OverageHandler(),
    SplitHandler(),
    NormalHandler(),
]


def _interpret_raw_row(raw_row):
    """1 行の raw データを「中間表現」に変換 (ハンドラレジストリ経由).

    返値: dict with 'type' key (各 RowHandler の interpret が返す形).
    どのハンドラも detect しなければ 'empty' (何も書かれてない行).

    新ケース追加は ROW_HANDLERS リストへの登録のみ. ここは触らない.
    """
    if not isinstance(raw_row, dict):
        return {'type': 'invalid', 'raw': raw_row}
    for handler in ROW_HANDLERS:
        if handler.detect(raw_row):
            return handler.interpret(raw_row)
    return {'type': 'empty'}


# ─────────────────────────────────────────────────────────────────
# Layer 1→2 の橋渡し: interp dict を rides リストに反映する RideBuilder
# ─────────────────────────────────────────────────────────────────
# Phase 2: type 分岐 (旧 if-elif 7 段) を Builder レジストリに置き換え。
# 新ケース追加は (1) RowHandler サブクラス + ROW_HANDLERS 登録 →
# (2) RideBuilder サブクラス + RIDE_BUILDERS 登録、の 2 手で完結する。

class RideBuilder:
    """interp dict を rides リストに反映する責務.

    サブクラスは type_name と build メソッドを実装する.
    build は副作用ベース (rides を mutate); 通常は append、karamawashi 系は
    直前の ride を更新する.
    """
    type_name = None

    def build(self, interp, raw, rides, needs_review):
        raise NotImplementedError


class AttachOverageBuilder(RideBuilder):
    """karamawashi / meter_overage_standalone: 独立行ではなく、
    直前の通常行/分割行に overage_amount を足す."""
    # type_name は使わず、登録時に複数 type にマッピング

    def build(self, interp, raw, rides, needs_review):
        if rides and rides[-1].get('case') in ('normal', 'split'):
            rides[-1]['case'] = 'overage'
            rides[-1]['overage_amount'] = interp.get('overage_amount') or 0
            if needs_review:
                rides[-1]['needs_review'] = True


class OverageRideBuilder(RideBuilder):
    """メーター超過: 客が支払った額を nippou_amount に、超過分を overage_amount に."""
    type_name = 'overage'

    def build(self, interp, raw, rides, needs_review):
        rides.append({
            'time': interp.get('time') or '',
            'passengers': interp.get('passengers'),
            'case': 'overage',
            'kind': interp.get('kind') or '未収',
            'nippou_amount': interp.get('customer_amount'),
            'overage_amount': interp.get('overage_amount') or 0,
            'memo': interp.get('memo') or '',
            'needs_review': needs_review,
        })


class DiscountRideBuilder(RideBuilder):
    """障害者割引: 独立行、未収側に計上."""
    type_name = 'discount'

    def build(self, interp, raw, rides, needs_review):
        rides.append({
            'case': 'discount',
            'nippou_amount': interp.get('amount'),
            'memo': interp.get('memo'),
            'needs_review': needs_review,
        })


class CharterRideBuilder(RideBuilder):
    """貸切: メーター外の独立案件."""
    type_name = 'charter'

    def build(self, interp, raw, rides, needs_review):
        rides.append({
            'time': interp.get('time') or '',
            'passengers': interp.get('passengers'),
            'case': 'charter',
            'kind': interp.get('kind') or '現収',
            'nippou_amount': interp.get('amount'),
            'memo': interp.get('memo') or '貸切',
            'needs_review': needs_review,
        })


class SplitRideBuilder(RideBuilder):
    """分割払い: 現金+カード等の併用."""
    type_name = 'split'

    def build(self, interp, raw, rides, needs_review):
        rides.append({
            'time': interp.get('time') or '',
            'passengers': interp.get('passengers'),
            'case': 'split',
            'gen_amount': interp.get('gen'),
            'mi_amount': interp.get('mi'),
            'memo': interp.get('memo') or '',
            'needs_review': needs_review,
        })


class NormalRideBuilder(RideBuilder):
    """通常乗車."""
    type_name = 'normal'

    def build(self, interp, raw, rides, needs_review):
        rides.append({
            'time': interp.get('time') or '',
            'passengers': interp.get('passengers'),
            'kind': interp.get('kind'),
            'case': 'normal',
            'nippou_amount': interp.get('amount'),
            'memo': interp.get('memo') or '',
            'needs_review': needs_review,
        })


# レジストリ: type_name → builder.
# karamawashi と meter_overage_standalone は同じ AttachOverageBuilder で処理.
_attach_overage = AttachOverageBuilder()
RIDE_BUILDERS = {
    'karamawashi': _attach_overage,
    'meter_overage_standalone': _attach_overage,
    'overage': OverageRideBuilder(),
    'discount': DiscountRideBuilder(),
    'charter': CharterRideBuilder(),
    'split': SplitRideBuilder(),
    'normal': NormalRideBuilder(),
}


def interpret_raw_rows(raw_rows):
    """raw_rows → rides リストに変換 (RowHandler + RideBuilder の合成).

    新ケース追加は ROW_HANDLERS と RIDE_BUILDERS への登録のみで済む.
    この関数本体は触らない.

    paper_row (紙の絶対座標) は ride にそのまま伝播される. これによって
    後段の処理が「紙の N 行目に対応する ride」を番地で参照できる
    ([[座標ベース設計 — Shuchan の哲学]]).

    'empty' / 'invalid' / 未登録 type は黙ってスキップ (= 空行や読み取り不能行).
    """
    rides = []
    for raw in (raw_rows or []):
        if not isinstance(raw, dict):
            continue
        interp = _interpret_raw_row(raw)
        t = interp.get('type')
        builder = RIDE_BUILDERS.get(t)
        if builder is None:
            continue  # empty / invalid / 未登録 type
        needs_review = bool(raw.get('needs_review'))
        rides_before = len(rides)
        builder.build(interp, raw, rides, needs_review)
        # paper_row を新規追加 ride に伝播 (karamawashi のような前 ride 更新型は除く)
        if len(rides) > rides_before:
            paper_row = raw.get('paper_row')
            if paper_row is not None:
                rides[-1]['paper_row'] = paper_row
    return rides


def validate_paper_row_continuity(raw_rows):
    """paper_row が連番か検証 (1 から始まる連続整数).

    AI が紙の罫線で区切られた区画を見落とすと paper_row が不連続になる.
    これを検出して issues として返す.

    返値: list of issue dicts (空なら全て連番).
    """
    issues = []
    if not raw_rows:
        return issues
    seen = []
    for idx, raw in enumerate(raw_rows):
        if not isinstance(raw, dict):
            continue
        pr = raw.get('paper_row')
        if isinstance(pr, int):
            seen.append(pr)
    if not seen:
        return issues
    seen.sort()
    expected = list(range(seen[0], seen[0] + len(seen)))
    if seen != expected:
        # 不連続: 欠番を特定
        missing = []
        for n in range(seen[0], seen[-1] + 1):
            if n not in seen:
                missing.append(n)
        issues.append({
            'stage': 'nippou',
            'type': 'paper_row_gap',
            'detail': f'紙日報の paper_row が不連続。欠番: {missing} (AI が行を見落とした可能性)',
            'missing': missing,
        })
    return issues


_VALID_CASES = {'normal', 'overage', 'discount', 'split', 'charter'}


def _finalize_rides(rides):
    """rides -> {rides, issues} に正規化。
    AI 出力の欠損・null・型不正をここで吸収。下流の build_report が安全に動く保証を作る。
    issues の where は `index N` 形式 (rides 配列の位置)。AI は日報に No 列を読ませない
    設計なので、ride 自体には行番号属性は無い。
    """
    rides = rides or []
    normalized = []
    issues = []
    for idx, r in enumerate(rides):
        where = f'index {idx}'
        if not isinstance(r, dict):
            issues.append({'stage': 'nippou', 'type': 'invalid_row', 'where': where,
                           'detail': f'行データが dict ではない: {type(r).__name__}'})
            continue
        case = r.get('case') or 'normal'
        if case not in _VALID_CASES:
            issues.append({'stage': 'nippou', 'type': 'invalid_case', 'where': where,
                           'detail': f'未知の case 値「{case}」→ normal として扱う'})
            case = 'normal'
        passengers = _coerce_int(r.get('passengers'), default=1) or 1
        if passengers < 0:
            passengers = 1
        kind = r.get('kind') or '現収'
        if case in ('normal', 'overage', 'charter') and kind not in ('現収', '未収'):
            issues.append({'stage': 'nippou', 'type': 'invalid_kind', 'where': where,
                           'detail': f'kind 値が不正「{kind}」→ 現収 として扱う'})
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
                issues.append({'stage': 'nippou', 'type': 'split_missing_amounts', 'where': where,
                               'detail': 'split なのに gen_amount/mi_amount 両方欠損'})
        elif case == 'overage':
            if overage_amount is None or overage_amount <= 0:
                issues.append({'stage': 'nippou', 'type': 'overage_missing_amount', 'where': where,
                               'detail': 'overage なのに overage_amount が無効'})
        elif case == 'discount':
            if nippou_amount is None or nippou_amount <= 0:
                issues.append({'stage': 'nippou', 'type': 'discount_missing_amount', 'where': where,
                               'detail': 'discount なのに nippou_amount が無効、行スキップ'})
                continue  # 金額が無い障割は集計不能、データ破棄
        elif case == 'charter':
            if nippou_amount is None or nippou_amount <= 0:
                issues.append({'stage': 'nippou', 'type': 'charter_missing_amount', 'where': where,
                               'detail': 'charter なのに nippou_amount が無効、行スキップ'})
                continue  # 金額が無い貸切は集計不能、データ破棄

        normalized.append({
            'time': time_str,
            'passengers': passengers, 'kind': kind,
            'memo': memo, 'case': case,
            'nippou_amount': nippou_amount, 'overage_amount': overage_amount,
            'gen_amount': gen_amount, 'mi_amount': mi_amount,
            'needs_review': bool(r.get('needs_review')),
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

# ─────────────────────────────────────────────────────────────────
# Layer 2/3 出力レーン: ReportEmitter レジストリ
# ─────────────────────────────────────────────────────────────────
# Layer 2 (メーター行ループ) は build_report 本体に残し、Layer 3
# (メーター外の独立案件) を ReportEmitter サブクラス + REPORT_EMITTERS 辞書で
# モジュール化する。新 Layer 3 case 追加は emitter を登録するだけ。

class ReportEmitter:
    """Layer 3: メーター明細と独立に出力する責務 (障割・貸切・他).

    サブクラスは case_name と emit メソッドを実装する.
    emit は ride 1 つを output リストに反映する (append or insert).
    index は同一 case_name 内の通し番号 (ラベル付けに使う).
    """
    case_name = None

    def emit(self, ride, last_real_meter_no, output, index=0):
        raise NotImplementedError


class DiscountEmitter(ReportEmitter):
    """障害者割引: 1/9 リインバース行を未収側に計上.
    ラベルは通し番号「障1」「障2」… (旧「20+」形式は同金額複数件で no 衝突 →
    Streamlit の widget key が重複してクラッシュした実例があるため変更)."""
    case_name = 'discount'

    def emit(self, ride, last_real_meter_no, output, index=0):
        n_amt = ride.get('nippou_amount')
        if not isinstance(n_amt, (int, float)) or int(n_amt) <= 0:
            return
        output.append({
            'no': f'障{index + 1}',
            'passengers': 0, 'time': '',
            'gen': 0, 'mi': int(n_amt),
            'memo': ride.get('memo') or '障割',
            'state': 'discount',
            'needs_review': bool(ride.get('needs_review')),
        })


class CharterEmitter(ReportEmitter):
    """貸切: メーター不使用の独立案件. 件数・人数は通常乗車として計上.
    紙の時刻に基づいて output 内の適切な位置に insert する (末尾 append ではなく、
    紙日報の順序を再現). ラベルは「貸1」「貸2」… の通し番号.
    ([[project-charter-rules]])"""
    case_name = 'charter'

    def emit(self, ride, last_real_meter_no, output, index=0):
        n_amt = ride.get('nippou_amount')
        if not isinstance(n_amt, (int, float)) or int(n_amt) <= 0:
            return
        kind = ride.get('kind') or '現収'
        passengers = int(ride.get('passengers') or 1)
        amount = int(n_amt)
        time_str = ride.get('time') or ''
        row = {
            'no': f'貸{index + 1}',
            'passengers': passengers,
            'time': time_str,
            'gen': amount if kind == '現収' else 0,
            'mi': amount if kind == '未収' else 0,
            'memo': ride.get('memo') or '貸切',
            'state': 'charter',
            'paper_time': time_str,
            'needs_review': bool(ride.get('needs_review')),
        }
        # 紙日報の順序を再現: 紙時刻 (paper_time) より「後」の最初の
        # メーター行の直前に挿入する. メーター行以外 (discount/charter) は
        # 既に挿入済みの他案件なので位置判定からスキップ.
        paper_t = _parse_hhmm(time_str)
        insert_idx = len(output)
        if paper_t is not None:
            for i, existing in enumerate(output):
                if existing.get('state') in ('charter', 'discount'):
                    continue
                ex_t = _parse_hhmm(existing.get('time'))
                if ex_t is not None and ex_t > paper_t:
                    insert_idx = i
                    break
        output.insert(insert_idx, row)


# レジストリ: case → emitter.
# 順序が出力順を決める (discount → charter の順で append される).
REPORT_EMITTERS = {
    'discount': DiscountEmitter(),
    'charter': CharterEmitter(),
}


def _split_rides(rides):
    """rides を Layer 2 (meter-aligned) と Layer 3 (independent cases) に分離.

    Layer 3 の case は REPORT_EMITTERS のキーから動的に決まる. 新 Layer 3
    case を増やす時は REPORT_EMITTERS に追加するだけで _split_rides も
    自動的に追従する.

    返値:
        real: Layer 2 で meter にアラインする rides (normal/overage/split 等)
        by_layer3: dict[case_name -> list of rides], REPORT_EMITTERS のキー単位
    """
    layer3_cases = set(REPORT_EMITTERS.keys())
    real = [r for r in rides if r.get('case') not in layer3_cases]
    by_layer3 = {c: [r for r in rides if r.get('case') == c] for c in layer3_cases}
    return real, by_layer3


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
    # 紙の時刻 vs メーター時刻の許容差。
    # 乗務員は乗車終了後に時計を見て手書きするため、忙しい時はメーター倒してすぐ
    # 次の客に向かい、後でなんとなく書くので 20 分のズレも普通に出る。
    # ただし乗務員は **記入順序** は実際の乗車順を保つので、それを利用して disambiguation する。
    # ([[project_paper_time_drift]])
    TIME_PROXIMITY_THRESHOLD = 20  # 分 (時刻の絶対値ずれ許容)

    # 順序保存のため、Pass 1 で assign 済みの「paper ride → meter no」マッピングを構築
    ride_idx_to_meter_no = {}
    for meter_no_assigned, assigned_ride in rides_by_meter_no.items():
        for i, r in enumerate(real_rides):
            if r is assigned_ride and i not in ride_idx_to_meter_no:
                ride_idx_to_meter_no[i] = meter_no_assigned
                break

    # 未 assign の paper ride を、paper 順 (= 配列 index 順) で処理
    unassigned_ride_idx = sorted([i for i in range(len(real_rides)) if i not in assigned_ride_idx])
    for ride_idx in unassigned_ride_idx:
        ride = real_rides[ride_idx]
        r_time = _parse_hhmm(ride.get('time'))
        if r_time is None:
            continue  # 時刻無しは推定不能、orphan として捨てる

        # 順序制約: paper 順で前の ride が assign された meter no より「後」、
        # paper 順で次の ride が assign された meter no より「前」の範囲内に絞る
        prev_meter_no = -1  # 下限 (これより大きい meter no が候補)
        for prev_idx in range(ride_idx - 1, -1, -1):
            if prev_idx in ride_idx_to_meter_no:
                prev_meter_no = ride_idx_to_meter_no[prev_idx]
                break
        next_meter_no = float('inf')  # 上限 (これより小さい meter no が候補)
        for next_idx in range(ride_idx + 1, len(real_rides)):
            if next_idx in ride_idx_to_meter_no:
                next_meter_no = ride_idx_to_meter_no[next_idx]
                break

        # 順序範囲内の未 assign meter 行で時刻最近接を探す
        best_no = None
        best_diff = float('inf')
        for m in meter_rows_list:
            if m['no'] in rides_by_meter_no:
                continue
            if m['no'] <= prev_meter_no or m['no'] >= next_meter_no:
                continue  # 順序違反
            m_time = _parse_hhmm(m.get('time'))
            if m_time is None:
                continue
            diff = abs(r_time - m_time)
            if diff < best_diff:
                best_diff = diff
                best_no = m['no']

        if best_no is not None and best_diff <= TIME_PROXIMITY_THRESHOLD:
            rides_by_meter_no[best_no] = ride
            ride_idx_to_meter_no[ride_idx] = best_no
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
    real_rides, by_layer3 = _split_rides(rides)
    aligned = _align_rides_to_meter(real_rides, meter_rows_list)

    # 状況証拠ベースの貸切検出:
    # アラインメントに失敗した「孤立 ride」(メーター明細に対応行が無い)
    # で、金額が妥当な範囲なら自動的に貸切候補として Layer 3 に昇格させる。
    # ([[project-charter-rules]]: 貸切はメーター不使用 → 明細に出ない)
    # ([[feedback-ask-with-choices]]: 自動判定にせよ needs_review で人間が確認できる)
    aligned_ids = {id(r) for r, _ in aligned if r is not None}
    for ride in real_rides:
        if id(ride) in aligned_ids:
            continue
        # 孤立 ride: メーター明細にも紐付かなかった
        amt = _ride_effective_amount(ride)
        if amt is None or amt < 1000:
            continue  # 金額不明 or OCR ゴミ判定で捨てる
        # 通常乗車 (case='normal'/'split') から charter に変換、要確認フラグ立て
        original_memo = ride.get('memo') or ''
        # 既に '貸切' が memo にあれば '(自動判定: 貸切)' は付けない (二重マーカー回避)
        if '貸切' in original_memo:
            new_memo = original_memo
        else:
            new_memo = (original_memo + ' (自動判定: 貸切)').strip()
        promoted = {
            'time': ride.get('time') or '',
            'passengers': ride.get('passengers') or 1,
            'case': 'charter',
            'kind': ride.get('kind') or '現収',
            'nippou_amount': amt,
            'memo': new_memo,
            'needs_review': True,  # 人間に確認を促す
        }
        by_layer3.setdefault('charter', []).append(promoted)

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
        needs_review = bool(ride.get('needs_review'))

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
                'paper_time': ride.get('time') or '',  # 紙の時刻 (アラート用)
                'needs_review': needs_review,
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
                'paper_time': ride.get('time') or '',
                'needs_review': needs_review,
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
                'paper_time': ride.get('time') or '',  # 紙の時刻 (アラート用)
                'needs_review': needs_review,
            })

    # Layer 3: メーター外案件を REPORT_EMITTERS 経由で出力.
    # 新 case 追加は REPORT_EMITTERS への登録のみで完結 (この本体は触らない).
    # discount を先 → charter を後で処理することで、charter は完成した output
    # 内のメーター行の位置を見て insert 位置を決められる.
    for case_name, emitter in REPORT_EMITTERS.items():
        for idx, ride in enumerate(by_layer3.get(case_name, [])):
            emitter.emit(ride, last_real_meter_no, output, index=idx)

    # 障割の数学検出 (ヒント表示のみ、自動確定はしない)
    _add_discount_hints(output, meter_rows_list)

    return output


def _add_discount_hints(report_rows, meter_rows_list):
    """障害者割引の数学的検出 (ヒントのみ、case 変更や集計影響は無し)。

    根拠: 日本のタクシー障害者割引は「メーター額 = 原運賃 × 0.9 (既に1割引で表示)」。
    別途、運転手が会社に未収請求する 1割分 (= 原運賃 × 0.1 = メーター × 1/9) が
    日報の別行に記録される。memo に「障割」キーワードが無くても、額の比率で検出可能。

    判定: mismatch 行で nippou_amount × 9 ≒ いずれかのメーター額 (±15円) なら障割候補。
          row に `discount_hint=True` と `discount_hint_for_meter=<メーター額>` を立てる。
    描画: render_detail_table が hint を見て「💡 障割の可能性 (No.X)」と表示する。
    """
    # 同金額のメーター行が複数あり得るので list of (no, amount) で保持
    meter_pairs = [(m.get('no'), int(m.get('amount') or 0)) for m in meter_rows_list]
    TOLERANCE = 10  # 円 (10円単位丸めの誤差吸収)
    for row in report_rows:
        if row.get('state') != 'mismatch':
            continue
        n = row.get('nippou_amount')
        if not isinstance(n, int) or n <= 0 or n > 500:
            continue  # 障割は通常 100〜500 円程度
        # いずれかのメーター額の 1/9 値と一致するか
        for m_no, m_amt in meter_pairs:
            if m_amt <= 0:
                continue
            expected_discount = m_amt / 9
            if abs(n - expected_discount) <= TOLERANCE:
                row['discount_hint'] = True
                row['discount_hint_for_meter'] = m_no
                row['discount_hint_meter_amount'] = m_amt
                break


def reverify_mismatches(client, nippou_img, report_rows):
    """第 2 段 OCR: mismatch 行を AI に再確認させ、補正可能なら適用。

    1 段目 OCR (classify_nippou) で paper の値が meter と一致しなかった行について、
    AI に「メーター額が読める可能性は?」と再質問。AI が「やっぱりメーター額に見える」
    と訂正したら state を 'ok' に戻し、紙の数字も meter 値に揃える。
    紙が本当に違う数字を書いてる場合は AI が "keep" を返すので mismatch のまま。

    cost 対策: mismatch 行が無い時は呼ばれない (run_pipeline 側で条件分岐)。
    精度対策: prompt で「自信無いなら keep」と明示 (誤訂正の防止)。
    """
    mismatches = []
    for orig_i, r in enumerate(report_rows):
        if r.get('state') != 'mismatch':
            continue
        if r.get('discount_hint'):
            continue  # 障割候補はメーターに寄せると害になる
        if not isinstance(r.get('nippou_amount'), int):
            continue
        if not isinstance(r.get('meter_amount'), int):
            continue
        mismatches.append((orig_i, r))

    if not mismatches:
        return report_rows

    lines = [
        f'行 {idx}: メーター ¥{r["meter_amount"]:,} ({r.get("time") or "時刻不明"}) — '
        f'AI は前回 ¥{r["nippou_amount"]:,} と読んだ'
        for idx, (_, r) in enumerate(mismatches)
    ]

    prompt = (
        f'これは先程と同じタクシー日報の写真です。\n'
        f'以下の {len(mismatches)} 個の行で、メーター額 (印字なので正解) と AI 読み取り値が一致しません。\n'
        f'日報の該当行を改めてよく見て、メーター額が読み取れる可能性があるか判定してください。\n\n'
        + '\n'.join(lines)
        + '\n\n【判定ルール】\n'
        '- "confirm": よく見たらメーター額の通り読める (前回の読み取りは digit OCR ミス)\n'
        '- "keep": やはり AI の読み取り値で正しい (紙の数字がメーターと違う = 紙のミス)\n'
        '- "uncertain": 判定できない\n\n'
        '【厳守】\n'
        '- メーター額に寄せる確信がない時は "keep" (誤訂正を避ける)\n'
        '- 障害者割引等で意図的に違う額の場合も "keep"\n\n'
        'JSON 配列のみ返す (前後にコメント不要):\n'
        '[{"row_index": 0, "verdict": "confirm" or "keep" or "uncertain"}, ...]\n'
    )

    try:
        res = client.messages.create(
            model='claude-opus-4-5',
            max_tokens=1500,
            temperature=0,
            messages=[{'role': 'user', 'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': to_b64(nippou_img)}},
                {'type': 'text', 'text': prompt},
            ]}]
        )
    except Exception:
        return report_rows  # API 失敗時は補正せず元のまま (mismatch のまま見せる)

    text = res.content[0].text.strip()
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if not m:
        return report_rows
    try:
        verdicts = json.loads(m.group(0))
    except (json.JSONDecodeError, ValueError):
        return report_rows

    for v in verdicts:
        if not isinstance(v, dict):
            continue
        ri = v.get('row_index')
        if not isinstance(ri, int) or ri < 0 or ri >= len(mismatches):
            continue
        if v.get('verdict') != 'confirm':
            continue
        _, row = mismatches[ri]
        # AI が「やっぱりメーター額」と再確認した → mismatch を解消
        row['state'] = 'ok'
        row['nippou_amount'] = row['meter_amount']
        row['reverified'] = True
    return report_rows


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
      - + 貸切の nippou_amount 合計 (メーター不使用、独立案件)
      missing_nippou 行も「現収と仮定」で合計に貢献しているので、期待値から引かない。
    """
    output_total = sum((r.get('gen') or 0) + (r.get('mi') or 0) for r in report_rows)
    meter_rows_list = sorted(meter_data.get('rows', []), key=lambda r: r['no'])
    rides = nippou_data.get('rides', [])
    _, by_layer3 = _split_rides(rides)

    meter_total = sum(int(r['amount']) for r in meter_rows_list)
    # Layer 3 case ごとの nippou_amount 合計を全部加算 (REPORT_EMITTERS のキーから動的に拾う)
    layer3_total = 0
    for case_name in REPORT_EMITTERS:
        for ride in by_layer3.get(case_name, []):
            n = ride.get('nippou_amount')
            if isinstance(n, (int, float)) and int(n) > 0:
                layer3_total += int(n)
    expected = meter_total + layer3_total
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
    state_class_map = {'mismatch': 'mismatch', 'special': 'special', 'missing_nippou': 'missing_nippou', 'charter': 'charter'}
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
        # 障割の数学検出ヒントがあれば併記 ('障割の可能性'，自動確定はしない)。
        # 紙の時刻 (paper_time) があれば、ユーザーが紙の上で該当行を探すアンカーとして表示。
        # ([[project_paper_time_drift]]: 紙時刻はメーター時刻と最大 20 分ズレるが、
        # ユーザーは「自分が紙に書いた時刻」を起点に物理的な行を見つけられる)
        meter_amt = r.get('meter_amount')
        nippou_amt = r.get('nippou_amount')
        paper_t = r.get('paper_time') or ''
        paper_anchor = f'{paper_t} ' if paper_t else ''
        meter_t = r.get('time') or ''
        meter_anchor = f'{meter_t} ' if meter_t else ''
        if state == 'mismatch':
            if r.get('discount_hint'):
                dh_meter = r.get('discount_hint_for_meter')
                state_display = f'💡 紙の {paper_anchor}¥{nippou_amt:,} の行は障割の可能性 (No.{dh_meter})'
            elif isinstance(nippou_amt, int) and isinstance(meter_amt, int):
                state_display = f'🟠 紙の {paper_anchor}¥{nippou_amt:,} の行 → ¥{meter_amt:,} に直す'
            elif isinstance(meter_amt, int):
                state_display = f'🟠 紙の {paper_anchor}行を ¥{meter_amt:,} に直す'
            else:
                state_display = '🟠 日報の数字を確認'
        elif state == 'missing_nippou' and isinstance(meter_amt, int):
            state_display = f'🔴 {meter_anchor}¥{meter_amt:,} の乗車を新しい行で書き加える'
        elif r.get('needs_review') and state in ('ok', '', None):
            # AI が確信を持てなかった行 (mismatch じゃない時のみヒント表示、mismatch なら mismatch を優先)
            state_display = '⚠ AI 確信なし、紙を確認'
        elif state == 'special':
            state_display = 'メーター超過'
        elif state == 'discount':
            state_display = '障割'
        elif state == 'charter':
            state_display = '貸切 (メーター外)'
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


def apply_user_choices(rows, choices=None):
    """ユーザーの選択 (session_state) を report rows に反映する.

    ([[feedback-ask-with-choices]]: 推測で進めず、選択肢で人間に選ばせる)

    対象 1: state='missing_nippou' 行 (メーター明細にあるが日報書き漏れ)
        キー: `missing_choice_{no}`, 値: '現収' (デフォルト) / '未収'
        効果: gen/mi の振り分けを上書き

    対象 2: state='discount' 行 (障害者割引リインバース)
        キー: `discount_status_{no}` = '合ってる' (デフォルト) / '違う'
              `discount_amount_{no}` = 数値 (status='違う' 時のみ参照)
        効果: status='違う' なら amount_key の値で mi を上書き

    対象 3: state='charter' 行 (貸切)
        キー: `charter_status_{no}` = '合ってる' (デフォルト) / '違う'
              `charter_amount_{no}` = 数値 (status='違う' 時のみ参照)
        効果: status='違う' なら amount_key の値で kind に応じて gen/mi を上書き

    手書き由来の数字 (障害者割引・貸切) は AI 誤読しやすいので
    Yes/No で確認 → 違うならテンキー入力で確定. ([[feedback-accuracy-first]])

    Args:
        rows: report rows (build_report の出力).
        choices: 選択値の辞書 (テスト用). None なら st.session_state を参照.
    """
    if choices is None:
        choices = st.session_state
    for r in rows:
        state = r.get('state')
        if state == 'missing_nippou':
            choice_key = f'missing_choice_{r["no"]}'
            choice = choices.get(choice_key, '現収')
            meter_amt = int(r.get('meter_amount') or 0)
            if choice == '未収':
                r['gen'], r['mi'] = 0, meter_amt
                r['kind'] = '未収'
            else:  # '現収' (デフォルト)
                r['gen'], r['mi'] = meter_amt, 0
                r['kind'] = '現収'
        elif state == 'discount':
            status_key = f'discount_status_{r["no"]}'
            status = choices.get(status_key, '合ってる')
            if status == '違う':
                override = choices.get(f'discount_amount_{r["no"]}')
                if isinstance(override, (int, float)) and int(override) >= 0:
                    r['mi'] = int(override)
            # '合ってる' なら AI 読み値そのまま (r['mi'] のまま)
        elif state == 'charter':
            status_key = f'charter_status_{r["no"]}'
            status = choices.get(status_key, '合ってる')
            if status == '違う':
                override = choices.get(f'charter_amount_{r["no"]}')
                if isinstance(override, (int, float)) and int(override) >= 0:
                    amt = int(override)
                    kind = r.get('kind') or '現収'
                    if kind == '未収':
                        r['gen'], r['mi'] = 0, amt
                    else:
                        r['gen'], r['mi'] = amt, 0
            # '合ってる' なら AI 読み値そのまま
    return rows


def render_missing_choices(rows):
    """missing_nippou 行 1 件ずつ 現収/未収 を選ばせるラジオ UI を描画.

    テーブルの下に出す. 行が無ければ何も出さない.
    ([[feedback-ask-with-choices]] / [[project-correction-philosophy]])
    """
    missing_rows = [r for r in rows if r.get('state') == 'missing_nippou']
    if not missing_rows:
        return
    st.markdown('---')
    st.markdown('### 🔴 日報に未記載の乗車')
    st.caption('メーター明細にあるけど紙の日報に書かれてない乗車です。'
               '現収 (現金) か未収 (カード等) かを選んでください。'
               '選び直すと合計が自動で再計算されます。')
    for r in missing_rows:
        meter_amt = int(r.get('meter_amount') or 0)
        meter_t = r.get('time') or ''
        st.radio(
            f'No.{r["no"]} ({meter_t}) ¥{meter_amt:,}',
            options=['現収', '未収'],
            key=f'missing_choice_{r["no"]}',
            horizontal=True,
        )


def render_discount_confirmations(rows):
    """障害者割引 (discount) 行の額を確認する UI (Yes/No → 違うならテンキー入力).

    手書きの障割リインバース額 (例 270 vs 380) は AI 誤読しやすい.
    実際の Shuchan の事例: AI が 300 と読んだが正解は 380.
    ([[feedback-accuracy-first]]: 正確さ第一、ユーザーに確認させる)
    """
    discount_rows = [r for r in rows if r.get('state') == 'discount']
    if not discount_rows:
        return
    st.markdown('---')
    st.markdown('### ♿ 障害者割引の金額確認')
    st.caption('手書きの数字が滲んで読みづらいことがあります。'
               'AI が読んだ額で合ってるかチェックして、違ったら正しい数字を入力してください。')
    for r in discount_rows:
        ai_amt = int(r.get('mi') or 0)
        memo = r.get('memo') or '障割'
        st.markdown(f'**{memo}** ─ AI 読み: **¥{ai_amt:,}**')
        status = st.radio(
            'この金額で合ってますか？',
            options=['合ってる', '違う'],
            key=f'discount_status_{r["no"]}',
            horizontal=True,
            label_visibility='collapsed',
        )
        if status == '違う':
            st.number_input(
                '正しい金額を入力 (円)',
                value=ai_amt,
                min_value=0,
                step=10,
                key=f'discount_amount_{r["no"]}',
            )


def render_charter_confirmations(rows):
    """貸切 (charter) 行の金額を確認する UI (Yes/No → 違うならテンキー入力).

    貸切はメーター不使用 = 紙の手書きが唯一の情報源。AI 誤読を疑って確認。
    ([[project-charter-rules]] / [[feedback-accuracy-first]])
    """
    charter_rows = [r for r in rows if r.get('state') == 'charter']
    if not charter_rows:
        return
    st.markdown('---')
    st.markdown('### 🚖 貸切の金額確認')
    st.caption('貸切はメーターを回さないため、紙の手書きが唯一の情報源です。'
               'AI が読んだ額で合ってるかチェックして、違ったら正しい数字を入力してください。')
    for r in charter_rows:
        ai_amt = int((r.get('gen') or 0) + (r.get('mi') or 0))
        memo = r.get('memo') or '貸切'
        time_str = r.get('paper_time') or r.get('time') or ''
        st.markdown(f'**{time_str} {memo}** ─ AI 読み: **¥{ai_amt:,}**')
        status = st.radio(
            'この金額で合ってますか？',
            options=['合ってる', '違う'],
            key=f'charter_status_{r["no"]}',
            horizontal=True,
            label_visibility='collapsed',
        )
        if status == '違う':
            st.number_input(
                '正しい金額を入力 (円)',
                value=ai_amt,
                min_value=0,
                step=100,
                key=f'charter_amount_{r["no"]}',
            )


def aggregate_totals(rows):
    """件数・人数・現収・未収・総収・消費税・税抜運収を集計。

    state ごとの件数(ken)・人数(nin)カウント方針【業務ルール】:
      - 'special'（メーター超過）: 除外。同一乗客の超過分のため二重計上回避。
      - 'discount'（障割）: 除外。割引額の独立行は会計調整であり「乗客」ではないため。
      - 'missing_nippou'（日報未記載・現収仮定）: 含める。1 件 1 人の乗車として計上
        （合計を成立させる仮置き。ユーザーが訂正したらそれに従う）。
      - 'charter'（貸切）: 含める。メーター不使用だが実際の乗車案件。([[project-charter-rules]])
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

    # Phase 4 (92-95%): 統合
    loader_steps(loader, list(range(92, 96)), '統合中', sleep=0.03)
    report_rows = build_report(meter_data, nippou_data)

    # Phase 4.5 (96-99%): mismatch があれば AI に第 2 段 OCR で再確認
    # 1 段目で digit OCR ミスがあれば、ここで AI 自身が「やっぱりメーター値」と訂正
    # する可能性。mismatch が無ければスキップ (コストゼロ)。
    if any(r.get('state') == 'mismatch' for r in report_rows):
        loader_steps(loader, list(range(96, 99)), '違和感を AI に再確認中', sleep=0.04)
        report_rows = reverify_mismatches(client, nippou_img, report_rows)

    # Phase 5 (99-100%): 検証
    loader_steps(loader, list(range(99, 101)), '検証中', sleep=0.03)
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
        # 上下の警告で同じ事実 (missing_nippou 行) を基準にすることで矛盾を防ぐ。
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
        #   1. apply_user_choices で missing_nippou 行の現収/未収を確定
        #   2. render_summary（件数・現収・未収・総収・消費税・税抜）
        #   3. render_detail_table（日報の行一覧）
        #   4. render_missing_choices（未記載行のラジオ UI）
        #   この後: 整合性チェック → デバッグ expander → リセットボタン
        rows = apply_user_choices(rows)
        ken, nin, gen, mi, sou, tax, net = aggregate_totals(rows)
        render_summary(ken, nin, gen, mi, sou, tax, net)
        render_detail_table(rows)
        render_missing_choices(rows)
        render_discount_confirmations(rows)
        render_charter_confirmations(rows)
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

        # 「画面で見える問題」(🟠/🔴 行 or 合計不一致) が無い時は issues panel を出さない。
        # AI normalize 段で拾ったゆらぎは後段で吸収済みなので、見せても混乱するだけ。
        _visible_alerts = any(r.get('state') in ('mismatch', 'missing_nippou') for r in rows)
        _has_actionable = _visible_alerts or (not valid)

        _meter_issues = meter_data.get('issues', []) or []
        _nippou_issues = nippou_data.get('issues', []) or []
        _all_issues = _meter_issues + _nippou_issues

        if _all_issues and _has_actionable:
            # ユーザー言語ラベル (内部用語 case / kind / index 等は出さない)。
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
                """issue の where 文字列をユーザー表現に変換。
                日報側: 'index N' → 'N+1 行目'
                メーター側: 'No.X' はそのまま (既にユーザー言語)。
                """
                s = where_str or ''
                m = re.match(r'^index (\d+)$', s)
                if m:
                    return f'{int(m.group(1)) + 1} 行目'
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

            def _ride_compact(r, idx):
                """1 行コンパクト表示 (idx は rides 配列の 0-origin 位置)。"""
                c = r.get('case') or 'normal'
                pos = idx + 1
                if c == 'split':
                    return f'**#{pos}**:{r.get("gen_amount", 0)}+{r.get("mi_amount", 0)}(分割)'
                amt = r.get('nippou_amount')
                kind_initial = (r.get('kind') or '?')[0]
                return f'**#{pos}**:{amt if amt is not None else "?"}({kind_initial})'

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
                parts = ['<table class="detail-table"><thead><tr><th>順</th><th>時刻</th><th>人数</th><th>kind</th><th>memo</th><th>case</th><th>金額</th></tr></thead><tbody>']
                for idx, r in enumerate(rides, start=1):
                    parts.append(
                        f'<tr><td>{idx}</td>'
                        f'<td>{r.get("time", "")}</td>'
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
            compact2 = '  '.join(_ride_compact(r, i) for i, r in enumerate(rides))
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
### 0. 🐦‍⬛ AI エンジン八咫烏

このアプリの心臓部には、日本神話の道案内の神「**八咫烏（やたがらす）**」と名付けた AI エンジンが組み込まれている。

手書きのミス・読み取り違い・書き漏れを判断し、ユーザーを「日報完成」というゴールまで導く役割を担う。神武天皇を熊野から大和へ導いた三本足の烏のごとく、現場の苦しみから完成への道を後ろから支える。

### 1. 日報の書き方ルール
このアプリを正しく使うには、手書き日報の書き方にルールがあります。

- **通常の乗車（現金）**：現収欄に金額を記入。未収欄は空欄、または横線（―）を引く。
- **通常の乗車（カード・電子マネー等）**：未収欄に金額を記入。現収欄は空欄、または横線（―）を引く。
- **障害者割引（障割）**：
  - 1行目：割引後の乗客支払い額を現収または未収欄に記入（支払い方法による）。
  - 2行目（別段）：割引額を未収欄に記入。摘要欄に「障割」と明記。
- **メーター超過（消し忘れ等の自己負担）**：
  - 1行目：乗客支払い額を現収または未収欄に記入（支払い方法による）。
  - 2行目（別段）：超過額を現収欄に記入。摘要欄に「メーター」と明記（自己負担で会社に現金納金する分）。

### 2. 使い方
1. 写真2枚をアップ（手書き日報＋営業明細書）。
2. 「日報を完成させる」を押して待つ。
3. 完成したらアラートチェック。指示に従って手書き日報を修正。
4. もう一度確認したい場合は再度写真をアップして確認。

### 3. このアプリについて
- **なぜ生まれたか**：日報入力に毎日10分、ハマる日は30分も格闘してなかなか合わない手書き日報。年間60〜100時間以上の無駄な作業とありえないストレスが積み重なる毎日。「仕事終わりの最後の締めがこんな苦行でいいのか、こんなアホなことをやり続けるのは無理だ」という怒りから、このアプリは生まれた。
- **AIが代わりにやること**：手書き文字解読、画像照合、業務ルール判断、自動計算。
- **何がすごいか**：OCRではなくAIが画像を「理解」、数年前まで研究段階だった技術。

### 4. プライバシー
写真はこのアプリのサーバーに保存されません。AI処理元（Anthropic社）に一時送信されますが、学習には使われず、30日以内に自動削除されます。

### 5. 更新履歴 (直近のみ)

詳しい変更履歴は [CHANGELOG.md](https://github.com/shuchan-daze/taxi-ocr/blob/main/CHANGELOG.md) を参照。

- **v1.22.00** (2026-05-15): メーター超過の新書式 (memo「メーター」キーワード) を追加サポート。日報書き方ルールを明文化。
- **v1.21.00** (2026-05-15): AI 自信シグナル `needs_review` を導入。AI が「自信ない行」だけマークし、ユーザーが目視確認できるように。
- **v1.20.00** (2026-05-15): テスト整備 (Phase 1 単体テスト 78 件 + Phase 2 E2E フレームワーク) を導入。今後のリファクタが安全に。
- **v1.19.00** (2026-05-15): 第 2 段 OCR (mismatch 時の AI 再確認) + 障害者割引の数学的検出を導入。
- **v1.18.00** (2026-05-15): 大規模クリーンアップ (-558 行)。死蔵 `meter_no` フィールド撲滅、パッチ的なコード削除。
- **v1.17.00** (2026-05-14): 完了導線の哲学転換。「直して再アップ」強制ループから脱却、ユーザーが「次へ進む」を選んだら結果を尊重する形に。
- **v1.16.00** (2026-05-14): アライメント大改善。Pass 2 を「順番割当」から「時刻最近接マッチ」に切替、紙の書き漏れケースで嘘の mismatch を作らないように。
- **v1.15.00** (2026-05-14): constraint-aware OCR を導入。日報 OCR にメーター情報を参考として渡し、AI が曖昧な手書き数字でメーター値と整合する候補を選べるように。
- **v1.14.00** (2026-05-14): アラインメント大改修。日報には「No 列」が無いという前提を反映し、AI には行番号を読ませず、アラインメントは金額 + 時刻で実施。

作者＞怒りの山本
''')

# AI エンジン八咫烏バッジ (アプリ全体のブランド署名)
# 神社の八咫烏シルエット (熊野皇大神社の御朱印帳から抽出) を金色化して使用。
# 神社への使用許可は別途取得予定 (Shuchan 案件)。
# モジュール起動時に PNG を base64 化、HTML に inline 埋め込み。
_YATAGARASU_PNG_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'yatagarasu.png')
try:
    with open(_YATAGARASU_PNG_PATH, 'rb') as _f:
        _YATAGARASU_PNG_B64 = base64.b64encode(_f.read()).decode('ascii')
except FileNotFoundError:
    _YATAGARASU_PNG_B64 = ''  # ファイル無しでも crash しないように

# 視覚的バッジ (HTML、pointer-events: none で透過)
st.markdown(
    f'<div class="yata-badge">'
    f'<img src="data:image/png;base64,{_YATAGARASU_PNG_B64}" class="yata-icon-img" alt="八咫烏" />'
    '<div class="yata-text">'
    '<span class="label-small">POWERED BY</span>'
    '<span class="label-main">AI エンジン 八咫烏</span>'
    '<span class="label-en">YATAGARASU</span>'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)


@st.dialog('🐦‍⬛ AI エンジン八咫烏について')
def _show_yatagarasu_dialog():
    st.markdown('''
### 八咫烏 (やたがらす) とは

日本神話に登場する **三本足のカラス**。神武天皇を熊野から大和まで導いた
**道案内の神**として、古事記・日本書紀に記録されている。
現代では日本サッカー協会のエンブレムとしても知られる。

### このアプリでの役割

本アプリの心臓部には、その「道案内の神」の名を冠した AI エンジンが組み込まれている。

- **手書き OCR**: 数字・摘要・人数・時刻を画像から読み取る。
- **digit OCR 補正**: メーター額と照合してあいまいな数字を最適候補に解決。
- **業務ルール判定**: 障害者割引・メーター超過・分割払い・からまわしを自動分類。
- **アライメント**: 紙の日報と印字メーター明細書を、金額と時刻で自動照合。
- **書き漏れ検出**: メーター行に対応する紙の記入が無い場合に警告。
- **AI 自信シグナル**: AI 自身が「自信が無い行」を明示。
- **集計**: 件数・人数・現収・未収・消費税・税抜運収を自動算出。

手書きの苦しみを「日報完成」というゴールまで、八咫烏が後ろから導く。

### 技術スタック

- **画像理解 AI**: Anthropic Claude Opus 4.5。
- **印字 OCR**: Google Cloud Vision API。
- **5 段パイプライン**: 識別 → 鮮明度 → メーター OCR → 日報 OCR → 統合。
- **哲学**: 「メーターは絶対、AI は判断、人間は最終確認」の三層モデル。

### このプロジェクトの起点

> 「日報入力に毎日 10 分、ハマる日は 30 分も格闘して合わない手書き日報。
> 年間 60〜100 時間以上の無駄とありえないストレス。仕事終わりの最後の
> 締めがこんな苦行でいいのか、こんなアホなことやってられるか」

— 作者の怒りから生まれたアプリ。
''')


# バッジに重ねる透明 button: バッジ全体をクリック領域として機能させる
if st.button(' ', key='yata_dialog_btn', use_container_width=True):
    _show_yatagarasu_dialog()
