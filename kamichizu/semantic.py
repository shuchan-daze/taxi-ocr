"""Build semantic row views from physical source maps and format maps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import FormatMap, SourceMap


@dataclass(frozen=True)
class SemanticValue:
    field: str
    value: Any
    raw: str
    global_cell_id: str
    local_cell_id: str


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
    """Resolve physical cells into semantic rows using only format_map."""

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
        )
    return [rows[key] for key in sorted(rows)]
