"""
Core data structures for the DeFi portfolio analyzer (V0).

This module defines the basic data model:

- Asset: a single position with symbol, amount and price.
- Portfolio: a collection of assets with helpers to compute
  total value and per-asset allocation weights.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Asset:
    """
    Represent an individual asset position in the portfolio.

    Attributes:
        symbol:
            Ticker of the asset (e.g. "ETH", "BTC").
        amount:
            Quantity of the asset held.
        price:
            Price of the asset in USD, assumed to be provided
            directly in the input JSON for V0.
    """

    symbol: str
    amount: float
    price: float

    def market_value(self) -> float:
        """
        Compute the current market value of this asset position.

        The market value is defined as ``amount * price``.

        Returns:
            Market value as a float.

        Example:
            >>> Asset("ETH", 2.0, 2000.0).market_value()
            4000.0
        """
        return self.amount * self.price


class Portfolio:
    """
    Represent a portfolio composed of multiple assets.

    Attributes:
        name:
            Human-readable name of the portfolio.
        assets:
            List of :class:`Asset` instances that belong to the portfolio.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a new portfolio with the given name.

        Args:
            name: Name of the portfolio.
        """
        self.name: str = name
        self.assets: List[Asset] = []

    def add_asset(self, asset: Asset) -> None:
        """
        Add an asset position to the portfolio.

        Args:
            asset: The :class:`Asset` instance to be added.
        """
        self.assets.append(asset)

    def total_value(self) -> float:
        """
        Compute the total market value of the portfolio.

        Returns:
            Sum of the market values of all assets as a float.
        """
        return sum(a.market_value() for a in self.assets)

    def weights(self) -> Dict[str, float]:
        """
        Compute allocation weights by asset symbol.

        The weight of an asset is its market value divided by the total
        portfolio value. If the total value is not strictly positive,
        all weights are returned as 0.0.

        Returns:
            Dictionary mapping asset symbol to its portfolio weight in
            the range [0.0, 1.0]. If several assets share the same symbol,
            their market values are aggregated before computing weights.

        Example:
            >>> p = Portfolio("demo")
            >>> p.add_asset(Asset("ETH", 1.0, 2000.0))
            >>> p.add_asset(Asset("BTC", 0.1, 30000.0))
            >>> round(p.weights()["ETH"], 2)
            0.40
        """
        total = self.total_value()
        if total <= 0:
            return {a.symbol: 0.0 for a in self.assets}

        values: Dict[str, float] = {}
        for a in self.assets:
            values[a.symbol] = values.get(a.symbol, 0.0) + a.market_value()
        return {sym: val / total for sym, val in values.items()}
