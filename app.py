import streamlit as st
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
/* 粒子の動きを不規則に：nth-child で7種類のイージング曲線をローテーション */
.particle:nth-child(7n)   {animation-timing-function: cubic-bezier(0.30, 0.10, 0.70, 0.90) !important;}
.particle:nth-child(7n+1) {animation-timing-function: cubic-bezier(0.62, 0.04, 0.32, 1.00) !important;}
.particle:nth-child(7n+2) {animation-timing-function: cubic-bezier(0.20, 0.45, 0.85, 0.55) !important;}
.particle:nth-child(7n+3) {animation-timing-function: cubic-bezier(0.85, 0.05, 0.18, 0.98) !important;}
.particle:nth-child(7n+4) {animation-timing-function: cubic-bezier(0.45, 0.65, 0.55, 0.35) !important;}
.particle:nth-child(7n+5) {animation-timing-function: cubic-bezier(0.55, 0.00, 0.45, 1.00) !important;}
.particle:nth-child(7n+6) {animation-timing-function: cubic-bezier(0.10, 0.30, 0.92, 0.72) !important;}
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


def _img_to_bytes(img, max_size=3000, quality=95):
    """PIL Image を JPEG bytes に変換（Vision API 用）"""
    img_copy = img.copy()
    img_copy.thumbnail((max_size, max_size))
    buf = io.BytesIO()
    img_copy.save(buf, format='JPEG', quality=quality)
    return buf.getvalue()


# ============================================================
# 1.5 Google Vision API クライアント取得
# ============================================================
#
# 認証元の優先順:
#   1) st.secrets["gcp_service_account"]（Streamlit Cloud）
#   2) ローカルの key.json
#   3) 取得不能なら None（Claude にフォールバック）
# ============================================================

@st.cache_resource
def get_vision_client():
    """Returns the Vision API client. Failure detail is stored in session_state to surface in UI.
    Note: @st.cache_resource は client インスタンスをキャッシュするので、再認証は走らない。"""
    err_chain = []

    # 1) Streamlit Secrets を試行
    secrets_has_key = False
    try:
        secrets_has_key = 'gcp_service_account' in st.secrets
    except Exception as e:
        err_chain.append(f'st.secrets アクセス失敗: {type(e).__name__}: {e}')

    if secrets_has_key:
        try:
            info = dict(st.secrets['gcp_service_account'])
            credentials = service_account.Credentials.from_service_account_info(info)
            client = vision.ImageAnnotatorClient(credentials=credentials)
            return client
        except Exception as e:
            err_chain.append(f'secrets 認証失敗: {type(e).__name__}: {e}')
    else:
        err_chain.append('st.secrets に "gcp_service_account" セクションが存在しない')

    # 2) ローカル key.json を試行
    if os.path.exists('key.json'):
        try:
            credentials = service_account.Credentials.from_service_account_file('key.json')
            client = vision.ImageAnnotatorClient(credentials=credentials)
            return client
        except Exception as e:
            err_chain.append(f'key.json 認証失敗: {type(e).__name__}: {e}')
    else:
        err_chain.append('ローカル key.json も存在しない')

    # 失敗内容を session_state に残し、サーバ stdout にも出力
    msg = ' / '.join(err_chain)
    try:
        st.session_state['_vision_auth_error'] = msg
    except Exception:
        pass
    print(f'[VISION] auth failed: {msg}')
    return None


def _get_vision_auth_error():
    """get_vision_client() が記録した認証失敗理由を返す（無ければ空文字）"""
    try:
        return st.session_state.get('_vision_auth_error', '')
    except Exception:
        return ''


# ============================================================
# 2. 画像識別
# ============================================================

def _identify_meter_via_vision(img):
    """Vision API で「営業明細書」等のキーワードを検出。検出されれば 'meter'、それ以外は None。"""
    vc = get_vision_client()
    if vc is None:
        return None
    try:
        image = vision.Image(content=_img_to_bytes(img, max_size=2000, quality=85))
        response = vc.text_detection(image=image)
        if response.error.message:
            return None
        text = response.full_text_annotation.text if response.full_text_annotation else ''
        if any(kw in text for kw in ['営業明細書', '明細書', 'メーター']):
            return 'meter'
        return None
    except Exception:
        return None


