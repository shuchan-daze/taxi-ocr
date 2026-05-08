import streamlit as st
import anthropic
import base64
from PIL import Image, ExifTags
from pillow_heif import register_heif_opener
import io
import os
import re

register_heif_opener()
st.set_page_config(page_title='タクシー日報', layout='centered', initial_sidebar_state='collapsed')

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stApp {background: #010519;}
.block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 600px;}
h1, h2, h3, h4, h5, h6, p, span, div, label {color: #010519;}
.stApp > header {background: transparent;}
.title-block {margin-bottom: 1.5rem;}
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
    padding: 1rem !important;
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
[data-testid="stFileUploaderDropzoneInstructions"] {color: #010519 !important;}
[data-testid="stFileUploaderDropzoneInstructions"] * {color: #010519 !important;}
[data-testid="stFileUploader"] button {color: #010519 !important; background: white !important; border: 1px solid #010519 !important;}

.stButton button {
    background: #d4af37 !important;
    color: #010519 !important;
    border: none !important;
    border-radius: 16px !important;
    padding: 1rem !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    box-shadow: 0 4px 14px rgba(212,175,55,0.35) !important;
    letter-spacing: 0.05em !important;
    width: 100% !important;
}
.stButton button:hover {background: #c89f2e !important; transform: translateY(-1px);}
.stImage img {border-radius: 12px;}
.complete-bar {background: #f5f5f7; border-radius: 12px; padding: 14px 16px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; border-left: 3px solid #d4af37;}
.complete-bar .label {font-size: 14px; font-weight: 500; color: #010519; margin: 0;}
.complete-bar .stats {font-size: 18px; font-weight: 500; color: #010519; margin: 0;}
.complete-bar .stats small {font-size: 11px; color: #888;}
.metric-grid-3 {display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 8px;}
.metric-grid-2 {display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 14px;}
.metric {background: #f5f5f7; border-radius: 10px; padding: 8px 10px;}
.metric.dark {background: #d4af37;}
.metric.dark .label {color: #010519 !important;}
.metric.dark .value {color: #010519 !important;}
.metric .label {font-size: 10px; color: #888; margin: 0; letter-spacing: 0.05em;}

.metric .value {font-size: 15px; font-weight: 500; margin: 2px 0 0; color: #010519;}

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
[data-testid="stFileUploaderDropzoneInstructions"] {
    padding: 0 !important;
    margin: 0 !important;
}
[data-testid="stFileUploader"] section {
    padding: 0.5rem !important;
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
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-block">
  <h1>タクシー日報<span style="font-size: 13px; color: #d4af37; font-weight: 400; margin-left: 8px;">by 怒りの山本</span></h1>
  <p class="subtitle">DAILY REPORT · OCR ASSIST</p>
  <div class="divider"></div>
</div>
""", unsafe_allow_html=True)

def fix_orientation(img):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = img._getexif()
        if exif is not None:
            o = exif.get(orientation)
            if o == 3: img = img.rotate(180, expand=True)
            elif o == 6: img = img.rotate(270, expand=True)
            elif o == 8: img = img.rotate(90, expand=True)
    except: pass
    return img

def to_b64(img):
    img.thumbnail((2000,2000))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode()

def is_meter(client, img):
    res = client.messages.create(
        model='claude-opus-4-5', max_tokens=10,
        messages=[{'role':'user','content':[
            {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(img)}},
            {'type':'text','text':'この画像に「営業明細書」という文字がありますか？「はい」か「いいえ」だけ答えてください。'}
        ]}]
    )
    return 'はい' in res.content[0].text

files = st.file_uploader('日報と営業明細書をアップしてください', type=['jpg','jpeg','png','heic'], accept_multiple_files=True)

imgs = []
if files:
    cols = st.columns(len(files))
    for i, f in enumerate(files):
        img = fix_orientation(Image.open(f))
        imgs.append(img)
        with cols[i]:
            st.image(img, use_container_width=True)

if len(imgs) == 2:
    if st.button('🔍 日報を完成させる', use_container_width=True, type='primary'):
        progress = st.progress(0, text='📸 画像を判別中... (1/3)')
        try:
            api_key = os.environ.get('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY')
            client = anthropic.Anthropic(api_key=api_key)
            if is_meter(client, imgs[0]):
                meter_img, nippou_img = imgs[0], imgs[1]
            else:
                meter_img, nippou_img = imgs[1], imgs[0]
            progress.progress(33, text='✓ 判別完了 → 🔍 メーター明細と照合中... (2/3)')
        except Exception as e:
            st.error(f'エラー: {e}')
            st.stop()
        try:
                prompt = """【最重要ルール】金額は必ずメーター明細書（2枚目の画像）の値を使用すること。日報（1枚目）の金額は無視すること。

手順：
1. メーター明細書（2枚目）の各行の時刻と金額を全て読み取る
2. 日報（1枚目）の各行を読み取り、現収欄・未収欄のどちらに数字が書かれているか確認する
3. 各行について、メーター明細の金額を、日報で数字が書かれている側（現収または未収）に配置する
4. 摘要は日報の記載をそのまま使う

【絶対禁止】メーター明細にない金額を出力しないこと。日報の金額を優先しないこと。

以下の形式で出力：

## 集計
件数: N件
総人数: N人
現収合計: ¥X,XXX
未収合計: ¥X,XXX
総収: ¥X,XXX
消費税: ¥X,XXX
税抜運収: ¥X,XXX

## 明細
マークダウンテーブル。列: No / 人数 / 降車時刻 / 現収 / 未収 / 摘要

※消費税は総収÷11を10円単位で四捨五入。税抜運収は総収マイナス消費税。"""
                res = client.messages.create(
                    model='claude-opus-4-5', max_tokens=4000,
                    messages=[{'role':'user','content':[
                        {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(nippou_img)}},
                        {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(meter_img)}},
                        {'type':'text','text':prompt}
                    ]}]
                )
                text = res.content[0].text
                
                def grab(pattern):
                    m = re.search(pattern, text)
                    return m.group(1).replace(',', '').strip() if m else '0'
                
                ken = grab(r'件数[:：]\s*(\d+)')
                nin = grab(r'総人数[:：]\s*(\d+)')
                gen = grab(r'現収合計[:：]\s*¥?([\d,]+)')
                mi = grab(r'未収合計[:：]\s*¥?([\d,]+)')
                sou = grab(r'総収[:：]\s*¥?([\d,]+)')
                tax = grab(r'消費税[:：]\s*¥?([\d,]+)')
                net = grab(r'税抜運収[:：]\s*¥?([\d,]+)')
                
                fmt = lambda x: f'¥{int(x):,}'
                
                progress.progress(100, text='✓ 完成しました！')
                st.balloons()
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
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
                
                table_match = re.search(r'## 明細\s*(.+)', text, re.DOTALL)
                if table_match:
                    st.markdown(table_match.group(1))
                
                st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f'エラー: {e}')
elif files and len(files) != 2:
    st.warning(f'2枚選択してください（現在{len(files)}枚）')
