import streamlit as st
import anthropic
import base64
from PIL import Image
from pillow_heif import register_heif_opener
import io

register_heif_opener()
st.set_page_config(page_title='タクシー日報OCR', layout='wide')
st.title('タクシー日報OCR')
client = anthropic.Anthropic()

st.info('① 日報写真 → ② メーター写真 の順にアップロードしてください')

col1, col2 = st.columns(2)
with col1:
    st.subheader('① 日報写真（手書き）')
    nippou = st.file_uploader('日報写真をアップロード', type=['jpg','jpeg','png','heic'], key='nippou')
    if nippou:
        st.image(Image.open(nippou), use_container_width=True)
with col2:
    st.subheader('② メーター明細写真')
    meter = st.file_uploader('メーター写真をアップロード', type=['jpg','jpeg','png','heic'], key='meter')
    if meter:
        st.image(Image.open(meter), use_container_width=True)

def to_b64(img):
    img.thumbnail((2000,2000))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode()

if nippou and meter:
    if st.button('照合して日報を作成'):
        with st.spinner('照合中...'):
            n_img = Image.open(nippou)
            m_img = Image.open(meter)
            prompt = '''1枚目は手書きのタクシー日報、2枚目はメーター明細書です。

ルール：
- 現収か未収かの判定は、手書き日報の現収欄・未収欄に数字が書いてある方に従う
- 金額はメーター明細の値を正として使用する
- 摘要は手書き日報の記載に従う

日報をマークダウンテーブルで出力してください。
列：No / 人数 / 降車時刻 / 現収 / 未収 / 摘要
最後に現収合計・未収合計・総営収を表示してください。'''
            res = client.messages.create(
                model='claude-opus-4-5',
                max_tokens=4000,
                messages=[{'role':'user','content':[
                    {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(n_img)}},
                    {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(m_img)}},
                    {'type':'text','text':prompt}
                ]}]
            )
            st.markdown(res.content[0].text)
