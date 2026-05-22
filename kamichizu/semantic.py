"""Build semantic row views from physical source maps and format maps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import FormatMap, SourceMap, make_local_cell_id


@dataclass(frozen=True)
class SemanticValue:
    field: str
    value: Any
    raw: str
    global_cell_id: str
    local_cell_id: str
    state: str = "observed"
    marks: tuple[str, ...] = ()


@dataclass(frozen=True)
class SemanticRow:
    source_id: str
    row_addr: str
    fields: dict[str, SemanticValue] = field(default_factory=dict)

    def value(self, field_name: str) -> Any:
        item = self.fields.get(field_name)
        return None if item is None else item.value

    def raw(self, field_name: str) -> str:
        item = self.fields.get(field_name)
        return "" if item is None else item.raw


def build_semantic_rows(source_map: SourceMap, format_map: FormatMap) -> list[SemanticRow]:
    """Resolve physical cells into semantic rows using only format_map.

    If any cell in a physical row is observed, the row keeps every field
    declared by the format map.  Blank or unread cells are still real paper
    addresses; dropping them turns the map into an observation list.
    """

    rows: dict[str, SemanticRow] = {}
    for local_cell_id, cell in sorted(source_map.cells.items()):
        field_name = format_map.field_for_column(cell.col_addr)
        if field_name is None:
            continue
        row = rows.setdefault(cell.row_addr, SemanticRow(source_map.meta.source_id, cell.row_addr, {}))
        row.fields[field_name] = SemanticValue(
            field=field_name,
            value=cell.value,
            raw=cell.raw,
            global_cell_id=source_map.global_cell_id(local_cell_id),
            local_cell_id=local_cell_id,
            state=cell.state,
            marks=cell.marks,
        )
    for row_addr, row in rows.items():
        for col_addr, field_name in format_map.columns.items():
            if field_name in row.fields:
                continue
            local_cell_id = make_local_cell_id(row_addr, col_addr)
            row.fields[field_name] = SemanticValue(
                field=field_name,
                value=None,
                raw="",
                global_cell_id=source_map.global_cell_id(local_cell_id),
                local_cell_id=local_cell_id,
                state="blank",
            )
    return [rows[key] for key in sorted(rows)]
