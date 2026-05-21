"""Formal app-to-Kamichizu input adapter.

The adapter accepts only the materials Kamichizu owns:
- paper_map.cells, keyed by fixed cell_id
- meter_data["rows"], the meter receipt ride observations

It does not consume aggregate totals, display rows, or row-list paper maps.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .meter import build_meter_receipt_from_mappings
from .models import ObservedState, PaperMap, ReconciledReport
from .paper_map import build_paper_map, cell_from_observation, default_daily_report_template, parse_cell_id
from .reconcile import reconcile_exact_amounts


class AppInputError(ValueError):
    """Raised when app.py hands Kamichizu something other than official inputs."""


def _observed_state(value: Any) -> ObservedState:
    if isinstance(value, ObservedState):
        return value
    if isinstance(value, str):
        try:
            return ObservedState(value)
        except ValueError:
            pass
    return ObservedState.EMPTY_UNKNOWN


def _cells_payload(payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if payload is None:
        raise AppInputError("paper_map is required")
    if not isinstance(payload, Mapping):
        raise AppInputError("paper_map must be a mapping")
    if "cells" not in payload:
        if "rows" in payload:
            raise AppInputError("row-list paper map form is not accepted; cells is required")
        raise AppInputError("paper_map.cells is required")
    cells = payload.get("cells")
    if not isinstance(cells, Mapping):
        raise AppInputError("paper_map.cells must be a mapping")
    if not cells:
        raise AppInputError("paper_map.cells must not be empty")
    return cells


def build_paper_map_from_payload(
    payload: Mapping[str, Any],
    *,
    image_id: str = "app-paper-map",
) -> PaperMap:
    """Build a PaperMap from paper_map.cells.

    Cell IDs are the only accepted paper addresses. No address is inferred from
    row order, and row-list paper maps are rejected before construction.
    """

    cells_payload = _cells_payload(payload)
    max_row = 25
    for cell_id in cells_payload:
        address = parse_cell_id(str(cell_id))
        max_row = max(max_row, address.paper_row)

    template = default_daily_report_template(row_count=max_row)
    observed_cells = []
    for cell_id, cell_payload in cells_payload.items():
        address = parse_cell_id(str(cell_id))
        if not isinstance(cell_payload, Mapping):
            cell_payload = {}
        observed_cells.append(
            cell_from_observation(
                address.paper_row,
                address.field,
                raw="" if cell_payload.get("raw") is None else str(cell_payload.get("raw")),
                observed_value=cell_payload.get("observed_value", cell_payload.get("value")),
                confidence=cell_payload.get("confidence"),
                ambiguous=bool(cell_payload.get("ambiguous")),
                observed_state=_observed_state(cell_payload.get("observed_state")),
                notes="" if cell_payload.get("notes") is None else str(cell_payload.get("notes")),
            )
        )

    return build_paper_map(template=template, image_id=image_id, observed_cells=observed_cells)


def _meter_rows_payload(meter_payload: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None) -> Sequence[Mapping[str, Any]]:
    if meter_payload is None:
        raise AppInputError("meter_data is required")
    if isinstance(meter_payload, Mapping):
        if "rows" not in meter_payload:
            raise AppInputError("meter_data.rows is required")
        rows = meter_payload.get("rows")
    elif isinstance(meter_payload, Sequence) and not isinstance(meter_payload, (str, bytes)):
        rows = meter_payload
    else:
        raise AppInputError("meter_data must be a mapping with rows")

    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise AppInputError("meter_data.rows must be a sequence")
    if not rows:
        raise AppInputError("meter_data.rows must not be empty")
    return rows


def build_reconciled_report_from_app_inputs(
    paper_map: Mapping[str, Any],
    meter_data: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    *,
    paper_image_id: str = "app-paper-map",
    meter_image_id: str = "app-meter-receipt",
) -> ReconciledReport:
    """Official app.py entrypoint for Kamichizu report generation.

    Required inputs:
    - paper_map.cells
    - meter_data["rows"]

    Aggregate totals, display rows, and row-list paper maps are not accepted as truth.
    """

    paper_map = build_paper_map_from_payload(paper_map, image_id=paper_image_id)
    template = default_daily_report_template(row_count=max(paper_map.cell(cell_id).paper_row for cell_id in paper_map.cells))
    meter_rows = []
    for row in _meter_rows_payload(meter_data):
        if not isinstance(row, Mapping):
            raise AppInputError("meter_data.rows entries must be mappings")
        item = dict(row)
        if "ride_id" not in item and "no" in item:
            try:
                item["ride_id"] = f"M{int(item['no']):02d}"
            except (TypeError, ValueError):
                pass
        meter_rows.append(item)
    meter_receipt = build_meter_receipt_from_mappings(image_id=meter_image_id, rows=meter_rows)
    return reconcile_exact_amounts(paper_map, meter_receipt, template)
