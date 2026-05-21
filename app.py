import json
from pathlib import Path

import streamlit as st

from kamichizu_engine.app_inputs import AppInputError, build_reconciled_report_from_app_inputs
from kamichizu_engine.diagnostics import build_reconciled_report_package
from kamichizu_engine.debug import write_reconciled_report_package


CASE_ROOT = Path(".kamichizu_cases")


def load_json_input(uploaded_file, text_value):
    text_value = (text_value or "").strip()
    if text_value:
        return json.loads(text_value)
    if uploaded_file is None:
        return None
    return json.loads(uploaded_file.getvalue().decode("utf-8"))


def load_json_file(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def find_local_case_names(case_root=CASE_ROOT):
    case_root = Path(case_root)
    if not case_root.exists():
        return []
    return [
        path.name
        for path in sorted(case_root.iterdir())
        if path.is_dir()
        and (path / "paper_map.json").is_file()
        and (path / "meter_data.json").is_file()
    ]


def load_local_case_inputs(case_name, case_root=CASE_ROOT):
    case_dir = Path(case_root) / case_name
    return (
        load_json_file(case_dir / "paper_map.json"),
        load_json_file(case_dir / "meter_data.json"),
    )


def build_report_package_from_inputs(paper_map, meter_data):
    report = build_reconciled_report_from_app_inputs(paper_map, meter_data)
    package = build_reconciled_report_package(report)
    write_reconciled_report_package(report, Path(".kamichizu_debug"))
    return package


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
    package = package or {}
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


def build_summary_metric_rows(package):
    summary = (package or {}).get("summary") or {}
    return [
        {"label": "総売上", "key": "sou", "value": summary.get("sou", 0), "display": yen_text(summary.get("sou", 0))},
        {
            "label": "現収",
            "key": "confirmed_gen",
            "value": summary.get("confirmed_gen", 0),
            "display": yen_text(summary.get("confirmed_gen", 0)),
        },
        {
            "label": "未収",
            "key": "confirmed_mi",
            "value": summary.get("confirmed_mi", 0),
            "display": yen_text(summary.get("confirmed_mi", 0)),
        },
        {
            "label": "確認待ち売上",
            "key": "pending_meter_sales",
            "value": summary.get("pending_meter_sales", 0),
            "display": yen_text(summary.get("pending_meter_sales", 0)),
        },
        {
            "label": "障割請求",
            "key": "discount_claim_total",
            "value": summary.get("discount_claim_total", 0),
            "display": yen_text(summary.get("discount_claim_total", 0)),
        },
    ]


def build_detail_table_sections(package):
    return {"明細": build_detail_rows(package)}


def build_download_payloads(package):
    package = package or {}
    diagnostics_markdown = package.get("diagnostics_markdown") or ""
    return {
        "package_json": {
            "label": "package JSON をダウンロード",
            "data": json.dumps(package, ensure_ascii=False, indent=2),
            "file_name": "reconciled_report_package.json",
            "mime": "application/json",
        },
        "diagnostics_markdown": {
            "label": "diagnostics Markdown をダウンロード",
            "data": diagnostics_markdown,
            "file_name": "reconciled_report_diagnostics.md",
            "mime": "text/markdown",
        },
    }


def render_package(package):
    summary = package.get("summary") or {}
    st.subheader("売上サマリー")
    cols = st.columns(5)
    for col, metric in zip(cols, build_summary_metric_rows(package)):
        col.metric(metric["label"], metric["display"])
    if summary.get("formula"):
        st.caption(summary["formula"])

    st.subheader("明細")
    detail_rows = build_detail_table_sections(package)["明細"]
    if detail_rows:
        st.dataframe(detail_rows, use_container_width=True)
    else:
        st.info("明細なし")

    st.subheader("Diagnostics")
    diagnostics_markdown = package.get("diagnostics_markdown") or ""
    st.markdown(diagnostics_markdown)
    payloads = build_download_payloads(package)
    download_cols = st.columns(2)
    for col, payload in zip(download_cols, payloads.values()):
        col.download_button(
            payload["label"],
            data=payload["data"],
            file_name=payload["file_name"],
            mime=payload["mime"],
            use_container_width=True,
        )
    st.caption(".kamichizu_debug/reconciled_report_package.json / reconciled_report_diagnostics.md に出力しました")


def main():
    st.set_page_config(page_title="神地図エンジン", layout="wide")
    st.title("神地図エンジン")
    st.caption("紙面固定セル住所とメーター明細から、採用根拠つきの診断レポートを作ります。")

    st.subheader("入力")
    st.caption("ファイルアップロードまたは貼り付けJSONのどちらでも使えます。貼り付けJSONがある場合はそちらを優先します。")

    st.subheader("ローカルテストケース")
    case_names = find_local_case_names()
    if case_names:
        selected_case = st.selectbox("ケース", case_names)
        if st.button("このケースで神地図レポート作成", use_container_width=True):
            try:
                paper_map, meter_data = load_local_case_inputs(selected_case)
                st.session_state["kamichizu_package"] = build_report_package_from_inputs(paper_map, meter_data)
            except (AppInputError, json.JSONDecodeError, OSError) as e:
                st.error(f"ローカルケース入力エラー: {type(e).__name__}: {e}")
            except Exception as e:
                st.error(f"神地図レポート生成エラー: {type(e).__name__}: {e}")
    else:
        st.info(".kamichizu_cases/ に case_name/paper_map.json と meter_data.json を置いてください。")

    paper_file = st.file_uploader("paper_map JSON ファイル", type=["json"], key="paper_map_json")
    paper_text = st.text_area("paper_map JSON を貼り付け", key="paper_map_text", height=220)

    meter_file = st.file_uploader("meter_data JSON ファイル", type=["json"], key="meter_data_json")
    meter_text = st.text_area("meter_data JSON を貼り付け", key="meter_data_text", height=220)

    if st.button("神地図レポートを作成", type="primary", use_container_width=True):
        try:
            paper_map = load_json_input(paper_file, paper_text)
            meter_data = load_json_input(meter_file, meter_text)
            st.session_state["kamichizu_package"] = build_report_package_from_inputs(paper_map, meter_data)
        except (AppInputError, json.JSONDecodeError, UnicodeDecodeError) as e:
            st.error(f"入力エラー: {type(e).__name__}: {e}")
        except Exception as e:
            st.error(f"神地図レポート生成エラー: {type(e).__name__}: {e}")

    package = st.session_state.get("kamichizu_package")
    if package:
        render_package(package)


if __name__ == "__main__":
    main()
