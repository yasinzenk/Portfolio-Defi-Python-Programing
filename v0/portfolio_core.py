"""
Core data structures for the DeFi portfolio analyzer.

Classes:
    Asset: Represents an individual asset in the portfolio.
    Portfolio: Represents a portfolio of multiple assets.
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
        price: Price of the asset in USD.
    """

    symbol: str
    amount: float
    price: float

    def market_value(self) -> float:
        """Return the market value (amount * price)."""
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
