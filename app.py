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
st.caption('日報とメーター明細を2枚同時に選択してください')

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

files = st.file_uploader('2枚同時選択', type=['jpg','jpeg','png','heic'], accept_multiple_files=True)

if files:
    cols = st.columns(len(files))
    imgs = []
    for i, f in enumerate(files):
        img = fix_orientation(Image.open(f))
        imgs.append(img)
        with cols[i]:
            st.image(img, use_container_width=True)

if len(imgs if files else []) == 2:
    if st.button('日報を完成させる', use_container_width=True, type='primary'):
        with st.spinner('照合中...'):
            try:
                api_key = os.environ.get('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY')
                client = anthropic.Anthropic(api_key=api_key)
                prompt = 'まず2枚の画像を判別してください。メーター明細書の特徴：時刻と金額だけが縦1列に20行以上並ぶ細長いレシート。手書き日報の特徴：人数・乗車区間・現収・未収・摘要など横に複数列ある表。この判別を行ったうえで、現収か未収かは日報の記載に従い、金額はメーター明細の値を使用する。マークダウンテーブルで出力。列:No/人数/降車時刻/現収/未収/摘要。最後に現収合計・未収合計・総営収・消費税（総営収を11で割り10円単位四捨五入）・税抜運収（総営収マイナス消費税）を表示。'
                res = client.messages.create(
                    model='claude-opus-4-5',
                    max_tokens=4000,
                    messages=[{'role':'user','content':[
                        {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(imgs[0])}},
                        {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':to_b64(imgs[1])}},
                        {'type':'text','text':prompt}
                    ]}]
                )
                st.success('完成！')
                st.markdown(res.content[0].text)
            except Exception as e:
                st.error(str(e))
elif files and len(files) != 2:
    st.warning('2枚選択してください（現在{}枚）'.format(len(files)))
