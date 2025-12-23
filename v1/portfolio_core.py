"""
Core data structures for the DeFi portfolio analyzer (V1).

In V1, assets can have prices fetched dynamically from an API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Asset:
    """
    Represents an asset in the portfolio.

    Attributes:
        symbol: Ticker of the asset (e.g., "ETH", "BTC").
        amount: Quantity of the asset held.
        price: Price in USD (can be None until fetched).
        crypto_id: API identifier for price fetching.
    """

    symbol: str
    amount: float
    price: float | None = None
    crypto_id: str | None = None

    def market_value(self) -> float:
        """Return the market value (amount * price)."""
        if self.price is None:
            raise ValueError(
                f"Price is missing for {self.symbol}. "
                "Fetch prices before computing market value."
            )
        return self.amount * self.price


class Portfolio:
    """
    Represents a portfolio of assets.

    Attributes:
        name: Name of the portfolio.
        assets: List of assets in the portfolio.
    """

    def __init__(self, name: str):
        """Initialize a new portfolio with the given name."""
        self.name = name
        self.assets: List[Asset] = []

    def add_asset(self, asset: Asset) -> None:
        """Add an asset to the portfolio."""
        self.assets.append(asset)

    def total_value(self) -> float:
        """Return the total value of all assets."""
        return sum(a.market_value() for a in self.assets)

    def weights(self) -> Dict[str, float]:
        """Return the weight of each asset as a proportion (0.0 to 1.0)."""
        total = self.total_value()
        if total <= 0:
            return {a.symbol: 0.0 for a in self.assets}

        values: Dict[str, float] = {}
        for a in self.assets:
            values[a.symbol] = values.get(a.symbol, 0.0) + a.market_value()
        return {sym: val / total for sym, val in values.items()}
