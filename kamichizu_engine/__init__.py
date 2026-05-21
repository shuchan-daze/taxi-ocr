"""Yatagarasu v3 Kamichizu engine.

This package is intentionally not connected to the current production app.
It defines the new engine contracts first: fixed paper cell addresses,
observations, reconciliation, special rules, and diagnostics.
"""

from .config import EngineConfig, FareConfig
from .models import (
    Adjustment,
    AdjustmentKind,
    AdoptedAmount,
    AmountSource,
    BBox,
    CellAddress,
    Diagnostic,
    DiagnosticSeverity,
    Evidence,
    FieldName,
    LinkStatus,
    MeterReceipt,
    MeterRide,
    ObservedState,
    PaperCell,
    PaperMap,
    PaperTemplate,
    ReconciledReport,
    ReconciledRide,
    SalesComponents,
)
from .app_inputs import AppInputError, build_paper_map_from_payload, build_reconciled_report_from_app_inputs
from .paper_map import (
    DEFAULT_FIELDS,
    build_empty_paper_map,
    build_paper_map,
    default_daily_report_template,
    make_cell_id,
    parse_cell_id,
)

__all__ = [
    "AppInputError",
    "Adjustment",
    "AdjustmentKind",
    "AdoptedAmount",
    "AmountSource",
    "BBox",
    "CellAddress",
    "DEFAULT_FIELDS",
    "Diagnostic",
    "DiagnosticSeverity",
    "EngineConfig",
    "Evidence",
    "FareConfig",
    "FieldName",
    "LinkStatus",
    "MeterReceipt",
    "MeterRide",
    "ObservedState",
    "PaperCell",
    "PaperMap",
    "PaperTemplate",
    "ReconciledReport",
    "ReconciledRide",
    "SalesComponents",
    "build_empty_paper_map",
    "build_paper_map_from_payload",
    "build_reconciled_report_from_app_inputs",
    "build_paper_map",
    "default_daily_report_template",
    "make_cell_id",
    "parse_cell_id",
]

