"""Meter receipt structures for Layer 2 input."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .models import Diagnostic, DiagnosticSeverity, MeterReceipt, MeterRide


def build_meter_receipt(
    image_id: str,
    rides: Iterable[MeterRide],
    schema: str = "meter_receipt",
) -> MeterReceipt:
    return MeterReceipt(schema=schema, image_id=image_id, rides=tuple(rides))


def meter_ride_from_mapping(sequence_no: int, data: Mapping[str, Any]) -> MeterRide:
    amount = data.get("amount")
    if amount is None:
        amount = data.get("meter_amount")
    if amount is None:
        raise ValueError("meter ride amount is required")

    ride_id = str(data.get("ride_id") or f"M{sequence_no:02d}")
    return MeterRide(
        ride_id=ride_id,
        sequence_no=sequence_no,
        time=data.get("time"),
        amount=int(amount),
        payment_hint=data.get("payment_hint") or data.get("payment"),
        raw=dict(data),
    )


def build_meter_receipt_from_mappings(
    image_id: str,
    rows: Iterable[Mapping[str, Any]],
    schema: str = "meter_receipt",
) -> MeterReceipt:
    rides = tuple(
        meter_ride_from_mapping(index, row)
        for index, row in enumerate(rows, start=1)
    )
    diagnostics: tuple[Diagnostic, ...] = ()
    if not rides:
        diagnostics = (
            Diagnostic(
                code="meter_receipt_empty",
                message="meter receipt contains no rides",
                severity=DiagnosticSeverity.WARNING,
            ),
        )
    return MeterReceipt(schema=schema, image_id=image_id, rides=rides, diagnostics=diagnostics)

