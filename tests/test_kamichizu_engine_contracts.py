from __future__ import annotations

import pytest

from kamichizu_engine.config import FareConfig
from kamichizu_engine.diagnostics import paper_map_quality_summary
from kamichizu_engine.fixtures.sample_maps import sparse_two_row_paper_map, two_row_template
from kamichizu_engine.models import (
    AdoptedAmount,
    AdjustmentKind,
    AmountSource,
    CellAddress,
    FieldName,
    LinkStatus,
    ObservedState,
    PaperCell,
    ReconciledRide,
    SalesComponents,
)
from kamichizu_engine.paper_map import (
    build_empty_paper_map,
    build_paper_map,
    cell_from_observation,
    make_cell_id,
    parse_cell_id,
)
from kamichizu_engine.rules import build_public_discount_adjustment, public_discount_candidates


def test_template_generates_all_fixed_cell_addresses() -> None:
    template = two_row_template()

    assert len(template.expected_cell_ids()) == 12
    assert template.expected_cell_ids() == (
        "R01_PASSENGERS",
        "R01_ROUTE",
        "R01_TIME",
        "R01_GEN",
        "R01_MI",
        "R01_MEMO",
        "R02_PASSENGERS",
        "R02_ROUTE",
        "R02_TIME",
        "R02_GEN",
        "R02_MI",
        "R02_MEMO",
    )


def test_empty_cells_keep_their_cell_id() -> None:
    template = two_row_template()
    paper_map = build_empty_paper_map(template, image_id="empty")

    assert len(paper_map.cells) == 12
    assert paper_map.cell("R02_MI").cell_id == "R02_MI"
    assert paper_map.cell("R02_MI").observed_state == ObservedState.MISSING
    assert paper_map.missing_cell_ids(template) == ()


def test_sparse_observation_does_not_shift_later_addresses() -> None:
    paper_map = sparse_two_row_paper_map()

    assert paper_map.cell("R01_MI").observed_state == ObservedState.MISSING
    assert paper_map.cell("R02_MI").observed_value == 2430
    assert paper_map.cell("R02_MI").observed_state == ObservedState.OBSERVED


def test_cell_id_must_match_fixed_address() -> None:
    with pytest.raises(ValueError, match="cell_id conflict"):
        PaperCell(cell_id="R02_MI", paper_row=1, field=FieldName.MI)


def test_build_paper_map_rejects_cells_outside_template() -> None:
    template = two_row_template()
    outside_cell = cell_from_observation(3, "mi", raw="900", observed_value=900)

    with pytest.raises(ValueError, match="outside template"):
        build_paper_map(template, image_id="bad", observed_cells=(outside_cell,))


def test_cell_id_helpers_do_not_depend_on_visible_order() -> None:
    assert make_cell_id(3, FieldName.MI) == "R03_MI"
    address = parse_cell_id("R17_MEMO")

    assert address.paper_row == 17
    assert address.field == FieldName.MEMO
    assert address.cell_id == "R17_MEMO"


def test_observed_value_and_adopted_amount_are_separate() -> None:
    ride = ReconciledRide(
        ride_key="ride-03",
        paper_cell_ids=("R03_MI",),
        meter_ride_ids=("M03",),
        link_status=LinkStatus.LINKED,
        observed_mi=2400,
        adopted_mi=AdoptedAmount(
            amount=2430,
            source=AmountSource.METER,
        ),
    )

    assert ride.observed_mi == 2400
    assert ride.adopted_mi is not None
    assert ride.adopted_mi.amount == 2430
    assert ride.adopted_mi.source == AmountSource.METER


def test_public_discount_candidates_use_integer_math_for_pickup_case() -> None:
    candidates = public_discount_candidates(3620, FareConfig())

    assert [candidate.discount_amount for candidate in candidates] == [380]
    assert candidates[0].pickup_fee == 200
    assert candidates[0].discount_base_after == 3420


def test_public_discount_candidate_without_pickup_case() -> None:
    candidates = public_discount_candidates(2430, FareConfig())

    assert [candidate.discount_amount for candidate in candidates] == [270]
    assert candidates[0].pickup_fee == 0


def test_discount_adjustment_is_not_counted_as_ride_or_passenger() -> None:
    adjustment = build_public_discount_adjustment(
        adjustment_id="D03",
        amount=270,
        target_ride_key="ride-03",
        source_cell_ids=("R04_MI",),
        evidence_detail="R04_MI linked to ride-03",
    )

    assert adjustment.kind == AdjustmentKind.PUBLIC_DISCOUNT_CLAIM
    assert adjustment.include_in_sales is True
    assert adjustment.include_in_count is False
    assert adjustment.include_in_passengers is False
    assert adjustment.target_ride_key == "ride-03"


def test_sales_components_keep_discount_claim_separate_from_confirmed_mi() -> None:
    sales = SalesComponents(
        confirmed_gen=30420,
        confirmed_mi=28610,
        pending_meter_sales=7220,
        discount_claim_total=650,
    )

    assert sales.confirmed_mi == 28610
    assert sales.discount_claim_total == 650
    assert sales.total_sales == 66900


def test_quality_summary_counts_fixed_address_states() -> None:
    template = two_row_template()
    paper_map = sparse_two_row_paper_map()
    summary = paper_map_quality_summary(paper_map, template)

    assert summary["expected_cell_count"] == 12
    assert summary["actual_cell_count"] == 12
    assert summary["missing_cell_ids"] == []
    assert summary["observed_state_counts"]["observed"] == 1
    assert summary["observed_state_counts"]["missing"] == 11
