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


def yen_text(amount):
    if amount is None:
        return ""
    try:
        return f"¥{int(amount):,}"
    except (TypeError, ValueError):
        return str(amount)


def evidence_text(evidences):
    parts = []
    for evidence in evidences or []:
        source = evidence.get("source") or ""
        reference = evidence.get("reference") or ""
        detail = evidence.get("detail") or ""
        label = ":".join(part for part in (source, reference) if part)
        parts.append(" / ".join(part for part in (label, detail) if part))
    return "; ".join(part for part in parts if part)


def adopted_amount_text(adopted):
    if not adopted:
        return "", ""
    return yen_text(adopted.get("amount")), evidence_text(adopted.get("evidences"))


def build_detail_rows(package):
    explanation = package.get("explanation") or {}
    rows = []

    for ride in explanation.get("rides") or []:
        adopted = ride.get("adopted") or {}
        total, total_evidence = adopted_amount_text(adopted.get("total"))
        gen, gen_evidence = adopted_amount_text(adopted.get("gen"))
        mi, mi_evidence = adopted_amount_text(adopted.get("mi"))
        rows.append(
            {
                "区分": "採用金額",
                "ID": ride.get("ride_key") or "",
                "総額": total,
                "現収": gen,
                "未収": mi,
                "対象": "",
                "紙セル": ", ".join(ride.get("paper_cell_ids") or []),
                "メーター": ", ".join(ride.get("meter_ride_ids") or []),
                "根拠": "; ".join(part for part in (total_evidence, gen_evidence, mi_evidence) if part),
                "状態": ride.get("link_status") or "",
            }
        )

    for ride in explanation.get("pending_meter_rides") or []:
        rows.append(
            {
                "区分": "確認待ち売上",
                "ID": ride.get("ride_id") or "",
                "総額": yen_text(ride.get("amount")),
                "現収": "",
                "未収": "",
                "対象": "",
                "紙セル": "",
                "メーター": ride.get("ride_id") or "",
                "根拠": "meter_receipt",
                "状態": ride.get("time") or "",
            }
        )

    adjustments = (explanation.get("adjustments") or {})
    for adjustment in adjustments.get("linked_sales_adjustments") or []:
        rows.append(
            {
                "区分": "障割・特例請求",
                "ID": adjustment.get("adjustment_id") or "",
                "総額": yen_text(adjustment.get("amount")),
                "現収": "",
                "未収": "",
                "対象": adjustment.get("target_ride_key") or "",
                "紙セル": ", ".join(adjustment.get("source_cell_ids") or []),
                "メーター": "",
                "根拠": evidence_text(adjustment.get("evidences")),
                "状態": "売上採用",
            }
        )

    for adjustment in adjustments.get("unlinked_or_excluded_adjustments") or []:
        rows.append(
            {
                "区分": "未リンク・未採用",
                "ID": adjustment.get("adjustment_id") or "",
                "総額": yen_text(adjustment.get("amount")),
                "現収": "",
                "未収": "",
                "対象": adjustment.get("target_ride_key") or "",
                "紙セル": ", ".join(adjustment.get("source_cell_ids") or []),
                "メーター": "",
                "根拠": evidence_text(adjustment.get("evidences")),
                "状態": "売上未採用",
            }
        )

    for diagnostic in explanation.get("diagnostics") or []:
        rows.append(
            {
                "区分": "診断",
                "ID": diagnostic.get("code") or "",
                "総額": "",
                "現収": "",
                "未収": "",
                "対象": "",
                "紙セル": ", ".join(diagnostic.get("references") or []),
                "メーター": "",
                "根拠": diagnostic.get("message") or "",
                "状態": diagnostic.get("severity") or "",
            }
        )

    return rows


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

    detail_rows = build_detail_rows(package)
    st.subheader("明細")
    if detail_rows:
        st.dataframe(detail_rows, use_container_width=True)
    else:
        st.info("明細なし")

    st.subheader("Diagnostics")
    diagnostics_markdown = package.get("diagnostics_markdown") or ""
    st.markdown(diagnostics_markdown)
    package_json = json.dumps(package, ensure_ascii=False, indent=2)
    download_cols = st.columns(2)
    download_cols[0].download_button(
        "package JSON をダウンロード",
        data=package_json,
        file_name="reconciled_report_package.json",
        mime="application/json",
        use_container_width=True,
    )
    download_cols[1].download_button(
        "diagnostics Markdown をダウンロード",
        data=diagnostics_markdown,
        file_name="reconciled_report_diagnostics.md",
        mime="text/markdown",
        use_container_width=True,
    )
    st.caption(".kamichizu_debug/reconciled_report_package.json / reconciled_report_diagnostics.md に出力しました")
