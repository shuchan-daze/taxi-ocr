from pathlib import Path

import pytest

from kamichizu_engine.anthropic_ocr import (
    AnthropicOcrError,
    normalize_meter_ocr_response,
    normalize_paper_ocr_response,
)


def test_normalize_paper_ocr_response_builds_cells_mapping():
    payload = {
        "schema": "paper_observations",
        "cells": [
            {
                "cell_id": "R03_MI",
                "raw": "2,430円",
                "value": "2,430円",
                "confidence": 0.9,
                "ambiguous": False,
                "observed_state": "observed",
                "notes": "",
            },
            {
                "cell_id": "R03_MEMO",
                "raw": "障割",
                "value": "障割",
                "confidence": 0.8,
                "ambiguous": False,
                "observed_state": "observed",
                "notes": "",
            },
        ],
    }

    normalized = normalize_paper_ocr_response(payload)

    assert normalized == {
        "schema": "paper_map",
        "cells": {
            "R03_MI": {
                "raw": "2,430円",
                "value": 2430,
                "confidence": 0.9,
                "ambiguous": False,
                "observed_state": "observed",
                "notes": "",
            },
            "R03_MEMO": {
                "raw": "障割",
                "value": "障割",
                "confidence": 0.8,
                "ambiguous": False,
                "observed_state": "observed",
                "notes": "",
            },
        },
    }


def test_normalize_paper_ocr_response_rejects_empty_cells():
    with pytest.raises(AnthropicOcrError, match="no usable cells"):
        normalize_paper_ocr_response({"schema": "paper_observations", "cells": []})


def test_normalize_paper_ocr_response_requires_top_level_cells():
    with pytest.raises(AnthropicOcrError, match="top-level cells"):
        normalize_paper_ocr_response({"schema": "paper_observations", "paper_map": {"cells": []}})


def test_normalize_paper_ocr_response_rejects_cells_alias_rows():
    with pytest.raises(AnthropicOcrError, match="top-level cells"):
        normalize_paper_ocr_response({"schema": "paper_observations", "rows": []})


def test_normalize_paper_ocr_response_rejects_non_list_cells():
    with pytest.raises(AnthropicOcrError, match="cells must be a list"):
        normalize_paper_ocr_response({"schema": "paper_observations", "cells": {"R03_MI": {}}})


def test_normalize_meter_ocr_response_builds_meter_rows():
    payload = {
        "schema": "meter_rows",
        "rows": [
            {"ride_id": "M01", "time": "10:44", "amount": "2,630円", "payment_hint": None, "raw": "10:44 2630"},
            {"ride_id": "", "time": "13:40", "amount": "16,400", "payment_hint": "貸切", "raw": "13:40 16400"},
        ],
    }

    normalized = normalize_meter_ocr_response(payload)

    assert normalized == {
        "schema": "meter_data",
        "rows": [
            {"ride_id": "M01", "time": "10:44", "amount": 2630, "payment_hint": None, "raw": "10:44 2630"},
            {"ride_id": "M02", "time": "13:40", "amount": 16400, "payment_hint": "貸切", "raw": "13:40 16400"},
        ],
    }


def test_normalize_meter_ocr_response_rejects_nested_meter_data_rows():
    payload = {
        "schema": "meter_data",
        "meter_data": {
            "rows": [
                {"ride_id": "M01", "time": "10:44", "amount": "2,630円", "payment_hint": None, "raw": "10:44 2630"},
            ]
        },
    }

    with pytest.raises(AnthropicOcrError, match="top-level rows"):
        normalize_meter_ocr_response(payload)


def test_normalize_meter_ocr_response_rejects_meter_rows_alias():
    with pytest.raises(AnthropicOcrError, match="top-level rows"):
        normalize_meter_ocr_response(
            {
                "schema": "meter_data",
                "meter_rows": [
                    {
                        "ride_id": "M01",
                        "time": "10:44",
                        "amount": "2,630円",
                        "payment_hint": None,
                        "raw": "10:44 2630",
                    }
                ],
            }
        )


def test_normalize_meter_ocr_response_rejects_empty_rows():
    with pytest.raises(AnthropicOcrError, match="no usable rows"):
        normalize_meter_ocr_response({"schema": "meter_rows", "rows": [{"amount": "not amount"}]})


def test_normalize_meter_ocr_response_rejects_non_list_rows():
    with pytest.raises(AnthropicOcrError, match="rows must be a list"):
        normalize_meter_ocr_response({"schema": "meter_data", "rows": {"M01": {"amount": 900}}})


def test_normalize_meter_ocr_response_reports_missing_rows_keys():
    with pytest.raises(AnthropicOcrError, match="top-level rows"):
        normalize_meter_ocr_response({"schema": "meter_data", "items": []})


def test_anthropic_ocr_does_not_hardcode_api_keys():
    source = Path("kamichizu_engine/anthropic_ocr.py").read_text(encoding="utf-8")

    assert "sk-ant-" not in source
    assert "sk-proj-" not in source