def identify_image(client, img):
    """画像を判定して 'meter' / 'nippou' / 'unclear' を返す。
    Vision API で 'meter' 確定なら早期リターン、それ以外は Claude で判定。"""
    v = _identify_meter_via_vision(img)
    if v == 'meter':
        return 'meter'

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
# 4. Stage 1 - メーター明細書のみを読み取る（金額確定）
# ============================================================
#
# 【ハイブリッド構成】
#   1) Google Vision API で OCR → 正規表現で構造化（高精度・機械印字向け）
#   2) Vision で行抽出に失敗した場合のみ Claude にフォールバック
#
# 【契約】
# - 入力：メーター明細書1枚のみ（日報は渡さない）
# - 出力：rows = [{no, time, amount}, ...], total, source（'vision' or 'claude'）
# - この関数の出力金額は、以降のすべての処理で「真実」として扱う。
#   build_report ではこの金額を改変せずに使用する。
# ============================================================

def _parse_meter_vision(meter_img):
    """Stage 1: Vision API で OCR したテキストに、レシート書式専用の正規表現を当てる。

    レシート書式: 「N.HH:MM [...] ¥X,XXX円」
    パターン: r'(\\d+)\\.\\s*(\\d{1,2}:\\d{2})[^\\n¥]*¥([\\d,]+)円'
    - グループ1: レシート印字の行番号 N
    - グループ2: 時刻 HH:MM
    - グループ3: 金額（カンマ含む）

    成功時: {'success': True, 'rows': [{'no':1,'time':'10:32','amount':4100},...], 'total': N,
             'source': 'vision', 'raw_text': str}
    失敗時: {'success': False, 'stage': 'auth'|'api_call'|'api_response'|'ocr'|'parser', 'reason': str, 'raw_text': str|None}
    """
    vc = get_vision_client()
    if vc is None:
        auth_err = _get_vision_auth_error() or 'Vision client 取得失敗（理由不明）'
        return {'success': False, 'stage': 'auth',
                'reason': f'Vision client 取得失敗: {auth_err}', 'raw_text': None}

    try:
        image = vision.Image(content=_img_to_bytes(meter_img, max_size=3000, quality=95))
        response = vc.document_text_detection(image=image)
    except Exception as e:
        return {'success': False, 'stage': 'api_call',
                'reason': f'Vision API 呼び出し例外: {type(e).__name__}: {e}', 'raw_text': None}

    if response.error.message:
        return {'success': False, 'stage': 'api_response',
                'reason': f'Vision API エラー応答: {response.error.message}', 'raw_text': None}

    full_text = response.full_text_annotation.text if response.full_text_annotation else ''
    if not full_text.strip():
        return {'success': False, 'stage': 'ocr',
                'reason': 'OCRテキストが空', 'raw_text': ''}

    pattern = re.compile(r'(\d+)\.\s*(\d{1,2}:\d{2})[^\n¥]*¥([\d,]+)円')
    rows = []
    for m in pattern.finditer(full_text):
        no = int(m.group(1))
        h, mi = m.group(2).split(':')
        time_str = f"{int(h):02d}:{mi}"
        amount = int(m.group(3).replace(',', ''))
        rows.append({'no': no, 'time': time_str, 'amount': amount})
    rows.sort(key=lambda r: r['no'])

    # デバッグ出力: 抽出した各行を Streamlit Cloud ログに
    for r in rows:
        print(f"[METER LINE No.{r['no']}] {r['time']} ¥{r['amount']:,}")

    if not rows:
        return {'success': False, 'stage': 'parser',
                'reason': 'Parser: 「N.HH:MM ... ¥X,XXX円」形式の行を抽出できませんでした',
                'raw_text': full_text}

    total = sum(r['amount'] for r in rows)
    return {'success': True, 'rows': rows, 'total': total,
            'source': 'vision', 'raw_text': full_text}


