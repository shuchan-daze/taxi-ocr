"""Demo source-map builders for the minimal UI."""

from __future__ import annotations

from .models import Cell, FormatMap, HumanReport, SourceMap, SourceMeta, ViewMap
from .pipeline import build_human_report_from_sources
from .specials import make_charter_claim, make_public_discount_claim


def _source(source_id: str, source_role: str, source_type: str, format_id: str, cells: dict[str, object]) -> SourceMap:
    return SourceMap(
        meta=SourceMeta(
            source_id=source_id,
            source_role=source_role,
            source_type=source_type,
            label=source_type,
            format_id=format_id,
        ),
        cells={cell_id: Cell(local_cell_id=cell_id, raw=str(value), value=value) for cell_id, value in cells.items()},
    )


def build_demo_human_report() -> HumanReport:
    """Build a tiny report through the formal source-map route."""

    paper = _source(
        "P01",
        "primary",
        "daily_report",
        "daily_minimal",
        {
            "01_AA": 1,
            "01_AB": 2,
            "01_AD": "10:44",
            "01_AF": 2400,
            "02_AA": 2,
            "02_AB": 1,
            "02_AD": "13:40",
            "02_AG": "貸切",
        },
    )
    paper_format = FormatMap(
        format_id="daily_minimal",
        columns={
            "AA": "no",
            "AB": "passengers",
            "AD": "time",
            "AE": "gen",
            "AF": "mi",
            "AG": "memo",
        },
    )
    meter = _source(
        "E01",
        "evidence",
        "meter_receipt",
        "meter_minimal",
        {
            "01_AA": "10:44",
            "01_AB": 2430,
        },
    )
    meter_format = FormatMap(format_id="meter_minimal", columns={"AA": "time", "AB": "amount"})
    discount_claim = make_public_discount_claim(target_row_addr="01", meter_amount=2430, expected_claim_amount=270)
    claims = (
        *(claim for claim in (discount_claim,) if claim is not None),
        make_charter_claim(target_row_addr="02", amount=16400, payment_kind="gen"),
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
    return build_human_report_from_sources(
        paper=paper,
        paper_format=paper_format,
        evidences=[(meter, meter_format)],
        claims=claims,
        view_map=view_map,
    )
