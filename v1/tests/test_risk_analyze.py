"""
Unit tests for risk_analyzer module.

Tests the financial metrics calculations including volatility,
Sharpe ratio, and VaR.
"""

import pytest
import numpy as np
import pandas as pd
from risk_analyzer import (
    prices_to_returns,
    annualized_volatility,
    sharpe_ratio,
    historical_var,
    correlation_matrix,
)


class TestPricesToReturns:
    """Tests for prices_to_returns function."""

    def test_simple_returns(self):
        """Test basic return calculation."""
        prices = pd.DataFrame({"ETH": [100, 110, 105]})
        returns = prices_to_returns(prices)
        
        # 110/100 - 1 = 0.10, 105/110 - 1 = -0.0454...
        assert len(returns) == 2  # First row dropped
        assert abs(returns["ETH"].iloc[0] - 0.10) < 0.001

    def test_multiple_columns(self):
        """Test returns with multiple assets."""
        prices = pd.DataFrame({
            "ETH": [100, 110],
            "BTC": [50000, 51000]
        })
        returns = prices_to_returns(prices)
        assert "ETH" in returns.columns
        assert "BTC" in returns.columns


class TestAnnualizedVolatility:
    """Tests for annualized_volatility function."""

    def test_constant_returns_zero_volatility(self):
        """Test that constant returns give zero volatility."""
        returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        vol = annualized_volatility(returns)
        assert vol == 0.0

    def test_volatility_is_positive(self):
        """Test that volatility is always positive."""
        returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.005])
        vol = annualized_volatility(returns)
        assert vol > 0

    def test_insufficient_data_returns_nan(self):
        """Test that less than 2 points returns NaN."""
        returns = pd.Series([0.01])
        vol = annualized_volatility(returns)
        assert np.isnan(vol)


class TestSharpeRatio:
    """Tests for sharpe_ratio function."""

    def test_positive_sharpe_for_good_returns(self):
        """Test positive Sharpe for consistently positive returns."""
        returns = pd.Series([0.01, 0.02, 0.015, 0.01, 0.02])
        sr = sharpe_ratio(returns, risk_free_rate=0.0)
        assert sr > 0

    def test_insufficient_data_returns_nan(self):
        """Test that less than 2 points returns NaN."""
        returns = pd.Series([0.01])
        sr = sharpe_ratio(returns)
        assert np.isnan(sr)


class TestHistoricalVaR:
    """Tests for historical_var function."""

    def test_var_is_negative_for_normal_returns(self):
        """Test that VaR is typically negative (represents loss)."""
        returns = pd.Series([-0.05, -0.02, 0.01, 0.02, -0.03, 0.015])
        var = historical_var(returns, confidence=0.95)
        assert var < 0

    def test_empty_returns_nan(self):
        """Test that empty series returns NaN."""
        returns = pd.Series([], dtype=float)
        var = historical_var(returns)
        assert np.isnan(var)


class TestCorrelationMatrix:
    """Tests for correlation_matrix function."""

    def test_diagonal_is_one(self):
        """Test that self-correlation is always 1."""
        returns = pd.DataFrame({
            "ETH": [0.01, -0.02, 0.015],
            "BTC": [0.02, -0.01, 0.01]
        })
        corr = correlation_matrix(returns)
        assert corr.loc["ETH", "ETH"] == 1.0
        assert corr.loc["BTC", "BTC"] == 1.0

    def test_correlation_is_symmetric(self):
        """Test that correlation matrix is symmetric."""
        returns = pd.DataFrame({
            "ETH": [0.01, -0.02, 0.015],
            "BTC": [0.02, -0.01, 0.01]
        })
        corr = correlation_matrix(returns)
        assert corr.loc["ETH", "BTC"] == corr.loc["BTC", "ETH"]