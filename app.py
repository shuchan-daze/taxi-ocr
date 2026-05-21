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


def amount_text(amount):
    if amount is None:
        return ""
    try:
        return f"{int(amount):,}"
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


def amount_from_adopted(adopted):
    if not adopted:
        return None
    return adopted.get("amount")


def ride_display_value(ride, key):
    display = ride.get("display") or {}
    value = display.get(key)
    return "" if value is None else value


def row_no_from_ride_key(ride_key):
    text = str(ride_key or "")
    if text.startswith("R") and text[1:].isdigit():
        return str(int(text[1:]))
    return text


def row_no_from_adjustment(adjustment):
    target = adjustment.get("target_ride_key") or ""
    no = row_no_from_ride_key(target)
    return f"△{no}" if no else "△"


def build_detail_rows(package):
    package = package or {}
    explanation = package.get("explanation") or {}
    rows = []

    for ride in explanation.get("rides") or []:
        adopted = ride.get("adopted") or {}
        observed = ride.get("observed") or {}
        gen_amount = amount_from_adopted(adopted.get("gen"))
        mi_amount = amount_from_adopted(adopted.get("mi"))
        if gen_amount is None:
            gen_amount = observed.get("gen")
        if mi_amount is None:
            mi_amount = observed.get("mi")
        state = "明細反映" if ride.get("diagnostic_reasons") else ""
        rows.append(
            {
                "No": ride_display_value(ride, "no") or row_no_from_ride_key(ride.get("ride_key")),
                "人数": ride_display_value(ride, "passengers"),
                "時刻": ride_display_value(ride, "time"),
                "現収": amount_text(gen_amount),
                "未収": amount_text(mi_amount),
                "摘要": ride_display_value(ride, "memo"),
                "状態": state,
            }
        )

    for ride in explanation.get("pending_meter_rides") or []:
        rows.append(
            {
                "No": "",
                "人数": "",
                "時刻": ride.get("time") or "",
                "現収": "",
                "未収": "",
                "摘要": f"明細 {amount_text(ride.get('amount'))}",
                "状態": "確認",
            }
        )

    adjustments = (explanation.get("adjustments") or {})
    for adjustment in adjustments.get("linked_sales_adjustments") or []:
        rows.append(
            {
                "No": row_no_from_adjustment(adjustment),
                "人数": "",
                "時刻": "",
                "現収": "",
                "未収": amount_text(adjustment.get("amount")),
                "摘要": "障割",
                "状態": "請求",
            }
        )

    for adjustment in adjustments.get("unlinked_or_excluded_adjustments") or []:
        rows.append(
            {
                "No": "△",
                "人数": "",
                "時刻": "",
                "現収": "",
                "未収": "",
                "摘要": "障割",
                "状態": "紐づけ確認",
            }
        )

    return rows


def build_summary_metric_rows(package):
    summary = (package or {}).get("summary") or {}
    displayed_mi = (
        (summary.get("confirmed_mi") or 0)
        + (summary.get("discount_claim_total") or 0)
    )
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
            "key": "displayed_mi",
            "value": displayed_mi,
            "display": yen_text(displayed_mi),
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
    cols = st.columns(3)
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

    diagnostics_markdown = package.get("diagnostics_markdown") or ""
    with st.expander("診断メモ"):
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
