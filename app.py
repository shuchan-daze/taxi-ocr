"""Minimal Streamlit UI for Kamichizu HumanReport.

This UI is intentionally small.  Engine logic stays in kamichizu; this file
only renders HumanReport fields.
"""

from __future__ import annotations

from kamichizu.models import HumanReport
from kamichizu.demo import build_demo_human_report

try:
    import streamlit as st
except ModuleNotFoundError:  # Keep py_compile usable without Streamlit.
    st = None

APP_TITLE = "神地図エンジン"
APP_VERSION = "0.1.0"


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


def main() -> None:
    if st is None:
        raise RuntimeError("Streamlit is required to run app.py")

    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    st.caption(f"v{APP_VERSION}")

    human_report = build_demo_human_report()
    render_human_report(human_report)


if __name__ == "__main__":
    main()
