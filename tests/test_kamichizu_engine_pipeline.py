from __future__ import annotations

from kamichizu_engine.fixtures.sample_maps import (
    matched_two_row_meter_receipt,
    matched_two_row_paper_map,
    two_row_template,
)
from kamichizu_engine.meter import build_meter_receipt_from_mappings
from kamichizu_engine.models import AmountSource, DiagnosticSeverity, LinkStatus
from kamichizu_engine.paper_map import build_paper_map, cell_from_observation
from kamichizu_engine.reconcile import reconcile_exact_amounts
from kamichizu_engine.rules import apply_adjustments, build_public_discount_adjustment


def test_minimum_pipeline_builds_reconciled_report_without_app() -> None:
    paper_map = matched_two_row_paper_map()
    meter_receipt = matched_two_row_meter_receipt()
    report = reconcile_exact_amounts(paper_map, meter_receipt, two_row_template())

    assert report.schema == "reconciled_report"
    assert report.paper_map is paper_map
    assert report.meter_receipt is meter_receipt
    assert len(report.rides) == 1
    assert report.sales.confirmed_gen == 0
    assert report.sales.confirmed_mi == 2430
    assert report.sales.total_sales == 2430

    ride = report.rides[0]
    assert ride.ride_key == "R02"
    assert ride.paper_cell_ids == ("R02_MI",)
    assert ride.meter_ride_ids == ("M01",)
    assert ride.link_status == LinkStatus.LINKED
    assert ride.observed_mi == 2430
    assert ride.adopted_mi is not None
    assert ride.adopted_mi.amount == 2430
    assert ride.adopted_mi.source == AmountSource.METER


def test_pipeline_keeps_observed_and_adopted_amount_evidence() -> None:
    report = reconcile_exact_amounts(
        matched_two_row_paper_map(),
        matched_two_row_meter_receipt(),
        two_row_template(),
    )
    adopted = report.rides[0].adopted_mi

    assert adopted is not None
    assert [evidence.source for evidence in adopted.evidences] == [
        "meter_receipt",
        "paper_map",
    ]
    assert [evidence.reference for evidence in adopted.evidences] == [
        "M01",
        "R02_MI",
    ]


def test_pipeline_diagnoses_paper_amount_without_meter_match() -> None:
    report = reconcile_exact_amounts(
        matched_two_row_paper_map(),
        build_meter_receipt_from_mappings(
            image_id="meter",
            rows=({"ride_id": "M01", "amount": 2400, "time": "10:44"},),
        ),
        two_row_template(),
    )

    assert len(report.rides) == 1
    ride = report.rides[0]
    assert ride.paper_cell_ids == ("R02_MI",)
    assert ride.meter_ride_ids == ("M01",)
    assert ride.observed_mi == 2430
    assert ride.adopted_mi is not None
    assert ride.adopted_mi.amount == 2400
    assert ride.diagnostic_reasons == ("paper_amount_corrected_by_meter_time",)
    assert report.sales.confirmed_mi == 2400
    assert report.sales.pending_meter_sales == 0
    assert report.sales.total_sales == 2400
    diagnostic = next(
        item for item in report.diagnostics if item.code == "paper_row_amount_corrected_by_time"
    )
    assert diagnostic.severity == DiagnosticSeverity.INFO
    assert diagnostic.references == ("R02_MI", "M01")
    assert diagnostic.details["paper_amount"] == 2430
    assert diagnostic.details["meter_amount"] == 2400


def test_pipeline_adopts_meter_amount_to_paper_mi_side_by_time() -> None:
    template = two_row_template()
    paper_map = build_paper_map(
        template=template,
        image_id="paper",
        observed_cells=(
            cell_from_observation(2, "time", raw="10:44", observed_value="10:44"),
            cell_from_observation(2, "mi", raw="2,400", observed_value=2400),
        ),
    )
    report = reconcile_exact_amounts(
        paper_map,
        build_meter_receipt_from_mappings(
            image_id="meter",
            rows=({"ride_id": "M01", "amount": 2430, "time": "10:44"},),
        ),
        template,
    )

    assert len(report.rides) == 1
    ride = report.rides[0]
    assert ride.observed_mi == 2400
    assert ride.adopted_mi is not None
    assert ride.adopted_mi.amount == 2430
    assert ride.adopted_gen is None
    assert report.sales.confirmed_mi == 2430
    assert report.sales.pending_meter_sales == 0
    assert any(item.code == "paper_row_amount_corrected_by_time" for item in report.diagnostics)


def test_pipeline_adopts_meter_amount_to_paper_gen_side_by_time() -> None:
    template = two_row_template()
    paper_map = build_paper_map(
        template=template,
        image_id="paper",
        observed_cells=(
            cell_from_observation(2, "time", raw="18:50", observed_value="18:50"),
            cell_from_observation(2, "gen", raw="1,700", observed_value=1700),
        ),
    )
    report = reconcile_exact_amounts(
        paper_map,
        build_meter_receipt_from_mappings(
            image_id="meter",
            rows=({"ride_id": "M01", "amount": 1800, "time": "18:50"},),
        ),
        template,
    )

    assert len(report.rides) == 1
    ride = report.rides[0]
    assert ride.observed_gen == 1700
    assert ride.adopted_gen is not None
    assert ride.adopted_gen.amount == 1800
    assert ride.adopted_mi is None
    assert report.sales.confirmed_gen == 1800
    assert report.sales.pending_meter_sales == 0


