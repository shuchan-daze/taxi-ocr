import streamlit as st
import anthropic
import base64
from PIL import Image, ExifTags
from pillow_heif import register_heif_opener
import io
import os

register_heif_opener()
st.set_page_config(page_title='タクシー日報OCR', layout='centered')
st.title('タクシー日報 OCR')

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

col1, col2 = st.columns(2)
with col1:
    st.caption('1枚目')
    file1 = st.file_uploader('1枚目', type=['jpg','jpeg','png','heic'], key='f1', label_visibility='collapsed')
    if file1:
        img1 = fix_orientation(Image.open(file1))
        st.image(img1, use_container_width=True)
with col2:
    st.caption('2枚目')
    file2 = st.file_uploader('2枚目', type=['jpg','jpeg','png','heic'], key='f2', label_visibility='collapsed')
    if file2:
        img2 = fix_orientation(Image.open(file2))
        st.image(img2, use_container_width=True)

if file1 and file2:
    if st.button('日報を完成させる', use_container_width=True, type='primary'):
        with st.spinner('照合中...'):
            try:
                api_key = os.environ.get('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY')
                client = anthropic.Anthropic(api_key=api_key)
                prompt = '2枚の画像のうち1枚は手書きタクシー日報、もう1枚はメーター明細書。自動判断し照合。現収未収は日報の記載に従い金額はメーター値を正とする。マークダウンテーブルで出力。列:No/人数/降車時刻/現収/未収/摘要。最後に現収合計・未収合計・総営収・消費税（総営収を11で割り10円単位四捨五入）・税抜運収を表示。'
                res = client.messages.create(
                    model='claude-opus-4-5',
                    max_tokens=4000,
                    messages=[{'role':'user','content':[
                        {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(img1)}},
                        {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(img2)}},
                        {'type':'text','text':prompt}
                    ]}]
                )
                st.success('完成！')
                st.markdown(res.content[0].text)
            except Exception as e:
                st.error(str(e))
