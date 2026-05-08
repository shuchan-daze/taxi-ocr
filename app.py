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

.particles {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    overflow: hidden;
    pointer-events: none;
}
.particle {
    position: absolute;
    width: 6px; height: 6px;
    background: rgba(212, 175, 55, 0.6);
    border-radius: 50%;
    box-shadow: 0 0 12px rgba(212, 175, 55, 0.8);
}
@keyframes float1 { 0%{transform:translate(0,0) rotate(0deg) scale(1)} 25%{transform:translate(60vw,30vh) rotate(180deg) scale(1.5)} 50%{transform:translate(80vw,-40vh) rotate(360deg) scale(0.5)} 75%{transform:translate(-30vw,50vh) rotate(540deg) scale(1.3)} 100%{transform:translate(0,0) rotate(720deg) scale(1)} }
@keyframes float2 { 0%{transform:translate(0,0) rotate(0deg) scale(1)} 25%{transform:translate(-70vw,40vh) rotate(-180deg) scale(0.7)} 50%{transform:translate(50vw,60vh) rotate(-360deg) scale(1.4)} 75%{transform:translate(40vw,-50vh) rotate(-540deg) scale(0.8)} 100%{transform:translate(0,0) rotate(-720deg) scale(1)} }
@keyframes float3 { 0%{transform:translate(0,0) rotate(0deg) scale(1)} 25%{transform:translate(50vw,-60vh) rotate(270deg) scale(1.6)} 50%{transform:translate(-60vw,-30vh) rotate(540deg) scale(0.6)} 75%{transform:translate(-40vw,40vh) rotate(810deg) scale(1.2)} 100%{transform:translate(0,0) rotate(1080deg) scale(1)} }
@keyframes float4 { 0%{transform:translate(0,0) rotate(0deg) scale(1)} 25%{transform:translate(-50vw,-50vh) rotate(-270deg) scale(0.8)} 50%{transform:translate(70vw,30vh) rotate(-540deg) scale(1.5)} 75%{transform:translate(20vw,-60vh) rotate(-810deg) scale(0.9)} 100%{transform:translate(0,0) rotate(-1080deg) scale(1)} }
@keyframes float5 { 0%{transform:translate(0,0) rotate(0deg)} 33%{transform:translate(80vw,80vh) rotate(360deg)} 66%{transform:translate(-80vw,-80vh) rotate(720deg)} 100%{transform:translate(0,0) rotate(1080deg)} }


































