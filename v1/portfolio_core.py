"""
Core data structures for the DeFi portfolio analyzer.

This module defines the fundamental data structures used to represent
individual assets and portfolios. An asset holds basic position and
pricing information, while a portfolio aggregates multiple assets and
exposes convenience methods for computing total value and weights.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Asset:
    """
    Represent a single asset position in the portfolio.

    Attributes:
        symbol:
            Ticker of the asset (e.g. "ETH", "BTC").
        amount:
            Quantity of the asset held (in units of `symbol`).
        price:
            Latest price in quote currency (e.g. USD). May be ``None``
            if prices have not been fetched yet.
        crypto_id:
            Identifier used by external APIs for price fetching
            (e.g. "ethereum", "bitcoin").
    """

    symbol: str
    amount: float
    price: float | None = None
    crypto_id: str | None = None

    def market_value(self) -> float:
        """
        Compute the current market value of this asset position.

        The market value is defined as ``amount * price`` and is
        expressed in the same currency as `price` (typically USD).

        Returns:
            The market value as a float.

        Raises:
            ValueError: If `price` is ``None``, meaning that market data
                has not been populated yet.

        Example:
            >>> asset = Asset(symbol="ETH", amount=2.0, price=2000.0)
            >>> asset.market_value()
            4000.0
        """
        if self.price is None:
            raise ValueError(
                f"Price is missing for {self.symbol}. "
                "Fetch prices before computing market value."
            )
        return self.amount * self.price


class Portfolio:
    """
    Represent a portfolio composed of multiple assets.

    A portfolio stores a collection of :class:`Asset` instances and
    provides convenience methods to compute aggregate quantities
    such as total market value and asset weights.

    Attributes:
        name:
            Human-readable name of the portfolio.
        assets:
            List of :class:`Asset` objects held in the portfolio.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a new portfolio with the given name.

        Args:
            name: Non-empty name of the portfolio.

        Raises:
            AssertionError: If `name` is empty.
        """
        assert isinstance(name, str) and name, "Portfolio name must be a non-empty string"
        self.name: str = name
        self.assets: List[Asset] = []

    def add_asset(self, asset: Asset) -> None:
        """
        Add a new asset position to the portfolio.

        Args:
            asset: The :class:`Asset` instance to be added.

        Raises:
            AssertionError: If `asset` is not an :class:`Asset` instance.
        """
        assert isinstance(asset, Asset), "asset must be an Asset instance"
        self.assets.append(asset)
        logger.debug(
            "Added asset to portfolio: %s (amount=%s)",
            asset.symbol,
            asset.amount,
        )

    def total_value(self) -> float:
        """
        Compute the total market value of the portfolio.

        Sums the market values of all contained assets. All assets are
        assumed to be priced in the same quote currency.

        Returns:
            Total portfolio value as a float.

        Raises:
            ValueError: If any asset has a missing price.
        """
        return sum(a.market_value() for a in self.assets)

    def weights(self) -> Dict[str, float]:
        """
        Compute portfolio weights by asset symbol.

        The weight of an asset is defined as its market value divided by
        the total portfolio value. If the total value is not strictly
        positive, all weights are returned as 0.0.

        Returns:
            Dictionary mapping asset symbol to its portfolio weight in
            the range [0.0, 1.0]. Symbols are aggregated, so if several
            :class:`Asset` objects share the same symbol, their values
            are combined.

        Example:
            >>> from portfolio_core import Asset, Portfolio
            >>> p = Portfolio("demo")
            >>> p.add_asset(Asset("ETH", 1.0, price=2000.0))
            >>> p.add_asset(Asset("BTC", 0.1, price=30000.0))
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
