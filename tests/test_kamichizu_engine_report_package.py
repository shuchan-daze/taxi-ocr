from __future__ import annotations

import json

from kamichizu_engine import diagnostics
from kamichizu_engine.debug import write_reconciled_report_package
from kamichizu_engine.fixtures.sample_maps import matched_two_row_meter_receipt, matched_two_row_paper_map, two_row_template
from kamichizu_engine.meter import build_meter_receipt_from_mappings
from kamichizu_engine.paper_map import build_paper_map, cell_from_observation
from kamichizu_engine.reconcile import reconcile_exact_amounts
from kamichizu_engine.rules import apply_adjustments, build_public_discount_adjustment


def test_report_package_uses_existing_explanation_and_markdown_functions(monkeypatch) -> None:
    report = reconcile_exact_amounts(
        matched_two_row_paper_map(),
        matched_two_row_meter_receipt(),
        two_row_template(),
    )
    calls = []

    def fake_explain(target_report):
        assert target_report is report
        calls.append("explain")
        return {
            "sales": {
                "components": {
                    "confirmed_gen": 1,
                    "confirmed_mi": 2,
                    "pending_meter_sales": 3,
                    "discount_claim_total": 4,
                    "charter_sales": 0,
                },
                "total_sales": 10,
            }
        }

    def fake_markdown(target_report):
        assert target_report is report
        calls.append("markdown")
        return "diagnostics text"

    monkeypatch.setattr(diagnostics, "explain_reconciled_report", fake_explain)
    monkeypatch.setattr(diagnostics, "render_reconciled_report_markdown", fake_markdown)

    package = diagnostics.build_reconciled_report_package(report)

    assert calls == ["explain", "markdown"]
    assert package["summary"] == {
        "confirmed_gen": 1,
        "confirmed_mi": 2,
        "pending_meter_sales": 3,
        "discount_claim_total": 4,
        "sou": 10,
        "formula": "1 + 2 + 3 + 4 = 10",
    }
    assert package["diagnostics_markdown"] == "diagnostics text"


def test_write_reconciled_report_package_outputs_json_and_markdown(tmp_path) -> None:
    template = two_row_template()
    paper_map = build_paper_map(
        template=template,
        image_id="paper",
        observed_cells=(
            cell_from_observation(1, "gen", raw="30,420", observed_value=30420),
            cell_from_observation(2, "mi", raw="28,610", observed_value=28610),
        ),
    )
    meter_receipt = build_meter_receipt_from_mappings(
        image_id="meter",
        rows=(
            {"ride_id": "M01", "amount": 30420},
            {"ride_id": "M02", "amount": 28610},
            {"ride_id": "M03", "amount": 7220},
        ),
    )
    report = reconcile_exact_amounts(paper_map, meter_receipt, template)
    adjusted = apply_adjustments(
        report,
        (
            build_public_discount_adjustment(
                adjustment_id="D01",
                amount=650,
                target_ride_key="R02",
                source_cell_ids=("R02_MI",),
                evidence_detail="linked discount claim for component sample",
            ),
        ),
    )

    paths = write_reconciled_report_package(adjusted, tmp_path)

    assert paths["json"].name == "reconciled_report_package.json"
    assert paths["markdown"].name == "reconciled_report_diagnostics.md"
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    markdown = paths["markdown"].read_text(encoding="utf-8")
    assert payload["summary"]["sou"] == 66900
    assert "66,900" in markdown
