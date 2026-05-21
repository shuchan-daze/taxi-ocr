"""UI adapter boundary.

UI rows are allowed only as a derived view. They must never become the source
of paper addresses or reconciliation truth.
"""

from __future__ import annotations

from typing import Any

from .models import ReconciledReport


def derive_display_model(report: ReconciledReport) -> dict[str, Any]:
    """Return a minimal display model without leaking debug internals."""

    return {
        "sales": report.sales.to_dict(),
        "rides": [ride.to_dict() for ride in report.rides],
        "adjustments": [adjustment.to_dict() for adjustment in report.adjustments],
    }

