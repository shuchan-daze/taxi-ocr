"""Human-facing view building."""

from __future__ import annotations

from typing import Any

from .models import AdoptedReport, HumanReport, ViewMap
from .totals import SalesTotals, compute_sales_totals


def build_human_rows(report: AdoptedReport, view_map: ViewMap) -> list[dict[str, Any]]:
    """Build rows for human display from an adopted report and a view map."""

    output: list[dict[str, Any]] = []
    for row in report.rows:
        item: dict[str, Any] = {}
        for field_name, label in view_map.columns:
            if field_name == "status":
                item[label] = "要確認" if row.alerts else ""
            else:
                item[label] = row.values.get(field_name)
        output.append(item)
    return output


def build_claim_rows(report: AdoptedReport) -> list[dict[str, Any]]:
    """Build human-facing rows for special claims.

    Claims are shown separately from ride body sales.  This keeps disability
    discount claims and future special charges visible without mixing them into
    gen/mi body columns.
    """

    rows: list[dict[str, Any]] = []
    labels = {
        "public_discount_claim": "障割請求",
        "charter_sale": "貸切",
    }
    payment_labels = {
        "gen": "現収",
        "mi": "未収",
    }
    for claim in report.claims:
        rows.append(
            {
                "種別": labels.get(claim.claim_type, claim.claim_type),
                "対象行": claim.target_row_addr,
                "区分": payment_labels.get(claim.payment_kind, ""),
                "金額": claim.amount,
                "根拠": " / ".join(f"{link.paper_cell} ← {link.evidence_cell}" for link in claim.evidence),
            }
        )
    return rows


def build_summary_rows(report: AdoptedReport, totals: SalesTotals | None = None) -> list[dict[str, Any]]:
    """Build human-facing summary rows.

    This is display data, not engine calculation.  It keeps ride body sales and
    special claims visible so UI code does not have to know internal structures.
    """

    active_totals = totals or compute_sales_totals(report)
    return [
        {"項目": "現収", "金額": active_totals.gen, "内訳": f"通常 {active_totals.ride_gen} + 特例 {active_totals.claim_gen}"},
        {"項目": "未収", "金額": active_totals.mi, "内訳": f"通常 {active_totals.ride_mi} + 特例 {active_totals.claim_mi}"},
        {"項目": "特例請求", "金額": active_totals.claim_other, "内訳": "障割請求など"},
        {"項目": "総売上", "金額": active_totals.sou, "内訳": "現収 + 未収 + 特例請求"},
    ]


def build_human_report(report: AdoptedReport, view_map: ViewMap) -> HumanReport:
    """Build the complete human-facing report package for UI layers."""

    return HumanReport(
        summary_rows=tuple(build_summary_rows(report)),
        ride_rows=tuple(build_human_rows(report, view_map)),
        claim_rows=tuple(build_claim_rows(report)),
        diagnostics=report.diagnostics,
    )
