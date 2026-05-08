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
st.caption('日報とメーター明細を読み取り、完成日報を作ります')

def fix_orientation(img):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = img._getexif()
        if exif is not None:
            o = exif.get(orientation)
            if o == 3:
                img = img.rotate(180, expand=True)
            elif o == 6:
                img = img.rotate(270, expand=True)
            elif o == 8:
                img = img.rotate(90, expand=True)
    except:
        pass
    return img

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader('写真1', type=['jpg','jpeg','png','heic'], key='file1', label_visibility='collapsed')
    st.caption('① 1枚目（日報またはメーター）')
    if file1:
        img1 = fix_orientation(Image.open(file1))
        st.image(img1, use_container_width=True)
with col2:
    file2 = st.file_uploader('写真2', type=['jpg','jpeg','png','heic'], key='file2', label_visibility='collapsed')
    st.caption('② 2枚目（日報またはメーター）')
    if file2:
        img2 = fix_orientation(Image.open(file2))
        st.image(img2, use_container_width=True)

def to_b64(img):
    img.thumbnail((2000,2000))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode()

if file1 and file2:
    if st.button('日報を完成させる', use_container_width=True, type='primary'):
        with st.spinner('照合中...'):
            api_key = os.environ.get('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY')
            client = anthropic.Anthropic(api_key=api_key)
            prompt = '2枚の画像のうち、1枚は手書きのタクシー日報、もう1枚はメーター明細書です。どちらがどちらかを自動判断し

