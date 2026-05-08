import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image
import io
import json
import os

st.set_page_config(page_title="タクシー日報OCR", layout="wide")
st.title("🚕 タクシー日報OCR (テスト版)")

# 認証情報の読み込み(Cloud と Local の両対応)
def get_credentials():
    # Streamlit Cloud では st.secrets から読み込む
    if "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        return service_account.Credentials.from_service_account_info(info)
    # ローカルでは key.json から読み込む
    elif os.path.exists("key.json"):
        return service_account.Credentials.from_service_account_file("key.json")
    else:
        st.error("認証情報が見つかりません。key.json または Streamlit Secrets を設定してください。")
        st.stop()

credentials = get_credentials()
client = vision.ImageAnnotatorClient(credentials=credentials)

# ファイルアップロード
uploaded_file = st.file_uploader(
    "日報またはメーターレシートの写真をアップロード",
    type=["jpg", "jpeg", "png", "heic"]
)

if uploaded_file is not None:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📷 アップロード画像")
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)

    with col2:
        st.subheader("🔍 OCR結果")
        with st.spinner("Google Vision APIで解析中..."):
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            content = img_byte_arr.getvalue()

            vision_image = vision.Image(content=content)
            response = client.document_text_detection(
                image=vision_image,
                image_context={"language_hints": ["ja"]}
            )

            if response.error.message:
                st.error(f"APIエラー: {response.error.message}")
            else:
                full_text = response.full_text_annotation.text
                st.text_area("認識テキスト", full_text, height=600)
                st.success(f"✅ 解析完了 ({len(full_text)}文字)")
