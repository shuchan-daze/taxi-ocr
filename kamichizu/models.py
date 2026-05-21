"""Core data models for the Kamichizu engine.

Design rule: addresses are physical.  Meanings such as gen, mi, memo, time are
not allowed inside cell IDs.  Meanings live in FormatMap and ViewMap only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


SEMANTIC_ID_PARTS = (
    "GEN",
    "MI",
    "MEMO",
    "PASSENGERS",
    "TIME",
    "ROUTE",
    "AMOUNT",
)


def normalize_row_addr(row_addr: int | str) -> str:
    if isinstance(row_addr, int):
        if row_addr < 0:
            raise ValueError("row address must be positive")
        return f"{row_addr:02d}"
    text = str(row_addr).strip()
    if not text.isdigit():
        raise ValueError(f"row address must be numeric: {row_addr!r}")
    return f"{int(text):02d}"


def normalize_col_addr(col_addr: str) -> str:
    text = str(col_addr).strip().upper()
    if not text.isalpha():
        raise ValueError(f"column address must be alphabetic: {col_addr!r}")
    return text


def make_local_cell_id(row_addr: int | str, col_addr: str) -> str:
    return f"{normalize_row_addr(row_addr)}_{normalize_col_addr(col_addr)}"


def split_local_cell_id(cell_id: str) -> tuple[str, str]:
    text = str(cell_id).strip().upper()
    parts = text.split("_")
    if len(parts) != 2:
        raise ValueError(f"cell_id must be physical row_col address: {cell_id!r}")
    row_addr = normalize_row_addr(parts[0])
    col_addr = normalize_col_addr(parts[1])
    normalized = f"{row_addr}_{col_addr}"
    if normalized != text:
        raise ValueError(f"cell_id must use normalized physical address: {cell_id!r}")
    for forbidden in SEMANTIC_ID_PARTS:
        if forbidden in parts:
            raise ValueError(f"cell_id must not contain semantic name: {cell_id!r}")
    return row_addr, col_addr


def make_global_cell_id(source_id: str, local_cell_id: str) -> str:
    split_local_cell_id(local_cell_id)
    source = str(source_id).strip().upper()
    if not source:
        raise ValueError("source_id is required")
    return f"{source}:{local_cell_id.upper()}"


@dataclass(frozen=True)
class SourceMeta:
    source_id: str
    source_role: str
    source_type: str
    label: str
    format_id: str


@dataclass(frozen=True)
class Cell:
    local_cell_id: str
    raw: str = ""
    value: Any = None
    confidence: float | None = None
    state: str = "observed"
    bbox: tuple[float, float, float, float] | None = None

    def __post_init__(self) -> None:
        split_local_cell_id(self.local_cell_id)

    @property
    def row_addr(self) -> str:
        return split_local_cell_id(self.local_cell_id)[0]

    @property
    def col_addr(self) -> str:
        return split_local_cell_id(self.local_cell_id)[1]


@dataclass(frozen=True)
class SourceMap:
    meta: SourceMeta
    cells: Mapping[str, Cell]

    def __post_init__(self) -> None:
        for key, cell in self.cells.items():
            if key != cell.local_cell_id:
                raise ValueError(f"cell key and local_cell_id differ: {key!r}")
            split_local_cell_id(key)

    def global_cell_id(self, local_cell_id: str) -> str:
        return make_global_cell_id(self.meta.source_id, local_cell_id)


@dataclass(frozen=True)
class FormatMap:
    format_id: str
    columns: Mapping[str, str]

    def __post_init__(self) -> None:
        normalized = {normalize_col_addr(col): field_name for col, field_name in self.columns.items()}
        if dict(self.columns) != normalized:
            raise ValueError("format columns must use normalized column addresses")

    def field_for_column(self, col_addr: str) -> str | None:
        return self.columns.get(normalize_col_addr(col_addr))


@dataclass(frozen=True)
class ViewMap:
    view_id: str
    columns: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class EvidenceLink:
    paper_cell: str
    evidence_cell: str
    reason: str


@dataclass(frozen=True)
class Claim:
    """A non-ride claim linked to a target ride, such as disability discount."""

    claim_type: str
    amount: int
    target_row_addr: str
    evidence: tuple[EvidenceLink, ...] = ()


@dataclass(frozen=True)
class AdoptedRow:
    row_addr: str
    values: Mapping[str, Any]
    alerts: Mapping[str, str] = field(default_factory=dict)
    evidence: tuple[EvidenceLink, ...] = ()


@dataclass(frozen=True)
class AdoptedReport:
    rows: tuple[AdoptedRow, ...]
    claims: tuple[Claim, ...] = ()
    diagnostics: tuple[str, ...] = ()
