"""Minimal Streamlit UI for Kamichizu HumanReport.

This UI is intentionally small.  Engine logic stays in kamichizu; this file
only renders HumanReport fields.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable

from kamichizu.models import HumanReport
from kamichizu.demo import build_demo_human_report
from kamichizu.case import build_human_report_from_case
from kamichizu.openai_ocr import DEFAULT_OPENAI_OCR_MODEL, OcrImage, build_case_from_images

try:
    import streamlit as st
except ModuleNotFoundError:  # Keep py_compile usable without Streamlit.
    st = None

APP_TITLE = "神地図エンジン"
APP_VERSION = "0.3.1"


def build_report_table_rows(human_report: HumanReport) -> list[dict[str, object]]:
    """Build the single human-facing report table from HumanReport only."""

    rows = [dict(row) for row in human_report.ride_rows]
    columns = list(rows[0].keys()) if rows else ["No", "人数", "時刻", "現収", "未収", "摘要", "状態"]

    def normalize_no(value: object) -> str:
        text = str(value or "").strip()
        return str(int(text)) if text.isdigit() else text

    def claim_row(claim: dict[str, object]) -> dict[str, object]:
        target = normalize_no(claim.get("対象行"))
        item = {column: "" for column in columns}
        if "No" in item:
            item["No"] = f"△{target}" if target else "△"
        payment_label = claim.get("区分")
        if payment_label in item:
            item[payment_label] = claim.get("金額")
        if "摘要" in item:
            item["摘要"] = claim.get("種別", "")
        if "状態" in item:
            item["状態"] = ""
        return item

    claims_by_target: dict[str, list[dict[str, object]]] = {}
    for claim in human_report.claim_rows:
        claims_by_target.setdefault(normalize_no(claim.get("対象行")), []).append(claim_row(claim))

    table_rows: list[dict[str, object]] = []
    used_targets: set[str] = set()
    for row in rows:
        table_rows.append(row)
        target = normalize_no(row.get("No"))
        if target in claims_by_target:
            table_rows.extend(claims_by_target[target])
            used_targets.add(target)

    for target, claim_rows in claims_by_target.items():
        if target not in used_targets:
            table_rows.extend(claim_rows)

    return table_rows


def render_human_report(human_report: HumanReport) -> None:
    """Render only HumanReport fields."""

    st.subheader("集計")
    st.dataframe(list(human_report.summary_rows), hide_index=True, use_container_width=True)

    st.subheader("日報表")
    st.dataframe(build_report_table_rows(human_report), hide_index=True, use_container_width=True)

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


def _secret(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value
    try:
        secret_value = st.secrets.get(name)
    except Exception:
        return None
    return str(secret_value) if secret_value else None


def _ocr_images_from_uploads(uploaded_files) -> list[OcrImage]:
    images: list[OcrImage] = []
    for uploaded_file in uploaded_files or []:
        images.append(
            OcrImage(
                name=uploaded_file.name,
                mime_type=uploaded_file.type or "image/jpeg",
                data=uploaded_file.getvalue(),
            )
        )
    return images


def build_human_report_from_uploaded_images(
    uploaded_files,
    progress: Callable[[int, str], None] | None = None,
) -> HumanReport:
    def update(percent: int, message: str) -> None:
        if progress is not None:
            progress(percent, message)

    update(10, "写真を確認しています")
    images = _ocr_images_from_uploads(uploaded_files)
    if len(images) < 2:
        raise RuntimeError("紙日報とメーター明細の写真を2枚以上選択してください。順番は自動判別します。")

    api_key = _secret("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY が未設定です。Streamlit Secrets または環境変数に設定してください。")
    model = _secret("OPENAI_OCR_MODEL") or DEFAULT_OPENAI_OCR_MODEL
    update(35, "OCRに送信しています")
    case_data = build_case_from_images(images, api_key=api_key, model=model)
    update(80, "神地図入力を検査しています")
    human_report = build_human_report_from_case(case_data)
    update(100, "日報を作成しました")
    return human_report


def main() -> None:
    if st is None:
        raise RuntimeError("Streamlit is required to run app.py")

    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    st.caption(f"v{APP_VERSION}")

    photo_files = st.file_uploader(
        "写真を2枚以上まとめて選択（紙日報・メーター明細は自動判別）",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )
    run_col, state_col = st.columns([2, 1])
    with run_col:
        run_photo_ocr = st.button("写真から日報を作成", type="primary")
    progress_bar = state_col.progress(0)
    progress_text = state_col.empty()
    if run_photo_ocr:
        try:
            human_report = build_human_report_from_uploaded_images(
                photo_files,
                progress=lambda percent, message: (progress_bar.progress(percent), progress_text.caption(message)),
            )
            st.session_state["human_report"] = human_report
        except Exception as exc:
            progress_bar.progress(0)
            progress_text.caption("作成できませんでした")
            st.error(str(exc))

    uploaded_file = st.file_uploader("神地図ケースJSON", type=["json"])
    human_report = st.session_state.get("human_report")
    if uploaded_file is not None:
        try:
            human_report = build_human_report_from_uploaded_json(uploaded_file)
            st.session_state["human_report"] = human_report
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            st.error(f"神地図ケースJSONを読めませんでした: {exc}")

    if human_report is None:
        st.caption("確認用の最小デモを表示しています。")
        human_report = build_demo_human_report()

    render_human_report(human_report)


if __name__ == "__main__":
    main()
