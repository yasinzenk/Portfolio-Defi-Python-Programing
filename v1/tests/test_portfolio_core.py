"""
Unit tests for portfolio_core module.

Tests the Asset and Portfolio classes to ensure correct
calculation of market values and portfolio weights.
"""

import pytest
from portfolio_core import Asset, Portfolio


class TestAsset:
    """Tests for the Asset dataclass."""

    def test_market_value_calculation(self):
        """Test that market_value() returns amount * price."""
        asset = Asset(
            symbol="ETH",
            amount=2.0,
            price=3000.0,
            crypto_id="ETH"
        )
        assert asset.market_value() == 6000.0

    def test_market_value_with_zero_amount(self):
        """Test market_value with zero amount."""
        asset = Asset(symbol="ETH", amount=0.0, price=3000.0, crypto_id="ETH")
        assert asset.market_value() == 0.0

    def test_market_value_missing_price_raises_error(self):
        """Test that ValueError is raised when price is None."""
        asset = Asset(symbol="ETH", amount=2.0, price=None, crypto_id="ETH")
        with pytest.raises(ValueError):
            asset.market_value()

    def test_asset_is_immutable(self):
        """Test that Asset is frozen (immutable)."""
        asset = Asset(symbol="ETH", amount=1.0, price=3000.0, crypto_id="ETH")
        with pytest.raises(Exception):  # FrozenInstanceError
            asset.amount = 2.0


class TestPortfolio:
    """Tests for the Portfolio class."""

    def test_empty_portfolio_total_value(self):
        """Test that empty portfolio has zero value."""
        portfolio = Portfolio(name="test")
        assert portfolio.total_value() == 0.0

    def test_single_asset_total_value(self):
        """Test total_value with one asset."""
        portfolio = Portfolio(name="test")
        portfolio.add_asset(Asset("ETH", 1.0, 3000.0, "ETH"))
        assert portfolio.total_value() == 3000.0

    def test_multiple_assets_total_value(self):
        """Test total_value with multiple assets."""
        portfolio = Portfolio(name="test")
        portfolio.add_asset(Asset("ETH", 1.0, 3000.0, "ETH"))
        portfolio.add_asset(Asset("BTC", 0.1, 50000.0, "BTC"))
        assert portfolio.total_value() == 8000.0  # 3000 + 5000

    def test_weights_single_asset(self):
        """Test that single asset has 100% weight."""
        portfolio = Portfolio(name="test")
        portfolio.add_asset(Asset("ETH", 1.0, 3000.0, "ETH"))
        weights = portfolio.weights()
        assert weights["ETH"] == 1.0

    def test_weights_equal_assets(self):
        """Test weights with two equal-value assets."""
        portfolio = Portfolio(name="test")
        portfolio.add_asset(Asset("ETH", 1.0, 1000.0, "ETH"))
        portfolio.add_asset(Asset("BTC", 1.0, 1000.0, "BTC"))
        weights = portfolio.weights()
        assert weights["ETH"] == 0.5
        assert weights["BTC"] == 0.5

    def test_weights_empty_portfolio(self):
        """Test weights of empty portfolio."""
        portfolio = Portfolio(name="test")
        weights = portfolio.weights()
        assert weights == {}