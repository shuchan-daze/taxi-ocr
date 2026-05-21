import pytest

from kamichizu_engine.app_inputs import (
    AppInputError,
    build_paper_map_from_payload,
    build_reconciled_report_from_app_inputs,
)


def _paper_payload(**extra):
    payload = {
        "schema": "paper_map",
        "cells": {
            "R01_GEN": {
                "raw": "900",
                "value": 900,
                "observed_state": "observed",
            },
            "R02_MI": {
                "raw": "2,300",
                "value": 2300,
                "observed_state": "observed",
            },
        },
    }
    payload.update(extra)
    return payload


def _meter_data(**extra):
    payload = {
        "rows": [
            {"no": 1, "time": "09:46", "amount": 900},
            {"no": 2, "time": "11:08", "amount": 2300},
            {"no": 3, "time": "14:06", "amount": 1300},
        ]
    }
    payload.update(extra)
    return payload


def test_build_paper_map_from_payload_uses_cell_ids_as_addresses():
    paper_map = build_paper_map_from_payload(_paper_payload())

    assert paper_map.cell("R01_GEN").observed_value == 900
    assert paper_map.cell("R02_MI").observed_value == 2300
    assert paper_map.cell("R01_MI").observed_state.value == "missing"


def test_build_reconciled_report_from_app_inputs_uses_observed_materials_not_totals():
    report = build_reconciled_report_from_app_inputs(
        _paper_payload(total=999999, ignored_summary={"sou": 999999}),
        _meter_data(total=999999),
    )

    assert report.sales.confirmed_gen == 900
    assert report.sales.confirmed_mi == 2300
    assert report.sales.pending_meter_sales == 1300
    assert report.sales.total_sales == 4500
    assert [ride.ride_key for ride in report.rides] == ["R01", "R02"]


def test_app_inputs_reject_missing_paper_cells():
    with pytest.raises(AppInputError, match="paper_map.cells is required"):
        build_reconciled_report_from_app_inputs({"schema": "paper_map"}, _meter_data())


def test_app_inputs_reject_empty_paper_cells():
    with pytest.raises(AppInputError, match="paper_map.cells must not be empty"):
        build_reconciled_report_from_app_inputs({"schema": "paper_map", "cells": {}}, _meter_data())


def test_app_inputs_reject_row_list_paper_map_without_cells():
    payload = {"schema": "paper_map"}
    payload["rows"] = []

    with pytest.raises(AppInputError, match="row-list paper map form is not accepted"):
        build_reconciled_report_from_app_inputs(payload, _meter_data())


def test_app_inputs_reject_missing_meter_data():
    with pytest.raises(AppInputError, match="meter_data is required"):
        build_reconciled_report_from_app_inputs(_paper_payload(), None)


def test_app_inputs_reject_missing_meter_rows():
    with pytest.raises(AppInputError, match="meter_data.rows is required"):
        build_reconciled_report_from_app_inputs(_paper_payload(), {"total": 999999})


def test_app_inputs_reject_empty_meter_rows():
    with pytest.raises(AppInputError, match="meter_data.rows must not be empty"):
        build_reconciled_report_from_app_inputs(_paper_payload(), {"rows": []})
