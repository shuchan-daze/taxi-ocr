import json
from pathlib import Path

"""Compatibility-free debug helpers for the new engine."""

from .diagnostics import build_reconciled_report_package, diagnose_paper_map, explain_reconciled_report, paper_map_quality_summary, render_reconciled_report_markdown, to_debug_payload, write_debug_json

__all__ = [
    "build_reconciled_report_package",
    "diagnose_paper_map",
    "explain_reconciled_report",
    "paper_map_quality_summary",
    "render_reconciled_report_markdown",
    "to_debug_payload",
    "write_debug_json",
    "write_reconciled_report_package",
]

def write_reconciled_report_package(report, output_dir):
    """Write the pre-app.py report package for standalone debug use.

    The report is not recalculated here. This only serializes the safe
    handoff package and the human-readable diagnostics Markdown.
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    package = build_reconciled_report_package(report)
    json_path = output_path / "reconciled_report_package.json"
    markdown_path = output_path / "reconciled_report_diagnostics.md"
    json_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(package["diagnostics_markdown"], encoding="utf-8")
    return {
        "json": json_path,
        "markdown": markdown_path,
    }
