"""Minimal Streamlit UI for Kamichizu HumanReport.

This UI is intentionally small.  Engine logic stays in kamichizu; this file
only renders HumanReport fields.
"""

from __future__ import annotations

import json

from kamichizu.models import HumanReport
from kamichizu.demo import build_demo_human_report
from kamichizu.case import build_human_report_from_case

try:
    import streamlit as st
except ModuleNotFoundError:  # Keep py_compile usable without Streamlit.
    st = None

APP_TITLE = "神地図エンジン"
APP_VERSION = "0.2.0"


def render_human_report(human_report: HumanReport) -> None:
    """Render only HumanReport fields."""

    st.subheader("集計")
    st.dataframe(list(human_report.summary_rows), hide_index=True, use_container_width=True)

    st.subheader("明細")
    st.dataframe(list(human_report.ride_rows), hide_index=True, use_container_width=True)

    if human_report.claim_rows:
        st.subheader("特例")
        st.dataframe(list(human_report.claim_rows), hide_index=True, use_container_width=True)

    if human_report.diagnostics:
        st.subheader("確認メモ")
        for item in human_report.diagnostics:
            st.info(item)


def build_human_report_from_uploaded_json(uploaded_file) -> HumanReport | None:
    """Build HumanReport from the single formal JSON case input."""

    if uploaded_file is None:
        return None
    case_data = json.load(uploaded_file)
    return build_human_report_from_case(case_data)


def main() -> None:
    if st is None:
        raise RuntimeError("Streamlit is required to run app.py")

    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    st.caption(f"v{APP_VERSION}")

    uploaded_file = st.file_uploader("神地図ケースJSON", type=["json"])
    human_report = None
    if uploaded_file is not None:
        try:
            human_report = build_human_report_from_uploaded_json(uploaded_file)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            st.error(f"神地図ケースJSONを読めませんでした: {exc}")

    if human_report is None:
        st.caption("確認用の最小デモを表示しています。")
        human_report = build_demo_human_report()

    render_human_report(human_report)


if __name__ == "__main__":
    main()
