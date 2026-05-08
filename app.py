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
.title-block h1 {color: white !important; font-size: 22px !important; font-weight: 500 !important; margin: 0 0 6px !important; display: flex; align-items: center; gap: 10px;}
.title-block .subtitle {color: #d4af37; font-size: 11px; letter-spacing: 0.15em; margin: 0 0 8px;}
.title-block .divider {height: 1px; background: linear-gradient(90deg, #d4af37, transparent);}
.upload-card, .result-card {background: white; border-radius: 16px; padding: 1.25rem; margin-bottom: 1rem;}
[data-testid="stFileUploader"] section {
    background: #fafafa !important;
    border: 2px dashed #ddd !important;
    border-radius: 14px !important;
    padding: 1rem !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small {color: #999 !important; font-size: 11px !important;}
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
.metric.dark {background: #010519;}
.metric .label {font-size: 10px; color: #888; margin: 0; letter-spacing: 0.05em;}
.metric.dark .label {color: #d4af37;}
.metric .value {font-size: 15px; font-weight: 500; margin: 2px 0 0; color: #010519;}
.metric.dark .value {color: white;}
table {width: 100%; font-size: 12px; border-collapse: collapse; border-radius: 12px; overflow: hidden; border: 0.5px solid #eee;}
thead tr {background: #010519 !important; color: white !important;}
thead tr th {padding: 8px 6px !important; font-weight: 500 !important; color: white !important;}
tbody tr td {padding: 6px !important; color: #010519 !important;}
tbody tr:nth-child(even) {background: #fafafa !important;}
.stAlert {border-radius: 12px !important;}
.stSpinner > div {border-top-color: #d4af37 !important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-block">
  <h1><span style="color:#d4af37;">●</span> タクシー日報</h1>
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

st.markdown('<div class="upload-card">', unsafe_allow_html=True)
files = st.file_uploader('日報と明細の写真をアップしてください', type=['jpg','jpeg','png','heic'], accept_multiple_files=True)

imgs = []
if files:
    cols = st.columns(len(files))
    for i, f in enumerate(files):
        img = fix_orientation(Image.open(f))
        imgs.append(img)
        with cols[i]:
            st.image(img, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if len(imgs) == 2:
    if st.button('🔍 日報を完成させる', use_container_width=True, type='primary'):
        with st.spinner('画像を判別中...'):
            try:
                api_key = os.environ.get('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY')
                client = anthropic.Anthropic(api_key=api_key)
                if is_meter(client, imgs[0]):
                    meter_img, nippou_img = imgs[0], imgs[1]
                else:
                    meter_img, nippou_img = imgs[1], imgs[0]
            except Exception as e:
                st.error(f'エラー: {e}')
                st.stop()
        with st.spinner('メーター明細と照合中...'):
            try:
                prompt = """1枚目は手書きタクシー日報、2枚目はメーター明細書です。現収か未収かは日報の現収欄・未収欄に数字が書いてある方に従う。金額はメーター明細の値を使用する。摘要は日報の記載に従う。

以下の形式で出力してください：

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
