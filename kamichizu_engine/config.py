"""Configuration for the Kamichizu engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FareConfig:
    """Minimal fare config used by rule checks.

    The engine trusts meter receipt amounts as source numbers. Fare config is
    for verification and special-rule calculations, not for recreating every
    meter fare from distance and time.
    """

    pickup_fee: int = 200
    public_discount_rate_num: int = 1
    public_discount_rate_den: int = 10
    pickup_fee_discountable: bool = False
    fare_unit: int = 10

    def validate(self) -> None:
        if self.pickup_fee < 0:
            raise ValueError("pickup_fee must be non-negative")
        if self.public_discount_rate_num <= 0:
            raise ValueError("public_discount_rate_num must be positive")
        if self.public_discount_rate_den <= self.public_discount_rate_num:
            raise ValueError("discount denominator must be greater than numerator")
        if self.fare_unit <= 0:
            raise ValueError("fare_unit must be positive")


@dataclass(frozen=True)
class EngineConfig:
    """Top-level engine config.

    This is intentionally small until the new engine proves its contracts.
    """

    template_id: str = "daiichi_taxi_daily_report"
    paper_row_count: int = 25
    fare: FareConfig = FareConfig()

    def validate(self) -> None:
        if self.paper_row_count <= 0:
            raise ValueError("paper_row_count must be positive")
        self.fare.validate()

