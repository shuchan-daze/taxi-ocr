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
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 0 8px rgba(255,255,255,0.9), 0 0 20px rgba(212,175,55,0.7);
    filter: blur(2px);
}
@keyframes warp1 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(21.9vmax, 67.5vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp2 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-12.2vmax, -92.2vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp3 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(33.1vmax, 100.7vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp4 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(47.1vmax, -55.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp5 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(91.1vmax, 52.3vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp6 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-63.0vmax, 44.2vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp7 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(81.3vmax, 45.2vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp8 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(82.6vmax, 87.0vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp9 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(63.2vmax, -32.3vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp10 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(89.0vmax, 13.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp11 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(67.7vmax, 40.6vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp12 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-96.9vmax, 65.6vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp13 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-4.0vmax, 84.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp14 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(78.2vmax, 84.3vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp15 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(62.5vmax, -24.2vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp16 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-100.4vmax, 63.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp17 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(38.1vmax, -55.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp18 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-22.8vmax, 94.3vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp19 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-57.6vmax, 94.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp20 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(96.9vmax, 63.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp21 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(14.1vmax, 113.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp22 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(74.6vmax, -75.3vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp23 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-31.0vmax, 103.4vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp24 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(70.6vmax, 33.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp25 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(81.5vmax, 83.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp26 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(45.3vmax, 70.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp27 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(27.7vmax, 76.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp28 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(70.2vmax, -15.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp29 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-5.0vmax, -114.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp30 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(92.0vmax, 2.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp31 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-110.7vmax, -7.7vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp32 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-92.9vmax, -37.0vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp33 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(18.7vmax, 58.0vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp34 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(61.7vmax, 12.6vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp35 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(91.9vmax, -31.0vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp36 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-57.0vmax, 42.3vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp37 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(70.2vmax, -76.7vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp38 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-0.1vmax, 77.0vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp39 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(55.1vmax, -105.5vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp40 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-32.6vmax, -55.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp41 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(82.6vmax, 72.7vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp42 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-32.5vmax, -69.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp43 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(48.9vmax, 83.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp44 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-94.8vmax, -6.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp45 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-28.9vmax, -81.0vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp46 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-14.6vmax, 101.0vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp47 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(37.9vmax, 72.7vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp48 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-17.7vmax, -110.6vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp49 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-42.3vmax, -55.7vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp50 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-77.0vmax, -62.3vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp51 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-72.7vmax, 30.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp52 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-7.3vmax, -59.6vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp53 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-96.8vmax, -43.2vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp54 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(80.1vmax, -79.7vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp55 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-82.1vmax, -51.6vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp56 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(108.8vmax, -40.2vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp57 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-110.9vmax, 5.3vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp58 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(58.2vmax, -83.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp59 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(38.7vmax, -91.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp60 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-6.0vmax, -85.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp61 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-62.3vmax, -9.5vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp62 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(49.8vmax, 33.4vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp63 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(57.6vmax, -41.5vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp64 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-76.3vmax, -41.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp65 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-69.8vmax, 53.6vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp66 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(79.6vmax, 87.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp67 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-9.3vmax, -90.5vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp68 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(33.2vmax, 105.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp69 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(41.1vmax, -63.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp70 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(66.3vmax, 35.0vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp71 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-63.3vmax, -9.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp72 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-66.0vmax, 1.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp73 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(66.6vmax, 27.4vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp74 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(82.6vmax, -59.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp75 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-10.2vmax, -66.2vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp76 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-5.7vmax, 87.8vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp77 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(41.1vmax, 50.4vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp78 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(57.7vmax, -47.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp79 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(33.2vmax, 66.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp80 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-93.4vmax, 41.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp81 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-102.9vmax, 53.5vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp82 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-26.2vmax, -107.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp83 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(15.1vmax, 78.6vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp84 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-51.7vmax, -51.6vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp85 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-2.5vmax, -63.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp86 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-119.9vmax, 4.4vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp87 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-74.9vmax, -4.5vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp88 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-58.6vmax, 43.5vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp89 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-51.7vmax, 83.2vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp90 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-76.5vmax, -85.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp91 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(66.6vmax, 7.4vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp92 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(113.0vmax, -1.9vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp93 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(105.0vmax, -1.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp94 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-49.8vmax, 43.3vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp95 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(61.7vmax, -86.2vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp96 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-1.0vmax, -113.0vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp97 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-59.7vmax, -42.1vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp98 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(36.0vmax, -67.0vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp99 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(48.0vmax, 65.2vmax) scale(2); opacity: 0; filter: blur(0px);}
}
@keyframes warp100 {
  0% {transform: translate(0,0) scale(0.5); opacity: 0; filter: blur(4px);}
  15% {opacity: 1; filter: blur(2px);}
  60% {filter: blur(1px);}
  100% {transform: translate(-57.0vmax, 73.5vmax) scale(2); opacity: 0; filter: blur(0px);}
}
.p1 {top: 58%; left: 61%; animation: warp1 1.96s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.53s;}
.p2 {top: 42%; left: 21%; animation: warp2 2.87s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.15s;}
.p3 {top: 72%; left: 89%; animation: warp3 2.73s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.87s;}
.p4 {top: 59%; left: 57%; animation: warp4 1.80s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.64s;}
.p5 {top: 53%; left: 82%; animation: warp5 2.56s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.10s;}
.p6 {top: 50%; left: 70%; animation: warp6 2.62s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.70s;}
.p7 {top: 78%; left: 56%; animation: warp7 3.30s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.42s;}
.p8 {top: 55%; left: 16%; animation: warp8 3.34s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.64s;}
.p9 {top: 86%; left: 66%; animation: warp9 3.39s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.64s;}
.p10 {top: 24%; left: 14%; animation: warp10 2.87s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.68s;}
.p11 {top: 90%; left: 64%; animation: warp11 2.73s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.52s;}
.p12 {top: 76%; left: 27%; animation: warp12 3.07s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.22s;}
.p13 {top: 66%; left: 37%; animation: warp13 3.15s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.51s;}
.p14 {top: 17%; left: 70%; animation: warp14 2.94s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.12s;}
.p15 {top: 87%; left: 29%; animation: warp15 1.69s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.57s;}
.p16 {top: 32%; left: 32%; animation: warp16 1.92s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.24s;}
.p17 {top: 39%; left: 73%; animation: warp17 3.22s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.45s;}
.p18 {top: 74%; left: 19%; animation: warp18 3.17s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.35s;}
.p19 {top: 61%; left: 58%; animation: warp19 2.30s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.66s;}
.p20 {top: 78%; left: 57%; animation: warp20 1.58s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.49s;}
.p21 {top: 66%; left: 61%; animation: warp21 2.81s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.61s;}
.p22 {top: 23%; left: 49%; animation: warp22 2.13s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.06s;}
.p23 {top: 59%; left: 41%; animation: warp23 3.42s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.53s;}
.p24 {top: 42%; left: 63%; animation: warp24 3.31s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.50s;}
.p25 {top: 78%; left: 71%; animation: warp25 2.01s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.53s;}
.p26 {top: 88%; left: 62%; animation: warp26 2.86s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.42s;}
.p27 {top: 66%; left: 89%; animation: warp27 3.27s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.38s;}
.p28 {top: 47%; left: 55%; animation: warp28 3.28s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.67s;}
.p29 {top: 63%; left: 43%; animation: warp29 2.91s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.63s;}
.p30 {top: 61%; left: 54%; animation: warp30 2.56s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.01s;}
.p31 {top: 31%; left: 49%; animation: warp31 2.39s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.82s;}
.p32 {top: 69%; left: 63%; animation: warp32 2.74s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.53s;}
.p33 {top: 46%; left: 87%; animation: warp33 3.50s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.23s;}
.p34 {top: 84%; left: 19%; animation: warp34 2.33s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.48s;}
.p35 {top: 90%; left: 81%; animation: warp35 2.65s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.78s;}
.p36 {top: 60%; left: 22%; animation: warp36 2.03s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.32s;}
.p37 {top: 67%; left: 26%; animation: warp37 2.90s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.67s;}
.p38 {top: 56%; left: 32%; animation: warp38 2.43s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.38s;}
.p39 {top: 33%; left: 58%; animation: warp39 3.50s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.29s;}
.p40 {top: 70%; left: 90%; animation: warp40 2.56s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.99s;}
.p41 {top: 11%; left: 76%; animation: warp41 2.49s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.34s;}
.p42 {top: 82%; left: 10%; animation: warp42 2.77s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.33s;}
.p43 {top: 43%; left: 62%; animation: warp43 3.34s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.59s;}
.p44 {top: 53%; left: 16%; animation: warp44 3.01s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.63s;}
.p45 {top: 17%; left: 66%; animation: warp45 1.96s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.75s;}
.p46 {top: 31%; left: 72%; animation: warp46 2.23s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.24s;}
.p47 {top: 81%; left: 35%; animation: warp47 2.81s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.26s;}
.p48 {top: 24%; left: 20%; animation: warp48 1.77s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.18s;}
.p49 {top: 75%; left: 14%; animation: warp49 2.21s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.13s;}
.p50 {top: 88%; left: 39%; animation: warp50 1.82s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.09s;}
.p51 {top: 90%; left: 53%; animation: warp51 1.86s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.44s;}
.p52 {top: 76%; left: 73%; animation: warp52 1.96s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.67s;}
.p53 {top: 40%; left: 22%; animation: warp53 3.09s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.50s;}
.p54 {top: 30%; left: 20%; animation: warp54 1.83s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.78s;}
.p55 {top: 50%; left: 42%; animation: warp55 2.29s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.20s;}
.p56 {top: 26%; left: 30%; animation: warp56 2.07s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.22s;}
.p57 {top: 25%; left: 47%; animation: warp57 1.64s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.41s;}
.p58 {top: 50%; left: 87%; animation: warp58 2.15s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.32s;}
.p59 {top: 58%; left: 14%; animation: warp59 1.95s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.60s;}
.p60 {top: 46%; left: 12%; animation: warp60 2.52s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.60s;}
.p61 {top: 32%; left: 39%; animation: warp61 1.92s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.59s;}
.p62 {top: 82%; left: 30%; animation: warp62 2.63s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.11s;}
.p63 {top: 26%; left: 35%; animation: warp63 2.76s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.25s;}
.p64 {top: 33%; left: 42%; animation: warp64 1.80s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.73s;}
.p65 {top: 74%; left: 14%; animation: warp65 1.65s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.35s;}
.p66 {top: 65%; left: 53%; animation: warp66 2.72s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.48s;}
.p67 {top: 39%; left: 30%; animation: warp67 1.92s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.42s;}
.p68 {top: 88%; left: 65%; animation: warp68 1.85s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.90s;}
.p69 {top: 32%; left: 41%; animation: warp69 1.84s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.06s;}
.p70 {top: 79%; left: 74%; animation: warp70 2.55s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.75s;}
.p71 {top: 60%; left: 63%; animation: warp71 1.98s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.30s;}
.p72 {top: 52%; left: 82%; animation: warp72 3.09s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.12s;}
.p73 {top: 65%; left: 14%; animation: warp73 3.35s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.65s;}
.p74 {top: 44%; left: 33%; animation: warp74 2.01s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.31s;}
.p75 {top: 35%; left: 47%; animation: warp75 1.82s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.56s;}
.p76 {top: 77%; left: 49%; animation: warp76 1.61s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.83s;}
.p77 {top: 39%; left: 55%; animation: warp77 3.17s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.52s;}
.p78 {top: 50%; left: 55%; animation: warp78 2.58s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.12s;}
.p79 {top: 13%; left: 12%; animation: warp79 2.19s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.02s;}
.p80 {top: 10%; left: 19%; animation: warp80 2.37s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.77s;}
.p81 {top: 73%; left: 57%; animation: warp81 2.25s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.24s;}
.p82 {top: 51%; left: 43%; animation: warp82 1.73s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.12s;}
.p83 {top: 14%; left: 18%; animation: warp83 2.74s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.08s;}
.p84 {top: 89%; left: 49%; animation: warp84 2.38s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.78s;}
.p85 {top: 87%; left: 12%; animation: warp85 3.05s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.49s;}
.p86 {top: 46%; left: 12%; animation: warp86 3.30s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.82s;}
.p87 {top: 51%; left: 64%; animation: warp87 2.71s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.14s;}
.p88 {top: 46%; left: 23%; animation: warp88 1.64s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.70s;}
.p89 {top: 72%; left: 68%; animation: warp89 1.67s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.08s;}
.p90 {top: 20%; left: 82%; animation: warp90 2.32s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.69s;}
.p91 {top: 84%; left: 85%; animation: warp91 3.10s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -0.87s;}
.p92 {top: 11%; left: 23%; animation: warp92 3.38s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.15s;}
.p93 {top: 46%; left: 27%; animation: warp93 2.33s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.24s;}
.p94 {top: 63%; left: 33%; animation: warp94 1.66s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.79s;}
.p95 {top: 42%; left: 48%; animation: warp95 1.82s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.10s;}
.p96 {top: 14%; left: 25%; animation: warp96 1.64s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -1.89s;}
.p97 {top: 47%; left: 26%; animation: warp97 3.19s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.45s;}
.p98 {top: 49%; left: 74%; animation: warp98 2.50s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.54s;}
.p99 {top: 46%; left: 68%; animation: warp99 2.52s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -3.21s;}
.p100 {top: 88%; left: 39%; animation: warp100 1.64s cubic-bezier(0.7, 0, 0.95, 0.5) infinite; animation-delay: -2.22s;}
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
