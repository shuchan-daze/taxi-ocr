import streamlit as st
import anthropic
import base64
from PIL import Image
from pillow_heif import register_heif_opener
import io
import os

register_heif_opener()
st.set_page_config(page_title='タクシー日報OCR', layout='centered')
st.title('タクシー日報 OCR')
st.caption('日報とメーター明細を読み取り、完成日報を作ります')

col1, col2 = st.columns(2)
with col1:
    nippou = st.file_uploader('日報写真', type=['jpg','jpeg','png','heic'], key='nippou', label_visibility='collapsed')
    st.caption('① 日報写真')
    if nippou:
        st.image(Image.open(nippou), use_container_width=True)
with col2:
    meter = st.file_uploader('明細写真', type=['jpg','jpeg','png','heic'], key='meter', label_visibility='collapsed')
    st.caption('② メーター明細写真')
    if meter:
        st.image(Image.open(meter), use_container_width=True)

def to_b64(img):
    img.thumbnail((2000,2000))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode()

if nippou and meter:
    if st.button('日報を完成させる', use_container_width=True, type='primary'):
        with st.spinner('照合中...'):
            api_key = os.environ.get('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY')
            client = anthropic.Anthropic(api_key=api_key)
            n_img = Image.open(nippou)
            m_img = Image.open(meter)
            prompt = '1枚目は手書きのタクシー日報、2枚目はメーター明細書です。現収か未収かの判定は手書き日報の現収欄・未収欄に数字が書いてある方に従う。金額はメーター明細の値を正として使用する。摘要は手書き日報の記載に従う。日報をマークダウンテーブルで出力。列：No/人数/降車時刻/現収/未収/摘要。最後に現収合計・未収合計・総営収を表示。'
            res = client.messages.create(
                model='claude-opus-4-5',
                max_tokens=4000,
                messages=[{'role':'user','content':[
                    {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(n_img)}},
                    {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(m_img)}},
                    {'type':'text','text':prompt}
                ]}]
            )
            st.success('完成しました！')
            st.markdown(res.content[0].text)
