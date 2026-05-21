"""Layer 3 special modules.

Special modules add non-ride claims or exceptional entries.  They must not turn
ordinary rides into special rows and must not mix claims into gen/mi body sales.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import Claim, EvidenceLink, normalize_row_addr


@dataclass(frozen=True)
class PublicDiscountConfig:
    discount_num: int = 1
    discount_den: int = 10
    pickup_fee: int = 200
    pickup_fee_discountable: bool = False
    fare_unit: int = 10


@dataclass(frozen=True)
class DiscountCandidate:
    claim_amount: int
    pickup_fee_used: int
    discounted_fare: int
    original_fare: int


def public_discount_candidates(meter_amount: int, config: PublicDiscountConfig | None = None) -> list[DiscountCandidate]:
    """Return possible public-discount claim amounts from a meter amount.

    For a 10% discount, if the receipt amount is the discounted fare, the claim
    amount is discounted_fare / 9.  Pickup fee can be excluded from the discount
    base depending on the company rule.
    """

    active = config or PublicDiscountConfig()
    candidates: list[DiscountCandidate] = []
    pickup_options = (0,) if active.pickup_fee_discountable else (0, active.pickup_fee)
    for pickup_fee in pickup_options:
        discounted_fare = meter_amount - pickup_fee
        if discounted_fare <= 0:
            continue
        divisor = active.discount_den - active.discount_num
        numerator = discounted_fare * active.discount_num
        if divisor <= 0 or numerator % divisor != 0:
            continue
        claim_amount = numerator // divisor
        if claim_amount <= 0 or claim_amount % active.fare_unit != 0:
            continue
        candidates.append(
            DiscountCandidate(
                claim_amount=claim_amount,
                pickup_fee_used=pickup_fee,
                discounted_fare=discounted_fare,
                original_fare=discounted_fare + claim_amount,
            )
        )
    return candidates


def make_public_discount_claim(
    *,
    target_row_addr: str,
    target_global_cell_id: str,
    meter_amount: int,
    expected_claim_amount: int | None = None,
    evidence: tuple[EvidenceLink, ...],
    config: PublicDiscountConfig | None = None,
) -> Claim | None:
    """Build a disability/public discount claim when the amount is unambiguous."""

    candidates = public_discount_candidates(meter_amount, config)
    if expected_claim_amount is not None:
        candidates = [candidate for candidate in candidates if candidate.claim_amount == expected_claim_amount]
    if len(candidates) != 1:
        return None
    return Claim(
        claim_type="public_discount_claim",
        claim_amount=candidates[0].claim_amount,
        target_row_addr=normalize_row_addr(target_row_addr),
        target_global_cell_id=target_global_cell_id,
        payment_kind="mi",
        evidence=evidence,
    )


def make_charter_claim(
    *,
    target_row_addr: str,
    target_global_cell_id: str,
    claim_amount: int,
    payment_kind: str,
    evidence: tuple[EvidenceLink, ...],
) -> Claim:
    """Build a charter special sale claim.

    Charter is not an ordinary meter ride.  It is a special sale component and
    stays outside normal ride rows.
    """

    if claim_amount <= 0:
        raise ValueError("charter claim_amount must be positive")
    if payment_kind not in ("gen", "mi"):
        raise ValueError("charter payment_kind must be gen or mi")
    return Claim(
        claim_type="charter_sale",
        claim_amount=claim_amount,
        target_row_addr=normalize_row_addr(target_row_addr),
        target_global_cell_id=target_global_cell_id,
        payment_kind=payment_kind,
        evidence=evidence,
    )


def claim_total(claims: tuple[Claim, ...] | list[Claim], claim_type: str | None = None) -> int:
    return sum(claim.claim_amount for claim in claims if claim_type is None or claim.claim_type == claim_type)
