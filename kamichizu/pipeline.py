"""Single formal entry from source maps to human report."""

from __future__ import annotations

from dataclasses import replace

from .models import Claim, FormatMap, HumanReport, SourceMap, ViewMap
from .reconcile import ReconciliationRule, reconcile_sources
from .view import build_human_report


def build_human_report_from_sources(
    *,
    paper: SourceMap,
    paper_format: FormatMap,
    evidences: list[tuple[SourceMap, FormatMap]],
    view_map: ViewMap,
    claims: tuple[Claim, ...] = (),
    rule: ReconciliationRule | None = None,
) -> HumanReport:
    """Build HumanReport through the only formal engine route."""

    adopted_report = reconcile_sources(paper, paper_format, evidences, rule)
    if claims:
        adopted_report = replace(adopted_report, claims=claims)
    return build_human_report(adopted_report, view_map)
