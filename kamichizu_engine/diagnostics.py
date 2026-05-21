"""Diagnostics and explanations for Kamichizu shadow development."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    Adjustment,
    AdoptedAmount,
    Diagnostic,
    DiagnosticSeverity,
    Evidence,
    ObservedState,
    PaperMap,
    PaperTemplate,
    ReconciledReport,
    ReconciledRide,
)


def diagnose_paper_map(paper_map: PaperMap, template: PaperTemplate) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    missing_cell_ids = paper_map.missing_cell_ids(template)
    if missing_cell_ids:
        diagnostics.append(
            Diagnostic(
                code="missing_fixed_cell_addresses",
                message="expected fixed cell addresses are missing",
                severity=DiagnosticSeverity.ERROR,
                references=missing_cell_ids,
            )
        )

    unreadable = tuple(
        cell_id
        for cell_id, cell in paper_map.cells.items()
        if cell.observed_state == ObservedState.UNREADABLE
    )
    if unreadable:
        diagnostics.append(
            Diagnostic(
                code="unreadable_cells",
                message="some fixed cells were observed but unreadable",
                severity=DiagnosticSeverity.WARNING,
                references=unreadable,
            )
        )

    return tuple(diagnostics)


def paper_map_quality_summary(paper_map: PaperMap, template: PaperTemplate) -> dict[str, Any]:
    state_counts: dict[str, int] = {state.value: 0 for state in ObservedState}
    by_field: dict[str, dict[str, int]] = {}

    for cell in paper_map.cells.values():
        state_counts[cell.observed_state.value] = state_counts.get(cell.observed_state.value, 0) + 1
        field_counts = by_field.setdefault(cell.field.value, {state.value: 0 for state in ObservedState})
        field_counts[cell.observed_state.value] = field_counts.get(cell.observed_state.value, 0) + 1

    return {
        "template_id": template.template_id,
        "expected_cell_count": len(template.expected_cell_ids()),
        "actual_cell_count": len(paper_map.cells),
        "missing_cell_ids": list(paper_map.missing_cell_ids(template)),
        "observed_state_counts": state_counts,
        "by_field": by_field,
    }


def to_debug_payload(paper_map: PaperMap, template: PaperTemplate) -> dict[str, Any]:
    diagnostics = diagnose_paper_map(paper_map, template)
    return {
        "paper_map": paper_map.to_dict(),
        "paper_map_quality": paper_map_quality_summary(paper_map, template),
        "diagnostics": [diagnostic.to_dict() for diagnostic in diagnostics],
    }


def write_debug_json(payload: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def explain_reconciled_report(report: ReconciledReport) -> dict[str, Any]:
    """Explain a reconciled report without changing production behavior.

    The explanation is intentionally separate from UI concerns. It shows which
    observed paper cells and meter rides produced adopted values, which meter
    rides remain pending, and which linked adjustments contributed to sales.
    """

    linked_meter_ids = {
        meter_ride_id
        for ride in report.rides
        for meter_ride_id in ride.meter_ride_ids
    }
    pending_meter_rides = [
        ride.to_dict()
        for ride in report.meter_receipt.rides
        if ride.ride_id not in linked_meter_ids
    ]
    linked_adjustments = [
        _explain_adjustment(adjustment)
        for adjustment in report.adjustments
        if adjustment.target_ride_key and adjustment.include_in_sales
    ]
    unlinked_adjustments = [
        _explain_adjustment(adjustment)
        for adjustment in report.adjustments
        if not (adjustment.target_ride_key and adjustment.include_in_sales)
    ]

    return {
        "schema": "kamichizu_report_explanation",
        "sales": _explain_sales(report),
        "rides": [_explain_ride(ride, report.paper_map) for ride in report.rides],
        "pending_meter_rides": pending_meter_rides,
        "adjustments": {
            "linked_sales_adjustments": linked_adjustments,
            "unlinked_or_excluded_adjustments": unlinked_adjustments,
        },
        "diagnostics": [diagnostic.to_dict() for diagnostic in report.diagnostics],
    }


def _explain_sales(report: ReconciledReport) -> dict[str, Any]:
    components = report.sales.to_dict()
    formula_terms = (
        "confirmed_gen",
        "confirmed_mi",
        "pending_meter_sales",
        "discount_claim_total",
        "charter_sales",
    )
    formula_values = {term: components[term] for term in formula_terms}
    component_sum = sum(formula_values.values())
    return {
        "formula": "confirmed_gen + confirmed_mi + pending_meter_sales + discount_claim_total + charter_sales",
        "components": formula_values,
        "total_sales": components["total_sales"],
        "component_sum": component_sum,
        "component_sum_matches_total": component_sum == components["total_sales"],
    }


def _explain_ride(ride: ReconciledRide, paper_map: PaperMap) -> dict[str, Any]:
    row_values = _paper_row_values(ride, paper_map)
    return {
        "ride_key": ride.ride_key,
        "paper_row": row_values["paper_row"],
        "paper_cell_ids": list(ride.paper_cell_ids),
        "meter_ride_ids": list(ride.meter_ride_ids),
        "link_status": ride.link_status.value,
        "display": {
            "no": row_values["no"],
            "passengers": row_values["passengers"],
            "time": row_values["time"],
            "route": row_values["route"],
            "memo": row_values["memo"],
        },
        "observed": {
            "gen": ride.observed_gen,
            "mi": ride.observed_mi,
        },
        "adopted": {
            "total": _explain_adopted_amount(ride.adopted_total),
            "gen": _explain_adopted_amount(ride.adopted_gen),
            "mi": _explain_adopted_amount(ride.adopted_mi),
        },
        "diagnostic_reasons": list(ride.diagnostic_reasons),
    }


def _paper_row_values(ride: ReconciledRide, paper_map: PaperMap) -> dict[str, Any]:
    paper_rows = [
        paper_map.cells[cell_id].paper_row
        for cell_id in ride.paper_cell_ids
        if cell_id in paper_map.cells
    ]
    paper_row = min(paper_rows) if paper_rows else None
    cells = [
        cell
        for cell in paper_map.cells.values()
        if paper_row is not None and cell.paper_row == paper_row and cell.has_observed_value
    ]
    values = {cell.field.value: cell.observed_value for cell in cells}
    return {
        "paper_row": paper_row,
        "no": str(paper_row) if paper_row is not None else "",
        "passengers": values.get("passengers", ""),
        "time": values.get("time", ""),
        "route": values.get("route", ""),
        "memo": values.get("memo", ""),
    }


def _explain_adjustment(adjustment: Adjustment) -> dict[str, Any]:
    return {
        "adjustment_id": adjustment.adjustment_id,
        "kind": adjustment.kind.value,
        "amount": adjustment.amount,
        "target_ride_key": adjustment.target_ride_key,
        "source_cell_ids": list(adjustment.source_cell_ids),
        "include_in_sales": adjustment.include_in_sales,
        "include_in_count": adjustment.include_in_count,
        "include_in_passengers": adjustment.include_in_passengers,
        "evidences": [_explain_evidence(evidence) for evidence in adjustment.evidences],
    }


def _explain_adopted_amount(adopted_amount: AdoptedAmount | None) -> dict[str, Any] | None:
    if adopted_amount is None:
        return None
    return {
        "amount": adopted_amount.amount,
        "source": adopted_amount.source.value,
        "evidences": [_explain_evidence(evidence) for evidence in adopted_amount.evidences],
    }


def _explain_evidence(evidence: Evidence) -> dict[str, Any]:
    return {
        "source": evidence.source,
        "reference": evidence.reference,
        "detail": evidence.detail,
        "confidence": evidence.confidence,
    }

def build_reconciled_report_package(report: ReconciledReport) -> dict[str, Any]:
    """Build the pre-app.py handoff package for UI/debug consumers.

    This function does not recalculate the report. It wraps the existing
    structured explanation and diagnostics Markdown so callers do not need
    to inspect internal dataclasses directly.
    """

    explanation = explain_reconciled_report(report)
    diagnostics_markdown = render_reconciled_report_markdown(report)
    sales = explanation["sales"]
    components = sales["components"]
    return {
        "summary": {
            "confirmed_gen": components["confirmed_gen"],
            "confirmed_mi": components["confirmed_mi"],
            "pending_meter_sales": components["pending_meter_sales"],
            "discount_claim_total": components["discount_claim_total"],
            "sou": sales["total_sales"],
            "formula": _formula_numbers(components, sales["total_sales"]),
        },
        "explanation": explanation,
        "diagnostics_markdown": diagnostics_markdown,
    }


def render_reconciled_report_markdown(report: ReconciledReport) -> str:
    """Render a human-readable explanation for engine diagnostics.

    This remains a diagnostic artifact. It does not decide UI layout and does
    not connect the new engine to production.
    """

    explanation = explain_reconciled_report(report)
    sales = explanation["sales"]
    components = sales["components"]
    formula_numbers = _formula_numbers(components, sales["total_sales"])
    lines = [
        "# 神地図エンジン 診断レポート",
        "",
        "## 売上成分",
        f"- confirmed_gen: {_yen(components['confirmed_gen'])}",
        f"- confirmed_mi: {_yen(components['confirmed_mi'])}",
        f"- pending_meter_sales: {_yen(components['pending_meter_sales'])}",
        f"- discount_claim_total: {_yen(components['discount_claim_total'])}",
        f"- charter_sales: {_yen(components['charter_sales'])}",
        f"- sou: {_yen(sales['total_sales'])}",
        f"- 計算式: {formula_numbers}",
        "",
        "## 採用根拠",
    ]

    if explanation["rides"]:
        for ride in explanation["rides"]:
            lines.extend(_render_ride_markdown(ride))
    else:
        lines.append("- 採用済み乗車はありません。")

    lines.extend(["", "## 確認待ちメーター明細"])
    if explanation["pending_meter_rides"]:
        for ride in explanation["pending_meter_rides"]:
            time_text = f" / {ride['time']}" if ride.get("time") else ""
            lines.append(f"- {ride['ride_id']}: {_yen(ride['amount'])}{time_text}")
    else:
        lines.append("- ありません。")

    lines.extend(["", "## 障割・特例請求"])
    linked = explanation["adjustments"]["linked_sales_adjustments"]
    unlinked = explanation["adjustments"]["unlinked_or_excluded_adjustments"]
    if linked:
        for adjustment in linked:
            detail = _evidence_details(adjustment["evidences"])
            detail_text = f" / 根拠 {detail}" if detail else ""
            lines.append(
                f"- {adjustment['adjustment_id']}: {_yen(adjustment['amount'])}"
                f" / 対象 {adjustment['target_ride_key']}"
                f" / 元セル {', '.join(adjustment['source_cell_ids'])}"
                f"{detail_text}"
            )
    else:
        lines.append("- 売上に入る請求はありません。")

    if unlinked:
        lines.append("")
        lines.append("## 未リンク・未採用")
        for adjustment in unlinked:
            lines.append(
                f"- {adjustment['adjustment_id']}: {_yen(adjustment['amount'])}"
                f" / {adjustment['kind']} / 売上未採用"
            )

    if explanation["diagnostics"]:
        lines.extend(["", "## 診断"])
        for diagnostic in explanation["diagnostics"]:
            refs = ", ".join(diagnostic.get("references") or [])
            suffix = f" / {refs}" if refs else ""
            lines.append(f"- {diagnostic['severity']}: {diagnostic['code']}{suffix}")

    return "\n".join(lines) + "\n"


def _render_ride_markdown(ride: dict[str, Any]) -> list[str]:
    adopted = ride["adopted"]
    parts = []
    for label, key in (("総額", "total"), ("現収", "gen"), ("未収", "mi")):
        amount = adopted.get(key)
        if amount is None:
            continue
        refs = ", ".join(
            f"{evidence['source']}:{evidence['reference']}"
            for evidence in amount["evidences"]
        )
        parts.append(f"{label} {_yen(amount['amount'])} ({amount['source']}: {refs})")
    adopted_text = " / ".join(parts) if parts else "採用金額なし"
    return [
        f"- {ride['ride_key']}: {adopted_text}",
        f"  - 紙セル: {', '.join(ride['paper_cell_ids'])}",
        f"  - メーター: {', '.join(ride['meter_ride_ids'])}",
    ]


def _formula_numbers(components: dict[str, int], total_sales: int) -> str:
    terms = [
        components["confirmed_gen"],
        components["confirmed_mi"],
        components["pending_meter_sales"],
        components["discount_claim_total"],
        components["charter_sales"],
    ]
    visible_terms = [amount for amount in terms if amount != 0]
    return " + ".join(f"{amount:,}" for amount in visible_terms) + f" = {total_sales:,}"


def _evidence_details(evidences: list[dict[str, Any]]) -> str:
    details = [evidence["detail"] for evidence in evidences if evidence.get("detail")]
    return "; ".join(details)


def _yen(amount: int | None) -> str:
    if amount is None:
        return "-"
    return f"¥{amount:,}"