.p1 {top: 56%; left: 53%; animation: curve2 4s linear infinite;}
.p2 {top: 34%; left: 36%; animation: curve1 4s linear infinite reverse;}
.p3 {top: 54%; left: 72%; animation: curve2 8s linear infinite;}
.p4 {top: 84%; left: 67%; animation: curve1 4s linear infinite;}
.p5 {top: 52%; left: 54%; animation: curve2 8s linear infinite;}
.p6 {top: 64%; left: 89%; animation: curve2 4s linear infinite reverse;}
.p7 {top: 15%; left: 72%; animation: curve1 8s linear infinite reverse;}
.p8 {top: 45%; left: 56%; animation: curve3 3s linear infinite;}
.p9 {top: 59%; left: 31%; animation: curve2 5s linear infinite;}
.p10 {top: 64%; left: 71%; animation: curve2 4s linear infinite reverse;}
.p11 {top: 11%; left: 50%; animation: curve2 4s linear infinite;}
.p12 {top: 61%; left: 81%; animation: curve2 4s linear infinite;}
.p13 {top: 9%; left: 19%; animation: curve2 3s linear infinite reverse;}
.p14 {top: 92%; left: 58%; animation: curve1 3s linear infinite;}
.p15 {top: 23%; left: 44%; animation: curve1 7s linear infinite reverse;}
.p16 {top: 47%; left: 22%; animation: curve1 7s linear infinite;}
.p17 {top: 12%; left: 86%; animation: curve1 4s linear infinite reverse;}
.p18 {top: 74%; left: 56%; animation: curve3 4s linear infinite reverse;}
.p19 {top: 12%; left: 21%; animation: curve2 8s linear infinite;}
.p20 {top: 82%; left: 57%; animation: curve1 3s linear infinite;}
.p21 {top: 23%; left: 42%; animation: curve2 4s linear infinite reverse;}
.p22 {top: 23%; left: 31%; animation: curve3 7s linear infinite reverse;}
.p23 {top: 34%; left: 37%; animation: curve3 3s linear infinite;}
.p24 {top: 91%; left: 14%; animation: curve3 7s linear infinite;}
.p25 {top: 79%; left: 11%; animation: curve2 5s linear infinite reverse;}
.p26 {top: 56%; left: 48%; animation: curve1 6s linear infinite reverse;}
.p27 {top: 52%; left: 73%; animation: curve2 3s linear infinite;}
.p28 {top: 52%; left: 56%; animation: curve2 6s linear infinite reverse;}
.p29 {top: 88%; left: 33%; animation: curve3 8s linear infinite;}
.p30 {top: 93%; left: 45%; animation: curve2 4s linear infinite reverse;}
.p31 {top: 42%; left: 61%; animation: curve1 3s linear infinite reverse;}
.p32 {top: 37%; left: 13%; animation: curve3 7s linear infinite reverse;}
.p33 {top: 66%; left: 73%; animation: curve3 4s linear infinite reverse;}
.p34 {top: 42%; left: 57%; animation: curve2 8s linear infinite;}
.p35 {top: 41%; left: 53%; animation: curve2 8s linear infinite reverse;}
.p36 {top: 29%; left: 53%; animation: curve2 5s linear infinite reverse;}
.p37 {top: 5%; left: 90%; animation: curve3 5s linear infinite;}
.p38 {top: 90%; left: 90%; animation: curve3 4s linear infinite reverse;}
.p39 {top: 95%; left: 34%; animation: curve3 6s linear infinite reverse;}
.p40 {top: 5%; left: 19%; animation: curve2 7s linear infinite;}
.p41 {top: 5%; left: 71%; animation: curve2 5s linear infinite reverse;}
.p42 {top: 31%; left: 38%; animation: curve1 8s linear infinite reverse;}
.p43 {top: 76%; left: 72%; animation: curve2 8s linear infinite reverse;}
.p44 {top: 30%; left: 7%; animation: curve3 3s linear infinite;}
.p45 {top: 79%; left: 9%; animation: curve1 3s linear infinite reverse;}
.p46 {top: 52%; left: 76%; animation: curve2 8s linear infinite reverse;}
.p47 {top: 29%; left: 17%; animation: curve1 6s linear infinite;}
.p48 {top: 38%; left: 63%; animation: curve2 5s linear infinite;}
.p49 {top: 62%; left: 93%; animation: curve1 8s linear infinite reverse;}
.p50 {top: 76%; left: 27%; animation: curve3 5s linear infinite;}
.p51 {top: 40%; left: 64%; animation: curve1 7s linear infinite;}
.p52 {top: 66%; left: 78%; animation: curve1 8s linear infinite;}
.p53 {top: 14%; left: 73%; animation: curve1 4s linear infinite;}
.p54 {top: 19%; left: 47%; animation: curve1 6s linear infinite reverse;}
.p55 {top: 88%; left: 5%; animation: curve2 7s linear infinite reverse;}
.p56 {top: 86%; left: 6%; animation: curve3 7s linear infinite reverse;}
.p57 {top: 38%; left: 26%; animation: curve2 4s linear infinite;}
.p58 {top: 55%; left: 9%; animation: curve3 3s linear infinite;}
.p59 {top: 76%; left: 42%; animation: curve1 4s linear infinite;}
.p60 {top: 94%; left: 58%; animation: curve2 4s linear infinite;}
.p61 {top: 67%; left: 26%; animation: curve3 5s linear infinite reverse;}
.p62 {top: 14%; left: 76%; animation: curve2 4s linear infinite;}
.p63 {top: 94%; left: 50%; animation: curve2 8s linear infinite;}
.p64 {top: 91%; left: 19%; animation: curve2 8s linear infinite;}
.p65 {top: 24%; left: 74%; animation: curve1 3s linear infinite reverse;}
.p66 {top: 26%; left: 50%; animation: curve2 8s linear infinite;}
.p67 {top: 48%; left: 11%; animation: curve1 5s linear infinite;}
.p68 {top: 44%; left: 27%; animation: curve1 8s linear infinite;}
.p69 {top: 68%; left: 87%; animation: curve1 7s linear infinite;}
.p70 {top: 53%; left: 92%; animation: curve2 3s linear infinite reverse;}
.p71 {top: 82%; left: 15%; animation: curve2 4s linear infinite reverse;}
.p72 {top: 52%; left: 37%; animation: curve2 5s linear infinite;}
.p73 {top: 79%; left: 55%; animation: curve3 3s linear infinite;}
.p74 {top: 21%; left: 6%; animation: curve2 5s linear infinite reverse;}
.p75 {top: 42%; left: 20%; animation: curve1 6s linear infinite;}
.p76 {top: 10%; left: 50%; animation: curve2 4s linear infinite reverse;}
.p77 {top: 47%; left: 89%; animation: curve1 5s linear infinite reverse;}
.p78 {top: 39%; left: 83%; animation: curve2 4s linear infinite;}
.p79 {top: 93%; left: 91%; animation: curve3 3s linear infinite reverse;}
.p80 {top: 58%; left: 70%; animation: curve2 8s linear infinite;}
.p81 {top: 72%; left: 57%; animation: curve2 3s linear infinite;}
.p82 {top: 87%; left: 38%; animation: curve2 4s linear infinite;}
.p83 {top: 60%; left: 5%; animation: curve1 7s linear infinite;}
.p84 {top: 21%; left: 28%; animation: curve3 8s linear infinite;}
.p85 {top: 37%; left: 28%; animation: curve1 7s linear infinite;}
.p86 {top: 5%; left: 87%; animation: curve2 3s linear infinite reverse;}
.p87 {top: 62%; left: 14%; animation: curve2 4s linear infinite;}
.p88 {top: 48%; left: 60%; animation: curve1 4s linear infinite;}
.p89 {top: 52%; left: 69%; animation: curve2 4s linear infinite reverse;}
.p90 {top: 31%; left: 17%; animation: curve2 6s linear infinite;}
.p91 {top: 27%; left: 22%; animation: curve2 6s linear infinite;}
.p92 {top: 92%; left: 37%; animation: curve2 4s linear infinite;}
.p93 {top: 35%; left: 35%; animation: curve2 7s linear infinite reverse;}
.p94 {top: 55%; left: 72%; animation: curve1 7s linear infinite;}
.p95 {top: 37%; left: 46%; animation: curve3 7s linear infinite reverse;}
.p96 {top: 29%; left: 17%; animation: curve1 8s linear infinite;}
.p97 {top: 60%; left: 12%; animation: curve2 5s linear infinite;}
.p98 {top: 89%; left: 42%; animation: curve3 4s linear infinite reverse;}
.p99 {top: 6%; left: 78%; animation: curve3 7s linear infinite;}
.p100 {top: 51%; left: 19%; animation: curve3 4s linear infinite reverse;}