def _parse_meter_claude(client, meter_img):
    """[フォールバック] Claude API でメーター明細を読み取る。"""
    res = client.messages.create(
        model='claude-opus-4-5', max_tokens=4000, temperature=0,
        messages=[{'role':'user','content':[
            {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(meter_img)}},
            {'type':'text','text':'''メーター明細書（営業明細書）の全行を読み取って JSON で出力してください。
このアプリ全体の精度は、ここでの読み取りが100%正確であることに完全に依存しています。

【★最重要：誤読防止プロセス★】
直近の誤読例（同じ間違いを繰り返さない）：
- ¥1,800 を ¥1,500 と読んだ（8 と 5 を取り違え）
- ¥1,100 を ¥5,100 と読んだ（千の位を別の数字と誤認）
- ¥1,500 を ¥1,800 と読んだ（5 と 8 を取り違え）

【読み取り手順 - この順番で必ず実行】

Step 1: 各行を1つずつ慎重に読む
- 各行の金額を「千・百・十・一」の4桁に分けて、1桁ずつ画像を見て確認する。
- 「ぱっと見」で読まない。1桁ずつ視線を動かしながら判別する。

Step 2: 紛らわしい数字に最大限注意
- 「3」と「2」（横棒の数の違い）
- 「8」と「2」「3」「5」（曲線の閉じ方）
- 「5」と「4」（横棒の位置）
- 「7」と「1」（横棒の有無）
- 「9」と「4」（上の閉じた円の有無）
- 「6」と「0」（中央の点・閉じ方）
- 「1」と「5」（千の位での誤認に特に注意）
- 「8」と「3」（曲線の閉じ方）

Step 3: 文脈推測の禁止
- 不確実な箇所も、前後の金額や合計から「だいたいこのくらい」と推測しない。
- 必ず画像のその位置の数字そのものを読む。判読できない場合は最も近い形を選ぶ。

Step 4: 全行読み終わったら、必ずもう一度先頭から各金額を再確認（セルフレビュー）
- 各行について、もう一度桁ごとに見て、Step 1 の結果と一致するか確認する。
- 一致しなかった行は、3度目の確認で最終決定する。
- 似た数字（3/2、8/2/5、5/4、7/1、9/4、6/0、1/5、8/3）が含まれる桁は特に念入りに。

【厳守】
- 全ての行を漏れなく出力（行を抜かさない）。行番号は明細書の表示通り（1から連番）。
- amount は整数（カンマ・¥・円なし）。
- time は HH:MM 形式。

【出力】
JSON 形式のみ（前後に余計なテキスト・コードブロック記号・思考過程の説明なし）：
{
  "rows": [
    {"no": 1, "time": "10:32", "amount": 4100},
    {"no": 2, "time": "10:50", "amount": 1000}
  ],
  "total": 5100
}

- total は全 amount の合計（検算用。算出時に1円も間違えない）'''}
        ]}]
    )
    text = res.content[0].text.strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        raise ValueError(f'メーター明細のJSONが見つかりません。応答: {text[:300]}')
    data = json.loads(m.group(0))
    data['source'] = 'claude'
    return data


def parse_meter(client, meter_img):
    """Stage 1 ディスパッチャ: Vision API を優先、失敗時は Claude にフォールバック。
    結果には _vision_diag フィールドが必ず付与され、Vision の試行結果（成功/失敗段階・理由・raw_text）が記録される。"""
    vision_result = _parse_meter_vision(meter_img)

    if vision_result.get('success'):
        # success=True なら Vision 経由の結果をそのまま返す。診断もポジティブに記録。
        vision_result['_vision_diag'] = {
            'attempted': True,
            'success': True,
            'failed_stage': None,
            'reason': '成功',
            'raw_text': vision_result.get('raw_text', ''),
            'rows_extracted': len(vision_result.get('rows', [])),
        }
        return vision_result

    # Vision 失敗 → Claude フォールバック
    claude_result = _parse_meter_claude(client, meter_img)
    claude_result['_vision_diag'] = {
        'attempted': True,
        'success': False,
        'failed_stage': vision_result.get('stage', 'unknown'),
        'reason': vision_result.get('reason', '不明'),
        'raw_text': vision_result.get('raw_text'),
        'rows_extracted': 0,
    }
    return claude_result


