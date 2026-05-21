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
