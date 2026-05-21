"""Kamichizu core engine.

The engine treats every document as a source map of physical cell addresses.
Meaning is attached later by a format map, and adoption is performed by rules.
"""

from .models import (
    AdoptedReport,
    AdoptedRow,
    Cell,
    Claim,
    EvidenceLink,
    FormatMap,
    HumanReport,
    SourceMap,
    SourceMeta,
    ViewMap,
)
from .case import build_human_report_from_case
from .reconcile import ReconciliationRule, reconcile_sources
from .semantic import SemanticRow, build_semantic_rows
from .totals import SalesTotals, compute_sales_totals
from .view import build_claim_rows, build_human_report, build_human_rows, build_summary_rows
from .pipeline import build_human_report_from_sources

__all__ = [
    "AdoptedReport",
    "AdoptedRow",
    "Cell",
    "Claim",
    "EvidenceLink",
    "FormatMap",
    "HumanReport",
    "ReconciliationRule",
    "SemanticRow",
    "SourceMap",
    "SourceMeta",
    "SalesTotals",
    "ViewMap",
    "build_human_report_from_case",
    "build_human_rows",
    "build_claim_rows",
    "build_human_report",
    "build_human_report_from_sources",
    "build_summary_rows",
    "build_semantic_rows",
    "compute_sales_totals",
    "reconcile_sources",
]