# ============================================================
# 5. Stage 2 - 日報を Claude で分類（金額には触れない）
# ============================================================
#
# 【契約】
# - 入力：日報1枚 + Stage 1 のメーター行リスト（テキストとしてプロンプトに添付）
# - 出力：{'rides': [{meter_no, passengers, kind, memo, case, overage_amount?}, ...]}
# - 各 ride は通常乗客行に対応。から回し（取り消し線つき +金額のみの行）は
#   独立した ride にせず、直前の通常行を case='overage' に更新する。
# ============================================================

def classify_nippou(client, nippou_img, meter_data):
    """Stage 2: 日報を Claude で分類。各通常乗客行を JSON 配列で返す。"""
    meter_summary = '\n'.join(f"  No.{r['no']}: {r['time']} ¥{r['amount']:,}" for r in meter_data.get('rows', []))
    prompt = f"""これはタクシー乗務員の手書き日報です。
別途、メーター明細書から下記の行リストを既に読み取り済みです。

【メーター明細リスト】
{meter_summary}

日報の各行を上から順に処理し、以下のルールで JSON 配列を返してください。

【通常行】
{{"meter_no": 連番（1始まり）, "passengers": 人数（数字）, "kind": "現収" or "未収", "memo": "Visa/Suica/Uber/交通系/現金 等", "case": "normal"}}

【現収/未収判定】
- 摘要に「Visa」「Uber」「Suica」「交通系」「PayPay」等のカード/電子マネー名 → 必ず「未収」
- 摘要が空欄、または「現金」 → 「現収」

【から回し行の判定】
- 乗車区間が取り消し線（横線・斜線・×印）で消されており、現収欄に「+100」「+200」のように「+金額」だけ書かれた行は「から回し」（メーター消し忘れ）。
- この行は ride として出力しない。
- 代わりに、この行の直前の通常行の case を "overage" に変更し、overage_amount にその金額（数値）をセットする。

【出力例】
[
  {{"meter_no": 1, "passengers": 2, "kind": "未収", "memo": "アプリ", "case": "normal"}},
  {{"meter_no": 2, "passengers": 1, "kind": "現収", "memo": "現金", "case": "normal"}},
  {{"meter_no": 21, "passengers": 2, "kind": "未収", "memo": "Visa", "case": "overage", "overage_amount": 100}}
]

【厳守】
- JSON 配列のみを返す。前後に余計なテキスト・コードブロック記号・思考過程は付けない。
- 「+100」を「1,100」と誤読しない。「+200」を「1,200」と誤読しない。
- 取り消し線行を独立した ride として出力しない。
- 通常の現収/未収欄の金額は読み取らない・出力しない（金額はメーター明細リストの値を Python が自動で割り当てる）。"""
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


# ============================================================
# 6. Stage 3 - 純 Python でデータ統合（AIは関与しない）
# ============================================================
#
# 【不変条件】
# - 通常乗車・障害者割引行の金額は meter_data['rows'][n]['amount'] を必ず使用。
#   AI（classify_nippou）が出力した値は kind/memo/case/passengers のみ参照。
# - メーター超過時:
#     客分 = meter_amount - overage_amount  （引き算で算出）
#     超過分 = overage_amount               （日報の +〇〇 そのまま）
#     検算: 客分 + 超過分 == meter_amount   （Python が保証）
# - 貸切・障害者割引現金は nippou_data['extras'] からそのまま使用（メーター外）。
# ============================================================

def build_report(meter_data, nippou_data):
    """Stage 3: メーター明細（金額確定）と日報の分類情報を統合して最終行リストを構築。"""
    meter_rows = {r['no']: r for r in meter_data.get('rows', [])}
    nippou_by_meter = {r['meter_no']: r for r in nippou_data.get('rides', [])}
    output = []

    for meter_no in sorted(meter_rows.keys()):
        meter_row = meter_rows[meter_no]
        meter_amount = int(meter_row['amount'])  # ← Stage 1 の値。絶対不変。
        n = nippou_by_meter.get(meter_no, {})
        passengers = int(n.get('passengers') or 1)
        kind = n.get('kind') or '現収'
        memo = n.get('memo') or ''
        case = n.get('case') or 'normal'

        if case == 'overage':
            overage = int(n.get('overage_amount') or 0)
            client_amount = meter_amount - overage
            # 検算: 客分 + 超過 = メーター額（必ず成立）
            assert client_amount + overage == meter_amount, \
                f'overage split invariant broken: {client_amount} + {overage} != {meter_amount}'
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
                'gen': meter_amount if kind == '現収' else 0,
                'mi': meter_amount if kind == '未収' else 0,
                'memo': display_memo, 'state': 'ok',
            })
        else:  # normal
            output.append({
                'no': meter_no, 'passengers': passengers, 'time': meter_row['time'],
                'gen': meter_amount if kind == '現収' else 0,
                'mi': meter_amount if kind == '未収' else 0,
                'memo': memo, 'state': 'ok',
            })

    # 貸切・障割現金（メーターにない追加行）は extras から
    next_no = (max(meter_rows.keys()) + 1) if meter_rows else 1
    for extra in nippou_data.get('extras', []):
        case = extra.get('case')
        amount = int(extra.get('amount') or 0)
        kind = extra.get('kind') or '現収'
        passengers = int(extra.get('passengers') or 0)
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

