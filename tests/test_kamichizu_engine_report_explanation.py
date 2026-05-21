from __future__ import annotations

from kamichizu_engine.diagnostics import build_reconciled_report_package, explain_reconciled_report, render_reconciled_report_markdown
from kamichizu_engine.fixtures.sample_maps import (
    matched_two_row_meter_receipt,
    matched_two_row_paper_map,
    two_row_template,
)
from kamichizu_engine.meter import build_meter_receipt_from_mappings
from kamichizu_engine.paper_map import build_paper_map, cell_from_observation
from kamichizu_engine.reconcile import reconcile_exact_amounts
from kamichizu_engine.rules import apply_adjustments, build_public_discount_adjustment


def test_report_explanation_shows_sales_formula_and_evidence() -> None:
    report = reconcile_exact_amounts(
        matched_two_row_paper_map(),
        matched_two_row_meter_receipt(),
        two_row_template(),
    )

    explanation = explain_reconciled_report(report)

    assert explanation["schema"] == "kamichizu_report_explanation"
    assert explanation["sales"] == {
        "formula": "confirmed_gen + confirmed_mi + pending_meter_sales + discount_claim_total + charter_sales",
        "components": {
            "confirmed_gen": 0,
            "confirmed_mi": 2430,
            "pending_meter_sales": 0,
            "discount_claim_total": 0,
            "charter_sales": 0,
        },
        "total_sales": 2430,
        "component_sum": 2430,
        "component_sum_matches_total": True,
    }
    assert explanation["rides"][0]["ride_key"] == "R02"
    assert explanation["rides"][0]["paper_cell_ids"] == ["R02_MI"]
    assert explanation["rides"][0]["meter_ride_ids"] == ["M01"]
    assert explanation["rides"][0]["observed"] == {"gen": None, "mi": 2430}
    assert explanation["rides"][0]["adopted"]["mi"]["amount"] == 2430
    assert [
        evidence["reference"]
        for evidence in explanation["rides"][0]["adopted"]["mi"]["evidences"]
    ] == ["M01", "R02_MI"]


def test_report_explanation_lists_pending_meter_sales_and_discount_claims() -> None:
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

    explanation = explain_reconciled_report(adjusted)

    assert explanation["sales"]["components"] == {
        "confirmed_gen": 30420,
        "confirmed_mi": 28610,
        "pending_meter_sales": 7220,
        "discount_claim_total": 650,
        "charter_sales": 0,
    }
    assert explanation["sales"]["total_sales"] == 66900
    assert explanation["sales"]["component_sum_matches_total"] is True
    assert explanation["pending_meter_rides"] == [
        {
            "ride_id": "M03",
            "sequence_no": 3,
            "time": None,
            "amount": 7220,
            "payment_hint": None,
            "raw": {"ride_id": "M03", "amount": 7220},
        }
    ]
    assert explanation["adjustments"]["linked_sales_adjustments"][0]["adjustment_id"] == "D01"
    assert explanation["adjustments"]["linked_sales_adjustments"][0]["amount"] == 650
    assert explanation["adjustments"]["linked_sales_adjustments"][0]["target_ride_key"] == "R02"
    assert explanation["adjustments"]["linked_sales_adjustments"][0]["include_in_count"] is False
    assert explanation["adjustments"]["linked_sales_adjustments"][0]["include_in_passengers"] is False


def test_report_explanation_separates_unlinked_adjustments_from_sales() -> None:
    report = reconcile_exact_amounts(
        matched_two_row_paper_map(),
        matched_two_row_meter_receipt(),
        two_row_template(),
    )
    adjusted = apply_adjustments(
        report,
        (
            build_public_discount_adjustment(
                adjustment_id="DXX",
                amount=270,
                target_ride_key="",
                source_cell_ids=("R01_MI",),
                evidence_detail="unlinked discount claim",
            ),
        ),
    )

    explanation = explain_reconciled_report(adjusted)

    assert explanation["sales"]["components"]["discount_claim_total"] == 0
    assert explanation["adjustments"]["linked_sales_adjustments"] == []
    assert explanation["adjustments"]["unlinked_or_excluded_adjustments"][0]["adjustment_id"] == "DXX"


def test_report_markdown_renders_human_readable_diagnostics() -> None:
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

    markdown = render_reconciled_report_markdown(adjusted)

    assert "# 神地図エンジン 診断レポート" in markdown
    assert "- confirmed_gen: ¥30,420" in markdown
    assert "- confirmed_mi: ¥28,610" in markdown
    assert "- pending_meter_sales: ¥7,220" in markdown
    assert "- discount_claim_total: ¥650" in markdown
    assert "- sou: ¥66,900" in markdown
    assert "- M03: ¥7,220" in markdown
    assert "- D01: ¥650 / 対象 R02 / 元セル R02_MI" in markdown


def test_report_package_wraps_summary_explanation_and_markdown() -> None:
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

    package = build_reconciled_report_package(adjusted)

    assert set(package) == {"summary", "explanation", "diagnostics_markdown"}
    assert package["summary"] == {
        "confirmed_gen": 30420,
        "confirmed_mi": 28610,
        "pending_meter_sales": 7220,
        "discount_claim_total": 650,
        "sou": 66900,
        "formula": "30,420 + 28,610 + 7,220 + 650 = 66,900",
    }
    assert package["explanation"]
    assert package["explanation"]["sales"]["total_sales"] == 66900
    assert "神地図エンジン 診断レポート" in package["diagnostics_markdown"]
