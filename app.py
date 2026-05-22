from __future__ import annotations

from typing import Any

from kamichizu.demo import build_demo_human_report
from kamichizu.models import HumanReport

try:
    import streamlit as st
except Exception:  # pragma: no cover - Streamlit is optional in unit tests.
    st = None  # type: ignore[assignment]


APP_TITLE = "手書きAI日報"
APP_VERSION = "0.4.0"


def _format_amount(value: object) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def _row_key(value: object) -> str:
    text = str(value or "").strip()
    return text.zfill(2) if text.isdigit() else text


def build_report_table_rows(human_report: HumanReport) -> list[dict[str, Any]]:
    """Build human-facing table rows from HumanReport only."""
    table_rows: list[dict[str, Any]] = []
    claims_by_no: dict[object, list[dict[str, Any]]] = {}

    for claim in human_report.claim_rows:
        claims_by_no.setdefault(_row_key(claim.get("対象行")), []).append(claim)

    for ride in human_report.ride_rows:
        no = ride.get("No")
        table_rows.append(
            {
                "No": no,
                "人数": ride.get("人数", ""),
                "時刻": ride.get("時刻", ""),
                "現収": _format_amount(ride.get("現収")),
                "未収": _format_amount(ride.get("未収")),
                "摘要": ride.get("摘要", ""),
                "状態": ride.get("状態", ""),
            }
        )

        for claim in claims_by_no.get(_row_key(no), []):
            payment_kind = claim.get("区分")
            table_rows.append(
                {
                    "No": f"△{no}",
                    "人数": "",
                    "時刻": "",
                    "現収": _format_amount(claim.get("金額")) if payment_kind == "現収" else "",
                    "未収": _format_amount(claim.get("金額")) if payment_kind == "未収" else "",
                    "摘要": claim.get("種別", ""),
                    "状態": "",
                }
            )

    return table_rows


def render_human_report(human_report: HumanReport) -> None:
    if st is None:
        raise RuntimeError("Streamlit is required to render the app")

    st.subheader("集計")
    st.table(human_report.summary_rows)

    st.subheader("日報表")
    st.table(build_report_table_rows(human_report))

    if human_report.diagnostics:
        st.subheader("確認メモ")
        for message in human_report.diagnostics:
            st.warning(message)


def main() -> None:
    if st is None:
        raise RuntimeError("Streamlit is required to run this app")

    st.set_page_config(page_title=APP_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.caption(f"v{APP_VERSION}")

    human_report = build_demo_human_report()
    render_human_report(human_report)


if __name__ == "__main__":
    main()
