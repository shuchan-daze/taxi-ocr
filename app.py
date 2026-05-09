import streamlit as st
import anthropic
import base64
from PIL import Image, ExifTags
from pillow_heif import register_heif_opener
import io
import json
import os
import re
import time

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
    box-shadow: 0 4px 14px rgba(212,175,55,0.17) !important;
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
    border-radius: 50%;
    background: rgba(255,255,255,0.25);
}
@keyframes warp1 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 4.9px; height: 4.9px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-29.8vmax, -60.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 10.5px; height: 10.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp2 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.8px; height: 2.8px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-86.4vmax, -91.7vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.0px; height: 4.0px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp3 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 3.4px; height: 3.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(0.8vmax, 92.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 10.8px; height: 10.8px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp4 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 3.8px; height: 3.8px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(90.3vmax, 22.4vmax) scale(1); opacity: 0; filter: blur(0px); width: 8.3px; height: 8.3px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp5 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.2px; height: 1.2px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-82.8vmax, 35.4vmax) scale(1); opacity: 0; filter: blur(0px); width: 3.4px; height: 3.4px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp6 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.6px; height: 1.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(66.2vmax, -10.5vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.0px; height: 4.0px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp7 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 4.6px; height: 4.6px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(71.5vmax, 109.7vmax) scale(1); opacity: 0; filter: blur(0px); width: 11.4px; height: 11.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp8 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.9px; height: 2.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(119.5vmax, -33.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.8px; height: 4.8px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp9 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.6px; height: 1.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(94.7vmax, -25.4vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.2px; height: 5.2px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp10 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.1px; height: 2.1px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-56.7vmax, 22.6vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.0px; height: 5.0px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp11 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 4.4px; height: 4.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(106.2vmax, 78.4vmax) scale(1); opacity: 0; filter: blur(0px); width: 11.6px; height: 11.6px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp12 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.6px; height: 2.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-78.9vmax, 70.7vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.6px; height: 5.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp13 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.4px; height: 1.4px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-2.9vmax, 114.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.4px; height: 4.4px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp14 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.7px; height: 2.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(19.0vmax, 118.5vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.9px; height: 5.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp15 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 7.2px; height: 7.2px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-135.9vmax, -5.3vmax) scale(1); opacity: 0; filter: blur(0px); width: 20.6px; height: 20.6px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp16 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 4.7px; height: 4.7px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(48.2vmax, 68.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 10.9px; height: 10.9px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp17 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 10.6px; height: 10.6px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-86.5vmax, -31.3vmax) scale(1); opacity: 0; filter: blur(0px); width: 26.7px; height: 26.7px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp18 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 5.0px; height: 5.0px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(37.3vmax, -100.3vmax) scale(1); opacity: 0; filter: blur(0px); width: 11.3px; height: 11.3px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp19 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.1px; height: 1.1px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(23.8vmax, -100.2vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.8px; height: 4.8px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp20 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 9.5px; height: 9.5px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-56.0vmax, -62.6vmax) scale(1); opacity: 0; filter: blur(0px); width: 23.4px; height: 23.4px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp21 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.8px; height: 2.8px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(36.6vmax, -88.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.3px; height: 4.3px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp22 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.5px; height: 2.5px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(107.8vmax, 26.6vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.5px; height: 5.5px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp23 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 3.1px; height: 3.1px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(86.9vmax, -33.2vmax) scale(1); opacity: 0; filter: blur(0px); width: 11.4px; height: 11.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp24 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 7.1px; height: 7.1px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-54.2vmax, -88.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 32.0px; height: 32.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp25 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.6px; height: 1.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-21.4vmax, -83.3vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.6px; height: 5.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp26 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 7.3px; height: 7.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-38.9vmax, 98.6vmax) scale(1); opacity: 0; filter: blur(0px); width: 21.0px; height: 21.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp27 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 4.8px; height: 4.8px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(51.3vmax, -95.1vmax) scale(1); opacity: 0; filter: blur(0px); width: 12.7px; height: 12.7px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp28 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.2px; height: 1.2px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(80.4vmax, -16.2vmax) scale(1); opacity: 0; filter: blur(0px); width: 3.3px; height: 3.3px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp29 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 4.8px; height: 4.8px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(70.3vmax, -9.7vmax) scale(1); opacity: 0; filter: blur(0px); width: 10.9px; height: 10.9px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp30 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 7.9px; height: 7.9px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(49.1vmax, -37.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 25.2px; height: 25.2px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp31 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 10.3px; height: 10.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-116.1vmax, 48.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 20.9px; height: 20.9px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp32 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.4px; height: 1.4px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-61.0vmax, -1.7vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.9px; height: 4.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp33 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.8px; height: 2.8px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-50.8vmax, -83.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.5px; height: 5.5px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp34 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.7px; height: 1.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-66.8vmax, 4.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.1px; height: 4.1px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp35 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 11.5px; height: 11.5px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(50.8vmax, 74.3vmax) scale(1); opacity: 0; filter: blur(0px); width: 26.4px; height: 26.4px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp36 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 3.4px; height: 3.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-76.4vmax, -56.4vmax) scale(1); opacity: 0; filter: blur(0px); width: 13.3px; height: 13.3px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp37 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 3.5px; height: 3.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(67.3vmax, -80.6vmax) scale(1); opacity: 0; filter: blur(0px); width: 9.4px; height: 9.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp38 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.1px; height: 1.1px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(96.9vmax, -78.9vmax) scale(1); opacity: 0; filter: blur(0px); width: 3.8px; height: 3.8px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp39 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 5.6px; height: 5.6px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(5.7vmax, 89.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 9.8px; height: 9.8px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp40 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.0px; height: 2.0px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-62.6vmax, 113.9vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.2px; height: 4.2px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp41 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 8.1px; height: 8.1px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(61.9vmax, 69.4vmax) scale(1); opacity: 0; filter: blur(0px); width: 24.7px; height: 24.7px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp42 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 5.0px; height: 5.0px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(61.9vmax, 45.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 12.3px; height: 12.3px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp43 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 5.5px; height: 5.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-92.7vmax, -28.5vmax) scale(1); opacity: 0; filter: blur(0px); width: 10.3px; height: 10.3px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp44 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.7px; height: 1.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-70.1vmax, -69.9vmax) scale(1); opacity: 0; filter: blur(0px); width: 3.1px; height: 3.1px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp45 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 4.3px; height: 4.3px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(71.1vmax, 24.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 11.3px; height: 11.3px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp46 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 3.5px; height: 3.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-90.4vmax, -51.5vmax) scale(1); opacity: 0; filter: blur(0px); width: 10.3px; height: 10.3px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp47 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 11.0px; height: 11.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-77.6vmax, 116.5vmax) scale(1); opacity: 0; filter: blur(0px); width: 33.0px; height: 33.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp48 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.3px; height: 2.3px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(6.8vmax, 66.7vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.4px; height: 5.4px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp49 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 7.3px; height: 7.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(62.6vmax, 49.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 33.1px; height: 33.1px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp50 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 7.0px; height: 7.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(76.9vmax, -4.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 29.2px; height: 29.2px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp51 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.6px; height: 2.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-60.4vmax, -103.7vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.4px; height: 5.4px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp52 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 8.4px; height: 8.4px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(29.6vmax, -53.4vmax) scale(1); opacity: 0; filter: blur(0px); width: 33.3px; height: 33.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp53 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 9.8px; height: 9.8px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-124.8vmax, 7.3vmax) scale(1); opacity: 0; filter: blur(0px); width: 31.2px; height: 31.2px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp54 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.9px; height: 1.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(98.4vmax, -55.6vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.1px; height: 5.1px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp55 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 3.9px; height: 3.9px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-9.3vmax, 83.5vmax) scale(1); opacity: 0; filter: blur(0px); width: 11.6px; height: 11.6px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp56 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.9px; height: 2.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-54.8vmax, -41.9vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.3px; height: 4.3px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp57 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.6px; height: 2.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-64.4vmax, 79.1vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.9px; height: 5.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp58 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.3px; height: 1.3px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-78.1vmax, -54.1vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.9px; height: 5.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp59 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.9px; height: 2.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-106.3vmax, -38.3vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.5px; height: 4.5px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp60 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 11.2px; height: 11.2px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(20.2vmax, -62.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 35.0px; height: 35.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp61 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 7.7px; height: 7.7px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-36.8vmax, 56.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 28.8px; height: 28.8px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp62 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 10.0px; height: 10.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-36.8vmax, 75.5vmax) scale(1); opacity: 0; filter: blur(0px); width: 32.0px; height: 32.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp63 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 6.1px; height: 6.1px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-79.2vmax, -50.6vmax) scale(1); opacity: 0; filter: blur(0px); width: 21.8px; height: 21.8px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp64 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 3.7px; height: 3.7px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(13.1vmax, -88.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 10.6px; height: 10.6px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp65 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 5.2px; height: 5.2px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(103.0vmax, 20.3vmax) scale(1); opacity: 0; filter: blur(0px); width: 13.5px; height: 13.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp66 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 4.8px; height: 4.8px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-20.7vmax, -66.9vmax) scale(1); opacity: 0; filter: blur(0px); width: 9.4px; height: 9.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp67 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.0px; height: 2.0px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(54.3vmax, 73.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.3px; height: 5.3px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp68 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 3.2px; height: 3.2px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(65.3vmax, 9.4vmax) scale(1); opacity: 0; filter: blur(0px); width: 11.0px; height: 11.0px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp69 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 5.2px; height: 5.2px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-93.1vmax, 75.7vmax) scale(1); opacity: 0; filter: blur(0px); width: 9.8px; height: 9.8px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp70 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.9px; height: 2.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(58.7vmax, -41.7vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.3px; height: 5.3px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp71 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 4.5px; height: 4.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-70.6vmax, 14.3vmax) scale(1); opacity: 0; filter: blur(0px); width: 13.5px; height: 13.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp72 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 10.9px; height: 10.9px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(107.7vmax, -86.2vmax) scale(1); opacity: 0; filter: blur(0px); width: 25.2px; height: 25.2px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp73 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 5.4px; height: 5.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(77.3vmax, 68.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 11.5px; height: 11.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp74 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 6.9px; height: 6.9px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-60.7vmax, 20.4vmax) scale(1); opacity: 0; filter: blur(0px); width: 34.2px; height: 34.2px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp75 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 11.2px; height: 11.2px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-48.1vmax, -35.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 30.1px; height: 30.1px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp76 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.7px; height: 2.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-31.5vmax, 129.2vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.7px; height: 4.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp77 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 4.6px; height: 4.6px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(10.5vmax, -94.4vmax) scale(1); opacity: 0; filter: blur(0px); width: 12.1px; height: 12.1px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp78 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.7px; height: 1.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(111.4vmax, -32.3vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.7px; height: 5.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp79 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 8.0px; height: 8.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-107.9vmax, -45.2vmax) scale(1); opacity: 0; filter: blur(0px); width: 21.7px; height: 21.7px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp80 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 10.3px; height: 10.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(68.9vmax, 73.9vmax) scale(1); opacity: 0; filter: blur(0px); width: 24.3px; height: 24.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp81 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 11.5px; height: 11.5px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(8.3vmax, -116.7vmax) scale(1); opacity: 0; filter: blur(0px); width: 23.1px; height: 23.1px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp82 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.3px; height: 2.3px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(9.8vmax, 130.6vmax) scale(1); opacity: 0; filter: blur(0px); width: 4.7px; height: 4.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp83 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 4.6px; height: 4.6px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-44.0vmax, 63.2vmax) scale(1); opacity: 0; filter: blur(0px); width: 13.3px; height: 13.3px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp84 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 8.0px; height: 8.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-122.0vmax, -57.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 26.2px; height: 26.2px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp85 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.1px; height: 2.1px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(75.7vmax, 14.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.5px; height: 5.5px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp86 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 3.4px; height: 3.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-4.9vmax, -71.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 10.0px; height: 10.0px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp87 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 8.3px; height: 8.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(85.0vmax, 87.5vmax) scale(1); opacity: 0; filter: blur(0px); width: 31.4px; height: 31.4px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp88 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 7.8px; height: 7.8px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(41.2vmax, -46.4vmax) scale(1); opacity: 0; filter: blur(0px); width: 22.3px; height: 22.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp89 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 5.4px; height: 5.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(30.8vmax, -66.2vmax) scale(1); opacity: 0; filter: blur(0px); width: 13.5px; height: 13.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp90 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 5.9px; height: 5.9px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(30.0vmax, 102.7vmax) scale(1); opacity: 0; filter: blur(0px); width: 8.1px; height: 8.1px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp91 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 5.3px; height: 5.3px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(16.2vmax, 104.7vmax) scale(1); opacity: 0; filter: blur(0px); width: 12.5px; height: 12.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp92 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.6px; height: 2.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-62.9vmax, 4.1vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.0px; height: 5.0px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp93 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.7px; height: 2.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(45.0vmax, -84.8vmax) scale(1); opacity: 0; filter: blur(0px); width: 5.6px; height: 5.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp94 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.7px; height: 1.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-83.9vmax, 32.5vmax) scale(1); opacity: 0; filter: blur(0px); width: 3.3px; height: 3.3px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp95 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 1.9px; height: 1.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-75.9vmax, 36.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 3.7px; height: 3.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp96 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(5px); width: 11.5px; height: 11.5px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
  10% {opacity: 1; filter: blur(3.0px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-23.9vmax, 70.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 34.3px; height: 34.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20);}
}
@keyframes warp97 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 4.1px; height: 4.1px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(74.8vmax, 5.0vmax) scale(1); opacity: 0; filter: blur(0px); width: 10.7px; height: 10.7px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp98 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 3.9px; height: 3.9px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-77.0vmax, -2.1vmax) scale(1); opacity: 0; filter: blur(0px); width: 11.5px; height: 11.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
@keyframes warp99 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(3px); width: 2.8px; height: 2.8px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
  10% {opacity: 0.5; filter: blur(1.8px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-114.6vmax, -18.1vmax) scale(1); opacity: 0; filter: blur(0px); width: 3.7px; height: 3.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20);}
}
@keyframes warp100 {
  0% {transform: translate(0,0) scale(1); opacity: 0; filter: blur(4px); width: 3.5px; height: 3.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
  10% {opacity: 0.85; filter: blur(2.4px);}
  70% {filter: blur(1px);}
  100% {transform: translate(-34.1vmax, 100.4vmax) scale(1); opacity: 0; filter: blur(0px); width: 11.8px; height: 11.8px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30);}
}
.p1 {top: 40%; left: 40%; width: 4.9px; height: 4.9px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp1 2.53s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.40s;}
.p2 {top: 78%; left: 45%; width: 2.8px; height: 2.8px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp2 2.98s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.61s;}
.p3 {top: 81%; left: 19%; width: 3.4px; height: 3.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp3 2.56s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.50s;}
.p4 {top: 27%; left: 37%; width: 3.8px; height: 3.8px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp4 1.82s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.85s;}
.p5 {top: 40%; left: 43%; width: 1.2px; height: 1.2px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp5 3.25s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.60s;}
.p6 {top: 46%; left: 73%; width: 1.6px; height: 1.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp6 3.98s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.17s;}
.p7 {top: 67%; left: 59%; width: 4.6px; height: 4.6px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp7 3.29s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.55s;}
.p8 {top: 25%; left: 16%; width: 2.9px; height: 2.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp8 3.45s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.92s;}
.p9 {top: 78%; left: 47%; width: 1.6px; height: 1.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp9 4.88s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.60s;}
.p10 {top: 32%; left: 74%; width: 2.1px; height: 2.1px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp10 2.93s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.90s;}
.p11 {top: 78%; left: 18%; width: 4.4px; height: 4.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp11 3.17s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.55s;}
.p12 {top: 78%; left: 26%; width: 2.6px; height: 2.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp12 2.98s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.73s;}
.p13 {top: 84%; left: 19%; width: 1.4px; height: 1.4px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp13 3.71s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.14s;}
.p14 {top: 24%; left: 37%; width: 2.7px; height: 2.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp14 4.00s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.94s;}
.p15 {top: 55%; left: 22%; width: 7.2px; height: 7.2px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp15 1.87s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.50s;}
.p16 {top: 54%; left: 62%; width: 4.7px; height: 4.7px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp16 1.97s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.20s;}
.p17 {top: 83%; left: 64%; width: 10.6px; height: 10.6px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp17 2.24s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.98s;}
.p18 {top: 50%; left: 30%; width: 5.0px; height: 5.0px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp18 2.83s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.47s;}
.p19 {top: 40%; left: 85%; width: 1.1px; height: 1.1px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp19 3.33s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.95s;}
.p20 {top: 47%; left: 62%; width: 9.5px; height: 9.5px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp20 2.23s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.21s;}
.p21 {top: 58%; left: 20%; width: 2.8px; height: 2.8px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp21 3.32s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.56s;}
.p22 {top: 17%; left: 16%; width: 2.5px; height: 2.5px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp22 3.28s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.34s;}
.p23 {top: 31%; left: 61%; width: 3.1px; height: 3.1px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp23 2.74s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.30s;}
.p24 {top: 67%; left: 42%; width: 7.1px; height: 7.1px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp24 1.80s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.52s;}
.p25 {top: 72%; left: 81%; width: 1.6px; height: 1.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp25 3.81s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.38s;}
.p26 {top: 57%; left: 45%; width: 7.3px; height: 7.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp26 2.00s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.67s;}
.p27 {top: 70%; left: 61%; width: 4.8px; height: 4.8px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp27 2.80s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.16s;}
.p28 {top: 43%; left: 43%; width: 1.2px; height: 1.2px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp28 4.19s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.99s;}
.p29 {top: 23%; left: 15%; width: 4.8px; height: 4.8px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp29 2.64s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.20s;}
.p30 {top: 41%; left: 51%; width: 7.9px; height: 7.9px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp30 2.13s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.58s;}
.p31 {top: 84%; left: 58%; width: 10.3px; height: 10.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp31 1.50s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.37s;}
.p32 {top: 17%; left: 74%; width: 1.4px; height: 1.4px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp32 2.80s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.47s;}
.p33 {top: 47%; left: 85%; width: 2.8px; height: 2.8px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp33 4.13s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.06s;}
.p34 {top: 60%; left: 41%; width: 1.7px; height: 1.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp34 3.57s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.84s;}
.p35 {top: 75%; left: 76%; width: 11.5px; height: 11.5px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp35 2.30s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.51s;}
.p36 {top: 20%; left: 59%; width: 3.4px; height: 3.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp36 2.51s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.26s;}
.p37 {top: 23%; left: 28%; width: 3.5px; height: 3.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp37 3.27s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.10s;}
.p38 {top: 52%; left: 63%; width: 1.1px; height: 1.1px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp38 3.01s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.36s;}
.p39 {top: 67%; left: 17%; width: 5.6px; height: 5.6px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp39 1.94s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.38s;}
.p40 {top: 21%; left: 36%; width: 2.0px; height: 2.0px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp40 4.02s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.00s;}
.p41 {top: 18%; left: 62%; width: 8.1px; height: 8.1px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp41 1.92s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.82s;}
.p42 {top: 39%; left: 66%; width: 5.0px; height: 5.0px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp42 3.18s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.74s;}
.p43 {top: 71%; left: 19%; width: 5.5px; height: 5.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp43 3.05s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.10s;}
.p44 {top: 64%; left: 19%; width: 1.7px; height: 1.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp44 3.65s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.24s;}
.p45 {top: 75%; left: 80%; width: 4.3px; height: 4.3px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp45 3.35s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.75s;}
.p46 {top: 55%; left: 64%; width: 3.5px; height: 3.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp46 3.26s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.71s;}
.p47 {top: 17%; left: 68%; width: 11.0px; height: 11.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp47 1.48s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.88s;}
.p48 {top: 77%; left: 52%; width: 2.3px; height: 2.3px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp48 4.38s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.78s;}
.p49 {top: 66%; left: 43%; width: 7.3px; height: 7.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp49 1.93s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.92s;}
.p50 {top: 69%; left: 75%; width: 7.0px; height: 7.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp50 1.89s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.95s;}
.p51 {top: 75%; left: 48%; width: 2.6px; height: 2.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp51 4.54s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.05s;}
.p52 {top: 65%; left: 26%; width: 8.4px; height: 8.4px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp52 2.06s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.39s;}
.p53 {top: 17%; left: 35%; width: 9.8px; height: 9.8px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp53 2.16s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.79s;}
.p54 {top: 27%; left: 77%; width: 1.9px; height: 1.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp54 2.62s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.98s;}
.p55 {top: 43%; left: 56%; width: 3.9px; height: 3.9px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp55 2.25s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.82s;}
.p56 {top: 35%; left: 24%; width: 2.9px; height: 2.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp56 4.77s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.45s;}
.p57 {top: 29%; left: 27%; width: 2.6px; height: 2.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp57 3.26s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.05s;}
.p58 {top: 43%; left: 51%; width: 1.3px; height: 1.3px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp58 4.60s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.51s;}
.p59 {top: 39%; left: 17%; width: 2.9px; height: 2.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp59 2.56s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.64s;}
.p60 {top: 78%; left: 84%; width: 11.2px; height: 11.2px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp60 1.32s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.51s;}
.p61 {top: 49%; left: 73%; width: 7.7px; height: 7.7px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp61 2.00s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.21s;}
.p62 {top: 75%; left: 42%; width: 10.0px; height: 10.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp62 2.12s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.71s;}
.p63 {top: 16%; left: 28%; width: 6.1px; height: 6.1px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp63 2.21s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.88s;}
.p64 {top: 43%; left: 27%; width: 3.7px; height: 3.7px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp64 2.88s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.88s;}
.p65 {top: 38%; left: 75%; width: 5.2px; height: 5.2px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp65 1.99s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.77s;}
.p66 {top: 30%; left: 47%; width: 4.8px; height: 4.8px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp66 3.30s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.46s;}
.p67 {top: 63%; left: 63%; width: 2.0px; height: 2.0px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp67 3.67s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.12s;}
.p68 {top: 23%; left: 61%; width: 3.2px; height: 3.2px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp68 2.65s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.52s;}
.p69 {top: 77%; left: 20%; width: 5.2px; height: 5.2px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp69 3.19s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.74s;}
.p70 {top: 18%; left: 46%; width: 2.9px; height: 2.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp70 3.54s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.13s;}
.p71 {top: 68%; left: 47%; width: 4.5px; height: 4.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp71 2.53s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.91s;}
.p72 {top: 72%; left: 67%; width: 10.9px; height: 10.9px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp72 1.41s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.50s;}
.p73 {top: 56%; left: 80%; width: 5.4px; height: 5.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp73 3.17s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.59s;}
.p74 {top: 23%; left: 50%; width: 6.9px; height: 6.9px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp74 2.45s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.56s;}
.p75 {top: 84%; left: 54%; width: 11.2px; height: 11.2px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp75 2.07s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.44s;}
.p76 {top: 44%; left: 32%; width: 2.7px; height: 2.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp76 4.72s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.91s;}
.p77 {top: 38%; left: 17%; width: 4.6px; height: 4.6px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp77 3.24s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.21s;}
.p78 {top: 56%; left: 20%; width: 1.7px; height: 1.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp78 2.87s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.34s;}
.p79 {top: 50%; left: 17%; width: 8.0px; height: 8.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp79 1.77s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.93s;}
.p80 {top: 61%; left: 51%; width: 10.3px; height: 10.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp80 2.12s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.54s;}
.p81 {top: 29%; left: 84%; width: 11.5px; height: 11.5px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp81 1.93s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.49s;}
.p82 {top: 67%; left: 69%; width: 2.3px; height: 2.3px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp82 2.99s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.84s;}
.p83 {top: 66%; left: 81%; width: 4.6px; height: 4.6px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp83 1.96s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.79s;}
.p84 {top: 24%; left: 66%; width: 8.0px; height: 8.0px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp84 1.46s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.76s;}
.p85 {top: 49%; left: 50%; width: 2.1px; height: 2.1px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp85 3.82s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.03s;}
.p86 {top: 22%; left: 60%; width: 3.4px; height: 3.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp86 2.03s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.27s;}
.p87 {top: 82%; left: 85%; width: 8.3px; height: 8.3px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp87 2.27s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.07s;}
.p88 {top: 23%; left: 77%; width: 7.8px; height: 7.8px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp88 1.71s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -1.32s;}
.p89 {top: 44%; left: 83%; width: 5.4px; height: 5.4px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp89 3.49s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.86s;}
.p90 {top: 55%; left: 40%; width: 5.9px; height: 5.9px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp90 2.74s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.29s;}
.p91 {top: 50%; left: 84%; width: 5.3px; height: 5.3px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp91 3.14s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.97s;}
.p92 {top: 50%; left: 73%; width: 2.6px; height: 2.6px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp92 4.20s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -4.00s;}
.p93 {top: 59%; left: 68%; width: 2.7px; height: 2.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp93 4.82s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.78s;}
.p94 {top: 27%; left: 80%; width: 1.7px; height: 1.7px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp94 3.54s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.50s;}
.p95 {top: 33%; left: 41%; width: 1.9px; height: 1.9px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp95 3.98s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -3.30s;}
.p96 {top: 78%; left: 37%; width: 11.5px; height: 11.5px; box-shadow: 0 0 12px rgba(255,255,255,0.50), 0 0 28px rgba(212,175,55,0.40), 0 0 50px rgba(212,175,55,0.20); animation: warp96 1.57s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.64s;}
.p97 {top: 64%; left: 50%; width: 4.1px; height: 4.1px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp97 2.20s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.14s;}
.p98 {top: 53%; left: 85%; width: 3.9px; height: 3.9px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp98 2.84s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.19s;}
.p99 {top: 23%; left: 43%; width: 2.8px; height: 2.8px; box-shadow: 0 0 4px rgba(255,255,255,0.30), 0 0 8px rgba(212,175,55,0.20); animation: warp99 3.23s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -0.74s;}
.p100 {top: 50%; left: 19%; width: 3.5px; height: 3.5px; box-shadow: 0 0 8px rgba(255,255,255,0.40), 0 0 16px rgba(212,175,55,0.30); animation: warp100 3.32s cubic-bezier(0.5, 0, 0.95, 0.4) infinite; animation-delay: -2.06s;}
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
[data-testid="stColumn"]:has([class*="st-key-del_"]) {position: relative;}
[class*="st-key-del_"] {position: absolute !important; bottom: 12px; right: 12px; width: auto !important; z-index: 10;}
[class*="st-key-del_"] button {background: rgba(0,0,0,0.6) !important; color: white !important; border: 1px solid rgba(255,255,255,0.3) !important; border-radius: 6px !important; padding: 4px 10px !important; min-height: auto !important; line-height: 1.2 !important; backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);}
[class*="st-key-del_"] button:hover {background: rgba(220,38,38,0.85) !important; border-color: rgba(255,255,255,0.5) !important;}
[class*="st-key-del_"] button p {font-size: 12px !important; margin: 0 !important; color: white !important;}
.detail-table {width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 14px;}
.detail-table th, .detail-table td {padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,0.15); text-align: left; color: white;}
.detail-table th {background: rgba(255,255,255,0.06); font-weight: 600;}
.detail-table tr.mismatch td {background: #fee2e2 !important; color: #7f1d1d !important;}
.detail-table tr.mismatch td:first-child {border-left: 4px solid #dc2626 !important;}
.detail-table tr.special td {background: #fef3c7 !important; color: #78350f !important;}
.detail-table tr.special td:first-child {border-left: 4px solid #d97706 !important;}
.detail-table tr.charter td {background: #dbeafe !important; color: #1e3a8a !important;}
.detail-table tr.charter td:first-child {border-left: 4px solid #2563eb !important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-block">
  <h1>AIタクシー日報<span style="font-size: 13px; color: #d4af37; font-weight: 400; margin-left: 8px;">by 怒りの山本</span></h1>
  <p class="subtitle">DAILY REPORT · OCR ASSIST</p>
  <div class="divider"></div>
</div>
""", unsafe_allow_html=True)

import streamlit.components.v1 as components
components.html('''
<script src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js"></script>
<script>
let audioStarted = false;
let interval = null;

async function startJazzDrums() {
  if (audioStarted) return;
  await Tone.start();
  audioStarted = true;
  
  // ハイハット（テッチッチ）
  const hihat = new Tone.MetalSynth({
    frequency: 250,
    envelope: {attack: 0.001, decay: 0.05, release: 0.05},
    harmonicity: 5.1,
    modulationIndex: 32,
    resonance: 4000,
    octaves: 1.5
  }).toDestination();
  hihat.volume.value = -20;
  
  // バスドラム
  const kick = new Tone.MembraneSynth().toDestination();
  kick.volume.value = -10;
  
  let beat = 0;
  interval = setInterval(() => {
    const time = Tone.now();
    // ジャズのスイングパターン: テッ・チッチ、テッ・チッチ
    if (beat % 4 === 0) {
      kick.triggerAttackRelease("C2", "8n", time);
      hihat.triggerAttackRelease("C5", "32n", time);
    } else if (beat % 4 === 2) {
      hihat.triggerAttackRelease("C5", "32n", time);
      hihat.triggerAttackRelease("C5", "32n", time + 0.1);
    } else {
      hihat.triggerAttackRelease("C5", "32n", time);
    }
    beat++;
  }, 250);
}

function stopJazzDrums() {
  if (interval) clearInterval(interval);
  audioStarted = false;
}

// オーバーレイ表示を監視
const observer = new MutationObserver(() => {
  const overlay = document.querySelector('.big-overlay');
  if (overlay && !audioStarted) startJazzDrums();
  if (!overlay && audioStarted) stopJazzDrums();
});
observer.observe(document.body, {childList: true, subtree: true});
</script>
''', height=0)

# ============================================================
# 1. 画像準備
# ============================================================

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
    img.thumbnail((3000, 3000))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=95)
    return base64.standard_b64encode(buf.getvalue()).decode()


# ============================================================
# 2. 画像識別
# ============================================================

def identify_image(client, img):
    """画像を判定して 'meter' / 'nippou' / 'unclear' を返す"""
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


# ============================================================
# 3. 鮮明度チェック
# ============================================================

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


# ============================================================
# 4. メーター明細を読み取る
# ============================================================

def parse_meter(client, meter_img):
    """メーター明細書から行リストを取得。返値: dict {rows: [...], total: int}"""
    res = client.messages.create(
        model='claude-opus-4-5', max_tokens=4000, temperature=0,
        messages=[{'role':'user','content':[
            {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(meter_img)}},
            {'type':'text','text':'''メーター明細書（営業明細書）の全行を読み取ってJSONで出力してください。

【厳密ルール】
- 金額は桁ごとに慎重に読み取る（千の位・百の位・十の位を順に確認）。
- 紛らわしい数字ペア（3/2、8/2、5/4、1/5、6/0、7/1、9/4、8/3）に最大限注意。
- 文脈で推測しない。あくまで画像上の文字を読む。
- 全ての行を漏れなく出力（行を抜かさない）。

【出力】
JSON 形式のみ（前後に余計なテキスト・コードブロック記号なし）：
{
  "rows": [
    {"no": 1, "time": "10:32", "amount": 4100},
    {"no": 2, "time": "10:50", "amount": 1000}
  ],
  "total": 5100
}

- amount は整数（カンマ・¥・円なし）
- time は HH:MM 形式
- total は全 amount の合計（検算用）'''}
        ]}]
    )
    text = res.content[0].text.strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        raise ValueError(f'メーター明細のJSONが見つかりません。応答: {text[:300]}')
    return json.loads(m.group(0))


# ============================================================
# 5. 日報を読み取る
# ============================================================

def parse_nippou(client, nippou_img, meter_data):
    """日報を読み取り、メーター明細との対応＋特殊ケースを取得。返値: dict {rides: [...], extras: [...]}"""
    meter_summary = '\n'.join(f"  No.{r['no']}: {r['time']} ¥{r['amount']:,}" for r in meter_data.get('rows', []))
    res = client.messages.create(
        model='claude-opus-4-5', max_tokens=4000, temperature=0,
        messages=[{'role':'user','content':[
            {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(nippou_img)}},
            {'type':'text','text':f'''これはタクシー乗務員の手書き日報です。
別途読み取り済みのメーター明細書（営業明細書）の行リストは以下：
{meter_summary}

【あなたのタスク】
日報の各行を読み取り、メーター明細書のどの行に対応するかを判定し、各行の補助情報（人数・現収/未収・摘要・特殊ケース）を取得してください。

【金額の扱い - 最重要】
日報の現収/未収欄に書かれた数字そのものは出力しないでください（金額はメーター明細を採用するため）。
ただし以下の例外のみ、日報から金額を読み取って出力します：
- メーター超過の「+〇〇」追記の値（例: +100 → overage_amount: 100）
- 貸切の金額（メーター明細にない料金体系）
- 障害者割引の割引額（日報に別行で「現金」として計上されている場合）

【現収/未収判定】
摘要を最優先で判断：
- 摘要に「Visa」「Uber」「Suica」「交通系」「PayPay」等のカード/電子マネー名 → 「未収」
- 摘要が空欄、または「現金」 → 「現収」
- 訂正線（取り消し線）で消された数字や記載は無視

【「+〇〇」記号の認識（メーター超過時）】
- 「+100」を「1,100」と誤読しない。「+200」を「1,200」と誤読しない。
- 「+」の先頭の小さな記号を絶対に見落とさない。
- 通常の現収/未収欄とは別に、行の付近に小さく書かれた数字は超過分の候補。
- 超過額は固定値ではなく、毎回異なる金額（+50、+100、+200、+300 など）。

【出力 - JSON のみ。前後に余計なテキスト・コードブロック記号なし】
{{
  "rides": [
    {{
      "meter_no": 1,
      "passengers": 2,
      "kind": "現収",
      "memo": "現金",
      "case": "normal",
      "overage_amount": null
    }},
    {{
      "meter_no": 2,
      "passengers": 1,
      "kind": "未収",
      "memo": "Visa",
      "case": "overage",
      "overage_amount": 100
    }}
  ],
  "extras": [
    {{
      "case": "charter",
      "passengers": 1,
      "kind": "現収",
      "memo": "貸切 △△商事",
      "amount": 12000
    }},
    {{
      "case": "discount_cash",
      "passengers": 0,
      "kind": "現収",
      "memo": "障割現金",
      "amount": 160,
      "linked_meter_no": 5
    }}
  ]
}}

【フィールド】
- meter_no: 対応するメーター明細の番号（1始まり）
- passengers: 人数（読み取り）
- kind: "現収" または "未収"
- memo: 摘要（Visa, Uber, 現金, 障割, 等）
- case:
  * "normal": 通常乗車
  * "overage": メーター超過（日報に+〇〇追記あり）。overage_amount に超過分の値を記入
  * "disabled": 障害者割引（摘要に「障割」記載）
- extras: メーター明細にない追加行
  * "charter": 貸切（メーター明細に該当無し）。amount に金額
  * "discount_cash": 障害者割引の割引現金行（日報に別行で計上）。amount に割引額、linked_meter_no で関連付け

【厳守】
- rides の数 ≦ メーター明細行数。マッチしない日報行は extras に入れる（charter/discount_cash どちらでもなければ無視）。
- 全ての値が JSON として valid であること（クォート・カンマ・null など）。
- メーター明細と1対1対応する rides を必ず meter_no 昇順で出力。'''}
        ]}]
    )
    text = res.content[0].text.strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        raise ValueError(f'日報のJSONが見つかりません。応答: {text[:300]}')
    return json.loads(m.group(0))


# ============================================================
# 6. データ統合
# ============================================================

def build_report(meter_data, nippou_data):
    """メーターを主、日報を補助として最終データを構築"""
    meter_rows = {r['no']: r for r in meter_data.get('rows', [])}
    nippou_by_meter = {r['meter_no']: r for r in nippou_data.get('rides', [])}
    output = []

    for meter_no in sorted(meter_rows.keys()):
        meter_row = meter_rows[meter_no]
        n = nippou_by_meter.get(meter_no, {})
        passengers = n.get('passengers') or 1
        kind = n.get('kind') or '現収'
        memo = n.get('memo') or ''
        case = n.get('case') or 'normal'

        if case == 'overage':
            overage = int(n.get('overage_amount') or 0)
            client_amount = meter_row['amount'] - overage
            output.append({
                'no': meter_no, 'passengers': passengers, 'time': meter_row['time'],
                'gen': client_amount if kind == '現収' else 0,
                'mi': client_amount if kind == '未収' else 0,
                'memo': memo, 'state': 'ok',
            })
            output.append({
                'no': meter_no, 'passengers': passengers, 'time': meter_row['time'],
                'gen': overage, 'mi': 0,
                'memo': 'メーター超過', 'state': 'special',
            })
        elif case == 'disabled':
            display_memo = memo if '障割' in memo else (f'障割 {memo}'.strip() if memo else '障割')
            output.append({
                'no': meter_no, 'passengers': passengers, 'time': meter_row['time'],
                'gen': meter_row['amount'] if kind == '現収' else 0,
                'mi': meter_row['amount'] if kind == '未収' else 0,
                'memo': display_memo, 'state': 'ok',
            })
        else:
            output.append({
                'no': meter_no, 'passengers': passengers, 'time': meter_row['time'],
                'gen': meter_row['amount'] if kind == '現収' else 0,
                'mi': meter_row['amount'] if kind == '未収' else 0,
                'memo': memo, 'state': 'ok',
            })

    next_no = (max(meter_rows.keys()) + 1) if meter_rows else 1
    for extra in nippou_data.get('extras', []):
        case = extra.get('case')
        amount = int(extra.get('amount') or 0)
        kind = extra.get('kind') or '現収'
        passengers = extra.get('passengers') or 0
        memo = extra.get('memo') or ''
        if case == 'charter':
            output.append({
                'no': next_no, 'passengers': passengers, 'time': '',
                'gen': amount if kind == '現収' else 0,
                'mi': amount if kind == '未収' else 0,
                'memo': memo or '貸切', 'state': 'charter',
            })
            next_no += 1
        elif case == 'discount_cash':
            linked = extra.get('linked_meter_no') or next_no
            output.append({
                'no': linked, 'passengers': 0, 'time': '',
                'gen': amount, 'mi': 0,
                'memo': memo or '障割現金', 'state': 'ok',
            })

    return output


# ============================================================
# 7. 整合性チェック
# ============================================================

def validate(report_rows, meter_data, nippou_data):
    """合計の整合性チェック。返値: (ok: bool, diff: int)"""
    output_total = sum((r['gen'] or 0) + (r['mi'] or 0) for r in report_rows)
    expected = meter_data.get('total') or sum(r['amount'] for r in meter_data.get('rows', []))
    for extra in nippou_data.get('extras', []):
        amt = int(extra.get('amount') or 0)
        if extra.get('case') in ('charter', 'discount_cash'):
            expected += amt
    diff = output_total - expected
    return diff == 0, diff


# ============================================================
# Loader 演出ヘルパー
# ============================================================

def _particles_html():
    return ''.join(f'<span class="particle p{i}"></span>' for i in range(1, 101))

def show_loader(loader, pct, label):
    loader.markdown(
        f'<div class="big-overlay"><div class="particles">{_particles_html()}</div>'
        f'<div class="big-num">{pct}%</div><div class="big-label">{label}</div></div>',
        unsafe_allow_html=True
    )

def loader_steps(loader, pcts, label, sleep=0.15):
    for pct in pcts:
        show_loader(loader, pct, label)
        time.sleep(sleep)


# ============================================================
# 8. 表示ヘルパー
# ============================================================

def render_summary(ken, nin, gen, mi, sou, tax, net):
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
    state_class_map = {'mismatch': 'mismatch', 'special': 'special', 'charter': 'charter'}
    for r in rows:
        cls = state_class_map.get(r.get('state', ''), '')
        row_class = f' class="{cls}"' if cls else ''
        gen = f"{r['gen']:,}" if r['gen'] else ''
        mi = f"{r['mi']:,}" if r['mi'] else ''
        parts.append(f'<tr{row_class}>')
        parts.append(f'<td>{r["no"]}</td>')
        parts.append(f'<td>{r["passengers"] if r["passengers"] else ""}</td>')
        parts.append(f'<td>{r["time"]}</td>')
        parts.append(f'<td>{gen}</td>')
        parts.append(f'<td>{mi}</td>')
        parts.append(f'<td>{r["memo"]}</td>')
        parts.append(f'<td>{r["state"]}</td>')
        parts.append('</tr>')
    parts.append('</tbody></table>')
    st.markdown(''.join(parts), unsafe_allow_html=True)


def aggregate_totals(rows):
    """件数・人数・現収・未収・総収・消費税・税抜運収を集計"""
    gen = sum((r.get('gen') or 0) for r in rows)
    mi = sum((r.get('mi') or 0) for r in rows)
    ken = sum(1 for r in rows if r.get('state') != 'special')
    nin = sum((r.get('passengers') or 0) for r in rows if r.get('state') != 'special')
    sou = gen + mi
    tax = round(sou / 11, -1)
    net = sou - tax
    return ken, nin, gen, mi, sou, int(tax), net


# ============================================================
# パイプライン本体
# ============================================================

def run_pipeline(client, imgs, loader):
    """End-to-end pipeline. 失敗時は RuntimeError。返値: (rows, valid, diff)"""
    loader_steps(loader, [3, 8, 14], '画像を判別中')
    kind1 = identify_image(client, imgs[0])
    kind2 = identify_image(client, imgs[1])

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

    loader_steps(loader, [18, 24, 30], '鮮明度を確認中')
    ok, reason = check_clarity(client, meter_img, nippou_img)
    if not ok:
        raise RuntimeError(f'画像の鮮明度が不足しています：{reason}\n撮り直して再アップしてください。')

    loader_steps(loader, [35, 42, 50], 'メーター明細を読み取り中')
    meter_data = parse_meter(client, meter_img)

    loader_steps(loader, [60, 70, 80], '日報を読み取り中')
    nippou_data = parse_nippou(client, nippou_img, meter_data)

    loader_steps(loader, [88, 94, 100], '統合中')
    report_rows = build_report(meter_data, nippou_data)
    valid, diff = validate(report_rows, meter_data, nippou_data)
    return report_rows, valid, diff


# ============================================================
# Reset / state
# ============================================================

def reset_app():
    st.session_state.uploader_counter = st.session_state.get('uploader_counter', 0) + 1
    st.session_state.kept_files = []
    for k in ('result_rows', 'result_valid', 'result_diff'):
        if k in st.session_state:
            del st.session_state[k]

if 'uploader_counter' not in st.session_state:
    st.session_state.uploader_counter = 0
if 'kept_files' not in st.session_state:
    st.session_state.kept_files = []
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
            report_rows, valid, diff = run_pipeline(client, imgs, loader)
            loader.empty()
            st.session_state.result_rows = report_rows
            st.session_state.result_valid = valid
            st.session_state.result_diff = diff
        except RuntimeError as e:
            loader.empty()
            for k in ('result_rows', 'result_valid', 'result_diff'):
                st.session_state.pop(k, None)
            st.error(str(e))
        except json.JSONDecodeError as e:
            loader.empty()
            for k in ('result_rows', 'result_valid', 'result_diff'):
                st.session_state.pop(k, None)
            st.error(f'AI応答のJSON解析に失敗しました: {e}\nもう一度お試しください。')
        except Exception as e:
            loader.empty()
            for k in ('result_rows', 'result_valid', 'result_diff'):
                st.session_state.pop(k, None)
            st.error(f'処理中にエラーが発生しました: {type(e).__name__}: {e}')
elif st.session_state.kept_files and len(st.session_state.kept_files) != 2:
    st.warning(f'2枚選択してください（現在{len(st.session_state.kept_files)}枚）')

# ============================================================
# 結果表示（result_rows が session_state にある時）
# ============================================================

if st.session_state.get('result_rows'):
    rows = st.session_state.result_rows
    valid = st.session_state.result_valid
    diff = st.session_state.result_diff

    st.markdown('<div class="result-card">', unsafe_allow_html=True)

    if not valid:
        st.warning(f'⚠️ 金額が ¥{abs(diff):,} ずれています。下の表で内容を確認してください。')

    ken, nin, gen, mi, sou, tax, net = aggregate_totals(rows)
    render_summary(ken, nin, gen, mi, sou, tax, net)
    render_detail_table(rows)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<br>', unsafe_allow_html=True)
    st.button('🔄 新しい日報を作成', on_click=reset_app, key='reset_btn', use_container_width=True)


with st.expander('？ このアプリについて・使い方'):
    st.markdown('''
### 1. 日報の書き方ルール
このアプリを正しく使うには、手書き日報の書き方にルールがあります。

- **通常の乗車**：日報の現収欄か未収欄に金額を記入
- **メーター超過（消し忘れ）**：客の支払いが終わった後にメーターが回ってしまった場合、別の行を追加して「現収」に超過分を記入する（自己負担で会社に納金）
  例：客が1,600円支払い→メーター1,700円なら、客分1,600円とは別に、超過分100円を「現収」で1行追加
- **障害者割引（障割）**：障害者割引適用の乗車は、別の行として記入する。摘要欄に「障割」と明記

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

作者＞怒りの山本
''')
