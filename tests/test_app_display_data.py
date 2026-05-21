import json

import pytest

import app


def _package():
    return {
        "summary": {
            "confirmed_gen": 900,
            "confirmed_mi": 2300,
            "pending_meter_sales": 1300,
            "discount_claim_total": 120,
            "sou": 4620,
            "formula": "900 + 2,300 + 1,300 + 120 = 4,620",
        },
        "explanation": {
            "rides": [
                {
                    "ride_key": "R01",
                    "display": {
                        "no": "1",
                        "passengers": 2,
                        "time": "09:46",
                        "memo": "現金",
                    },
                    "paper_cell_ids": ["R01_GEN"],
                    "meter_ride_ids": ["M01"],
                    "link_status": "linked",
                    "adopted": {
                        "total": {
                            "amount": 900,
                            "evidences": [
                                {"source": "meter_receipt", "reference": "M01", "detail": "amount matched"}
                            ],
                        },
                        "gen": {
                            "amount": 900,
                            "evidences": [
                                {"source": "paper_map", "reference": "R01_GEN", "detail": "cash cell"}
                            ],
                        },
                        "mi": None,
                    },
                }
            ],
            "pending_meter_rides": [
                {"ride_id": "M03", "time": "14:06", "amount": 1300}
            ],
            "adjustments": {
                "linked_sales_adjustments": [
                    {
                        "adjustment_id": "D01",
                        "amount": 120,
                        "target_ride_key": "R01",
                        "source_cell_ids": ["R01_MEMO"],
                        "evidences": [
                            {"source": "paper_map", "reference": "R01_MEMO", "detail": "claim note"}
                        ],
                    }
                ],
                "unlinked_or_excluded_adjustments": [
                    {
                        "adjustment_id": "D02",
                        "amount": 80,
                        "target_ride_key": "",
                        "source_cell_ids": ["R02_MEMO"],
                        "evidences": [],
                    }
                ],
            },
            "diagnostics": [
                {
                    "code": "needs_attention",
                    "message": "check observed cell",
                    "severity": "warning",
                    "references": ["R03_MI"],
                }
            ],
        },
        "diagnostics_markdown": "# 診断\n\n- check observed cell\n",
    }


def test_summary_metric_rows_are_safe_when_package_is_empty():
    rows = app.build_summary_metric_rows({})

    assert [row["label"] for row in rows] == ["総売上", "現収", "未収"]
    assert [row["value"] for row in rows] == [0, 0, 0]
    assert [row["display"] for row in rows] == ["¥0", "¥0", "¥0"]


def test_summary_metric_rows_use_package_summary_values():
    rows = app.build_summary_metric_rows(_package())

    assert rows[0] == {"label": "総売上", "key": "sou", "value": 4620, "display": "¥4,620"}
    assert rows[1] == {"label": "現収", "key": "confirmed_gen", "value": 900, "display": "¥900"}
    assert rows[2] == {"label": "未収", "key": "displayed_mi", "value": 2420, "display": "¥2,420"}


def test_detail_table_sections_use_only_package_explanation():
    sections = app.build_detail_table_sections(_package())
    rows = sections["明細"]

    assert list(rows[0]) == ["No", "人数", "時刻", "現収", "未収", "摘要", "状態"]
    assert rows == [
        {"No": "1", "人数": 2, "時刻": "09:46", "現収": "900", "未収": "", "摘要": "現金", "状態": ""},
        {"No": "", "人数": "", "時刻": "14:06", "現収": "", "未収": "", "摘要": "明細 1,300", "状態": "確認"},
        {"No": "△1", "人数": "", "時刻": "", "現収": "", "未収": "120", "摘要": "障割", "状態": "請求"},
        {"No": "△", "人数": "", "時刻": "", "現収": "", "未収": "", "摘要": "障割", "状態": "紐づけ確認"},
    ]


def test_detail_table_sections_are_empty_without_explanation():
    assert app.build_detail_table_sections({}) == {"明細": []}


def test_download_payloads_are_safe_when_markdown_is_missing():
    payloads = app.build_download_payloads({"summary": {"sou": 1}})

    package_payload = payloads["package_json"]
    markdown_payload = payloads["diagnostics_markdown"]
    assert json.loads(package_payload["data"]) == {"summary": {"sou": 1}}
    assert package_payload["file_name"] == "reconciled_report_package.json"
    assert package_payload["mime"] == "application/json"
    assert markdown_payload["data"] == ""
    assert markdown_payload["file_name"] == "reconciled_report_diagnostics.md"
    assert markdown_payload["mime"] == "text/markdown"


def _write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_find_local_case_names_returns_only_complete_cases(tmp_path):
    complete = tmp_path / "complete"
    complete.mkdir()
    _write_json(complete / "paper_map.json", {"cells": {}})
    _write_json(complete / "meter_data.json", {"rows": []})

    missing_meter = tmp_path / "missing_meter"
    missing_meter.mkdir()
    _write_json(missing_meter / "paper_map.json", {"cells": {}})

    missing_paper = tmp_path / "missing_paper"
    missing_paper.mkdir()
    _write_json(missing_paper / "meter_data.json", {"rows": []})

    assert app.find_local_case_names(tmp_path) == ["complete"]


def test_load_local_case_inputs_reads_case_json_files(tmp_path):
    case_dir = tmp_path / "case_a"
    case_dir.mkdir()
    paper_map = {"cells": {"R01_TIME": {"value": "09:00"}}}
    meter_data = {"rows": [{"ride_id": "M01", "amount": 900}]}
    _write_json(case_dir / "paper_map.json", paper_map)
    _write_json(case_dir / "meter_data.json", meter_data)

    assert app.load_local_case_inputs("case_a", tmp_path) == (paper_map, meter_data)


def test_load_local_case_inputs_raises_json_error_for_broken_file(tmp_path):
    case_dir = tmp_path / "broken"
    case_dir.mkdir()
    (case_dir / "paper_map.json").write_text("{", encoding="utf-8")
    _write_json(case_dir / "meter_data.json", {"rows": []})

    with pytest.raises(json.JSONDecodeError):
        app.load_local_case_inputs("broken", tmp_path)
