import streamlit as st
import anthropic
import base64
import io
import os
import re
import time
from PIL import Image, ExifTags
from pillow_heif import register_heif_opener

register_heif_opener()
st.set_page_config(page_title='タクシー日報', layout='centered', initial_sidebar_state='collapsed')

PARTICLES_HTML = """<span class="particle p1"></span><span class="particle p2"></span><span class="particle p3"></span><span class="particle p4"></span><span class="particle p5"></span><span class="particle p6"></span><span class="particle p7"></span><span class="particle p8"></span><span class="particle p9"></span><span class="particle p10"></span><span class="particle p11"></span><span class="particle p12"></span><span class="particle p13"></span><span class="particle p14"></span><span class="particle p15"></span><span class="particle p16"></span><span class="particle p17"></span><span class="particle p18"></span><span class="particle p19"></span><span class="particle p20"></span><span class="particle p21"></span><span class="particle p22"></span><span class="particle p23"></span><span class="particle p24"></span><span class="particle p25"></span><span class="particle p26"></span><span class="particle p27"></span><span class="particle p28"></span><span class="particle p29"></span><span class="particle p30"></span><span class="particle p31"></span><span class="particle p32"></span><span class="particle p33"></span><span class="particle p34"></span><span class="particle p35"></span><span class="particle p36"></span><span class="particle p37"></span><span class="particle p38"></span><span class="particle p39"></span><span class="particle p40"></span><span class="particle p41"></span><span class="particle p42"></span><span class="particle p43"></span><span class="particle p44"></span><span class="particle p45"></span><span class="particle p46"></span><span class="particle p47"></span><span class="particle p48"></span><span class="particle p49"></span><span class="particle p50"></span><span class="particle p51"></span><span class="particle p52"></span><span class="particle p53"></span><span class="particle p54"></span><span class="particle p55"></span><span class="particle p56"></span><span class="particle p57"></span><span class="particle p58"></span><span class="particle p59"></span><span class="particle p60"></span><span class="particle p61"></span><span class="particle p62"></span><span class="particle p63"></span><span class="particle p64"></span><span class="particle p65"></span><span class="particle p66"></span><span class="particle p67"></span><span class="particle p68"></span><span class="particle p69"></span><span class="particle p70"></span><span class="particle p71"></span><span class="particle p72"></span><span class="particle p73"></span><span class="particle p74"></span><span class="particle p75"></span><span class="particle p76"></span><span class="particle p77"></span><span class="particle p78"></span><span class="particle p79"></span><span class="particle p80"></span><span class="particle p81"></span><span class="particle p82"></span><span class="particle p83"></span><span class="particle p84"></span><span class="particle p85"></span><span class="particle p86"></span><span class="particle p87"></span><span class="particle p88"></span><span class="particle p89"></span><span class="particle p90"></span><span class="particle p91"></span><span class="particle p92"></span><span class="particle p93"></span><span class="particle p94"></span><span class="particle p95"></span><span class="particle p96"></span><span class="particle p97"></span><span class="particle p98"></span><span class="particle p99"></span><span class="particle p100"></span>"""

