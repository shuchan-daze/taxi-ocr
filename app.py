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

@keyframes float1 {
  0%   {transform: translate(0vw, 0vh) rotate(0deg) scale(1)}
  20%  {transform: translate(30vw, -25vh) rotate(120deg) scale(1.3)}
  40%  {transform: translate(60vw, 15vh) rotate(240deg) scale(0.8)}
  60%  {transform: translate(40vw, 50vh) rotate(360deg) scale(1.5)}
  80%  {transform: translate(-20vw, 30vh) rotate(480deg) scale(0.7)}
  100% {transform: translate(0vw, 0vh) rotate(720deg) scale(1)}
}
@keyframes float2 {
  0%   {transform: translate(0vw, 0vh) rotate(0deg) scale(1)}
  20%  {transform: translate(-35vw, -30vh) rotate(-120deg) scale(0.8)}
  40%  {transform: translate(-50vw, 20vh) rotate(-240deg) scale(1.4)}
  60%  {transform: translate(-20vw, 55vh) rotate(-360deg) scale(0.6)}
  80%  {transform: translate(30vw, 25vh) rotate(-480deg) scale(1.2)}
  100% {transform: translate(0vw, 0vh) rotate(-720deg) scale(1)}
}
@keyframes float3 {
  0%   {transform: translate(0vw, 0vh) rotate(0deg) scale(1)}
  25%  {transform: translate(45vw, -45vh) rotate(180deg) scale(1.6)}
  50%  {transform: translate(-30vw, -50vh) rotate(360deg) scale(0.5)}
  75%  {transform: translate(-50vw, 30vh) rotate(540deg) scale(1.3)}
  100% {transform: translate(0vw, 0vh) rotate(720deg) scale(1)}
}
@keyframes float4 {
  0%   {transform: translate(0vw, 0vh) rotate(0deg) scale(1)}
  25%  {transform: translate(-45vw, -40vh) rotate(-180deg) scale(0.7)}
  50%  {transform: translate(50vw, -25vh) rotate(-360deg) scale(1.5)}
  75%  {transform: translate(25vw, 50vh) rotate(-540deg) scale(0.9)}
  100% {transform: translate(0vw, 0vh) rotate(-720deg) scale(1)}
}
@keyframes float5 {
  0%   {transform: translate(0vw, 0vh) rotate(0deg) scale(1)}
  20%  {transform: translate(40vw, 30vh) rotate(140deg) scale(1.4)}
  40%  {transform: translate(60vw, -20vh) rotate(280deg) scale(0.6)}
  60%  {transform: translate(20vw, -50vh) rotate(420deg) scale(1.2)}
  80%  {transform: translate(-30vw, -20vh) rotate(560deg) scale(0.8)}
  100% {transform: translate(0vw, 0vh) rotate(720deg) scale(1)}
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
