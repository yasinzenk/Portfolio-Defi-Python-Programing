"""
Risk analysis utilities for DeFi portfolios.

This module provides reusable functions to transform historical price
data into standard financial risk metrics used in portfolio analysis,
such as volatility, Sharpe ratio, Value at Risk (VaR), and correlation
or covariance matrices.
"""

from __future__ import annotations

import logging
from typing import Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def prices_to_returns(prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert asset price time series to simple returns.

    Computes percentage change for each asset and drops
    leading rows with missing values induced by the shift.

    Args:
        prices_df: DataFrame of prices indexed by date, with one column per asset.

    Returns:
        DataFrame of simple returns with the same columns as `prices_df`.

    Raises:
        AssertionError: If `prices_df` is not a DataFrame or is empty.

    Example:
        >>> import pandas as pd
        >>> prices = pd.DataFrame({"ETH": [100, 105, 110]})
        >>> prices_to_returns(prices)
              ETH
        1  0.0500
        2  0.0476
    """
    assert isinstance(prices_df, pd.DataFrame), "prices_df must be a pandas DataFrame"
    assert not prices_df.empty, "prices_df must not be empty"

    logger.debug("Converting %d price rows to returns", len(prices_df))
    returns = prices_df.pct_change().dropna(how="all")
    logger.debug("Generated %d return rows", len(returns))
    return returns


def annualized_volatility(
    returns: pd.Series,
    periods_per_year: int = 365,
) -> float:
    """
    Compute annualized volatility of a return series.

    Volatility is estimated as the standard deviation of returns scaled by
    the square root of the number of periods per year, assuming returns
    are expressed in the same frequency.

    Args:
        returns: Series of periodic returns for a single asset.
        periods_per_year: Number of return observations per year
            (e.g. 252 for trading days, 365 for daily crypto data).

    Returns:
        Annualized volatility as a float. Returns NaN if there are fewer
        than 2 non-null observations.

    Raises:
        AssertionError: If `returns` is not a Series or `periods_per_year`
            is not positive.
    """
    assert isinstance(returns, pd.Series), "returns must be a pandas Series"
    assert periods_per_year > 0, "periods_per_year must be positive"

    r = returns.dropna()
    if len(r) < 2:
        return float("nan")

    vol = float(r.std(ddof=1) * np.sqrt(periods_per_year))
    logger.debug("Annualized volatility computed: %.6f", vol)
    return vol


def sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 365,
) -> float:
    """
    Compute the annualized Sharpe ratio of a return series.

    The Sharpe ratio is the mean excess return divided by its volatility,
    both expressed on an annual basis.

    Args:
        returns: Series of periodic returns for a single asset.
        risk_free_rate: Annual risk-free rate (e.g. 0.02 for 2%).
        periods_per_year: Number of return observations per year.

    Returns:
        Annualized Sharpe ratio as a float. Returns NaN if there are
        fewer than 2 non-null observations or zero volatility.

    Raises:
        AssertionError: If types or parameters are invalid.
    """
    assert isinstance(returns, pd.Series), "returns must be a pandas Series"
    assert periods_per_year > 0, "periods_per_year must be positive"
    assert isinstance(risk_free_rate, (float, int)), "risk_free_rate must be numeric"

    r = returns.dropna()
    if len(r) < 2:
        return float("nan")

    rf_per_period = risk_free_rate / periods_per_year
    excess = r - rf_per_period
    denom = excess.std(ddof=1)
    if denom == 0:
        logger.debug("Sharpe ratio undefined due to zero volatility")
        return float("nan")

    sharpe = float(excess.mean() / denom * np.sqrt(periods_per_year))
    logger.debug("Sharpe ratio computed: %.6f", sharpe)
    return sharpe


def historical_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Compute historical Value at Risk (VaR) for a return series.

    Uses the empirical distribution of returns without assuming normality.
    VaR is returned as the quantile at level (1 - confidence), typically
    a negative number representing a loss.

    Args:
        returns: Series of periodic returns.
        confidence: Confidence level between 0 and 1
            (e.g. 0.95 for 95% VaR).

    Returns:
        Historical VaR as a float. Returns NaN if the series is empty.

    Raises:
        AssertionError: If `returns` is not a Series or `confidence`
            is not in (0, 1).
    """
    assert isinstance(returns, pd.Series), "returns must be a pandas Series"
    assert 0.0 < confidence < 1.0, "confidence must be in (0, 1)"

    r = returns.dropna()
    if len(r) == 0:
        return float("nan")

    var = float(np.quantile(r, 1 - confidence))
    logger.debug("Historical VaR (confidence=%.3f) computed: %.6f", confidence, var)
    return var


def correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the correlation matrix between asset returns.

    Args:
        returns_df: DataFrame of asset returns with one column per asset.

    Returns:
        DataFrame whose (i, j) entry is the correlation between asset i
        and asset j.

    Raises:
        AssertionError: If `returns_df` is not a non-empty DataFrame.
    """
    assert isinstance(returns_df, pd.DataFrame), "returns_df must be a DataFrame"
    assert not returns_df.empty, "returns_df must not be empty"

    corr = returns_df.corr()
    logger.debug("Correlation matrix shape: %s", corr.shape)
    return corr


def covariance_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the covariance matrix between asset returns.

    Args:
        returns_df: DataFrame of asset returns with one column per asset.

    Returns:
        DataFrame whose (i, j) entry is the covariance between asset i
        and asset j.

    Raises:
        AssertionError: If `returns_df` is not a non-empty DataFrame.
    """
    assert isinstance(returns_df, pd.DataFrame), "returns_df must be a DataFrame"
    assert not returns_df.empty, "returns_df must not be empty"

    cov = returns_df.cov()
    logger.debug("Covariance matrix shape: %s", cov.shape)
    return cov


def portfolio_volatility(
    returns_df: pd.DataFrame,
    weights: Dict[str, float],
    periods_per_year: int = 365,
) -> float:
    """
    Compute the annualized volatility of a portfolio.

    The portfolio volatility is derived from the covariance matrix of
    asset returns and the weight vector associated to the portfolio.

    Args:
        returns_df: DataFrame of asset returns, with columns matching
            the keys of `weights`.
        weights: Mapping from asset symbol to portfolio weight.
            Weights are expected to sum to 1.
        periods_per_year: Number of return observations per year.

    Returns:
        Annualized portfolio volatility as a float.

    Raises:
        AssertionError: If inputs are invalid or weights do not cover
            all assets or sum to 1 (within a small tolerance).
    """
    assert isinstance(returns_df, pd.DataFrame), "returns_df must be a DataFrame"
    assert not returns_df.empty, "returns_df must not be empty"
    assert isinstance(weights, dict), "weights must be a dict"
    assert periods_per_year > 0, "periods_per_year must be positive"

    for col in returns_df.columns:
        assert col in weights, f"Missing weight for asset '{col}'"

    w = np.array([weights[col] for col in returns_df.columns], dtype=float)
    assert np.isclose(w.sum(), 1.0, atol=1e-3), "Portfolio weights must sum to 1"

    cov = covariance_matrix(returns_df)
    portfolio_var = float(w.T @ cov.values @ w)
    vol = float(np.sqrt(portfolio_var * periods_per_year))
    logger.debug("Portfolio annualized volatility computed: %.6f", vol)
    return vol