st.markdown("""
<style>
/* ===== 基本 ===== */
#MainMenu, footer, header {visibility: hidden;}
.stApp {background: #010519;}
.stApp > header {background: transparent;}
.block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 600px;}

/* ===== タイトル ===== */
.title-block {margin-bottom: 1.5rem;}
.title-block h1 {color: #d4af37 !important; font-size: 32px !important; font-weight: 600 !important; margin: 0 0 6px !important;}
.title-block h1 * {color: #d4af37 !important;}
.title-block .subtitle {color: #d4af37; font-size: 11px; letter-spacing: 0.15em; margin: 0 0 8px;}
.title-block .divider {height: 1px; background: linear-gradient(90deg, #d4af37, transparent);}

/* ===== カード ===== */
.upload-card, .result-card {background: white; border-radius: 16px; padding: 1.25rem; margin-bottom: 1rem;}
.upload-card:empty, .result-card:empty {display: none;}
.result-card h1, .result-card h2, .result-card h3, .result-card h4 {color: #010519 !important;}

/* ===== ファイルアップローダー ===== */
[data-testid="stFileUploader"] section {background: #fafafa; border: 2px dashed #ddd; border-radius: 14px; padding: 0.5rem; display: flex; flex-direction: row; align-items: center; gap: 12px;}
[data-testid="stFileUploader"] section > button {margin-left: auto !important; order: 99 !important;}
[data-testid="stFileUploader"] label {color: #010519; font-weight: 500;}
[data-testid="stFileUploaderDropzoneInstructions"] {padding: 0; margin: 0;}
[data-testid="stFileUploaderDropzoneInstructions"] span {font-size: 9px; color: #888; line-height: 1;}
[data-testid="stFileUploaderDropzoneInstructions"] > div::after {content: "日報と営業明細書をアップしてください"; color: #010519; font-size: 13px; display: block; margin-top: 4px;}
[data-testid="stFileUploader"] button {background: #010519 !important; color: white !important; border: none !important;}
[data-testid="stFileUploader"] button * {color: white !important;}
[data-testid="stFileUploader"] button:hover {background: #0a1845 !important;}

/* ===== ボタン ===== */
.stButton button {background: #d4af37 !important; color: #010519 !important; border: none !important; border-radius: 16px !important; padding: 1rem !important; font-size: 15px !important; font-weight: 500 !important; box-shadow: 0 4px 14px rgba(212,175,55,0.17); letter-spacing: 0.05em; width: 100%;}
.stButton button:hover {background: #c89f2e !important; transform: translateY(-1px);}

/* ===== 画像 ===== */
.stImage img {border-radius: 12px;}

/* ===== 結果カード内部 ===== */
.complete-bar {background: #f5f5f7; border-radius: 12px; padding: 14px 16px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; border-left: 3px solid #d4af37;}
.complete-bar .label {font-size: 16px; font-weight: 500; color: #010519; margin: 0;}
.complete-bar .stats {font-size: 32px; font-weight: 700; color: #010519; margin: 0;}
.complete-bar .stats small {font-size: 18px; color: #888;}

.metric-grid-3 {display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 8px;}
.metric-grid-2 {display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 14px;}
.metric {background: #f5f5f7; border-radius: 10px; padding: 8px 10px;}
.metric.dark {background: #d4af37;}
.metric .label {font-size: 15px; color: #888; margin: 0; letter-spacing: 0.05em; font-weight: 500;}
.metric .value {font-size: 38px; font-weight: 700; margin: 2px 0 0; color: #010519;}
.metric.dark .label, .metric.dark .value {color: #010519 !important;}

/* ===== テーブル ===== */
table {width: 100%; font-size: 12px; border-collapse: collapse; border-radius: 12px; overflow: hidden; border: 0.5px solid #eee;}
thead tr, thead tr th {background: #010519 !important; color: white !important; padding: 8px 6px !important; font-weight: 500 !important;}
tbody tr td {padding: 6px !important; color: #010519 !important; background: white !important;}
tbody tr:nth-child(even) td {background: #d8d8dc !important;}
.stAlert {border-radius: 12px;}

/* ===== ローディングオーバーレイ ===== */
.big-overlay {position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(1,5,25,0.92); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); z-index: 99999; display: flex; flex-direction: column; align-items: center; justify-content: center; pointer-events: none;}
.big-num {font-size: 120px; font-weight: 700; color: rgba(255,255,255,0.15); letter-spacing: -0.05em; line-height: 1; margin-bottom: 16px;}
.big-label {font-size: 14px; color: #d4af37; letter-spacing: 0.2em; font-weight: 400;}

/* ===== 粒子 ===== */
.particles {position: absolute; top: 0; left: 0; right: 0; bottom: 0; overflow: hidden; pointer-events: none;}
.particle {position: absolute; border-radius: 50%; background: rgba(255,255,255,0.5);}

@keyframes warp1{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:4.1px;height:4.1px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(47.5vmax,52.7vmax) scale(1);opacity:0;filter:blur(0);width:11.6px;height:11.6px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p1{top:46%;left:44%;width:4.1px;height:4.1px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp1 2.23s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.53s;}
@keyframes warp2{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:10.2px;height:10.2px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-121.6vmax,65.2vmax) scale(1);opacity:0;filter:blur(0);width:21.3px;height:21.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p2{top:40%;left:77%;width:10.2px;height:10.2px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp2 1.96s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.17s;}
@keyframes warp3{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:5.5px;height:5.5px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-79.6vmax,19.7vmax) scale(1);opacity:0;filter:blur(0);width:13.2px;height:13.2px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p3{top:34%;left:42%;width:5.5px;height:5.5px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp3 3.24s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.36s;}
@keyframes warp4{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:9.2px;height:9.2px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-76.9vmax,54.0vmax) scale(1);opacity:0;filter:blur(0);width:31.6px;height:31.6px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p4{top:55%;left:75%;width:9.2px;height:9.2px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp4 1.92s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.70s;}
@keyframes warp5{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:6.0px;height:6.0px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(111.0vmax,-80.4vmax) scale(1);opacity:0;filter:blur(0);width:11.2px;height:11.2px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p5{top:81%;left:74%;width:6.0px;height:6.0px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp5 2.59s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.21s;}
@keyframes warp6{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.4px;height:1.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-67.7vmax,-46.3vmax) scale(1);opacity:0;filter:blur(0);width:5.8px;height:5.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p6{top:71%;left:35%;width:1.4px;height:1.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp6 4.77s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.64s;}
@keyframes warp7{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.2px;height:1.2px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(129.1vmax,-54.2vmax) scale(1);opacity:0;filter:blur(0);width:3.5px;height:3.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p7{top:25%;left:68%;width:1.2px;height:1.2px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp7 2.72s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.24s;}
@keyframes warp8{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.8px;height:1.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(54.2vmax,-39.4vmax) scale(1);opacity:0;filter:blur(0);width:3.4px;height:3.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p8{top:40%;left:66%;width:1.8px;height:1.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp8 4.04s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.77s;}
@keyframes warp9{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.4px;height:8.4px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(67.1vmax,-35.7vmax) scale(1);opacity:0;filter:blur(0);width:31.5px;height:31.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p9{top:75%;left:60%;width:8.4px;height:8.4px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp9 2.14s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.87s;}
@keyframes warp10{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:6.9px;height:6.9px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(71.2vmax,65.8vmax) scale(1);opacity:0;filter:blur(0);width:34.1px;height:34.1px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p10{top:27%;left:30%;width:6.9px;height:6.9px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp10 1.47s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.71s;}
@keyframes warp11{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.8px;height:2.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(27.3vmax,-87.9vmax) scale(1);opacity:0;filter:blur(0);width:5.6px;height:5.6px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p11{top:78%;left:55%;width:2.8px;height:2.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp11 2.80s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.29s;}
@keyframes warp12{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.4px;height:2.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-56.4vmax,92.1vmax) scale(1);opacity:0;filter:blur(0);width:4.5px;height:4.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p12{top:21%;left:16%;width:2.4px;height:2.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp12 3.47s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.29s;}
@keyframes warp13{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:4.2px;height:4.2px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(26.8vmax,58.1vmax) scale(1);opacity:0;filter:blur(0);width:12.9px;height:12.9px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p13{top:26%;left:83%;width:4.2px;height:4.2px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp13 3.37s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.89s;}
@keyframes warp14{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:5.3px;height:5.3px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(78.7vmax,61.7vmax) scale(1);opacity:0;filter:blur(0);width:9.4px;height:9.4px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p14{top:54%;left:43%;width:5.3px;height:5.3px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp14 2.17s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.24s;}
@keyframes warp15{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:10.3px;height:10.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(83.6vmax,-76.0vmax) scale(1);opacity:0;filter:blur(0);width:25.8px;height:25.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p15{top:25%;left:71%;width:10.3px;height:10.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp15 2.41s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.02s;}
@keyframes warp16{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:7.8px;height:7.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-90.0vmax,-19.1vmax) scale(1);opacity:0;filter:blur(0);width:30.3px;height:30.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p16{top:76%;left:56%;width:7.8px;height:7.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp16 1.77s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.16s;}
@keyframes warp17{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:11.0px;height:11.0px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(35.2vmax,96.8vmax) scale(1);opacity:0;filter:blur(0);width:22.4px;height:22.4px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p17{top:71%;left:63%;width:11.0px;height:11.0px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp17 2.32s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.38s;}
@keyframes warp18{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.1px;height:8.1px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(22.8vmax,-90.2vmax) scale(1);opacity:0;filter:blur(0);width:24.4px;height:24.4px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p18{top:36%;left:39%;width:8.1px;height:8.1px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp18 2.04s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.97s;}
@keyframes warp19{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:7.4px;height:7.4px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(124.0vmax,2.8vmax) scale(1);opacity:0;filter:blur(0);width:32.9px;height:32.9px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p19{top:66%;left:59%;width:7.4px;height:7.4px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp19 1.89s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.01s;}
@keyframes warp20{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:5.8px;height:5.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(25.2vmax,-113.2vmax) scale(1);opacity:0;filter:blur(0);width:13.9px;height:13.9px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p20{top:80%;left:36%;width:5.8px;height:5.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp20 3.39s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.06s;}
@keyframes warp21{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.5px;height:8.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-4.9vmax,-72.8vmax) scale(1);opacity:0;filter:blur(0);width:28.4px;height:28.4px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p21{top:40%;left:51%;width:8.5px;height:8.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp21 2.22s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.30s;}
@keyframes warp22{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.9px;height:2.9px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(24.8vmax,67.6vmax) scale(1);opacity:0;filter:blur(0);width:4.3px;height:4.3px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p22{top:52%;left:62%;width:2.9px;height:2.9px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp22 4.88s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.17s;}
@keyframes warp23{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:5.4px;height:5.4px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(84.2vmax,-81.2vmax) scale(1);opacity:0;filter:blur(0);width:9.6px;height:9.6px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p23{top:31%;left:57%;width:5.4px;height:5.4px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp23 3.28s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.78s;}
@keyframes warp24{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:4.3px;height:4.3px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-0.1vmax,95.0vmax) scale(1);opacity:0;filter:blur(0);width:13.7px;height:13.7px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p24{top:61%;left:37%;width:4.3px;height:4.3px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp24 2.59s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.38s;}
@keyframes warp25{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.3px;height:8.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-35.1vmax,-59.4vmax) scale(1);opacity:0;filter:blur(0);width:32.4px;height:32.4px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p25{top:75%;left:76%;width:8.3px;height:8.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp25 1.89s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.99s;}
@keyframes warp26{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:6.1px;height:6.1px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-30.8vmax,51.5vmax) scale(1);opacity:0;filter:blur(0);width:24.9px;height:24.9px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p26{top:24%;left:78%;width:6.1px;height:6.1px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp26 1.94s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.13s;}
@keyframes warp27{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:6.1px;height:6.1px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(43.3vmax,49.8vmax) scale(1);opacity:0;filter:blur(0);width:24.8px;height:24.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p27{top:36%;left:48%;width:6.1px;height:6.1px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp27 1.73s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.19s;}
@keyframes warp28{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:7.4px;height:7.4px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(105.7vmax,39.9vmax) scale(1);opacity:0;filter:blur(0);width:31.3px;height:31.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p28{top:71%;left:35%;width:7.4px;height:7.4px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp28 1.53s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.75s;}
@keyframes warp29{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:3.5px;height:3.5px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-79.1vmax,-31.1vmax) scale(1);opacity:0;filter:blur(0);width:9.7px;height:9.7px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p29{top:24%;left:61%;width:3.5px;height:3.5px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp29 3.12s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.69s;}
@keyframes warp30{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:5.0px;height:5.0px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-12.2vmax,-76.0vmax) scale(1);opacity:0;filter:blur(0);width:12.9px;height:12.9px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p30{top:29%;left:25%;width:5.0px;height:5.0px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp30 2.06s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.35s;}
@keyframes warp31{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:9.9px;height:9.9px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-35.4vmax,55.7vmax) scale(1);opacity:0;filter:blur(0);width:22.5px;height:22.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p31{top:35%;left:44%;width:9.9px;height:9.9px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp31 2.32s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.24s;}
@keyframes warp32{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:3.6px;height:3.6px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-126.0vmax,2.7vmax) scale(1);opacity:0;filter:blur(0);width:9.1px;height:9.1px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p32{top:33%;left:29%;width:3.6px;height:3.6px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp32 3.04s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.05s;}
@keyframes warp33{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:5.8px;height:5.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-14.6vmax,-136.2vmax) scale(1);opacity:0;filter:blur(0);width:12.8px;height:12.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p33{top:71%;left:45%;width:5.8px;height:5.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp33 3.29s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.32s;}
@keyframes warp34{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.8px;height:2.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-2.5vmax,135.0vmax) scale(1);opacity:0;filter:blur(0);width:5.5px;height:5.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p34{top:62%;left:71%;width:2.8px;height:2.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp34 2.63s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.59s;}
@keyframes warp35{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:5.8px;height:5.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(35.5vmax,-90.3vmax) scale(1);opacity:0;filter:blur(0);width:8.8px;height:8.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p35{top:51%;left:16%;width:5.8px;height:5.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp35 2.29s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.97s;}
@keyframes warp36{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.1px;height:1.1px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-32.9vmax,-54.9vmax) scale(1);opacity:0;filter:blur(0);width:3.5px;height:3.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p36{top:57%;left:55%;width:1.1px;height:1.1px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp36 3.42s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.08s;}
@keyframes warp37{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.1px;height:2.1px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-7.8vmax,-112.7vmax) scale(1);opacity:0;filter:blur(0);width:5.1px;height:5.1px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p37{top:51%;left:17%;width:2.1px;height:2.1px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp37 3.74s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.60s;}
@keyframes warp38{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.3px;height:1.3px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(4.8vmax,92.9vmax) scale(1);opacity:0;filter:blur(0);width:4.2px;height:4.2px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p38{top:42%;left:21%;width:1.3px;height:1.3px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp38 2.91s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.27s;}
@keyframes warp39{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:3.0px;height:3.0px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(67.3vmax,-48.5vmax) scale(1);opacity:0;filter:blur(0);width:13.7px;height:13.7px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p39{top:31%;left:40%;width:3.0px;height:3.0px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp39 2.87s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.25s;}
@keyframes warp40{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:3.5px;height:3.5px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(58.4vmax,-26.3vmax) scale(1);opacity:0;filter:blur(0);width:12.6px;height:12.6px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p40{top:15%;left:34%;width:3.5px;height:3.5px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp40 2.66s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.75s;}
@keyframes warp41{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:3.2px;height:3.2px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(93.1vmax,101.8vmax) scale(1);opacity:0;filter:blur(0);width:11.5px;height:11.5px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p41{top:70%;left:58%;width:3.2px;height:3.2px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp41 1.95s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.01s;}
@keyframes warp42{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.5px;height:2.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-62.7vmax,-52.8vmax) scale(1);opacity:0;filter:blur(0);width:4.5px;height:4.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p42{top:70%;left:27%;width:2.5px;height:2.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp42 2.84s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.95s;}
@keyframes warp43{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.3px;height:1.3px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-58.2vmax,-109.5vmax) scale(1);opacity:0;filter:blur(0);width:5.1px;height:5.1px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p43{top:81%;left:36%;width:1.3px;height:1.3px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp43 4.70s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.40s;}
@keyframes warp44{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.5px;height:1.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-68.2vmax,-10.5vmax) scale(1);opacity:0;filter:blur(0);width:4.6px;height:4.6px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p44{top:65%;left:68%;width:1.5px;height:1.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp44 3.10s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.30s;}
@keyframes warp45{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.0px;height:8.0px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-92.2vmax,38.7vmax) scale(1);opacity:0;filter:blur(0);width:22.8px;height:22.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p45{top:19%;left:18%;width:8.0px;height:8.0px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp45 1.49s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.20s;}
@keyframes warp46{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:3.6px;height:3.6px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-85.8vmax,-45.3vmax) scale(1);opacity:0;filter:blur(0);width:13.4px;height:13.4px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p46{top:16%;left:47%;width:3.6px;height:3.6px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp46 2.13s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.46s;}
@keyframes warp47{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.7px;height:1.7px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-7.6vmax,116.8vmax) scale(1);opacity:0;filter:blur(0);width:3.4px;height:3.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p47{top:82%;left:54%;width:1.7px;height:1.7px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp47 2.65s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.83s;}
@keyframes warp48{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:3.7px;height:3.7px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-63.2vmax,77.5vmax) scale(1);opacity:0;filter:blur(0);width:11.6px;height:11.6px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p48{top:17%;left:63%;width:3.7px;height:3.7px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp48 3.31s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.98s;}
@keyframes warp49{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.6px;height:2.6px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(24.2vmax,136.9vmax) scale(1);opacity:0;filter:blur(0);width:3.1px;height:3.1px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p49{top:42%;left:37%;width:2.6px;height:2.6px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp49 3.13s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.77s;}
@keyframes warp50{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:6.0px;height:6.0px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-38.2vmax,-99.9vmax) scale(1);opacity:0;filter:blur(0);width:21.7px;height:21.7px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p50{top:25%;left:70%;width:6.0px;height:6.0px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp50 1.85s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.23s;}
@keyframes warp51{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:5.3px;height:5.3px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-17.5vmax,-71.9vmax) scale(1);opacity:0;filter:blur(0);width:13.4px;height:13.4px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p51{top:56%;left:48%;width:5.3px;height:5.3px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp51 2.26s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.97s;}
@keyframes warp52{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.4px;height:1.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(99.1vmax,-97.5vmax) scale(1);opacity:0;filter:blur(0);width:4.0px;height:4.0px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p52{top:49%;left:28%;width:1.4px;height:1.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp52 4.01s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.85s;}
@keyframes warp53{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.7px;height:8.7px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(12.5vmax,-73.9vmax) scale(1);opacity:0;filter:blur(0);width:20.3px;height:20.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p53{top:24%;left:48%;width:8.7px;height:8.7px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp53 2.14s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.13s;}
@keyframes warp54{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.6px;height:8.6px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(137.0vmax,-3.1vmax) scale(1);opacity:0;filter:blur(0);width:31.9px;height:31.9px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p54{top:80%;left:56%;width:8.6px;height:8.6px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp54 2.09s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.69s;}
@keyframes warp55{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.8px;height:2.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-79.9vmax,-51.4vmax) scale(1);opacity:0;filter:blur(0);width:4.2px;height:4.2px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p55{top:23%;left:41%;width:2.8px;height:2.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp55 3.60s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.96s;}
@keyframes warp56{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:6.5px;height:6.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(54.5vmax,-63.9vmax) scale(1);opacity:0;filter:blur(0);width:20.3px;height:20.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p56{top:31%;left:25%;width:6.5px;height:6.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp56 1.76s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.65s;}
@keyframes warp57{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:9.5px;height:9.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(20.9vmax,69.9vmax) scale(1);opacity:0;filter:blur(0);width:20.3px;height:20.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p57{top:42%;left:56%;width:9.5px;height:9.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp57 1.28s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.72s;}
@keyframes warp58{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:3.5px;height:3.5px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-20.1vmax,-70.2vmax) scale(1);opacity:0;filter:blur(0);width:8.8px;height:8.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p58{top:37%;left:51%;width:3.5px;height:3.5px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp58 2.33s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.74s;}
@keyframes warp59{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:4.2px;height:4.2px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-26.6vmax,75.5vmax) scale(1);opacity:0;filter:blur(0);width:8.6px;height:8.6px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p59{top:82%;left:49%;width:4.2px;height:4.2px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp59 3.08s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.91s;}
@keyframes warp60{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.5px;height:2.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-75.2vmax,61.3vmax) scale(1);opacity:0;filter:blur(0);width:5.5px;height:5.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p60{top:75%;left:47%;width:2.5px;height:2.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp60 3.94s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.87s;}
@keyframes warp61{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:7.8px;height:7.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-78.3vmax,-88.3vmax) scale(1);opacity:0;filter:blur(0);width:26.7px;height:26.7px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p61{top:47%;left:79%;width:7.8px;height:7.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp61 1.60s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.76s;}
@keyframes warp62{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:6.8px;height:6.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(118.3vmax,56.2vmax) scale(1);opacity:0;filter:blur(0);width:27.5px;height:27.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p62{top:81%;left:60%;width:6.8px;height:6.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp62 1.78s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.58s;}
@keyframes warp63{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.7px;height:1.7px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(70.8vmax,4.7vmax) scale(1);opacity:0;filter:blur(0);width:5.4px;height:5.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p63{top:25%;left:66%;width:1.7px;height:1.7px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp63 3.53s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.43s;}
@keyframes warp64{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.4px;height:1.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(28.0vmax,72.8vmax) scale(1);opacity:0;filter:blur(0);width:5.8px;height:5.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p64{top:53%;left:45%;width:1.4px;height:1.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp64 4.26s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.83s;}
@keyframes warp65{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.7px;height:2.7px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-75.2vmax,-67.5vmax) scale(1);opacity:0;filter:blur(0);width:5.0px;height:5.0px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p65{top:26%;left:39%;width:2.7px;height:2.7px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp65 2.58s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.35s;}
@keyframes warp66{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:4.2px;height:4.2px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-136.9vmax,17.7vmax) scale(1);opacity:0;filter:blur(0);width:11.0px;height:11.0px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p66{top:47%;left:71%;width:4.2px;height:4.2px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp66 2.39s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.39s;}
@keyframes warp67{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.4px;height:2.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(82.9vmax,-112.8vmax) scale(1);opacity:0;filter:blur(0);width:5.1px;height:5.1px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p67{top:44%;left:85%;width:2.4px;height:2.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp67 3.77s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.70s;}
@keyframes warp68{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:5.9px;height:5.9px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(71.9vmax,-105.9vmax) scale(1);opacity:0;filter:blur(0);width:11.6px;height:11.6px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p68{top:81%;left:37%;width:5.9px;height:5.9px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp68 2.32s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.07s;}
@keyframes warp69{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.1px;height:8.1px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-128.0vmax,-27.7vmax) scale(1);opacity:0;filter:blur(0);width:21.9px;height:21.9px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p69{top:23%;left:20%;width:8.1px;height:8.1px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp69 1.61s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.45s;}
@keyframes warp70{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.0px;height:8.0px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-29.1vmax,98.8vmax) scale(1);opacity:0;filter:blur(0);width:34.3px;height:34.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p70{top:85%;left:27%;width:8.0px;height:8.0px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp70 1.76s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.54s;}
@keyframes warp71{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.4px;height:1.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(86.8vmax,-95.4vmax) scale(1);opacity:0;filter:blur(0);width:3.3px;height:3.3px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p71{top:69%;left:65%;width:1.4px;height:1.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp71 3.42s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.37s;}
@keyframes warp72{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:3.8px;height:3.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(66.4vmax,27.8vmax) scale(1);opacity:0;filter:blur(0);width:13.5px;height:13.5px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p72{top:32%;left:60%;width:3.8px;height:3.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp72 3.36s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.47s;}
@keyframes warp73{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:4.8px;height:4.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-63.6vmax,41.6vmax) scale(1);opacity:0;filter:blur(0);width:11.6px;height:11.6px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p73{top:50%;left:52%;width:4.8px;height:4.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp73 2.03s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.55s;}
@keyframes warp74{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.6px;height:1.6px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-92.9vmax,-4.6vmax) scale(1);opacity:0;filter:blur(0);width:5.1px;height:5.1px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p74{top:85%;left:18%;width:1.6px;height:1.6px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp74 2.86s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.65s;}
@keyframes warp75{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:6.8px;height:6.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(54.4vmax,-88.6vmax) scale(1);opacity:0;filter:blur(0);width:24.5px;height:24.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p75{top:26%;left:64%;width:6.8px;height:6.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp75 1.29s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.97s;}
@keyframes warp76{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:5.0px;height:5.0px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(11.8vmax,-62.9vmax) scale(1);opacity:0;filter:blur(0);width:11.0px;height:11.0px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p76{top:45%;left:53%;width:5.0px;height:5.0px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp76 2.02s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.24s;}
@keyframes warp77{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.8px;height:2.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(20.6vmax,-126.3vmax) scale(1);opacity:0;filter:blur(0);width:4.7px;height:4.7px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p77{top:60%;left:31%;width:2.8px;height:2.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp77 4.85s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.26s;}
@keyframes warp78{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.4px;height:2.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-73.4vmax,-92.4vmax) scale(1);opacity:0;filter:blur(0);width:5.8px;height:5.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p78{top:40%;left:72%;width:2.4px;height:2.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp78 3.70s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.87s;}
@keyframes warp79{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.5px;height:2.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(30.4vmax,69.6vmax) scale(1);opacity:0;filter:blur(0);width:4.8px;height:4.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p79{top:70%;left:34%;width:2.5px;height:2.5px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp79 4.83s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.67s;}
@keyframes warp80{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.7px;height:8.7px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-44.6vmax,132.7vmax) scale(1);opacity:0;filter:blur(0);width:32.5px;height:32.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p80{top:19%;left:17%;width:8.7px;height:8.7px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp80 1.30s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.00s;}
@keyframes warp81{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:5.5px;height:5.5px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-22.2vmax,101.6vmax) scale(1);opacity:0;filter:blur(0);width:13.6px;height:13.6px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p81{top:32%;left:78%;width:5.5px;height:5.5px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp81 2.99s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.60s;}
@keyframes warp82{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.6px;height:2.6px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(61.4vmax,-94.9vmax) scale(1);opacity:0;filter:blur(0);width:4.7px;height:4.7px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p82{top:83%;left:62%;width:2.6px;height:2.6px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp82 4.80s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.06s;}
@keyframes warp83{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:7.5px;height:7.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-17.2vmax,-91.4vmax) scale(1);opacity:0;filter:blur(0);width:32.6px;height:32.6px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p83{top:67%;left:64%;width:7.5px;height:7.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp83 2.40s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.21s;}
@keyframes warp84{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.1px;height:2.1px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(7.1vmax,61.6vmax) scale(1);opacity:0;filter:blur(0);width:5.3px;height:5.3px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p84{top:47%;left:18%;width:2.1px;height:2.1px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp84 2.90s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.45s;}
@keyframes warp85{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:3.8px;height:3.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(79.9vmax,-71.2vmax) scale(1);opacity:0;filter:blur(0);width:10.4px;height:10.4px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p85{top:35%;left:66%;width:3.8px;height:3.8px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp85 3.13s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.02s;}
@keyframes warp86{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.8px;height:8.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-9.5vmax,-81.4vmax) scale(1);opacity:0;filter:blur(0);width:24.2px;height:24.2px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p86{top:55%;left:76%;width:8.8px;height:8.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp86 1.65s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.56s;}
@keyframes warp87{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:6.3px;height:6.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(17.7vmax,72.9vmax) scale(1);opacity:0;filter:blur(0);width:26.0px;height:26.0px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p87{top:74%;left:34%;width:6.3px;height:6.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp87 2.20s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.59s;}
@keyframes warp88{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:5.3px;height:5.3px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(-20.2vmax,-68.1vmax) scale(1);opacity:0;filter:blur(0);width:11.2px;height:11.2px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p88{top:42%;left:57%;width:5.3px;height:5.3px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp88 2.18s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.51s;}
@keyframes warp89{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.6px;height:2.6px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(86.1vmax,-22.5vmax) scale(1);opacity:0;filter:blur(0);width:4.2px;height:4.2px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p89{top:67%;left:46%;width:2.6px;height:2.6px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp89 3.33s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.74s;}
@keyframes warp90{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:6.3px;height:6.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-12.2vmax,-92.2vmax) scale(1);opacity:0;filter:blur(0);width:29.5px;height:29.5px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p90{top:42%;left:63%;width:6.3px;height:6.3px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp90 1.78s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-2.02s;}
@keyframes warp91{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.3px;height:2.3px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-34.1vmax,73.5vmax) scale(1);opacity:0;filter:blur(0);width:6.0px;height:6.0px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p91{top:70%;left:69%;width:2.3px;height:2.3px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp91 4.00s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.57s;}
@keyframes warp92{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.2px;height:8.2px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-115.0vmax,26.4vmax) scale(1);opacity:0;filter:blur(0);width:32.6px;height:32.6px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p92{top:71%;left:76%;width:8.2px;height:8.2px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp92 2.08s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.95s;}
@keyframes warp93{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:7.8px;height:7.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-117.4vmax,11.9vmax) scale(1);opacity:0;filter:blur(0);width:26.7px;height:26.7px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p93{top:27%;left:74%;width:7.8px;height:7.8px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp93 1.49s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.38s;}
@keyframes warp94{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.8px;height:1.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-9.9vmax,-75.3vmax) scale(1);opacity:0;filter:blur(0);width:5.7px;height:5.7px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p94{top:22%;left:55%;width:1.8px;height:1.8px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp94 4.61s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.49s;}
@keyframes warp95{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.6px;height:8.6px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(58.9vmax,59.9vmax) scale(1);opacity:0;filter:blur(0);width:28.1px;height:28.1px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p95{top:29%;left:15%;width:8.6px;height:8.6px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp95 1.42s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.88s;}
@keyframes warp96{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:3.1px;height:3.1px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(6.8vmax,-63.6vmax) scale(1);opacity:0;filter:blur(0);width:12.2px;height:12.2px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p96{top:20%;left:22%;width:3.1px;height:3.1px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp96 2.13s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.76s;}
@keyframes warp97{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:1.4px;height:1.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-9.5vmax,104.6vmax) scale(1);opacity:0;filter:blur(0);width:5.3px;height:5.3px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p97{top:74%;left:38%;width:1.4px;height:1.4px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp97 4.49s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.39s;}
@keyframes warp98{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(4px);width:3.7px;height:3.7px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}10%{opacity:0.85;filter:blur(2.4px);}70%{filter:blur(1px);}100%{transform:translate(32.2vmax,56.4vmax) scale(1);opacity:0;filter:blur(0);width:8.1px;height:8.1px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}}
.p98{top:28%;left:72%;width:3.7px;height:3.7px;box-shadow:0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);animation:warp98 3.20s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-3.74s;}
@keyframes warp99{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(3px);width:2.6px;height:2.6px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}10%{opacity:0.5;filter:blur(1.8px);}70%{filter:blur(1px);}100%{transform:translate(-64.4vmax,101.3vmax) scale(1);opacity:0;filter:blur(0);width:4.2px;height:4.2px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}}
.p99{top:62%;left:51%;width:2.6px;height:2.6px;box-shadow:0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);animation:warp99 3.32s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-1.21s;}
@keyframes warp100{0%{transform:translate(0,0) scale(1);opacity:0;filter:blur(5px);width:8.9px;height:8.9px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}10%{opacity:1;filter:blur(3.0px);}70%{filter:blur(1px);}100%{transform:translate(-4.3vmax,136.9vmax) scale(1);opacity:0;filter:blur(0);width:27.4px;height:27.4px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}}
.p100{top:18%;left:75%;width:8.9px;height:8.9px;box-shadow:0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);animation:warp100 1.37s cubic-bezier(0.5,0,0.95,0.4) infinite;animation-delay:-0.43s;}
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
    img.thumbnail((2000, 2000))
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

def show_overlay(loader, pct, label):
    loader.markdown(
        f'<div class="big-overlay"><div class="particles">{PARTICLES_HTML}</div><div class="big-num">{pct}%</div><div class="big-label">{label}</div></div>',
        unsafe_allow_html=True
    )


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
        try:
            for pct in [3, 8, 14, 21, 29]:
                show_overlay(loader, pct, 'どりゃ〜')
                time.sleep(0.15)
            api_key = os.environ.get('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY')
            client = anthropic.Anthropic(api_key=api_key)
            if is_meter(client, imgs[0]):
                meter_img, nippou_img = imgs[0], imgs[1]
            else:
                meter_img, nippou_img = imgs[1], imgs[0]
            for pct in [34, 42, 51, 58, 65, 71]:
                show_overlay(loader, pct, 'ぐぬぬぬっ')
                time.sleep(0.2)

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
            mi  = grab(r'未収合計[:：]\s*¥?([\d,]+)')
            sou = grab(r'総収[:：]\s*¥?([\d,]+)')
            tax = grab(r'消費税[:：]\s*¥?([\d,]+)')
            net = grab(r'税抜運収[:：]\s*¥?([\d,]+)')
            fmt = lambda x: f'¥{int(x):,}'

            for pct in [82, 91, 97, 100]:
                show_overlay(loader, pct, 'もうちょい')
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
            st.markdown('<br>', unsafe_allow_html=True)
            if st.button('🔄 新しい日報を作成', use_container_width=True):
                st.rerun()
        except Exception as e:
            st.error(f'エラー: {e}')
elif files and len(files) != 2:
    st.warning(f'2枚選択してください（現在{len(files)}枚）')
