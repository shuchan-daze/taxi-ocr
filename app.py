import json
from pathlib import Path

import streamlit as st

from kamichizu_engine.app_inputs import AppInputError, build_reconciled_report_from_app_inputs
from kamichizu_engine.diagnostics import build_reconciled_report_package
from kamichizu_engine.debug import write_reconciled_report_package


st.set_page_config(page_title="神地図エンジン", layout="wide")

st.title("神地図エンジン")
st.caption("紙面固定セル住所とメーター明細から、採用根拠つきの診断レポートを作ります。")


def load_json_input(uploaded_file, text_value):
    text_value = (text_value or "").strip()
    if text_value:
        return json.loads(text_value)
    if uploaded_file is None:
        return None
    return json.loads(uploaded_file.getvalue().decode("utf-8"))


st.subheader("入力")
st.caption("ファイルアップロードまたは貼り付けJSONのどちらでも使えます。貼り付けJSONがある場合はそちらを優先します。")

paper_file = st.file_uploader("paper_map JSON ファイル", type=["json"], key="paper_map_json")
paper_text = st.text_area("paper_map JSON を貼り付け", key="paper_map_text", height=220)

meter_file = st.file_uploader("meter_data JSON ファイル", type=["json"], key="meter_data_json")
meter_text = st.text_area("meter_data JSON を貼り付け", key="meter_data_text", height=220)

if st.button("神地図レポートを作成", type="primary", use_container_width=True):
    try:
        paper_map = load_json_input(paper_file, paper_text)
        meter_data = load_json_input(meter_file, meter_text)
        report = build_reconciled_report_from_app_inputs(paper_map, meter_data)
        package = build_reconciled_report_package(report)
        write_reconciled_report_package(report, Path(".kamichizu_debug"))
        st.session_state["kamichizu_package"] = package
    except (AppInputError, json.JSONDecodeError, UnicodeDecodeError) as e:
        st.error(f"入力エラー: {type(e).__name__}: {e}")
    except Exception as e:
        st.error(f"神地図レポート生成エラー: {type(e).__name__}: {e}")

package = st.session_state.get("kamichizu_package")
if package:
    summary = package.get("summary") or {}
    st.subheader("売上サマリー")
    cols = st.columns(5)
    cols[0].metric("総売上", f"¥{summary.get('sou', 0):,}")
    cols[1].metric("現収", f"¥{summary.get('confirmed_gen', 0):,}")
    cols[2].metric("未収", f"¥{summary.get('confirmed_mi', 0):,}")
    cols[3].metric("確認待ち売上", f"¥{summary.get('pending_meter_sales', 0):,}")
    cols[4].metric("障割請求", f"¥{summary.get('discount_claim_total', 0):,}")
    if summary.get("formula"):
        st.caption(summary["formula"])

    st.subheader("Diagnostics")
    st.markdown(package.get("diagnostics_markdown") or "")
    st.caption(".kamichizu_debug/reconciled_report_package.json / reconciled_report_diagnostics.md に出力しました")
