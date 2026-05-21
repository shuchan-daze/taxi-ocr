"""Layer 2 evidence application.

This module adopts normal ride values by applying evidence sources to a primary
paper map through format maps.  It does not infer meaning from cell_id strings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from .models import AdoptedReport, AdoptedRow, EvidenceLink, FormatMap, SourceMap
from .semantic import SemanticRow, build_semantic_rows


@dataclass(frozen=True)
class ReconciliationRule:
    name: str
    paper_time_field: str = "time"
    evidence_time_field: str = "time"
    evidence_amount_field: str = "amount"
    destination_fields: tuple[str, ...] = ("gen", "mi")
    time_window_minutes: int = 9


def _parse_minutes(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%H:%M", "%H.%M"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.hour * 60 + dt.minute
        except ValueError:
            pass
    return None


def _time_diff_minutes(left: Any, right: Any) -> int | None:
    left_minutes = _parse_minutes(left)
    right_minutes = _parse_minutes(right)
    if left_minutes is None or right_minutes is None:
        return None
    return abs(left_minutes - right_minutes)


def _has_value(value: Any) -> bool:
    return value not in (None, "")


def _find_destination(row: SemanticRow, destination_fields: Iterable[str]) -> str | None:
    for field_name in destination_fields:
        if field_name in row.fields and _has_value(row.value(field_name)):
            return field_name
    return None


def _candidate_score(paper_row: SemanticRow, evidence_row: SemanticRow, rule: ReconciliationRule) -> tuple[int, int] | None:
    diff = _time_diff_minutes(paper_row.value(rule.paper_time_field), evidence_row.value(rule.evidence_time_field))
    if diff is None or diff > rule.time_window_minutes:
        return None
    score = 100 - diff
    paper_amounts = [paper_row.value(field_name) for field_name in rule.destination_fields]
    evidence_amount = evidence_row.value(rule.evidence_amount_field)
    if evidence_amount in paper_amounts:
        score += 50
    return score, diff


def reconcile_sources(
    paper: SourceMap,
    paper_format: FormatMap,
    evidences: list[tuple[SourceMap, FormatMap]],
    rule: ReconciliationRule | None = None,
) -> AdoptedReport:
    """Create an adopted report from paper and evidence source maps."""

    active_rule = rule or ReconciliationRule(name="default_time_amount_match")
    paper_rows = build_semantic_rows(paper, paper_format)
    evidence_rows: list[SemanticRow] = []
    for source_map, format_map in evidences:
        evidence_rows.extend(build_semantic_rows(source_map, format_map))

    used_evidence: set[tuple[str, str]] = set()
    adopted_rows: list[AdoptedRow] = []
    diagnostics: list[str] = []

    for paper_row in paper_rows:
        values: dict[str, Any] = {field: item.value for field, item in paper_row.fields.items()}
        alerts: dict[str, str] = {}
        links: list[EvidenceLink] = []
        destination = _find_destination(paper_row, active_rule.destination_fields)

        if destination is not None:
            candidates: list[tuple[int, int, SemanticRow]] = []
            for evidence_row in evidence_rows:
                evidence_key = (evidence_row.source_id, evidence_row.row_addr)
                if evidence_key in used_evidence:
                    continue
                score = _candidate_score(paper_row, evidence_row, active_rule)
                if score is not None:
                    candidates.append((score[0], score[1], evidence_row))

            candidates.sort(key=lambda item: (-item[0], item[1], item[2].row_addr))
            if len(candidates) == 1:
                _, diff, evidence_row = candidates[0]
                amount_value = evidence_row.value(active_rule.evidence_amount_field)
                values[destination] = amount_value
                used_evidence.add((evidence_row.source_id, evidence_row.row_addr))
                paper_cell = paper_row.fields[destination].global_cell_id
                evidence_cell = evidence_row.fields[active_rule.evidence_amount_field].global_cell_id
                links.append(EvidenceLink(paper_cell, evidence_cell, f"time_within_{diff}_minutes"))
                original = paper_row.value(destination)
                if _has_value(original) and original != amount_value:
                    diagnostics.append(f"{paper_cell}: paper amount {original} adopted evidence amount {amount_value}")
            elif len(candidates) > 1:
                alerts[destination] = "candidate_conflict"
            else:
                alerts[destination] = "no_evidence_match"

        adopted_rows.append(AdoptedRow(row_addr=paper_row.row_addr, values=values, alerts=alerts, evidence=tuple(links)))

    for evidence_row in evidence_rows:
        evidence_key = (evidence_row.source_id, evidence_row.row_addr)
        if evidence_key not in used_evidence and _has_value(evidence_row.value(active_rule.evidence_amount_field)):
            diagnostics.append(f"unmatched evidence {evidence_row.source_id}:{evidence_row.row_addr}")

    return AdoptedReport(rows=tuple(adopted_rows), diagnostics=tuple(diagnostics))
