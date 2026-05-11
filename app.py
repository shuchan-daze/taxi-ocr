# バージョニング規約: SemVer 2.0 (MAJOR.MINOR.PATCH)
#   MAJOR: 大きな変更・仕様変更（後方互換なし）
#   MINOR: 部分的な機能追加・改善（後方互換あり）
#   PATCH: バグ修正・小さな調整
#
# v1.1.3 - 2026-05-11
#   - 包括的な README.md を整備（プロジェクト概要・アーキテクチャ・業務ルール・セットアップ）
# v1.1.2 - 2026-05-11
#   - 速度改善: to_b64() の per-image キャッシュ化（JPEG エンコード重複排除）
#   - dead code 削除: 未使用 HTML 属性 (data-metric / data-value / data-rowidx)
#   - dead code 削除: 旧 dblclick 編集 UI の名残 (cursor:pointer / .cell-edit クラス)
# v1.1.1 - 2026-05-11
#   - バージョン番号表示を 14px / opacity 0.7 に拡大
#   - タイトル下の余白を 1.5rem → 0.5rem に削減
#   - 完成バーのフォント拡大（✓完成:18px / 件数・人数:28px / 単位:14px）
# v1.1.0 - 2026-05-11
#   - 障害者割引（障割）対応の本格実装
#   - sequence ベースアライメント（meter_no が連番でない場合も正しく動作）
#   - 障割を日報順に '6+' 形式で挿入
#   - +α 要素（passengers=NULL の orphan ride）の救済
#   - 整合性チェックの誤検知修正、税抜運収の小数表示修正、ほか
# v1.0.0 - 2026-05-10 初回リリース
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
st.set_page_config(page_title='タクシー日報', layout='centered', initial_sidebar_state='collapsed')

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stApp {background: #010519;}
.block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 600px;}
h1, h2, h3, h4, h5, h6, p, span, div, label {color: #010519;}
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
    padding: 0.5rem !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small,
[data-testid="stFileUploaderDropzoneInstructions"] span small,
section[data-testid="stFileUploader"] small,
section[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] > div > small {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div::after {
    content: "日報と営業明細書をアップしてください";
    color: #010519 !important;
    font-size: 13px !important;
    display: block;
    margin-top: 4px;
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
.big-num {
    font-size: 120px !important;
    font-weight: 700 !important;
    color: rgba(255, 255, 255, 0.15) !important;
    letter-spacing: -0.05em;
    line-height: 1;
    margin-bottom: 16px;
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
/* mismatch: 現収/未収セルのみを薄赤で強調（行全体ではない） */
.detail-table tr.mismatch td[data-col="gen"],
.detail-table tr.mismatch td[data-col="mi"] {background: #fee2e2 !important; color: #7f1d1d !important; font-weight: 600;}
.detail-table tr.special td {background: #fef3c7 !important; color: #78350f !important;}
.detail-table tr.special td:first-child {border-left: 4px solid #d97706 !important;}
.detail-table tr.edited td {background: #fef9c3 !important; color: #713f12 !important;}
.detail-table tr.edited td:first-child {border-left: 4px solid #ca8a04 !important;}
</style>
""", unsafe_allow_html=True)

# タイトルブロック（ページ最上部、常時表示。結果の有無に関わらず常に最上段）
st.markdown("""
<div class="title-block">
  <h1>AIタクシー日報<span style="font-size: 13px; color: #d4af37; font-weight: 400; margin-left: 8px;">by 怒りの山本</span></h1>
  <p class="subtitle">DAILY REPORT · OCR ASSIST</p>
  <div class="divider"></div>
  <p style="color: rgba(255,255,255,0.7); font-size: 14px; letter-spacing: 0.08em; margin: 4px 0 0; text-align: right;">v1.1.3</p>
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
    res = client.messages.create(
        model='claude-opus-4-5', max_tokens=20, temperature=0,
        messages=[{'role':'user','content':[
            {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(img)}},
            {'type':'text','text':'''この画像を判定してください。

- メーター明細書（営業明細書）：機械印字、時刻と金額の2列構造、ヘッダに「営業明細書」または「明細」表記
- 日報：手書き、複数列（人数・時刻・現収・未収・摘要等）
- どちらでもない／判別不能：unclear

回答は以下のいずれか1単語のみで（前後に余計な語なし）：
meter
nippou
unclear'''}
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
    """両画像が読み取り可能な品質か判定。返値: (ok: bool, reason: str)"""
    res = client.messages.create(
        model='claude-opus-4-5', max_tokens=200, temperature=0,
        messages=[{'role':'user','content':[
            {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(meter_img)}},
            {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(nippou_img)}},
            {'type':'text','text':'''1枚目はメーター明細書、2枚目は日報です。

各画像が読み取り可能な品質か確認してください：
- メーター明細書：時刻と金額の桁が一つひとつはっきり判別できるか
- 日報：手書き数字、現収/未収欄、摘要が判読できるか

結果は以下のいずれかの形式のみで出力（前後に余計な文字なし）：
clarity: ok
または
clarity: ng
reason: <NGの場合の具体的な理由（どの画像のどこが不鮮明か）>'''}
        ]}]
    )
    text = res.content[0].text.strip()
    if 'clarity: ok' in text.lower() or 'clarity:ok' in text.lower():
        return True, ''
    m = re.search(r'reason:\s*(.+)', text, re.DOTALL)
    return False, (m.group(1).strip() if m else '画像が不鮮明です')


# Stage 1: メーター明細書を OCR → {'rows': [{no, time, amount}, ...]}
# 出力金額は build_report で「真実」として使用される。

def _parse_meter_claude(client, meter_img):
    """メーターレシート画像を Claude に直接送って JSON で返させる。"""
    prompt = """このタクシーメーターのレシート画像から全乗車明細を読み取り、
以下のJSON形式のみで返答せよ。説明文は不要。

{"rows": [
  {"no": 1, "time": "10:32", "amount": 4100},
  {"no": 2, "time": "10:50", "amount": 1000}
]}

・noはレシートの行番号
・timeは降車時刻（HH:MM形式）
・amountは¥の金額（数値のみ）
・JSON以外出力しない"""
    res = client.messages.create(
        model='claude-opus-4-5', max_tokens=4000, temperature=0,
        messages=[{'role': 'user', 'content': [
            {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': to_b64(meter_img)}},
            {'type': 'text', 'text': prompt},
        ]}]
    )
    text = res.content[0].text.strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        raise ValueError(f'メーター明細のJSONが見つかりません。応答: {text[:300]}')
    return json.loads(m.group(0))


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


def _parse_meter_vision(client_vision, meter_img, claude_client):
    """ハイブリッド: Vision API で OCR した生テキストを Claude に渡して JSON 構造化。
    claude_client は parse_meter 経由で main から渡される（毎回生成しない）。"""
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
    res = claude_client.messages.create(
        model='claude-opus-4-5', max_tokens=4000, temperature=0,
        messages=[{'role': 'user', 'content': prompt}]
    )
    text = res.content[0].text.strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        return None
    data = json.loads(m.group(0))
    rows = data.get('rows', [])
    if not rows:
        return None
    return {'rows': rows, 'total': sum(r['amount'] for r in rows)}


def parse_meter(client, meter_img):
    """Stage 1 ディスパッチャ: Vision+Claude ハイブリッド優先、失敗時のみ Claude 単独にフォールバック。"""
    vc = get_vision_client()
    if vc is not None:
        try:
            result = _parse_meter_vision(vc, meter_img, client)
            if result is not None:
                return result
        except Exception:
            pass
    return _parse_meter_claude(client, meter_img)


# Stage 2: 日報のみから乗客行を分類 → {'rides': [...]}
# meter_data に依存せず、meter_no は日報の上から 1 始まり連番で割当。
# 金額の主要値は読まないが、mismatch 検出のため nippou_amount として
# 日報の手書き金額を任意で記録する（読めない場合は null）。

def classify_nippou(client, nippou_img):
    """Stage 2: 日報を Claude で分類し、{rides: [...]} を返す。
    各 ride は通常乗客行に対応。
    case の値:
      - 'normal': 通常乗車
      - 'overage': から回し（メーター超過）。直前通常行の case を変更し overage_amount をセット
      - 'discount': 障害者割引（障割）。kind は強制的に '未収'
    nippou_amount: 日報の手書き金額（mismatch 検出用、null 可）。"""
    prompt = """これはタクシー乗務員の手書き日報です。
日報の各行を上から順に処理し、以下のルールで JSON 配列を返してください。

【通常行】
{"meter_no": 連番（1始まり、上から何番目の乗客か）, "passengers": 人数（数字）, "kind": "現収" or "未収", "memo": "Visa/Suica/Uber/交通系/現金 等", "case": "normal", "nippou_amount": 日報の現収/未収欄に書かれた金額の数字（読めない/書かれていない場合は null）}

【現収/未収判定】
- 摘要に「Visa」「Uber」「Suica」「交通系」「PayPay」等のカード/電子マネー名 → 必ず「未収」
- 摘要が空欄、または「現金」 → 「現収」

【nippou_amount について】
- 日報の現収/未収欄に手書きで書かれている金額をそのまま読み取る（数値のみ、カンマ無し）。
- 読み取れない・書かれていない・かすれている場合は null を返す。
- 「+100」のような追記は除外し、メインの金額のみを読む。
- この値は出力テーブルの金額にはならない（出力金額はメーター明細から取られる）。
  メーター明細との比較で「日報誤記の検知（mismatch ハイライト）」のためだけに使われる。

【障害者割引（障割）】
摘要に「障割」「障害者割引」の記載がある割引額行は、
日報の現収欄に書かれていても kind="未収" として読み取ること。
case="discount" として判定し、割引額を nippou_amount に記録する。

【から回し行の判定】
- 乗車区間が取り消し線（横線・斜線・×印）で消されており、現収欄に「+100」「+200」のように「+金額」だけ書かれた行は「から回し」（メーター消し忘れ）。
- この行は ride として出力しない。
- 代わりに、この行の直前の通常行の case を "overage" に変更し、overage_amount にその金額（数値）をセットする。

【出力例】
[
  {"meter_no": 1, "passengers": 2, "kind": "未収", "memo": "アプリ", "case": "normal", "nippou_amount": 1500},
  {"meter_no": 2, "passengers": 1, "kind": "現収", "memo": "現金", "case": "normal", "nippou_amount": null},
  {"meter_no": 21, "passengers": 2, "kind": "未収", "memo": "Visa", "case": "overage", "overage_amount": 100, "nippou_amount": 1600}
]

【厳守】
- JSON 配列のみを返す。前後に余計なテキスト・コードブロック記号・思考過程は付けない。
- 「+100」を「1,100」と誤読しない。「+200」を「1,200」と誤読しない。
- 取り消し線行を独立した ride として出力しない。
- 出力テーブルの最終金額は **メーター明細書の値** が使われる（nippou_amount は mismatch 検知のみに使われる）。"""
    res = client.messages.create(
        model='claude-opus-4-5', max_tokens=4000, temperature=0,
        messages=[{'role': 'user', 'content': [
            {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': to_b64(nippou_img)}},
            {'type': 'text', 'text': prompt},
        ]}]
    )
    text = res.content[0].text.strip()
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if not m:
        raise ValueError(f'日報のJSON配列が見つかりません。応答: {text[:300]}')
    rides = json.loads(m.group(0))
    return {'rides': rides}


# Stage 3: 純 Python でメーター×日報を統合（AIは関与しない）
# 通常行は meter_amount をそのまま gen/mi に振り分け。
# overage 行は客分 (meter - overage) と超過分 (overage) の 2 行に分割。

def _split_rides(rides):
    """rides を「通常乗車（normal/overage）」と「障割（discount）」に分離。"""
    real = [r for r in rides if r.get('case') != 'discount']
    adjustments = [r for r in rides if r.get('case') == 'discount']
    return real, adjustments


def build_report(meter_data, nippou_data):
    """Stage 3: メーター明細（金額確定）と日報の分類情報を統合して最終行リストを構築。

    アライメント方針【重要】:
      classify_nippou が出力する meter_no は「日報の上から何番目」の連番のため、
      メーター明細書の行番号と必ずしも一致しない（特に障割の空回しが無い場合にズレる）。
      そのため通常乗車（normal/overage）はメーター行と **順番（index）でマッチング**し、
      障割（discount）は別系統で nippou_amount を真値として処理する。

    case の扱い:
      - 'overage': 客分行 + 超過分(state='special')行の 2 行に分割
      - 'discount': 別ループで nippou_amount を mi に計上、state='discount'
      - その他 ('normal' or 不明): kind に従って gen/mi に振り分け 1 行出力
    日報金額（nippou_amount）がメーター額と異なる場合は state='mismatch' を立てる
    （ハイライトのみ。出力金額はメーター額のまま）。"""
    meter_rows_list = sorted(meter_data.get('rows', []), key=lambda r: r['no'])
    rides = nippou_data.get('rides', [])
    output = []

    # rides の順番をそのまま辿る。障割は「直前の通常行のメーター番号 + '+'」で挿入。
    # 通常乗車は real_idx をインクリメントしながら meter_rows_list[real_idx] とアラインメント。
    real_idx = 0
    for r in rides:
        case = r.get('case') or 'normal'

        if case == 'discount':
            nippou_amt = r.get('nippou_amount')
            if not isinstance(nippou_amt, (int, float)) or int(nippou_amt) <= 0:
                continue
            # ラベル: 直前の通常行の meter_no + '+'（例: row 6 の直後の障割は '6+'）
            if real_idx > 0 and real_idx <= len(meter_rows_list):
                prev_no = meter_rows_list[real_idx - 1]['no']
                label = f'{prev_no}+'
            else:
                label = '*'
            output.append({
                'no': label,
                'passengers': 0, 'time': '',
                'gen': 0, 'mi': int(nippou_amt),
                'memo': r.get('memo') or '障割',
                'state': 'discount',
            })
            continue  # discount は real_idx を進めない

        # 通常乗車: メーター行と順番アラインメント
        if real_idx >= len(meter_rows_list):
            continue  # メーター行が不足
        meter_row = meter_rows_list[real_idx]
        meter_no = meter_row['no']
        meter_amount = int(meter_row['amount'])
        passengers = int(r.get('passengers') or 1)
        kind = r.get('kind') or '現収'
        memo = r.get('memo') or ''
        time_str = meter_row['time']
        nippou_amt = r.get('nippou_amount')
        nippou_amt = int(nippou_amt) if isinstance(nippou_amt, (int, float)) else None

        if case == 'overage':
            overage = int(r.get('overage_amount') or 0)
            client_amount = meter_amount - overage
            client_state = 'mismatch' if (nippou_amt is not None and nippou_amt != client_amount) else 'ok'
            output.append({
                'no': meter_no, 'passengers': passengers, 'time': time_str,
                'gen': client_amount if kind == '現収' else 0,
                'mi': client_amount if kind == '未収' else 0,
                'memo': memo, 'state': client_state,
            })
            output.append({
                'no': f'{meter_no}+', 'passengers': passengers, 'time': time_str,
                'gen': overage, 'mi': 0,
                'memo': 'メーター超過', 'state': 'special',
            })
        else:  # 'normal' or 不明
            row_state = 'mismatch' if (nippou_amt is not None and nippou_amt != meter_amount) else 'ok'
            output.append({
                'no': meter_no, 'passengers': passengers, 'time': time_str,
                'gen': meter_amount if kind == '現収' else 0,
                'mi': meter_amount if kind == '未収' else 0,
                'memo': memo, 'state': row_state,
            })
        real_idx += 1

    return output


# 整合性チェック

def validate(report_rows, meter_data, nippou_data):
    """出力合計と期待値の整合性チェック。

    返値:
        (ok: bool, diff: int)
        - ok: True なら期待値と出力合計が完全一致
        - diff: 出力合計 − 期待値（正なら出力過多、負なら出力不足）

    期待値の算出（build_report の sequence ベースアライメントに合わせる）:
      - 通常乗車部分: 先頭から min(meter_count, real_ride_count) 行のメーター額合計
      - 障割部分: 全 discount rides の nippou_amount 合計
      - 期待値 = 通常乗車合計 + 障割合計
      これにより空回しの有無に関係なく正しく整合する。
    """
    output_total = sum((r.get('gen') or 0) + (r.get('mi') or 0) for r in report_rows)
    meter_rows_list = sorted(meter_data.get('rows', []), key=lambda r: r['no'])
    rides = nippou_data.get('rides', [])
    real_rides, adjustments = _split_rides(rides)
    aligned_count = min(len(meter_rows_list), len(real_rides))

    aligned_meter_total = sum(int(r['amount']) for r in meter_rows_list[:aligned_count])
    discount_total = sum(
        int(d['nippou_amount']) for d in adjustments
        if isinstance(d.get('nippou_amount'), (int, float)) and int(d['nippou_amount']) > 0
    )
    expected = aligned_meter_total + discount_total
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


# 速度改善: パーティクル HTML はパイプライン中 50+ 回 show_loader から呼ばれるが
# 出力は毎回同じ（決定論的）。モジュール起動時に一度だけ構築してキャッシュ。
_PARTICLES_HTML = _build_particles_html()


def show_loader(loader, pct, label, anim_class=''):
    cls = f'big-overlay {anim_class}'.strip()
    loader.markdown(
        f'<div class="{cls}" data-pct="{pct}">'
        f'<div class="particles-container">{_PARTICLES_HTML}</div>'
        f'<div class="big-num">{pct}%</div>'
        f'<div class="big-label">{label}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

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
    headers = ['No', '人数', '時刻', '現収', '未収', '摘要', '状態']
    parts = ['<table class="detail-table"><thead><tr>']
    parts.extend(f'<th>{h}</th>' for h in headers)
    parts.append('</tr></thead><tbody>')
    state_class_map = {'mismatch': 'mismatch', 'special': 'special'}
    for r in rows:
        cls = state_class_map.get(r.get('state', ''), '')
        row_class = f' class="{cls}"' if cls else ''
        gen_v = int(r.get('gen') or 0)
        mi_v = int(r.get('mi') or 0)
        gen = f"{gen_v:,}" if gen_v else ''
        mi = f"{mi_v:,}" if mi_v else ''
        parts.append(f'<tr{row_class}>')
        parts.append(f'<td>{r["no"]}</td>')
        parts.append(f'<td>{r["passengers"] if r["passengers"] else ""}</td>')
        parts.append(f'<td>{r["time"]}</td>')
        parts.append(f'<td data-col="gen">{gen}</td>')
        parts.append(f'<td data-col="mi">{mi}</td>')
        parts.append(f'<td>{r["memo"]}</td>')
        parts.append(f'<td>{r["state"]}</td>')
        parts.append('</tr>')
    parts.append('</tbody></table>')
    st.markdown(''.join(parts), unsafe_allow_html=True)


def aggregate_totals(rows):
    """件数・人数・現収・未収・総収・消費税・税抜運収を集計。

    state ごとの件数(ken)・人数(nin)カウント方針【業務ルール】:
      - 'special'（メーター超過）: 除外。同一乗客の超過分のため二重計上回避。
      - 'discount'（障割）: 除外。割引額の独立行は会計調整であり「乗客」ではないため。
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

def run_pipeline(client, imgs, loader):
    """End-to-end pipeline. 失敗時は RuntimeError。返値: (rows, valid, diff, meter_data, nippou_data)"""
    # 最初のステップでフェードイン演出（1% 刻み × 短sleep で滑らかに）
    loader_steps(loader, list(range(3, 15)), '画像を判別中', sleep=0.04, anim_class='entering')
    # 2 枚の判別は互いに独立なため並列実行（API レイテンシを 1 回分に短縮）
    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(identify_image, client, imgs[0])
        f2 = executor.submit(identify_image, client, imgs[1])
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

    loader_steps(loader, list(range(18, 31)), '鮮明度を確認中', sleep=0.035)
    ok, reason = check_clarity(client, meter_img, nippou_img)
    if not ok:
        raise RuntimeError(f'画像の鮮明度が不足しています：{reason}\n撮り直して再アップしてください。')

    # Step 3+4: メーター明細と日報を並列読み取り（互いに独立なため同時実行）
    with ThreadPoolExecutor(max_workers=2) as executor:
        meter_future = executor.submit(parse_meter, client, meter_img)
        nippou_future = executor.submit(classify_nippou, client, nippou_img)

        # 両 future 完了までローダーを動かす（早期完了なら break、1% 刻み）
        for pct in range(35, 85):
            if meter_future.done() and nippou_future.done():
                break
            show_loader(loader, pct, 'メーター明細と日報を並列読み取り中')
            time.sleep(LOADER_POLL_SLEEP)

        # 結果取得（例外があれば伝搬）
        meter_data = meter_future.result()
        nippou_data = nippou_future.result()

    loader_steps(loader, list(range(88, 101)), '統合中', sleep=0.035)
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
        rows = st.session_state.result_rows
        valid = st.session_state.result_valid
        diff = st.session_state.result_diff
        meter_data = st.session_state.get('result_meter', {'rows': [], 'total': 0})
        nippou_data = st.session_state.get('result_nippou', {'rides': []})

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
        _rides = nippou_data.get('rides', [])

        _meter_count = len(_meter_rows)
        _nippou_count = len(_rides)
        _row_diff = abs(_meter_count - _nippou_count)

        # 日報に対応付いたメーター行の合計金額（日報がカバーした金額）
        _meter_total = int(meter_data.get('total') or sum(int(r.get('amount', 0)) for r in _meter_rows))
        _matched_nos = {r.get('meter_no') for r in _rides if r.get('meter_no') is not None}
        _matched_meter_amt = sum(int(r.get('amount', 0)) for r in _meter_rows if r['no'] in _matched_nos)
        _nippou_total = _matched_meter_amt

        _gap_rate = abs(_meter_total - _nippou_total) / _meter_total if _meter_total > 0 else 0.0
        _amount_diff = abs(_meter_total - _nippou_total)

        if _row_diff >= 3 or _gap_rate >= 0.30:
            st.error(
                f'### ⚠️ メーターレシートと日報の内容が大きく乖離しています\n\n'
                f'- メーター: **{_meter_count}件** / 日報: **{_nippou_count}件**（{_row_diff}件の差）\n'
                f'- 金額差: **¥{_amount_diff:,}**（{_gap_rate*100:.0f}%の乖離）\n\n'
                f'写真が正しいか確認して、必要であれば再アップしてください。'
            )
            st.button('🔄 写真を再アップする', on_click=reset_app, key='reupload_btn', use_container_width=True)
        elif _row_diff == 2:
            st.warning(
                f'メーター({_meter_count}件) と 日報({_nippou_count}件) で 2 件の差があります。'
                f'読み落としや日報の書き漏れがないか確認してください。'
            )

        st.markdown('<div class="result-card">', unsafe_allow_html=True)

        if not valid:
            diff_abs = abs(diff)
            # 差額のパターンからヒントを推定
            hints = []
            if diff > 0:
                hints.append(f'出力合計が ¥{diff_abs:,} 多い → メーター明細の桁を多く読みすぎている可能性、または重複行の混入')
            else:
                hints.append(f'出力合計が ¥{diff_abs:,} 少ない → メーター明細の行を抜かしている、または桁を少なく読んだ可能性')
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
            st.warning(
                f'⚠️ 金額が ¥{diff_abs:,} ずれています。下の表で内容を確認してください。\n\n'
                + '\n'.join('- ' + h for h in hints)
                + '\n\nメーター明細の読み取り結果（下のデバッグセクション）を画像と照合してください。'
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

        st.markdown('<br>', unsafe_allow_html=True)
        st.button('🔄 新しい日報を作成', on_click=reset_app, key='reset_btn', use_container_width=True)

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
            if rides:
                parts = ['<table class="detail-table"><thead><tr><th>meter_no</th><th>人数</th><th>kind</th><th>memo</th><th>case</th><th>overage</th></tr></thead><tbody>']
                for r in rides:
                    parts.append(
                        f'<tr><td>{r.get("meter_no", "")}</td>'
                        f'<td>{r.get("passengers", "")}</td>'
                        f'<td>{r.get("kind", "")}</td>'
                        f'<td>{r.get("memo", "")}</td>'
                        f'<td>{r.get("case", "")}</td>'
                        f'<td>{r.get("overage_amount") or ""}</td></tr>'
                    )
                parts.append('</tbody></table>')
                st.markdown(''.join(parts), unsafe_allow_html=True)
            else:
                st.info('日報の分類データなし')

            st.markdown('**生 JSON:**')
            compact2 = '  '.join(
                f'**{r.get("meter_no")}**:{r.get("nippou_amount") or "?"}({(r.get("kind") or "?")[0]})'
                for r in rides
            )
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
    existing_keys = {(kf['name'], kf['size']) for kf in st.session_state.kept_files}
    added = False
    for f in new_files:
        key = (f.name, f.size)
        if key not in existing_keys:
            st.session_state.kept_files.append({'name': f.name, 'size': f.size, 'bytes': f.getvalue()})
            added = True
    if added:
        st.session_state.uploader_counter += 1
        st.rerun()

imgs = []
if st.session_state.kept_files:
    cols = st.columns(len(st.session_state.kept_files))
    for i, kf in enumerate(st.session_state.kept_files):
        img = fix_orientation(Image.open(io.BytesIO(kf['bytes'])))
        imgs.append(img)
        with cols[i]:
            st.image(img, use_container_width=True)
            if st.button('✕ 削除', key=f'del_{i}'):
                st.session_state.kept_files.pop(i)
                st.rerun()

if len(imgs) == 2:
    if st.button('🔍 日報を完成させる', use_container_width=True, type='primary'):
        loader = st.empty()
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
                # JSON 抽出失敗または JSON が見つからない (_parse_meter_claude / classify_nippou が raise)
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
- **v1.1.3** (2026-05-11): README.md 整備（プロジェクトの全記録ドキュメント）
- **v1.1.2** (2026-05-11): 速度改善（画像エンコードのキャッシュ化）、dead code 削除
- **v1.1.1** (2026-05-11): 表示の微調整（バージョン番号拡大・タイトル下余白削減・完成バー拡大）
- **v1.1.0** (2026-05-11): 障害者割引（障割）対応の本格実装、整合性チェック修正、税抜運収の表示修正など
- **v1.0.0** (2026-05-10): 初回リリース

作者＞怒りの山本
''')