@keyframes curve1 {
  0% {transform: translate(0,0) rotate(0deg);}
  25% {transform: translate(35vw, -15vh) rotate(180deg);}
  50% {transform: translate(60vw, 20vh) rotate(360deg);}
  75% {transform: translate(25vw, 45vh) rotate(540deg);}
  100% {transform: translate(0,0) rotate(720deg);}
}
@keyframes curve2 {
  0% {transform: translate(0,0) rotate(0deg);}
  25% {transform: translate(-30vw, 20vh) rotate(-180deg);}
  50% {transform: translate(-55vw, -10vh) rotate(-360deg);}
  75% {transform: translate(-15vw, -40vh) rotate(-540deg);}
  100% {transform: translate(0,0) rotate(-720deg);}
}
@keyframes curve3 {
  0% {transform: translate(0,0) rotate(0deg);}
  25% {transform: translate(40vw, 30vh) rotate(180deg);}
  50% {transform: translate(10vw, 55vh) rotate(360deg);}
  75% {transform: translate(-30vw, 30vh) rotate(540deg);}
  100% {transform: translate(0,0) rotate(720deg);}
}
.particle {animation-timing-function: cubic-bezier(0.45, 0, 0.55, 1) !important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-block">
  <h1>AIタクシー日報<span style="font-size: 13px; color: #d4af37; font-weight: 400; margin-left: 8px;">by 怒りの山本</span></h1>
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
        loader = st.empty()
        import time
        for pct in [3, 8, 14, 21, 29]:
            loader.markdown(f'<div class="big-overlay"><div class="particles"><span class="particle p1"></span><span class="particle p2"></span><span class="particle p3"></span><span class="particle p4"></span><span class="particle p5"></span><span class="particle p6"></span><span class="particle p7"></span><span class="particle p8"></span><span class="particle p9"></span><span class="particle p10"></span><span class="particle p11"></span><span class="particle p12"></span><span class="particle p13"></span><span class="particle p14"></span><span class="particle p15"></span><span class="particle p16"></span><span class="particle p17"></span><span class="particle p18"></span><span class="particle p19"></span><span class="particle p20"></span><span class="particle p21"></span><span class="particle p22"></span><span class="particle p23"></span><span class="particle p24"></span><span class="particle p25"></span><span class="particle p26"></span><span class="particle p27"></span><span class="particle p28"></span><span class="particle p29"></span><span class="particle p30"></span><span class="particle p31"></span><span class="particle p32"></span><span class="particle p33"></span><span class="particle p34"></span><span class="particle p35"></span><span class="particle p36"></span><span class="particle p37"></span><span class="particle p38"></span><span class="particle p39"></span><span class="particle p40"></span><span class="particle p41"></span><span class="particle p42"></span><span class="particle p43"></span><span class="particle p44"></span><span class="particle p45"></span><span class="particle p46"></span><span class="particle p47"></span><span class="particle p48"></span><span class="particle p49"></span><span class="particle p50"></span><span class="particle p51"></span><span class="particle p52"></span><span class="particle p53"></span><span class="particle p54"></span><span class="particle p55"></span><span class="particle p56"></span><span class="particle p57"></span><span class="particle p58"></span><span class="particle p59"></span><span class="particle p60"></span><span class="particle p61"></span><span class="particle p62"></span><span class="particle p63"></span><span class="particle p64"></span><span class="particle p65"></span><span class="particle p66"></span><span class="particle p67"></span><span class="particle p68"></span><span class="particle p69"></span><span class="particle p70"></span><span class="particle p71"></span><span class="particle p72"></span><span class="particle p73"></span><span class="particle p74"></span><span class="particle p75"></span><span class="particle p76"></span><span class="particle p77"></span><span class="particle p78"></span><span class="particle p79"></span><span class="particle p80"></span><span class="particle p81"></span><span class="particle p82"></span><span class="particle p83"></span><span class="particle p84"></span><span class="particle p85"></span><span class="particle p86"></span><span class="particle p87"></span><span class="particle p88"></span><span class="particle p89"></span><span class="particle p90"></span><span class="particle p91"></span><span class="particle p92"></span><span class="particle p93"></span><span class="particle p94"></span><span class="particle p95"></span><span class="particle p96"></span><span class="particle p97"></span><span class="particle p98"></span><span class="particle p99"></span><span class="particle p100"></span></div><div class="big-num">{pct}%</div><div class="big-label">画像を判別中</div></div>', unsafe_allow_html=True)
            time.sleep(0.15)
        try:
            api_key = os.environ.get('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY')
            client = anthropic.Anthropic(api_key=api_key)
            if is_meter(client, imgs[0]):
                meter_img, nippou_img = imgs[0], imgs[1]
            else:
                meter_img, nippou_img = imgs[1], imgs[0]
            for pct in [34, 42, 51, 58, 65, 71]:
                loader.markdown(f'<div class="big-overlay"><div class="particles"><span class="particle p1"></span><span class="particle p2"></span><span class="particle p3"></span><span class="particle p4"></span><span class="particle p5"></span><span class="particle p6"></span><span class="particle p7"></span><span class="particle p8"></span><span class="particle p9"></span><span class="particle p10"></span><span class="particle p11"></span><span class="particle p12"></span><span class="particle p13"></span><span class="particle p14"></span><span class="particle p15"></span><span class="particle p16"></span><span class="particle p17"></span><span class="particle p18"></span><span class="particle p19"></span><span class="particle p20"></span><span class="particle p21"></span><span class="particle p22"></span><span class="particle p23"></span><span class="particle p24"></span><span class="particle p25"></span><span class="particle p26"></span><span class="particle p27"></span><span class="particle p28"></span><span class="particle p29"></span><span class="particle p30"></span><span class="particle p31"></span><span class="particle p32"></span><span class="particle p33"></span><span class="particle p34"></span><span class="particle p35"></span><span class="particle p36"></span><span class="particle p37"></span><span class="particle p38"></span><span class="particle p39"></span><span class="particle p40"></span><span class="particle p41"></span><span class="particle p42"></span><span class="particle p43"></span><span class="particle p44"></span><span class="particle p45"></span><span class="particle p46"></span><span class="particle p47"></span><span class="particle p48"></span><span class="particle p49"></span><span class="particle p50"></span><span class="particle p51"></span><span class="particle p52"></span><span class="particle p53"></span><span class="particle p54"></span><span class="particle p55"></span><span class="particle p56"></span><span class="particle p57"></span><span class="particle p58"></span><span class="particle p59"></span><span class="particle p60"></span><span class="particle p61"></span><span class="particle p62"></span><span class="particle p63"></span><span class="particle p64"></span><span class="particle p65"></span><span class="particle p66"></span><span class="particle p67"></span><span class="particle p68"></span><span class="particle p69"></span><span class="particle p70"></span><span class="particle p71"></span><span class="particle p72"></span><span class="particle p73"></span><span class="particle p74"></span><span class="particle p75"></span><span class="particle p76"></span><span class="particle p77"></span><span class="particle p78"></span><span class="particle p79"></span><span class="particle p80"></span><span class="particle p81"></span><span class="particle p82"></span><span class="particle p83"></span><span class="particle p84"></span><span class="particle p85"></span><span class="particle p86"></span><span class="particle p87"></span><span class="particle p88"></span><span class="particle p89"></span><span class="particle p90"></span><span class="particle p91"></span><span class="particle p92"></span><span class="particle p93"></span><span class="particle p94"></span><span class="particle p95"></span><span class="particle p96"></span><span class="particle p97"></span><span class="particle p98"></span><span class="particle p99"></span><span class="particle p100"></span></div><div class="big-num">{pct}%</div><div class="big-label">明細と照合中</div></div>', unsafe_allow_html=True)
                time.sleep(0.2)
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
                
                for pct in [82, 91, 97, 100]:
                    loader.markdown(f'<div class="big-overlay"><div class="particles"><span class="particle p1"></span><span class="particle p2"></span><span class="particle p3"></span><span class="particle p4"></span><span class="particle p5"></span><span class="particle p6"></span><span class="particle p7"></span><span class="particle p8"></span><span class="particle p9"></span><span class="particle p10"></span><span class="particle p11"></span><span class="particle p12"></span><span class="particle p13"></span><span class="particle p14"></span><span class="particle p15"></span><span class="particle p16"></span><span class="particle p17"></span><span class="particle p18"></span><span class="particle p19"></span><span class="particle p20"></span><span class="particle p21"></span><span class="particle p22"></span><span class="particle p23"></span><span class="particle p24"></span><span class="particle p25"></span><span class="particle p26"></span><span class="particle p27"></span><span class="particle p28"></span><span class="particle p29"></span><span class="particle p30"></span><span class="particle p31"></span><span class="particle p32"></span><span class="particle p33"></span><span class="particle p34"></span><span class="particle p35"></span><span class="particle p36"></span><span class="particle p37"></span><span class="particle p38"></span><span class="particle p39"></span><span class="particle p40"></span><span class="particle p41"></span><span class="particle p42"></span><span class="particle p43"></span><span class="particle p44"></span><span class="particle p45"></span><span class="particle p46"></span><span class="particle p47"></span><span class="particle p48"></span><span class="particle p49"></span><span class="particle p50"></span><span class="particle p51"></span><span class="particle p52"></span><span class="particle p53"></span><span class="particle p54"></span><span class="particle p55"></span><span class="particle p56"></span><span class="particle p57"></span><span class="particle p58"></span><span class="particle p59"></span><span class="particle p60"></span><span class="particle p61"></span><span class="particle p62"></span><span class="particle p63"></span><span class="particle p64"></span><span class="particle p65"></span><span class="particle p66"></span><span class="particle p67"></span><span class="particle p68"></span><span class="particle p69"></span><span class="particle p70"></span><span class="particle p71"></span><span class="particle p72"></span><span class="particle p73"></span><span class="particle p74"></span><span class="particle p75"></span><span class="particle p76"></span><span class="particle p77"></span><span class="particle p78"></span><span class="particle p79"></span><span class="particle p80"></span><span class="particle p81"></span><span class="particle p82"></span><span class="particle p83"></span><span class="particle p84"></span><span class="particle p85"></span><span class="particle p86"></span><span class="particle p87"></span><span class="particle p88"></span><span class="particle p89"></span><span class="particle p90"></span><span class="particle p91"></span><span class="particle p92"></span><span class="particle p93"></span><span class="particle p94"></span><span class="particle p95"></span><span class="particle p96"></span><span class="particle p97"></span><span class="particle p98"></span><span class="particle p99"></span><span class="particle p100"></span></div><div class="big-num">{pct}%</div><div class="big-label">完成しました</div></div>', unsafe_allow_html=True)
                    time.sleep(0.15)
                loader.empty()
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
