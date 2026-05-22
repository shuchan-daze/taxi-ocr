"""Observation input adapter for the Kamichizu engine."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import Cell, FormatMap, HumanReport, SourceMap, SourceMeta, ViewMap
from .pipeline import build_human_report_from_sources


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


def _reject_keys(data: Mapping[str, Any], forbidden: tuple[str, ...], name: str) -> None:
    for key in forbidden:
        if key in data:
            raise ValueError(f"{name}.{key} is not part of the observation input contract")


def source_map_from_observation(data: Mapping[str, Any], name: str) -> SourceMap:
    """Build a SourceMap from physical-cell observations."""

    _reject_keys(data, ("rows",), name)
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
            marks=tuple(cell_obj.get("marks", ())),
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


def format_map_from_observation(data: Mapping[str, Any], name: str) -> FormatMap:
    """Build a FormatMap from a physical-column meaning map."""

    return FormatMap(
        format_id=str(_required(data, "format_id", name)),
        columns=_require_mapping(_required(data, "columns", name), f"{name}.columns"),
    )


def build_human_report_from_observations(observation_data: Mapping[str, Any], view_map: ViewMap) -> HumanReport:
    """Build HumanReport from observations only.

    This adapter accepts paper/evidence source observations and format maps.  It
    does not accept claims, view definitions, summaries, adopted rows, or totals.
    """

    data = _require_mapping(observation_data, "observation")
    _reject_keys(data, ("claims", "view", "summary", "adopted", "rows"), "observation")
    paper = source_map_from_observation(_require_mapping(_required(data, "paper", "observation"), "paper"), "paper")
    paper_format = format_map_from_observation(
        _require_mapping(_required(data, "paper_format", "observation"), "paper_format"),
        "paper_format",
    )
    evidences = []
    for index, evidence_data in enumerate(_require_list(_required(data, "evidences", "observation"), "observation.evidences")):
        evidence = _require_mapping(evidence_data, f"evidences[{index}]")
        source = source_map_from_observation(
            _require_mapping(_required(evidence, "source", f"evidences[{index}]"), "source"),
            "source",
        )
        format_map = format_map_from_observation(
            _require_mapping(_required(evidence, "format", f"evidences[{index}]"), "format"),
            "format",
        )
        evidences.append((source, format_map))
    return build_human_report_from_sources(
        paper=paper,
        paper_format=paper_format,
        evidences=evidences,
        view_map=view_map,
    )
