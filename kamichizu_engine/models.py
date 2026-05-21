"""Data contracts for the Kamichizu engine.

The central contract is that PaperMap.cells is the source of truth. Any row
view is derived later and must not be used as the paper address source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class FieldName(str, Enum):
    PASSENGERS = "passengers"
    ROUTE = "route"
    TIME = "time"
    GEN = "gen"
    MI = "mi"
    MEMO = "memo"


class ObservedState(str, Enum):
    OBSERVED = "observed"
    BLANK = "blank"
    UNREADABLE = "unreadable"
    MISSING = "missing"
    EMPTY_UNKNOWN = "empty_unknown"


class LinkStatus(str, Enum):
    LINKED = "linked"
    UNLINKED = "unlinked"
    AMBIGUOUS = "ambiguous"
    NOT_APPLICABLE = "not_applicable"


class AmountSource(str, Enum):
    METER = "meter"
    PAPER = "paper"
    USER = "user"
    RULE = "rule"
    NONE = "none"


class AdjustmentKind(str, Enum):
    PUBLIC_DISCOUNT_CLAIM = "public_discount_claim"
    CHARTER = "charter"
    PICKUP = "pickup"
    METER_OUTSIDE = "meter_outside"
    OTHER = "other"


class DiagnosticSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class BBox:
    x: float
    y: float
    width: float
    height: float

    def to_dict(self) -> dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class CellAddress:
    paper_row: int
    field: FieldName

    @property
    def cell_id(self) -> str:
        return f"R{self.paper_row:02d}_{self.field.value.upper()}"


@dataclass(frozen=True)
class PaperCell:
    cell_id: str
    paper_row: int
    field: FieldName
    raw: str = ""
    observed_value: Any = None
    confidence: float | None = None
    ambiguous: bool = False
    observed_state: ObservedState = ObservedState.MISSING
    bbox: BBox | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        expected = CellAddress(self.paper_row, self.field).cell_id
        if self.cell_id != expected:
            raise ValueError(f"cell_id conflict: expected {expected}, got {self.cell_id}")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

    @property
    def has_observed_value(self) -> bool:
        return self.observed_state == ObservedState.OBSERVED and self.observed_value not in (None, "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "paper_row": self.paper_row,
            "field": self.field.value,
            "raw": self.raw,
            "observed_value": self.observed_value,
            "confidence": self.confidence,
            "ambiguous": self.ambiguous,
            "observed_state": self.observed_state.value,
            "bbox": self.bbox.to_dict() if self.bbox else None,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class PaperTemplate:
    template_id: str
    row_numbers: tuple[int, ...]
    fields: tuple[FieldName, ...]

    def expected_cell_ids(self) -> tuple[str, ...]:
        return tuple(
            CellAddress(paper_row, field_name).cell_id
            for paper_row in self.row_numbers
            for field_name in self.fields
        )

    def address_for(self, paper_row: int, field_name: FieldName) -> CellAddress:
        if paper_row not in self.row_numbers:
            raise ValueError(f"unknown paper_row: {paper_row}")
        if field_name not in self.fields:
            raise ValueError(f"unknown field: {field_name}")
        return CellAddress(paper_row, field_name)


@dataclass(frozen=True)
class PaperMap:
    schema: str
    template_id: str
    image_id: str
    cells: Mapping[str, PaperCell]
    diagnostics: tuple["Diagnostic", ...] = ()

    def __post_init__(self) -> None:
        for cell_id, cell in self.cells.items():
            if cell_id != cell.cell_id:
                raise ValueError(f"cell map key conflict: {cell_id} != {cell.cell_id}")

    def cell(self, cell_id: str) -> PaperCell:
        return self.cells[cell_id]

    def missing_cell_ids(self, template: PaperTemplate) -> tuple[str, ...]:
        return tuple(cell_id for cell_id in template.expected_cell_ids() if cell_id not in self.cells)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "template_id": self.template_id,
            "image_id": self.image_id,
            "cells": {cell_id: cell.to_dict() for cell_id, cell in sorted(self.cells.items())},
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }


@dataclass(frozen=True)
class MeterRide:
    ride_id: str
    sequence_no: int
    time: str | None
    amount: int
    raw: Mapping[str, Any] = field(default_factory=dict)
    payment_hint: str | None = None

    def __post_init__(self) -> None:
        if self.sequence_no <= 0:
            raise ValueError("sequence_no must be positive")
        if self.amount < 0:
            raise ValueError("amount must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ride_id": self.ride_id,
            "sequence_no": self.sequence_no,
            "time": self.time,
            "amount": self.amount,
            "payment_hint": self.payment_hint,
            "raw": dict(self.raw),
        }


@dataclass(frozen=True)
class MeterReceipt:
    schema: str
    image_id: str
    rides: tuple[MeterRide, ...]
    diagnostics: tuple["Diagnostic", ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "image_id": self.image_id,
            "rides": [ride.to_dict() for ride in self.rides],
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }


@dataclass(frozen=True)
class Evidence:
    source: str
    reference: str
    detail: str = ""
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "reference": self.reference,
            "detail": self.detail,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class AdoptedAmount:
    amount: int
    source: AmountSource
    evidences: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("amount must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount": self.amount,
            "source": self.source.value,
            "evidences": [evidence.to_dict() for evidence in self.evidences],
        }


@dataclass(frozen=True)
class ReconciledRide:
    ride_key: str
    paper_cell_ids: tuple[str, ...]
    meter_ride_ids: tuple[str, ...]
    link_status: LinkStatus
    observed_gen: int | None = None
    observed_mi: int | None = None
    adopted_total: AdoptedAmount | None = None
    adopted_gen: AdoptedAmount | None = None
    adopted_mi: AdoptedAmount | None = None
    diagnostic_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ride_key": self.ride_key,
            "paper_cell_ids": list(self.paper_cell_ids),
            "meter_ride_ids": list(self.meter_ride_ids),
            "link_status": self.link_status.value,
            "observed_gen": self.observed_gen,
            "observed_mi": self.observed_mi,
            "adopted_total": self.adopted_total.to_dict() if self.adopted_total else None,
            "adopted_gen": self.adopted_gen.to_dict() if self.adopted_gen else None,
            "adopted_mi": self.adopted_mi.to_dict() if self.adopted_mi else None,
            "diagnostic_reasons": list(self.diagnostic_reasons),
        }


@dataclass(frozen=True)
class Adjustment:
    adjustment_id: str
    kind: AdjustmentKind
    amount: int
    target_ride_key: str | None
    source_cell_ids: tuple[str, ...] = ()
    evidences: tuple[Evidence, ...] = ()
    include_in_sales: bool = False
    include_in_count: bool = False
    include_in_passengers: bool = False

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("amount must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "adjustment_id": self.adjustment_id,
            "kind": self.kind.value,
            "amount": self.amount,
            "target_ride_key": self.target_ride_key,
            "source_cell_ids": list(self.source_cell_ids),
            "evidences": [evidence.to_dict() for evidence in self.evidences],
            "include_in_sales": self.include_in_sales,
            "include_in_count": self.include_in_count,
            "include_in_passengers": self.include_in_passengers,
        }


@dataclass(frozen=True)
class SalesComponents:
    confirmed_gen: int = 0
    confirmed_mi: int = 0
    pending_meter_sales: int = 0
    discount_claim_total: int = 0
    charter_sales: int = 0

    @property
    def total_sales(self) -> int:
        return (
            self.confirmed_gen
            + self.confirmed_mi
            + self.pending_meter_sales
            + self.discount_claim_total
            + self.charter_sales
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "confirmed_gen": self.confirmed_gen,
            "confirmed_mi": self.confirmed_mi,
            "pending_meter_sales": self.pending_meter_sales,
            "discount_claim_total": self.discount_claim_total,
            "charter_sales": self.charter_sales,
            "total_sales": self.total_sales,
        }


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.INFO
    references: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "references": list(self.references),
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class ReconciledReport:
    schema: str
    paper_map: PaperMap
    meter_receipt: MeterReceipt
    rides: tuple[ReconciledRide, ...] = ()
    adjustments: tuple[Adjustment, ...] = ()
    sales: SalesComponents = SalesComponents()
    diagnostics: tuple[Diagnostic, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "paper_map": self.paper_map.to_dict(),
            "meter_receipt": self.meter_receipt.to_dict(),
            "rides": [ride.to_dict() for ride in self.rides],
            "adjustments": [adjustment.to_dict() for adjustment in self.adjustments],
            "sales": self.sales.to_dict(),
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }
