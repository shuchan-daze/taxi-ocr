"""Layer 3 special-case rules."""

from __future__ import annotations

from dataclasses import dataclass

from .config import FareConfig
from .models import Adjustment, AdjustmentKind, Evidence, ReconciledReport, SalesComponents


@dataclass(frozen=True)
class DiscountCandidate:
    meter_amount: int
    pickup_fee: int
    discount_base_after: int
    discount_amount: int
    original_discountable_fare: int

    def to_dict(self) -> dict[str, int]:
        return {
            "meter_amount": self.meter_amount,
            "pickup_fee": self.pickup_fee,
            "discount_base_after": self.discount_base_after,
            "discount_amount": self.discount_amount,
            "original_discountable_fare": self.original_discountable_fare,
        }


def public_discount_candidates(
    meter_amount: int,
    fare_config: FareConfig | None = None,
) -> tuple[DiscountCandidate, ...]:
    """Return public-discount candidates using integer arithmetic.

    For a 10% discount, the post-discount fare is 9 parts and the discount is
    1 part. So discount = post_discount_fare / 9. No float arithmetic is used.
    """

    config = fare_config or FareConfig()
    config.validate()
    if meter_amount <= 0:
        return ()

    pickup_options = (0, config.pickup_fee) if config.pickup_fee else (0,)
    candidates: list[DiscountCandidate] = []

    for pickup_fee in pickup_options:
        if pickup_fee > meter_amount:
            continue
        discount_base_after = (
            meter_amount
            if config.pickup_fee_discountable
            else meter_amount - pickup_fee
        )
        if discount_base_after <= 0:
            continue

        numerator = discount_base_after * config.public_discount_rate_num
        denominator = config.public_discount_rate_den - config.public_discount_rate_num
        if numerator % denominator != 0:
            continue

        discount_amount = numerator // denominator
        if discount_amount % config.fare_unit != 0:
            continue

        candidates.append(
            DiscountCandidate(
                meter_amount=meter_amount,
                pickup_fee=pickup_fee,
                discount_base_after=discount_base_after,
                discount_amount=discount_amount,
                original_discountable_fare=discount_base_after + discount_amount,
            )
        )

    return tuple(candidates)


def build_public_discount_adjustment(
    adjustment_id: str,
    amount: int,
    target_ride_key: str,
    source_cell_ids: tuple[str, ...],
    evidence_detail: str,
) -> Adjustment:
    return Adjustment(
        adjustment_id=adjustment_id,
        kind=AdjustmentKind.PUBLIC_DISCOUNT_CLAIM,
        amount=amount,
        target_ride_key=target_ride_key,
        source_cell_ids=source_cell_ids,
        evidences=(
            Evidence(
                source="rule",
                reference=target_ride_key,
                detail=evidence_detail,
            ),
        ),
        include_in_sales=True,
        include_in_count=False,
        include_in_passengers=False,
    )



def apply_adjustments(
    report: ReconciledReport,
    adjustments: tuple[Adjustment, ...],
) -> ReconciledReport:
    """Return a report with linked adjustments reflected in separate components.

    Adjustments are never mixed into confirmed_gen or confirmed_mi. Public
    discount claims increase discount_claim_total only when linked to a ride.
    """

    discount_claim_total = sum(
        adjustment.amount
        for adjustment in adjustments
        if adjustment.kind == AdjustmentKind.PUBLIC_DISCOUNT_CLAIM
        and adjustment.target_ride_key
        and adjustment.include_in_sales
    )
    charter_sales = sum(
        adjustment.amount
        for adjustment in adjustments
        if adjustment.kind == AdjustmentKind.CHARTER
        and adjustment.include_in_sales
    )

    sales = SalesComponents(
        confirmed_gen=report.sales.confirmed_gen,
        confirmed_mi=report.sales.confirmed_mi,
        pending_meter_sales=report.sales.pending_meter_sales,
        discount_claim_total=report.sales.discount_claim_total + discount_claim_total,
        charter_sales=report.sales.charter_sales + charter_sales,
    )
    return ReconciledReport(
        schema=report.schema,
        paper_map=report.paper_map,
        meter_receipt=report.meter_receipt,
        rides=report.rides,
        adjustments=report.adjustments + adjustments,
        sales=sales,
        diagnostics=report.diagnostics,
    )
