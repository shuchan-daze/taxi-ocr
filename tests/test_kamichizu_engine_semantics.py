from __future__ import annotations

import pytest

from kamichizu_engine.fixtures.sample_maps import matched_two_row_meter_receipt, matched_two_row_paper_map, two_row_template
from kamichizu_engine.models import (
    Adjustment,
    AdjustmentKind,
    AmountSource,
    CellAddress,
    FieldName,
    ObservedState,
    PaperCell,
    SalesComponents,
)
from kamichizu_engine.paper_map import build_empty_paper_map, build_paper_map, cell_from_observation
from kamichizu_engine.reconcile import reconcile_exact_amounts
from kamichizu_engine.rules import apply_adjustments, build_public_discount_adjustment


def test_semantics_rejects_cell_id_that_disagrees_with_fixed_address() -> None:
    with pytest.raises(ValueError, match="cell_id conflict"):
        PaperCell(cell_id="R03_MI", paper_row=4, field=FieldName.MI)


def test_semantics_keeps_empty_fixed_addresses_present() -> None:
    template = two_row_template()
    paper_map = build_empty_paper_map(template, image_id="empty")

    assert paper_map.cell("R01_MI").observed_state == ObservedState.MISSING
    assert paper_map.cell("R02_MI").observed_state == ObservedState.MISSING
    assert paper_map.missing_cell_ids(template) == ()


def test_semantics_does_not_turn_observed_value_into_adopted_value_without_meter_evidence() -> None:
    template = two_row_template()
    paper_map = build_paper_map(
        template=template,
        image_id="paper",
        observed_cells=(cell_from_observation(2, "mi", raw="2,430", observed_value=2430),),
    )
    report = reconcile_exact_amounts(
        paper_map,
        matched_two_row_meter_receipt().__class__(
            schema="meter_receipt",
            image_id="empty-meter",
            rides=(),
        ),
        template,
    )

    assert report.rides == ()
    assert report.sales.total_sales == 0


def test_semantics_keeps_discount_claim_out_of_confirmed_mi() -> None:
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
                evidence_detail="discount linked to R02",
            ),
        ),
    )

    assert adjusted.sales.confirmed_mi == 2430
    assert adjusted.sales.discount_claim_total == 270
    assert adjusted.sales.total_sales == 2700


def test_semantics_requires_linked_discount_before_sales_inclusion() -> None:
    report = reconcile_exact_amounts(
        matched_two_row_paper_map(),
        matched_two_row_meter_receipt(),
        two_row_template(),
    )
    unlinked = Adjustment(
        adjustment_id="DXX",
        kind=AdjustmentKind.PUBLIC_DISCOUNT_CLAIM,
        amount=270,
        target_ride_key=None,
        source_cell_ids=("R01_MI",),
        include_in_sales=True,
    )
    adjusted = apply_adjustments(report, (unlinked,))

    assert adjusted.sales.discount_claim_total == 0
    assert adjusted.sales.total_sales == 2430


def test_semantics_total_sales_is_component_sum_not_a_target_number() -> None:
    sales = SalesComponents(
        confirmed_gen=30420,
        confirmed_mi=28610,
        pending_meter_sales=7220,
        discount_claim_total=650,
        charter_sales=0,
    )

    assert sales.total_sales == 66900
    assert sales.to_dict() == {
        "confirmed_gen": 30420,
        "confirmed_mi": 28610,
        "pending_meter_sales": 7220,
        "discount_claim_total": 650,
        "charter_sales": 0,
        "total_sales": 66900,
    }


def test_semantics_amount_source_names_do_not_include_old_mixed_states() -> None:
    assert {source.value for source in AmountSource} == {"meter", "paper", "user", "rule", "none"}


def test_semantics_cell_address_is_constructed_from_meaning_not_list_order() -> None:
    address = CellAddress(17, FieldName.MEMO)

    assert address.cell_id == "R17_MEMO"


def test_semantics_layer1_cell_observation_is_not_an_adopted_amount() -> None:
    cell = cell_from_observation(
        2,
        "mi",
        raw="2,430",
        observed_value=2430,
        observed_state=ObservedState.OBSERVED,
    )

    assert cell.has_observed_value is True
    assert not hasattr(cell, "adopted_amount")
    assert cell.observed_value == 2430


def test_semantics_layer1_preserves_location_even_when_value_is_unreadable() -> None:
    template = two_row_template()
    paper_map = build_paper_map(
        template=template,
        image_id="paper",
        observed_cells=(
            cell_from_observation(
                2,
                "memo",
                raw="",
                observed_value=None,
                observed_state=ObservedState.UNREADABLE,
                notes="something exists but cannot be read",
            ),
        ),
    )

    cell = paper_map.cell("R02_MEMO")
    assert cell.cell_id == "R02_MEMO"
    assert cell.observed_state == ObservedState.UNREADABLE
    assert cell.observed_value is None
    assert paper_map.missing_cell_ids(template) == ()
