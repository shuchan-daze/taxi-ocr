"""Layer 2 reconciliation shell.

This module does not use old row states as source concepts. It keeps observed
paper values separate from adopted values and leaves special cases to rules.
"""

from __future__ import annotations

from .config import FareConfig
from .models import (
    AdoptedAmount,
    AmountSource,
    Diagnostic,
    DiagnosticSeverity,
    Evidence,
    FieldName,
    LinkStatus,
    MeterReceipt,
    MeterRide,
    PaperMap,
    PaperCell,
    PaperTemplate,
    ReconciledReport,
    ReconciledRide,
    SalesComponents,
)


AMOUNT_FIELDS = (FieldName.GEN, FieldName.MI)


def validate_reconciliation_inputs(
    paper_map: PaperMap,
    meter_receipt: MeterReceipt,
    template: PaperTemplate,
) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []

    missing_cell_ids = paper_map.missing_cell_ids(template)
    if missing_cell_ids:
        diagnostics.append(
            Diagnostic(
                code="paper_map_missing_fixed_cells",
                message="paper map is missing fixed cell addresses",
                severity=DiagnosticSeverity.ERROR,
                references=missing_cell_ids,
            )
        )

    if not meter_receipt.rides:
        diagnostics.append(
            Diagnostic(
                code="meter_receipt_empty",
                message="meter receipt contains no rides",
                severity=DiagnosticSeverity.WARNING,
            )
        )

    return tuple(diagnostics)


def build_reconciliation_shell(
    paper_map: PaperMap,
    meter_receipt: MeterReceipt,
    template: PaperTemplate,
    fare_config: FareConfig | None = None,
) -> ReconciledReport:
    """Create a report shell without connecting old production logic.

    The shell is useful for debug/shadow work and for proving that the new
    engine can carry its contracts before real matching is added.
    """

    config = fare_config or FareConfig()
    config.validate()
    diagnostics = list(validate_reconciliation_inputs(paper_map, meter_receipt, template))
    diagnostics.append(
        Diagnostic(
            code="reconciliation_not_implemented",
            message="Layer 2 matching is intentionally not connected yet",
            severity=DiagnosticSeverity.INFO,
        )
    )
    return ReconciledReport(
        schema="reconciled_report",
        paper_map=paper_map,
        meter_receipt=meter_receipt,
        sales=SalesComponents(),
        diagnostics=tuple(diagnostics),
    )


def _amount_cells_by_row(paper_map: PaperMap) -> dict[int, list[PaperCell]]:
    by_row: dict[int, list[PaperCell]] = {}
    for cell in paper_map.cells.values():
        if cell.field not in AMOUNT_FIELDS:
            continue
        if not cell.has_observed_value:
            continue
        if not isinstance(cell.observed_value, int):
            continue
        by_row.setdefault(cell.paper_row, []).append(cell)
    return by_row


def _meter_matches_by_amount(amount: int, meter_rides: tuple[MeterRide, ...]) -> tuple[MeterRide, ...]:
    return tuple(ride for ride in meter_rides if ride.amount == amount)


def _amount_cells_total(amount_cells: list[PaperCell]) -> int:
    return sum(int(cell.observed_value) for cell in amount_cells)


def _amount_component(amount_cells: list[PaperCell], field_name: FieldName) -> PaperCell | None:
    matches = [cell for cell in amount_cells if cell.field == field_name]
    if len(matches) != 1:
        return None
    return matches[0]


def _adopted_from_cell_component(
    cell: PaperCell,
    meter_match: MeterRide,
    *,
    source: AmountSource,
) -> AdoptedAmount:
    return AdoptedAmount(
        amount=int(cell.observed_value),
        source=source,
        evidences=(
            Evidence(
                source="meter_receipt",
                reference=meter_match.ride_id,
                detail="component accepted because row total matches meter amount",
            ),
            Evidence(
                source="paper_map",
                reference=cell.cell_id,
                detail="observed component amount",
                confidence=cell.confidence,
            ),
        ),
    )


