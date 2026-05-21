"""Formal case input for the Kamichizu engine."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import Cell, Claim, EvidenceLink, FormatMap, HumanReport, SourceMap, SourceMeta, ViewMap
from .pipeline import build_human_report_from_sources
from .specials import make_charter_claim, make_public_discount_claim


def _require_mapping(data: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise ValueError(f"{name} must be an object")
    return data


def _require_list(data: Any, name: str) -> list[Any]:
    if not isinstance(data, list):
        raise ValueError(f"{name} must be a list")
    return data


def _required(data: Mapping[str, Any], key: str, name: str) -> Any:
    if key not in data:
        raise ValueError(f"{name}.{key} is required")
    return data[key]


def _source_map(data: Mapping[str, Any], name: str) -> SourceMap:
    cells_data = _require_mapping(_required(data, "cells", name), f"{name}.cells")
    cells: dict[str, Cell] = {}
    for cell_id, cell_data in cells_data.items():
        cell_obj = _require_mapping(cell_data, f"{name}.cells.{cell_id}")
        cells[str(cell_id)] = Cell(
            local_cell_id=str(cell_id),
            raw=str(cell_obj.get("raw", "")),
            value=cell_obj.get("value"),
            confidence=cell_obj.get("confidence"),
            state=str(cell_obj.get("state", "observed")),
            bbox=cell_obj.get("bbox"),
        )
    return SourceMap(
        meta=SourceMeta(
            source_id=str(_required(data, "source_id", name)),
            source_role=str(_required(data, "source_role", name)),
            source_type=str(_required(data, "source_type", name)),
            label=str(data.get("label", data.get("source_type", ""))),
            format_id=str(_required(data, "format_id", name)),
        ),
        cells=cells,
    )


def _format_map(data: Mapping[str, Any], name: str) -> FormatMap:
    return FormatMap(
        format_id=str(_required(data, "format_id", name)),
        columns=_require_mapping(_required(data, "columns", name), f"{name}.columns"),
    )


def _view_map(data: Mapping[str, Any]) -> ViewMap:
    columns = []
    for index, item in enumerate(_require_list(_required(data, "columns", "view"), "view.columns")):
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError(f"view.columns[{index}] must be [field, label]")
        columns.append((str(item[0]), str(item[1])))
    return ViewMap(view_id=str(_required(data, "view_id", "view")), columns=tuple(columns))


def _evidence_links(items: list[Any], name: str) -> tuple[EvidenceLink, ...]:
    links: list[EvidenceLink] = []
    for index, item in enumerate(items):
        link_data = _require_mapping(item, f"{name}.evidence[{index}]")
        links.append(
            EvidenceLink(
                paper_cell=str(_required(link_data, "paper_cell", f"{name}.evidence[{index}]")),
                evidence_cell=str(_required(link_data, "evidence_cell", f"{name}.evidence[{index}]")),
                reason=str(_required(link_data, "reason", f"{name}.evidence[{index}]")),
            )
        )
    return tuple(links)


def _claims(items: list[Any]) -> tuple[Claim, ...]:
    claims: list[Claim] = []
    for index, item in enumerate(items):
        claim_data = _require_mapping(item, f"claims[{index}]")
        claim_type = str(_required(claim_data, "type", f"claims[{index}]"))
        if claim_type == "public_discount_claim":
            evidence = _evidence_links(
                _require_list(_required(claim_data, "evidence", f"claims[{index}]"), f"claims[{index}].evidence"),
                f"claims[{index}]",
            )
            claim = make_public_discount_claim(
                target_row_addr=str(_required(claim_data, "target_row_addr", f"claims[{index}]")),
                target_global_cell_id=str(_required(claim_data, "target_global_cell_id", f"claims[{index}]")),
                meter_amount=int(_required(claim_data, "meter_amount", f"claims[{index}]")),
                expected_claim_amount=(
                    int(claim_data["expected_claim_amount"]) if "expected_claim_amount" in claim_data else None
                ),
                evidence=evidence,
            )
            if claim is None:
                raise ValueError(f"claims[{index}] public discount is ambiguous or invalid")
            claims.append(claim)
        elif claim_type == "charter_sale":
            evidence = _evidence_links(
                _require_list(_required(claim_data, "evidence", f"claims[{index}]"), f"claims[{index}].evidence"),
                f"claims[{index}]",
            )
            claims.append(
                make_charter_claim(
                    target_row_addr=str(_required(claim_data, "target_row_addr", f"claims[{index}]")),
                    target_global_cell_id=str(_required(claim_data, "target_global_cell_id", f"claims[{index}]")),
                    claim_amount=int(_required(claim_data, "claim_amount", f"claims[{index}]")),
                    payment_kind=str(_required(claim_data, "payment_kind", f"claims[{index}]")),
                    evidence=evidence,
                )
            )
        else:
            raise ValueError(f"claims[{index}].type is unknown: {claim_type}")
    return tuple(claims)


def build_human_report_from_case(case_data: Mapping[str, Any]) -> HumanReport:
    """Build a HumanReport from the single formal app input contract."""

    data = _require_mapping(case_data, "case")
    paper = _source_map(_require_mapping(_required(data, "paper", "case"), "case.paper"), "paper")
    paper_format = _format_map(
        _require_mapping(_required(data, "paper_format", "case"), "case.paper_format"),
        "paper_format",
    )
    evidences = []
    for index, evidence_data in enumerate(_require_list(_required(data, "evidences", "case"), "case.evidences")):
        evidence = _require_mapping(evidence_data, f"evidences[{index}]")
        source = _source_map(_require_mapping(_required(evidence, "source", f"evidences[{index}]"), "source"), "source")
        format_map = _format_map(
            _require_mapping(_required(evidence, "format", f"evidences[{index}]"), "format"),
            "format",
        )
        evidences.append((source, format_map))
    view_map = _view_map(_require_mapping(_required(data, "view", "case"), "case.view"))
    claims = _claims(_require_list(data.get("claims", []), "case.claims"))
    return build_human_report_from_sources(
        paper=paper,
        paper_format=paper_format,
        evidences=evidences,
        claims=claims,
        view_map=view_map,
    )
