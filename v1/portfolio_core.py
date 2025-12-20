"""
Main module for the DeFi portfolio core.

This module defines the main classes and functions for the DeFi portfolio core.

Classes:
    Asset: Représente un actif individuel dans le portfolio.
    Portfolio: Représente un portefeuille composé de plusieurs assets.

Example:
    >>> portfolio = Portfolio("defi_portfolio")
    >>> portfolio.add_asset(Asset("ETH", 1.5, 2200))
    >>> portfolio.add_asset(Asset("BTC", 0.1, 40000))
    >>> portfolio.total_value()
    6000.0

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Asset:
    """
    Represents an asset in the portfolio.

    An asset is immutable (frozen=True) because once created, its values
    should not change. To modify an asset, create a new one.

    Attributes:
        symbol: Ticker of the asset (ex: "ETH", "BTC", "AAVE").
        amount: Quantity of the asset.
        price: Price of the asset in USD.
    """
    symbol: str
    amount: float
    price: float | None = None
    coingecko_id: str | None = None

    def market_value(self) -> float:
        """
        Calculate the market value of the asset.

        Returns:
            The market value of the asset.
        """
        if self.price is None:
            raise ValueError(f"Price is missing for {self.symbol}. Fetch prices before computing market value.")
        return self.amount * self.price


class Portfolio:
    """
    Represents a portfolio of assets.

    Attributes:
        name: Name of the portfolio.
        assets: List of assets in the portfolio.
    """
    def __init__(self, name: str):
        """
        Initialize a new portfolio.

        Args:
            name: Name of the portfolio.
        """
        self.name = name
        self.assets: List[Asset] = []

    def add_asset(self, asset: Asset) -> None:
        """
        Add an asset to the portfolio.

        Args:
            asset: Asset to add to the portfolio.
        """
        self.assets.append(asset)

    def total_value(self) -> float:
        """
        Calculate the total value of the portfolio.

        Returns:
            The total value of the portfolio.
        """
        return sum(a.market_value() for a in self.assets)

    def weights(self) -> Dict[str, float]:
        """
        Calculate the weights of the assets in the portfolio.

        Returns:
            The weights of the assets in the portfolio. The weights are
            expressed as proportions (0.0 to 1.0), not percentages.
        """
        total = self.total_value()
        if total <= 0:
            return {a.symbol: 0.0 for a in self.assets}

        values: Dict[str, float] = {}
        for a in self.assets:
            values[a.symbol] = values.get(a.symbol, 0.0) + a.market_value()
        return {sym: val / total for sym, val in values.items()}