def _adopted_from_meter_component(cell: PaperCell, meter_match: MeterRide) -> AdoptedAmount:
    return AdoptedAmount(
        amount=meter_match.amount,
        source=AmountSource.METER,
        evidences=(
            Evidence(
                source="meter_receipt",
                reference=meter_match.ride_id,
                detail="amount adopted from meter ride after time link",
            ),
            Evidence(
                source="paper_map",
                reference=cell.cell_id,
                detail="paper cell position decides cash or receivable side",
                confidence=cell.confidence,
            ),
        ),
    )


def _adopted_from_meter_total(
    meter_match: MeterRide,
    amount_cells: list[PaperCell],
    *,
    detail: str = "exact row total match",
) -> AdoptedAmount:
    return AdoptedAmount(
        amount=meter_match.amount,
        source=AmountSource.METER,
        evidences=(
            Evidence(
                source="meter_receipt",
                reference=meter_match.ride_id,
                detail=detail,
            ),
            *(
                Evidence(
                    source="paper_map",
                    reference=cell.cell_id,
                    detail="observed row amount component",
                    confidence=cell.confidence,
                )
                for cell in amount_cells
            ),
        ),
    )


def _observed_cell_for_row(paper_map: PaperMap, paper_row: int, field_name: FieldName) -> PaperCell | None:
    cell_id = f"R{paper_row:02d}_{field_name.value.upper()}"
    cell = paper_map.cells.get(cell_id)
    if cell and cell.has_observed_value:
        return cell
    return None


def _paper_time_for_row(paper_map: PaperMap, paper_row: int) -> str | None:
    cell = _observed_cell_for_row(paper_map, paper_row, FieldName.TIME)
    if cell is None:
        return None
    value = str(cell.observed_value or "").strip()
    return value or None


def _unused_meter_matches_by_time(
    time_value: str | None,
    meter_rides: tuple[MeterRide, ...],
    used_meter_ids: set[str],
) -> tuple[MeterRide, ...]:
    if not time_value:
        return ()
    return tuple(
        ride
        for ride in meter_rides
        if ride.ride_id not in used_meter_ids and ride.time == time_value
    )