def show_loader(loader, pct, label, anim_class=''):
    cls = f'big-overlay {anim_class}'.strip()
    loader.markdown(
        f'<div class="{cls}"><div class="particles">{_particles_html()}</div>'
        f'<div class="big-num">{pct}%</div><div class="big-label">{label}</div></div>',
        unsafe_allow_html=True
    )

def loader_steps(loader, pcts, label, sleep=0.15, anim_class=''):
    for pct in pcts:
        show_loader(loader, pct, label, anim_class=anim_class)
        time.sleep(sleep)
        anim_class = ''  # 最初のステップだけアニメーション、以降は静的に


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
    """End-to-end pipeline. 失敗時は RuntimeError。返値: (rows, valid, diff, meter_data, nippou_data)"""
    # 最初のステップでフェードイン演出
    loader_steps(loader, [3, 8, 14], '画像を判別中', anim_class='entering')
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
    nippou_data = classify_nippou(client, nippou_img, meter_data)

    loader_steps(loader, [88, 94, 100], '統合中')
    report_rows = build_report(meter_data, nippou_data)
    valid, diff = validate(report_rows, meter_data, nippou_data)
    return report_rows, valid, diff, meter_data, nippou_data


# ============================================================
# Reset / state
# ============================================================

def reset_app():
    st.session_state.uploader_counter = st.session_state.get('uploader_counter', 0) + 1
    st.session_state.kept_files = []
    for k in ('result_rows', 'result_valid', 'result_diff', 'result_meter', 'result_nippou'):
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
            report_rows, valid, diff, meter_data, nippou_data = run_pipeline(client, imgs, loader)
            # フェードアウト演出
            show_loader(loader, 100, '完成しました', anim_class='exiting')
            time.sleep(0.3)
            loader.empty()
            st.session_state.result_rows = report_rows
            st.session_state.result_valid = valid
            st.session_state.result_diff = diff
            st.session_state.result_meter = meter_data
            st.session_state.result_nippou = nippou_data
            st.session_state._pending_scroll = True  # 結果表示後に自動スクロール
        except RuntimeError as e:
            loader.empty()
            for k in ('result_rows', 'result_valid', 'result_diff', 'result_meter', 'result_nippou'):
                st.session_state.pop(k, None)
            st.error(str(e))
        except json.JSONDecodeError as e:
            loader.empty()
            for k in ('result_rows', 'result_valid', 'result_diff', 'result_meter', 'result_nippou'):
                st.session_state.pop(k, None)
            st.error(f'AI応答のJSON解析に失敗しました: {e}\nもう一度お試しください。')
        except Exception as e:
            loader.empty()
            for k in ('result_rows', 'result_valid', 'result_diff', 'result_meter', 'result_nippou'):
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
    meter_data = st.session_state.get('result_meter', {'rows': [], 'total': 0})
    nippou_data = st.session_state.get('result_nippou', {'rides': [], 'extras': []})

    # Vision API 失敗時は最上部に目立つバナーを表示（expanderを開かなくても見える）
    _diag = meter_data.get('_vision_diag') or {}
    if _diag and not _diag.get('success'):
        _stage_jp = {
            'auth': '🔐 認証段階（Vision client 取得）',
            'api_call': '📡 API呼び出し段階',
            'api_response': '⚠️ API応答段階',
            'ocr': '👁️ OCR段階（テキスト未検出）',
            'parser': '🔍 Parser段階（行抽出失敗）',
        }.get(_diag.get('failed_stage'), _diag.get('failed_stage', '不明段階'))
        st.error(
            f'### 🟣 Vision API が動作せず Claude にフォールバック中\n\n'
            f'**失敗段階**: {_stage_jp}\n\n'
            f'**理由**: {_diag.get("reason", "不明")}\n\n'
            f'_詳細は下の「🔧 Stage 1: メーター明細生データ」expander を開いて確認できます。_'
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

    ken, nin, gen, mi, sou, tax, net = aggregate_totals(rows)
    render_summary(ken, nin, gen, mi, sou, tax, net)
    render_detail_table(rows)

    st.markdown('</div>', unsafe_allow_html=True)

    # ========== 値の破壊検出（Stage 1 vs 最終出力の整合性チェック）==========
    meter_amounts = {r['no']: int(r['amount']) for r in meter_data.get('rows', [])}
    discount_by_no = {}
    for extra in nippou_data.get('extras', []):
        if extra.get('case') == 'discount_cash':
            ln = extra.get('linked_meter_no')
            if ln in meter_amounts:
                discount_by_no[ln] = discount_by_no.get(ln, 0) + int(extra.get('amount') or 0)
    sum_by_no = {}
    for r in rows:
        if r.get('state') == 'charter':
            continue
        no = r.get('no')
        if no in meter_amounts:
            sum_by_no[no] = sum_by_no.get(no, 0) + int(r.get('gen') or 0) + int(r.get('mi') or 0)
    integrity_issues = []
    for no, meter_amt in sorted(meter_amounts.items()):
        expected = meter_amt + discount_by_no.get(no, 0)
        actual = sum_by_no.get(no, 0)
        if expected != actual:
            integrity_issues.append({
                'no': no, 'meter': meter_amt, 'discount': discount_by_no.get(no, 0),
                'expected': expected, 'actual': actual,
            })

    if integrity_issues:
        st.error(f'🚨 値の破壊を検出（{len(integrity_issues)}件）: Stage 1 で読み取った金額とテーブル出力が一致していません')
        parts = ['<table class="detail-table"><thead><tr><th>No</th><th>Stage1メーター額</th><th>+割引</th><th>期待値</th><th>テーブル合計</th><th>差</th></tr></thead><tbody>']
        for it in integrity_issues:
            diff_v = it['actual'] - it['expected']
            disc_disp = f'¥{it["discount"]:,}' if it['discount'] else '-'
            parts.append(
                f'<tr class="mismatch"><td>{it["no"]}</td>'
                f'<td>¥{it["meter"]:,}</td>'
                f'<td>{disc_disp}</td>'
                f'<td>¥{it["expected"]:,}</td>'
                f'<td>¥{it["actual"]:,}</td>'
                f'<td>{diff_v:+,}</td></tr>'
            )
        parts.append('</tbody></table>')
        st.markdown(''.join(parts), unsafe_allow_html=True)
        st.caption('差が出ている No について、下のデバッグセクションで Stage 1 の値と最終出力の値を照合してください。')

    # ========== Stage 1: メーター明細生データ ==========
    with st.expander('🔧 Stage 1: メーター明細生データ'):
        source = meter_data.get('source', 'unknown')
        source_label = {'vision': '🔵 Google Vision API', 'claude': '🟣 Claude API（フォールバック）'}.get(source, source)
        st.markdown(f'**読み取り元**: {source_label}')

        # Vision 試行の診断情報を表示（フォールバック理由など）
        diag = meter_data.get('_vision_diag') or {}
        if diag:
            stage_jp = {
                'auth': '認証段階（Vision client 取得）',
                'api_call': 'API呼び出し段階',
                'api_response': 'API応答段階',
                'ocr': 'OCR段階',
                'parser': 'Parser段階',
                'unknown': '不明段階',
            }
            if diag.get('success'):
                st.success(f'✅ Vision API 成功: {diag.get("rows_extracted", 0)} 行抽出')
            else:
                stage_label = stage_jp.get(diag.get('failed_stage'), diag.get('failed_stage', '不明'))
                st.warning(f'⚠️ Vision API 失敗 → Claude フォールバック\n\n'
                           f'**失敗段階**: {stage_label}\n\n'
                           f'**理由**: {diag.get("reason", "不明")}')

        # 抽出済み行のテーブル
        meter_rows_disp = meter_data.get('rows', [])
        if meter_rows_disp:
            parts = ['<table class="detail-table"><thead><tr><th>No</th><th>時刻</th><th>金額</th></tr></thead><tbody>']
            for r in meter_rows_disp:
                parts.append(f'<tr><td>{r["no"]}</td><td>{r["time"]}</td><td>¥{r["amount"]:,}</td></tr>')
            parts.append('</tbody></table>')
            st.markdown(''.join(parts), unsafe_allow_html=True)
            st.markdown(f'**合計**: ¥{meter_data.get("total", 0):,}（{len(meter_rows_disp)}行）')
        else:
            st.info('メーター明細データなし')

        # Vision の生テキスト（成功時 / 失敗時の両方で利用可能なら表示）
        raw_text = meter_data.get('raw_text') or diag.get('raw_text')
        if raw_text:
            st.markdown('**Vision API 生テキスト（OCR結果）:**')
            st.code(raw_text[:3000])
            st.caption(f'文字数: {len(raw_text)}、行数（空行除く）: {len([l for l in raw_text.split(chr(10)) if l.strip()])}')

            # 18. / 19. を含む箇所を周辺コンテキスト付きで抽出
            st.markdown('**🔍 「18.」「19.」を含む部分（処理前の生データ）:**')
            target_lines = []
            text_lines = raw_text.split('\n')
            for i, line in enumerate(text_lines):
                if '18.' in line or '19.' in line:
                    # 前後1行も付けて視認性を上げる
                    start = max(0, i - 1)
                    end = min(len(text_lines), i + 2)
                    for j in range(start, end):
                        marker = '→' if j == i else ' '
                        target_lines.append(f'{marker} L{j+1:03d}: {text_lines[j]}')
                    target_lines.append('---')
            if target_lines:
                st.code('\n'.join(target_lines))
            else:
                st.caption('（「18.」も「19.」も生テキスト中に見つかりませんでした）')
        elif diag and not diag.get('success'):
            st.caption('（Vision API の生テキストは取得できていません）')

        # 生 JSON（raw_text は除外して見やすく）
        st.markdown('**生 JSON:**')
        meter_data_disp = {k: v for k, v in meter_data.items() if k not in ('raw_text', '_vision_diag')}
        st.json(meter_data_disp)

    # ========== Stage 2: 日報分類生データ ==========
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

        extras = nippou_data.get('extras', [])
        if extras:
            st.markdown('**extras（貸切・障割現金）**')
            parts = ['<table class="detail-table"><thead><tr><th>case</th><th>人数</th><th>kind</th><th>memo</th><th>金額</th><th>linked</th></tr></thead><tbody>']
            for e in extras:
                parts.append(
                    f'<tr><td>{e.get("case", "")}</td>'
                    f'<td>{e.get("passengers", "")}</td>'
                    f'<td>{e.get("kind", "")}</td>'
                    f'<td>{e.get("memo", "")}</td>'
                    f'<td>¥{int(e.get("amount", 0) or 0):,}</td>'
                    f'<td>{e.get("linked_meter_no", "")}</td></tr>'
                )
            parts.append('</tbody></table>')
            st.markdown(''.join(parts), unsafe_allow_html=True)

        st.markdown('**生 JSON:**')
        st.json(nippou_data)

    # ========== Stage 3: build_report 入出力 ==========
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
            elif r.get('state') == 'charter':
                cls = ' class="charter"'
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

    st.markdown('<br>', unsafe_allow_html=True)
    st.button('🔄 新しい日報を作成', on_click=reset_app, key='reset_btn', use_container_width=True)

    # 結果が新しく生成されたターンのみ「✓ 完成」を画面トップへスムーススクロール
    if st.session_state.get('_pending_scroll'):
        st.session_state._pending_scroll = False
        components.html('''
<script>
setTimeout(() => {
    const target = parent.document.querySelector('.complete-bar');
    if (target) target.scrollIntoView({behavior: 'smooth', block: 'start'});
}, 120);
</script>
''', height=0)


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
