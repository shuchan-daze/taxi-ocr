"""Small source-map demo for the minimal UI."""

from __future__ import annotations

from .input import build_human_report_from_observations
from .models import Cell, EvidenceLink, FormatMap, HumanReport, SourceMap, SourceMeta, ViewMap
from .pipeline import build_human_report_from_sources
from .specials import make_charter_claim, make_public_discount_claim


def build_demo_observations() -> dict[str, object]:
    """Return tiny source observations for screen smoke checks."""

    return {
        "paper": {
            "source_id": "P01",
            "source_role": "primary",
            "source_type": "daily_report",
            "label": "daily_report",
            "format_id": "daily_minimal",
            "cells": {
                "01_AA": {"raw": "1", "value": 1},
                "01_AB": {"raw": "2", "value": 2},
                "01_AD": {"raw": "10:44", "value": "10:44"},
                "01_AF": {"raw": "2400", "value": 2400},
                "02_AA": {"raw": "2", "value": 2},
                "02_AB": {"raw": "1", "value": 1},
                "02_AD": {"raw": "13:40", "value": "13:40"},
                "02_AG": {"raw": "貸切", "value": "貸切"},
            },
        },
        "paper_format": {
            "format_id": "daily_minimal",
            "columns": {
                "AA": "no",
                "AB": "passengers",
                "AD": "time",
                "AE": "gen",
                "AF": "mi",
                "AG": "memo",
            },
        },
        "evidences": [
            {
                "source": {
                    "source_id": "E01",
                    "source_role": "evidence",
                    "source_type": "meter_receipt",
                    "label": "meter_receipt",
                    "format_id": "meter_minimal",
                    "cells": {
                        "01_AA": {"raw": "10:44", "value": "10:44"},
                        "01_AB": {"raw": "2430", "value": 2430},
                    },
                },
                "format": {
                    "format_id": "meter_minimal",
                    "columns": {
                        "AA": "time",
                        "AB": "amount",
                    },
                },
            }
        ],
    }


def build_demo_view() -> ViewMap:
    return ViewMap(
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


def _source_meta(source_id: str, role: str, source_type: str, format_id: str) -> SourceMeta:
    return SourceMeta(
        source_id=source_id,
        source_role=role,
        source_type=source_type,
        label=source_type,
        format_id=format_id,
    )


def _cell(local_cell_id: str, value: object, raw: str | None = None) -> Cell:
    return Cell(local_cell_id=local_cell_id, raw=str(value) if raw is None else raw, value=value)


def build_demo_sources() -> tuple[SourceMap, FormatMap, list[tuple[SourceMap, FormatMap]]]:
    """Build physical source maps used by the UI smoke report."""

    paper = SourceMap(
        meta=_source_meta("P01", "primary", "daily_report", "daily_minimal"),
        cells={
            "01_AA": _cell("01_AA", 1),
            "01_AB": _cell("01_AB", 2),
            "01_AD": _cell("01_AD", "10:10"),
            "01_AE": _cell("01_AE", 900),
            "02_AA": _cell("02_AA", 2),
            "02_AB": _cell("02_AB", 2),
            "02_AD": _cell("02_AD", "10:44"),
            "02_AF": _cell("02_AF", 2400),
            "02_AG": _cell("02_AG", "Uber"),
            "03_AH": _cell("03_AH", 270),
            "04_AA": _cell("04_AA", 4),
            "04_AB": _cell("04_AB", 4),
            "04_AD": _cell("04_AD", "13:40"),
            "04_AG": _cell("04_AG", "貸切"),
            "04_AH": _cell("04_AH", 16400),
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
    meter = SourceMap(
        meta=_source_meta("E01", "evidence", "meter_receipt", "meter_minimal"),
        cells={
            "01_AA": _cell("01_AA", "10:10"),
            "01_AB": _cell("01_AB", 900),
            "02_AA": _cell("02_AA", "10:46"),
            "02_AB": _cell("02_AB", 2430),
        },
    )
    meter_format = FormatMap(format_id="meter_minimal", columns={"AA": "time", "AB": "amount"})
    return paper, paper_format, [(meter, meter_format)]


def build_demo_claims() -> tuple:
    """Build Layer 3 claims without hand-building an adopted report."""

    discount = make_public_discount_claim(
        target_row_addr="02",
        target_global_cell_id="P01:02_AF",
        meter_amount=2430,
        expected_claim_amount=270,
        evidence=(EvidenceLink("P01:03_AH", "E01:02_AB", "public_discount_from_meter_amount"),),
    )
    charter = make_charter_claim(
        target_row_addr="04",
        target_global_cell_id="P01:04_AH",
        claim_amount=16400,
        payment_kind="gen",
        evidence=(EvidenceLink("P01:04_AH", "P01:04_AH", "charter_from_paper_special_cell"),),
    )
    return tuple(claim for claim in (discount, charter) if claim is not None)


def build_demo_human_report() -> HumanReport:
    """Build a tiny report through the formal source-map pipeline."""

    paper, paper_format, evidences = build_demo_sources()
    return build_human_report_from_sources(
        paper=paper,
        paper_format=paper_format,
        evidences=evidences,
        claims=build_demo_claims(),
        view_map=build_demo_view(),
    )
