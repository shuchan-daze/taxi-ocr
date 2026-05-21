import json
from pathlib import Path

import streamlit as st

from kamichizu_engine.app_inputs import AppInputError, build_reconciled_report_from_app_inputs
from kamichizu_engine.diagnostics import build_reconciled_report_package
from kamichizu_engine.debug import write_reconciled_report_package


st.set_page_config(page_title="神地図エンジン", layout="wide")

st.title("神地図エンジン")
st.caption("紙面固定セル住所とメーター明細から、採用根拠つきの診断レポートを作ります。")


def load_json(uploaded_file):
    if uploaded_file is None:
        return None
    return json.loads(uploaded_file.getvalue().decode("utf-8"))


paper_file = st.file_uploader("paper_map JSON", type=["json"], key="paper_map_json")
meter_file = st.file_uploader("meter_data JSON", type=["json"], key="meter_data_json")

if st.button("神地図レポートを作成", type="primary", use_container_width=True):
    try:
        paper_map = load_json(paper_file)
        meter_data = load_json(meter_file)
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
    st.subheader("Summary")
    st.json(package.get("summary") or {})
    st.subheader("Diagnostics")
    st.markdown(package.get("diagnostics_markdown") or "")
    st.caption(".kamichizu_debug/reconciled_report_package.json / reconciled_report_diagnostics.md に出力しました")