def test_pipeline_diagnoses_multiple_meter_matches() -> None:
    report = reconcile_exact_amounts(
        matched_two_row_paper_map(),
        build_meter_receipt_from_mappings(
            image_id="meter",
            rows=(
                {"ride_id": "M01", "amount": 2430, "time": "10:44"},
                {"ride_id": "M02", "amount": 2430, "time": "10:45"},
            ),
        ),
        two_row_template(),
    )

    assert report.rides == ()
    assert report.sales.pending_meter_sales == 4860
    assert report.sales.total_sales == 4860
    diagnostic = next(
        item for item in report.diagnostics if item.code == "paper_row_total_has_multiple_meter_matches"
    )
    assert diagnostic.references == ("R02_MI",)
    assert diagnostic.details["meter_ride_ids"] == ["M01", "M02"]


def test_pipeline_can_match_row_total_from_gen_and_mi_components() -> None:
    template = two_row_template()
    paper_map = build_paper_map(
        template=template,
        image_id="paper",
        observed_cells=(
            cell_from_observation(2, "gen", raw="900", observed_value=900),
            cell_from_observation(2, "mi", raw="2,430", observed_value=2430),
        ),
    )
    report = reconcile_exact_amounts(
        paper_map,
        build_meter_receipt_from_mappings(
            image_id="meter",
            rows=({"ride_id": "M01", "amount": 3330, "time": "10:44"},),
        ),
        template,
    )

    assert len(report.rides) == 1
    ride = report.rides[0]
    assert ride.paper_cell_ids == ("R02_GEN", "R02_MI")
    assert ride.observed_gen == 900
    assert ride.observed_mi == 2430
    assert ride.adopted_total is not None
    assert ride.adopted_total.amount == 3330
    assert ride.adopted_gen is not None
    assert ride.adopted_gen.amount == 900
    assert ride.adopted_mi is not None
    assert ride.adopted_mi.amount == 2430
    assert report.sales.confirmed_gen == 900
    assert report.sales.confirmed_mi == 2430
    assert report.sales.total_sales == 3330


def test_pipeline_diagnoses_row_total_without_meter_match() -> None:
    template = two_row_template()
    paper_map = build_paper_map(
        template=template,
        image_id="paper",
        observed_cells=(
            cell_from_observation(2, "gen", raw="900", observed_value=900),
            cell_from_observation(2, "mi", raw="2,430", observed_value=2430),
        ),
    )
    report = reconcile_exact_amounts(
        paper_map,
        matched_two_row_meter_receipt(),
        template,
    )

    assert report.rides == ()
    assert report.sales.pending_meter_sales == 2430
    assert report.sales.total_sales == 2430
    diagnostic = next(
        item for item in report.diagnostics if item.code == "paper_row_total_has_no_meter_match"
    )
    assert diagnostic.references == ("R02_GEN", "R02_MI")
    assert diagnostic.details["row_total"] == 3330
    assert diagnostic.details["components"] == {"gen": 900, "mi": 2430}


def test_public_discount_adjustment_adds_sales_without_touching_confirmed_mi() -> None:
    report = reconcile_exact_amounts(
        matched_two_row_paper_map(),
        matched_two_row_meter_receipt(),
        two_row_template(),
    )
    adjusted = apply_adjustments(
        report,
        (
            build_public_discount_adjustment(
                adjustment_id="D02",
                amount=270,
                target_ride_key="R02",
                source_cell_ids=("R01_MI",),
                evidence_detail="public discount linked to R02",
            ),
        ),
    )

    assert adjusted.sales.confirmed_gen == 0
    assert adjusted.sales.confirmed_mi == 2430
    assert adjusted.sales.discount_claim_total == 270
    assert adjusted.sales.total_sales == 2700
    assert len(adjusted.adjustments) == 1
    assert adjusted.adjustments[0].include_in_count is False
    assert adjusted.adjustments[0].include_in_passengers is False


def test_unlinked_public_discount_does_not_enter_sales() -> None:
    report = reconcile_exact_amounts(
        matched_two_row_paper_map(),
        matched_two_row_meter_receipt(),
        two_row_template(),
    )
    unlinked = build_public_discount_adjustment(
        adjustment_id="DXX",
        amount=270,
        target_ride_key="",
        source_cell_ids=("R01_MI",),
        evidence_detail="unlinked discount",
    )
    adjusted = apply_adjustments(report, (unlinked,))

    assert adjusted.sales.confirmed_mi == 2430
    assert adjusted.sales.discount_claim_total == 0
    assert adjusted.sales.total_sales == 2430
    assert len(adjusted.adjustments) == 1


def test_vertical_component_sample_reaches_66900_without_target_fitting() -> None:
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

    assert adjusted.sales.confirmed_gen == 30420
    assert adjusted.sales.confirmed_mi == 28610
    assert adjusted.sales.pending_meter_sales == 7220
    assert adjusted.sales.discount_claim_total == 650
    assert adjusted.sales.total_sales == 66900
    assert [ride.ride_key for ride in adjusted.rides] == ["R01", "R02"]
    assert any(diagnostic.code == "unused_meter_rides" for diagnostic in adjusted.diagnostics)
