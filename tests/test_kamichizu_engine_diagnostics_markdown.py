from __future__ import annotations

from kamichizu_engine.diagnostics import render_reconciled_report_markdown
from kamichizu_engine.meter import build_meter_receipt_from_mappings
from kamichizu_engine.paper_map import build_paper_map, cell_from_observation, default_daily_report_template
from kamichizu_engine.reconcile import reconcile_exact_amounts
from kamichizu_engine.rules import apply_adjustments, build_public_discount_adjustment


def normalize_markdown(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def test_66900_diagnostics_markdown_keeps_semantic_fragments() -> None:
    template = default_daily_report_template(row_count=14)
    paper_map = build_paper_map(
        template=template,
        image_id="paper",
        observed_cells=(
            cell_from_observation(3, "gen", raw="30,420", observed_value=30420),
            cell_from_observation(14, "mi", raw="28,610", observed_value=28610),
        ),
    )
    meter_receipt = build_meter_receipt_from_mappings(
        image_id="meter",
        rows=(
            {"ride_id": "M03", "amount": 30420},
            {"ride_id": "M14", "amount": 28610},
            {"ride_id": "M99", "amount": 7220},
        ),
    )
    report = reconcile_exact_amounts(paper_map, meter_receipt, template)
    adjusted = apply_adjustments(
        report,
        (
            build_public_discount_adjustment(
                adjustment_id="D03",
                amount=270,
                target_ride_key="R03",
                source_cell_ids=("R03_MI",),
                evidence_detail="障割 No.3 meter_receipt 2,630 -> 270",
            ),
            build_public_discount_adjustment(
                adjustment_id="D14",
                amount=380,
                target_ride_key="R14",
                source_cell_ids=("R14_MI",),
                evidence_detail="障割 No.14 meter_receipt 3,620 -> 380",
            ),
        ),
    )

    markdown = normalize_markdown(render_reconciled_report_markdown(adjusted))

    required_fragments = (
        "神地図エンジン 診断レポート",
        "confirmed_gen",
        "30,420",
        "confirmed_mi",
        "28,610",
        "pending_meter_sales",
        "7,220",
        "discount_claim_total",
        "650",
        "sou",
        "66,900",
        "30,420 + 28,610 + 7,220 + 650 = 66,900",
        "meter_receipt",
        "paper_map",
        "障割",
        "No.3",
        "2,630",
        "270",
        "No.14",
        "3,620",
        "380",
    )
    for fragment in required_fragments:
        assert fragment in markdown

