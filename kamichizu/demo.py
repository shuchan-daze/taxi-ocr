"""Small demo case for the minimal UI."""

from __future__ import annotations

from .case import build_human_report_from_case
from .models import HumanReport


def build_demo_case() -> dict[str, object]:
    """Return a tiny formal case input."""

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
        "claims": [
            {
                "type": "public_discount_claim",
                "target_row_addr": "01",
                "meter_amount": 2430,
                "expected_claim_amount": 270,
            },
            {
                "type": "charter_sale",
                "target_row_addr": "02",
                "amount": 16400,
                "payment_kind": "gen",
            },
        ],
        "view": {
            "view_id": "daiichi_taxi_minimal",
            "columns": [
                ["no", "No"],
                ["passengers", "人数"],
                ["time", "時刻"],
                ["gen", "現収"],
                ["mi", "未収"],
                ["memo", "摘要"],
                ["status", "状態"],
            ],
        },
    }


def build_demo_human_report() -> HumanReport:
    """Build a tiny report through the single formal case input."""

    return build_human_report_from_case(build_demo_case())
