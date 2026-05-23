from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from kamichizu.demo import build_demo_human_report, build_demo_view
from kamichizu.input import build_human_report_from_observations
from kamichizu.models import HumanReport
from kamichizu.openai_ocr import OcrImage, build_observations_from_images

try:
    import streamlit as st
except Exception:  # pragma: no cover - Streamlit is optional in unit tests.
    st = None  # type: ignore[assignment]


APP_TITLE = "手書きAI日報"
APP_VERSION = "0.5.2"
DEBUG_DIR = Path(".kamichizu_debug")


def _format_amount(value: object) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def _row_key(value: object) -> str:
    text = str(value or "").strip()
    return text.zfill(2) if text.isdigit() else text


def _write_debug_json(file_name: str, data: Any) -> None:
    """Save diagnostic data outside the repo-visible UI without affecting output."""

    try:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        (DEBUG_DIR / file_name).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    except OSError:
        return


def _human_report_debug_data(human_report: HumanReport) -> dict[str, Any]:
    return {
        "summary_rows": [dict(row) for row in human_report.summary_rows],
        "ride_rows": [dict(row) for row in human_report.ride_rows],
        "claim_rows": [dict(row) for row in human_report.claim_rows],
        "diagnostics": list(human_report.diagnostics),
    }


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


def _human_diagnostic_message(message: str) -> str:
    text = str(message)
    if text.startswith("unmatched evidence "):
        body = text.removeprefix("unmatched evidence ").strip()
        tokens = body.split()
        target = tokens[0] if tokens else ""
        details: dict[str, str] = {}
        for token in tokens[1:]:
            if "=" in token:
                key, value = token.split("=", 1)
                details[key] = value

        time_text = details.get("time")
        amount_text = _format_amount(int(details["amount"])) if details.get("amount", "").isdigit() else details.get("amount", "")
        evidence_label = target
        if time_text and amount_text:
            evidence_label = f"{time_text} / {amount_text}円"
        elif time_text:
            evidence_label = time_text

        reason = details.get("reason")
        if reason == "no_paper_time_within_9_minutes":
            return f"メーター明細（{evidence_label}）に対応する紙日報行が見つかりません。時刻の読み取り、写真の範囲、行の欠落を確認してください。"
        if reason == "paper_time_match_without_payment_destination":
            return f"メーター明細（{evidence_label}）に近い紙日報行はありますが、現収・未収・摘要の判断材料が不足しています。紙の該当行を確認してください。"
        if reason == "paper_time_match_not_adopted":
            near = details.get("near_paper")
            suffix = f" 近い紙行: {near}" if near else ""
            return f"メーター明細（{evidence_label}）は候補がありますが採用できていません。候補の重複や金額差を確認してください。{suffix}"
        if reason == "evidence_time_missing":
            return f"メーター明細（{target}）の時刻が読めないため、紙日報へ対応づけできません。"
        return f"メーター明細に未照合が残っています（{target}）"
    if "paper amount" in text and "adopted evidence amount" in text:
        return "紙の金額とメーター明細の金額が異なるため、メーター明細の金額を採用しました。"
    return text


def build_completion_issues(human_report: HumanReport) -> list[str]:
    """Return human-facing issues that prevent treating a report as complete."""

    issues: list[str] = []
    summary_amounts = {str(row.get("項目")): row.get("金額") for row in human_report.summary_rows}
    gen_amount = summary_amounts.get("現収")
    mi_amount = summary_amounts.get("未収")
    if (
        isinstance(gen_amount, int)
        and isinstance(mi_amount, int)
        and gen_amount == 0
        and mi_amount > 0
        and len(human_report.ride_rows) >= 5
    ):
        issues.append("現収が0円です。紙日報の現収欄・未収欄のOCR位置を確認してください。")

    unmatched_count = sum(1 for message in human_report.diagnostics if str(message).startswith("unmatched evidence "))
    if unmatched_count:
        issues.append(f"メーター明細に未照合が{unmatched_count}件残っています。")

    for ride in human_report.ride_rows:
        status = str(ride.get("状態") or "").strip()
        if status:
            no = str(ride.get("No") or "").strip()
            label = f"No.{no}" if no else "日報行"
            issues.append(f"{label} が要確認です。")
    return issues


