"""Sales totals for adopted reports.

Totals are built from two separate layers:
- ride body rows
- special claims

This module is the only place where those components are summed.  Claims stay
separate from row gen/mi values so the engine can explain what came from normal
rides and what came from special rules.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import AdoptedReport, Claim


@dataclass(frozen=True)
class SalesTotals:
    ride_gen: int
    ride_mi: int
    claim_gen: int
    claim_mi: int

    @property
    def gen(self) -> int:
        return self.ride_gen + self.claim_gen

    @property
    def mi(self) -> int:
        return self.ride_mi + self.claim_mi

    @property
    def sou(self) -> int:
        return self.gen + self.mi


def _as_int(value: object) -> int:
    if value in (None, ""):
        return 0
    return int(value)


def _claim_component(claim: Claim) -> tuple[int, int]:
    if claim.payment_kind == "gen":
        return claim.claim_amount, 0
    if claim.payment_kind == "mi":
        return 0, claim.claim_amount
    raise ValueError(f"unknown payment_kind: {claim.payment_kind!r}")


def compute_sales_totals(report: AdoptedReport) -> SalesTotals:
    """Compute final sales totals without mutating report rows or claims."""

    ride_gen = sum(_as_int(row.values.get("gen")) for row in report.rows)
    ride_mi = sum(_as_int(row.values.get("mi")) for row in report.rows)
    claim_gen = 0
    claim_mi = 0
    for claim in report.claims:
        gen, mi = _claim_component(claim)
        claim_gen += gen
        claim_mi += mi
    return SalesTotals(
        ride_gen=ride_gen,
        ride_mi=ride_mi,
        claim_gen=claim_gen,
        claim_mi=claim_mi,
    )
