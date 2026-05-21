"""Human-facing view building."""

from __future__ import annotations

from typing import Any

from .models import AdoptedReport, ViewMap


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
