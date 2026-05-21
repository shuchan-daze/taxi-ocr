"""Small deterministic fixtures for the Kamichizu engine."""

from __future__ import annotations

from kamichizu_engine.models import ObservedState
from kamichizu_engine.meter import build_meter_receipt_from_mappings
from kamichizu_engine.paper_map import (
    build_paper_map,
    cell_from_observation,
    default_daily_report_template,
)


def two_row_template():
    return default_daily_report_template(row_count=2)


def sparse_two_row_paper_map():
    """PaperMap with only one observed cell and all other addresses retained."""

    template = two_row_template()
    return build_paper_map(
        template=template,
        image_id="fixture-nippou",
        observed_cells=(
            cell_from_observation(
                2,
                "mi",
                raw="2,430",
                observed_value=2430,
                confidence=0.95,
                observed_state=ObservedState.OBSERVED,
            ),
        ),
    )


def matched_two_row_paper_map():
    """PaperMap with one normal ride that should reconcile by amount."""

    template = two_row_template()
    return build_paper_map(
        template=template,
        image_id="fixture-nippou",
        observed_cells=(
            cell_from_observation(
                2,
                "time",
                raw="10:44",
                observed_value="10:44",
                confidence=0.98,
                observed_state=ObservedState.OBSERVED,
            ),
            cell_from_observation(
                2,
                "mi",
                raw="2,430",
                observed_value=2430,
                confidence=0.95,
                observed_state=ObservedState.OBSERVED,
            ),
        ),
    )


def matched_two_row_meter_receipt():
    return build_meter_receipt_from_mappings(
        image_id="fixture-meter",
        rows=(
            {
                "ride_id": "M01",
                "time": "10:44",
                "amount": 2430,
                "payment_hint": "mi",
            },
        ),
    )