def reconcile_exact_amounts(
    paper_map: PaperMap,
    meter_receipt: MeterReceipt,
    template: PaperTemplate,
    fare_config: FareConfig | None = None,
) -> ReconciledReport:
    """Build the smallest real Layer 2 pipeline by exact amount.

    This is intentionally conservative:
    - fixed paper cells stay the address source
    - observed paper amount and adopted meter amount stay separate
    - ambiguous or unmatched amounts become diagnostics, not forced matches
    - special cases are not handled here
    """

    config = fare_config or FareConfig()
    config.validate()
    diagnostics = list(validate_reconciliation_inputs(paper_map, meter_receipt, template))
    rides: list[ReconciledRide] = []
    used_meter_ids: set[str] = set()
    confirmed_gen = 0
    confirmed_mi = 0

    for paper_row, amount_cells in sorted(_amount_cells_by_row(paper_map).items()):
        if len(amount_cells) > len(AMOUNT_FIELDS):
            diagnostics.append(
                Diagnostic(
                    code="paper_row_amount_ambiguous",
                    message="paper row has too many observed amount cells",
                    severity=DiagnosticSeverity.WARNING,
                    references=tuple(cell.cell_id for cell in amount_cells),
                )
            )
            continue

        amount_cells = sorted(amount_cells, key=lambda cell: AMOUNT_FIELDS.index(cell.field))
        paper_cell_ids = tuple(cell.cell_id for cell in amount_cells)
        row_total = _amount_cells_total(amount_cells)
        meter_matches = tuple(
            ride
            for ride in _meter_matches_by_amount(row_total, meter_receipt.rides)
            if ride.ride_id not in used_meter_ids
        )
        meter_match: MeterRide | None = None
        match_method = "amount"
        if not meter_matches:
            time_value = _paper_time_for_row(paper_map, paper_row)
            time_matches = _unused_meter_matches_by_time(time_value, meter_receipt.rides, used_meter_ids)
            if len(time_matches) == 1 and len(amount_cells) == 1:
                meter_match = time_matches[0]
                match_method = "time"
                diagnostics.append(
                    Diagnostic(
                        code="paper_row_amount_corrected_by_time",
                        message="meter amount was adopted because paper time linked to one meter ride",
                        severity=DiagnosticSeverity.INFO,
                        references=paper_cell_ids + (meter_match.ride_id,),
                        details={
                            "paper_amount": row_total,
                            "meter_amount": meter_match.amount,
                            "time": time_value,
                        },
                    )
                )
            else:
                diagnostics.append(
                    Diagnostic(
                        code="paper_row_total_has_no_meter_match",
                        message="paper row total did not match any meter ride",
                        severity=DiagnosticSeverity.WARNING,
                        references=paper_cell_ids,
                        details={
                            "row_total": row_total,
                            "components": {
                                cell.field.value: int(cell.observed_value)
                                for cell in amount_cells
                            },
                        },
                    )
                )
                continue
        elif len(meter_matches) > 1:
            diagnostics.append(
                Diagnostic(
                    code="paper_row_total_has_multiple_meter_matches",
                    message="paper row total matched multiple meter rides",
                    severity=DiagnosticSeverity.WARNING,
                    references=paper_cell_ids,
                    details={
                        "row_total": row_total,
                        "meter_ride_ids": [ride.ride_id for ride in meter_matches],
                    },
                )
            )
            continue
        else:
            meter_match = meter_matches[0]

        used_meter_ids.add(meter_match.ride_id)
        gen_cell = _amount_component(amount_cells, FieldName.GEN)
        mi_cell = _amount_component(amount_cells, FieldName.MI)
        adopted_total = _adopted_from_meter_total(
            meter_match,
            amount_cells,
            detail="time linked meter amount" if match_method == "time" else "exact row total match",
        )
        component_source = AmountSource.METER if len(amount_cells) == 1 else AmountSource.PAPER
        adopted_gen = (
            _adopted_from_meter_component(gen_cell, meter_match)
            if gen_cell and match_method == "time"
            else _adopted_from_cell_component(gen_cell, meter_match, source=component_source)
            if gen_cell
            else None
        )
        adopted_mi = (
            _adopted_from_meter_component(mi_cell, meter_match)
            if mi_cell and match_method == "time"
            else _adopted_from_cell_component(mi_cell, meter_match, source=component_source)
            if mi_cell
            else None
        )

        ride_kwargs = {
            "ride_key": f"R{paper_row:02d}",
            "paper_cell_ids": paper_cell_ids,
            "meter_ride_ids": (meter_match.ride_id,),
            "link_status": LinkStatus.LINKED,
            "observed_gen": int(gen_cell.observed_value) if gen_cell else None,
            "observed_mi": int(mi_cell.observed_value) if mi_cell else None,
            "adopted_total": adopted_total,
            "adopted_gen": adopted_gen,
            "adopted_mi": adopted_mi,
            "diagnostic_reasons": ("paper_amount_corrected_by_meter_time",) if match_method == "time" else (),
        }
        rides.append(ReconciledRide(**ride_kwargs))
        confirmed_gen += adopted_gen.amount if adopted_gen else 0
        confirmed_mi += adopted_mi.amount if adopted_mi else 0

    unused_meter_ids = tuple(
        ride.ride_id
        for ride in meter_receipt.rides
        if ride.ride_id not in used_meter_ids
    )
    unused_meter_rides = tuple(
        ride
        for ride in meter_receipt.rides
        if ride.ride_id not in used_meter_ids
    )
    pending_meter_sales = sum(ride.amount for ride in unused_meter_rides)
    if unused_meter_ids:
        diagnostics.append(
            Diagnostic(
                code="unused_meter_rides",
                message="some meter rides were not linked and remain pending",
                severity=DiagnosticSeverity.WARNING,
                references=unused_meter_ids,
                details={
                    "pending_meter_sales": pending_meter_sales,
                    "amounts": {ride.ride_id: ride.amount for ride in unused_meter_rides},
                },
            )
        )

    return ReconciledReport(
        schema="reconciled_report",
        paper_map=paper_map,
        meter_receipt=meter_receipt,
        rides=tuple(rides),
        sales=SalesComponents(
            confirmed_gen=confirmed_gen,
            confirmed_mi=confirmed_mi,
            pending_meter_sales=pending_meter_sales,
        ),
        diagnostics=tuple(diagnostics),
    )
