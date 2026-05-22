"""Layer 2 evidence application.

This module adopts normal ride values by applying evidence sources to a primary
paper map through format maps.  It does not infer meaning from cell_id strings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from .models import AdoptedReport, AdoptedRow, EvidenceLink, FormatMap, SourceMap
from .observations import has_effective_observation, has_effective_value, is_voided_observation
from .semantic import SemanticRow, build_semantic_rows


@dataclass(frozen=True)
class ReconciliationRule:
    name: str
    paper_time_field: str = "time"
    evidence_time_field: str = "time"
    evidence_amount_field: str = "amount"
    destination_fields: tuple[str, ...] = ("gen", "mi")
    time_window_minutes: int = 9
    payment_hint_field: str = "memo"
    gen_hint_terms: tuple[str, ...] = ("現金", "現収", "CASH")
    mi_hint_terms: tuple[str, ...] = ("カード", "CARD", "VISA", "UBER", "GO", "PAYPAY", "SUICA", "交通系", "チケット", "券")


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
    return has_effective_value(value)


def _has_observation(row: SemanticRow, field_name: str) -> bool:
    item = row.fields.get(field_name)
    if item is None:
        return False
    return has_effective_observation(item.value, item.raw, item.state, item.marks)


def _effective_row_values(row: SemanticRow) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for field, item in row.fields.items():
        values[field] = None if is_voided_observation(item.state, item.marks) else item.value
    return values


def _text_contains_any(value: Any, terms: Iterable[str]) -> bool:
    text = str(value or "").upper()
    return any(str(term).upper() in text for term in terms)


def _find_destination(row: SemanticRow, destination_fields: Iterable[str]) -> str | None:
    for field_name in destination_fields:
        if _has_observation(row, field_name):
            return field_name
    return None


def _find_payment_destination(row: SemanticRow, rule: ReconciliationRule) -> str | None:
    hint_text = row.raw(rule.payment_hint_field) or row.value(rule.payment_hint_field)
    if _text_contains_any(hint_text, rule.gen_hint_terms):
        return "gen"
    if _text_contains_any(hint_text, rule.mi_hint_terms):
        return "mi"
    destination = _find_destination(row, rule.destination_fields)
    return destination


def _paper_link_cell(row: SemanticRow, destination: str, rule: ReconciliationRule) -> str:
    if destination in row.fields:
        return row.fields[destination].global_cell_id
    if rule.payment_hint_field in row.fields:
        return row.fields[rule.payment_hint_field].global_cell_id
    raise ValueError(f"paper row {row.row_addr} has no cell to link destination {destination!r}")


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


def _diagnostic_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _near_paper_rows(evidence_row: SemanticRow, paper_rows: list[SemanticRow], rule: ReconciliationRule) -> list[tuple[SemanticRow, int]]:
    near_rows: list[tuple[SemanticRow, int]] = []
    for paper_row in paper_rows:
        diff = _time_diff_minutes(paper_row.value(rule.paper_time_field), evidence_row.value(rule.evidence_time_field))
        if diff is not None and diff <= rule.time_window_minutes:
            near_rows.append((paper_row, diff))
    near_rows.sort(key=lambda item: (item[1], item[0].row_addr))
    return near_rows


def _unmatched_evidence_diagnostic(
    evidence_row: SemanticRow,
    paper_rows: list[SemanticRow],
    rule: ReconciliationRule,
) -> str:
    evidence_time = _diagnostic_value(evidence_row.value(rule.evidence_time_field))
    evidence_amount = _diagnostic_value(evidence_row.value(rule.evidence_amount_field))
    near_rows = _near_paper_rows(evidence_row, paper_rows, rule)

    if _parse_minutes(evidence_row.value(rule.evidence_time_field)) is None:
        reason = "evidence_time_missing"
    elif not near_rows:
        reason = "no_paper_time_within_9_minutes"
    elif not any(_find_payment_destination(row, rule) is not None for row, _ in near_rows):
        reason = "paper_time_match_without_payment_destination"
    else:
        reason = "paper_time_match_not_adopted"

    parts = [
        f"unmatched evidence {evidence_row.source_id}:{evidence_row.row_addr}",
        f"reason={reason}",
    ]
    if evidence_time:
        parts.append(f"time={evidence_time}")
    if evidence_amount:
        parts.append(f"amount={evidence_amount}")
    if near_rows:
        near_text = ",".join(f"{row.row_addr}@{diff}m" for row, diff in near_rows[:3])
        parts.append(f"near_paper={near_text}")
    return " ".join(parts)


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
        values = _effective_row_values(paper_row)
        alerts: dict[str, str] = {}
        links: list[EvidenceLink] = []
        destination = _find_payment_destination(paper_row, active_rule)

        if destination is not None:
            for field_name in active_rule.destination_fields:
                if field_name != destination:
                    values[field_name] = None
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
                paper_cell = _paper_link_cell(paper_row, destination, active_rule)
                evidence_cell = evidence_row.fields[active_rule.evidence_amount_field].global_cell_id
                links.append(EvidenceLink(paper_cell, evidence_cell, f"time_within_{diff}_minutes"))
                original = paper_row.value(destination)
                if _has_value(original) and original != amount_value:
                    diagnostics.append(f"{paper_cell}: paper amount {original} adopted evidence amount {amount_value}")
                elif not _has_value(original) and paper_row.raw(destination):
                    diagnostics.append(f"{paper_cell}: paper amount unreadable adopted evidence amount {amount_value}")
            elif len(candidates) > 1:
                alerts[destination] = "candidate_conflict"
            else:
                alerts[destination] = "no_evidence_match"

        adopted_rows.append(AdoptedRow(row_addr=paper_row.row_addr, values=values, alerts=alerts, evidence=tuple(links)))

    for evidence_row in evidence_rows:
        evidence_key = (evidence_row.source_id, evidence_row.row_addr)
        if evidence_key not in used_evidence and _has_value(evidence_row.value(active_rule.evidence_amount_field)):
            diagnostics.append(_unmatched_evidence_diagnostic(evidence_row, paper_rows, active_rule))

    return AdoptedReport(rows=tuple(adopted_rows), diagnostics=tuple(diagnostics))
