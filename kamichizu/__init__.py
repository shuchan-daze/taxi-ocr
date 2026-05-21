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
    SourceMap,
    SourceMeta,
    ViewMap,
)
from .reconcile import ReconciliationRule, reconcile_sources
from .semantic import SemanticRow, build_semantic_rows
from .view import build_claim_rows, build_human_rows

__all__ = [
    "AdoptedReport",
    "AdoptedRow",
    "Cell",
    "Claim",
    "EvidenceLink",
    "FormatMap",
    "ReconciliationRule",
    "SemanticRow",
    "SourceMap",
    "SourceMeta",
    "ViewMap",
    "build_human_rows",
    "build_claim_rows",
    "build_semantic_rows",
    "reconcile_sources",
]
