"""Layer 1: fixed-address paper map construction."""

from __future__ import annotations

import re
from typing import Iterable

from .models import CellAddress, FieldName, ObservedState, PaperCell, PaperMap, PaperTemplate


DEFAULT_FIELDS: tuple[FieldName, ...] = (
    FieldName.PASSENGERS,
    FieldName.ROUTE,
    FieldName.TIME,
    FieldName.GEN,
    FieldName.MI,
    FieldName.MEMO,
)

CELL_ID_PATTERN = re.compile(r"^R(?P<row>\d{2})_(?P<field>[A-Z_]+)$")


def make_cell_id(paper_row: int, field_name: FieldName | str) -> str:
    field = FieldName(field_name)
    return CellAddress(paper_row, field).cell_id


def parse_cell_id(cell_id: str) -> CellAddress:
    match = CELL_ID_PATTERN.match(cell_id)
    if not match:
        raise ValueError(f"invalid cell_id: {cell_id}")
    field_value = match.group("field").lower()
    return CellAddress(int(match.group("row")), FieldName(field_value))


def default_daily_report_template(
    template_id: str = "daiichi_taxi_daily_report",
    row_count: int = 25,
) -> PaperTemplate:
    if row_count <= 0:
        raise ValueError("row_count must be positive")
    return PaperTemplate(
        template_id=template_id,
        row_numbers=tuple(range(1, row_count + 1)),
        fields=DEFAULT_FIELDS,
    )


def missing_cell(address: CellAddress) -> PaperCell:
    return PaperCell(
        cell_id=address.cell_id,
        paper_row=address.paper_row,
        field=address.field,
        observed_state=ObservedState.MISSING,
    )


def build_empty_paper_map(
    template: PaperTemplate,
    image_id: str,
    schema: str = "paper_map",
) -> PaperMap:
    cells = {
        cell_id: missing_cell(parse_cell_id(cell_id))
        for cell_id in template.expected_cell_ids()
    }
    return PaperMap(
        schema=schema,
        template_id=template.template_id,
        image_id=image_id,
        cells=cells,
    )


def build_paper_map(
    template: PaperTemplate,
    image_id: str,
    observed_cells: Iterable[PaperCell],
    schema: str = "paper_map",
) -> PaperMap:
    """Build a PaperMap without inferring addresses from order.

    Every expected cell address is present. Observed cells replace their fixed
    addresses only when they belong to the template.
    """

    cells = dict(build_empty_paper_map(template, image_id, schema=schema).cells)
    expected = set(template.expected_cell_ids())

    for cell in observed_cells:
        if cell.cell_id not in expected:
            raise ValueError(f"cell outside template: {cell.cell_id}")
        cells[cell.cell_id] = cell

    return PaperMap(
        schema=schema,
        template_id=template.template_id,
        image_id=image_id,
        cells=cells,
    )


def cell_from_observation(
    paper_row: int,
    field_name: FieldName | str,
    *,
    raw: str = "",
    observed_value: object = None,
    confidence: float | None = None,
    ambiguous: bool = False,
    observed_state: ObservedState = ObservedState.OBSERVED,
    notes: str = "",
) -> PaperCell:
    field = FieldName(field_name)
    address = CellAddress(paper_row, field)
    return PaperCell(
        cell_id=address.cell_id,
        paper_row=paper_row,
        field=field,
        raw=raw,
        observed_value=observed_value,
        confidence=confidence,
        ambiguous=ambiguous,
        observed_state=observed_state,
        notes=notes,
    )

