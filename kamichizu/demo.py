"""Demo HumanReport builders for the minimal UI."""

from __future__ import annotations

from .models import AdoptedReport, AdoptedRow, HumanReport, ViewMap
from .specials import make_charter_claim, make_public_discount_claim
from .view import build_human_report


def build_demo_human_report() -> HumanReport:
    """Build a tiny report for UI shape verification."""

    report = AdoptedReport(
        rows=(
            AdoptedRow(row_addr="01", values={"no": 1, "passengers": 2, "time": "10:44", "gen": None, "mi": 2430, "memo": ""}),
            AdoptedRow(row_addr="02", values={"no": 2, "passengers": 1, "time": "13:40", "gen": None, "mi": None, "memo": "貸切"}),
        ),
        claims=(
            make_public_discount_claim(target_row_addr="01", meter_amount=2430, expected_claim_amount=270),
            make_charter_claim(target_row_addr="02", amount=16400, payment_kind="gen"),
        ),
        diagnostics=("紙日報の金額と明細金額が違う場合は、明細金額を採用します。",),
    )
    view_map = ViewMap(
        view_id="daiichi_taxi_minimal",
        columns=(
            ("no", "No"),
            ("passengers", "人数"),
            ("time", "時刻"),
            ("gen", "現収"),
            ("mi", "未収"),
            ("memo", "摘要"),
            ("status", "状態"),
        ),
    )
    return build_human_report(report, view_map)
