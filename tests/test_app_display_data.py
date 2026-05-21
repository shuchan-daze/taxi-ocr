import json

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

    assert [row["label"] for row in rows] == ["総売上", "現収", "未収", "確認待ち売上", "障割請求"]
    assert [row["value"] for row in rows] == [0, 0, 0, 0, 0]
    assert [row["display"] for row in rows] == ["¥0", "¥0", "¥0", "¥0", "¥0"]


def test_summary_metric_rows_use_package_summary_values():
    rows = app.build_summary_metric_rows(_package())

    assert rows[0] == {"label": "総売上", "key": "sou", "value": 4620, "display": "¥4,620"}
    assert rows[1] == {"label": "現収", "key": "confirmed_gen", "value": 900, "display": "¥900"}
    assert rows[2] == {"label": "未収", "key": "confirmed_mi", "value": 2300, "display": "¥2,300"}
    assert rows[3] == {"label": "確認待ち売上", "key": "pending_meter_sales", "value": 1300, "display": "¥1,300"}
    assert rows[4] == {"label": "障割請求", "key": "discount_claim_total", "value": 120, "display": "¥120"}


def test_detail_table_sections_use_only_package_explanation():
    sections = app.build_detail_table_sections(_package())
    rows = sections["明細"]

    assert [row["区分"] for row in rows] == ["採用金額", "確認待ち売上", "障割・特例請求", "未リンク・未採用", "診断"]
    assert rows[0]["ID"] == "R01"
    assert rows[0]["現収"] == "¥900"
    assert rows[0]["紙セル"] == "R01_GEN"
    assert rows[0]["メーター"] == "M01"
    assert "meter_receipt:M01" in rows[0]["根拠"]
    assert rows[1]["ID"] == "M03"
    assert rows[1]["総額"] == "¥1,300"
    assert rows[1]["未収"] == ""
    assert rows[2]["総額"] == "¥120"
    assert rows[2]["対象"] == "R01"
    assert rows[3]["状態"] == "売上未採用"
    assert rows[4]["ID"] == "needs_attention"


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