def build_ocr_images(uploaded_files: list[Any]) -> list[OcrImage]:
    """Convert Streamlit uploads to OCR images without interpreting them."""

    images: list[OcrImage] = []
    for uploaded_file in uploaded_files:
        name = str(getattr(uploaded_file, "name", "image"))
        mime_type = str(getattr(uploaded_file, "type", "") or "image/jpeg")
        if hasattr(uploaded_file, "getvalue"):
            data = uploaded_file.getvalue()
        else:
            data = uploaded_file.read()
        images.append(OcrImage(name=name, mime_type=mime_type, data=bytes(data)))
    return images


def _openai_api_key() -> str | None:
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    if st is None:
        return None
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        secret_key = None
    return str(secret_key) if secret_key else None


def build_human_report_from_photo_uploads(uploaded_files: list[Any], api_key: str) -> HumanReport:
    """Build a HumanReport from uploaded photos through the formal pipeline."""

    observations = build_observations_from_images(build_ocr_images(uploaded_files), api_key=api_key)
    _write_debug_json("last_observations.json", observations)
    human_report = build_human_report_from_observations(observations, build_demo_view())
    _write_debug_json("last_human_report.json", _human_report_debug_data(human_report))
    return human_report


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
            st.warning(_human_diagnostic_message(message))


def render_photo_workflow() -> HumanReport | None:
    if st is None:
        raise RuntimeError("Streamlit is required to render the app")

    st.header("写真から日報を作成")
    uploaded_files = st.file_uploader(
        "紙日報とメーター明細の写真をまとめて選択",
        type=("png", "jpg", "jpeg"),
        accept_multiple_files=True,
    )
    if uploaded_files:
        st.caption(f"{len(uploaded_files)}枚の写真を読み込みます")
        for uploaded_file in uploaded_files:
            st.caption(f"{uploaded_file.name} を読み込み対象にしました")

    if not st.button("写真から日報を作成", type="primary"):
        return None

    st.session_state.pop("human_report", None)

    if not uploaded_files or len(uploaded_files) < 2:
        st.error("紙日報とメーター明細の写真を2枚以上選択してください。")
        return None

    api_key = _openai_api_key()
    if not api_key:
        st.error("OPENAI_API_KEY が未設定です。Streamlit Secrets または環境変数に設定してください。")
        return None

    progress = st.progress(0)
    try:
        progress.progress(15)
        with st.spinner("写真を読み取っています"):
            human_report = build_human_report_from_photo_uploads(list(uploaded_files), api_key)
        progress.progress(100)
        completion_issues = build_completion_issues(human_report)
        if completion_issues:
            st.error("日報はまだ完成していません。未照合または要確認が残っています。")
            for issue in completion_issues:
                st.warning(issue)
        else:
            st.success("日報を作成しました")
        return human_report
    except Exception as exc:
        progress.empty()
        st.error(f"作成できませんでした: {exc}")
        return None


def main() -> None:
    if st is None:
        raise RuntimeError("Streamlit is required to run this app")

    st.set_page_config(page_title=APP_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.caption(f"v{APP_VERSION}")

    human_report = render_photo_workflow()
    if human_report is not None:
        st.session_state["human_report"] = human_report

    current_report = st.session_state.get("human_report")
    if isinstance(current_report, HumanReport):
        render_human_report(current_report)
    else:
        with st.expander("開発者メニュー: 確認用デモ"):
            st.caption("写真を選択して日報を作成してください。確認用の最小デモも表示できます。")
            if st.button("確認用デモを表示"):
                st.session_state["human_report"] = build_demo_human_report()
                st.rerun()


if __name__ == "__main__":
    main()
