"""
Risk analysis module for portfolio metrics.

Provides functions to calculate common financial risk metrics
from historical price data.
"""

import numpy as np
import pandas as pd


def prices_to_returns(prices_df: pd.DataFrame) -> pd.DataFrame:
    """Convert a DataFrame of prices to simple returns."""
    return prices_df.pct_change().dropna(how="all")


def annualized_volatility(
    returns: pd.Series,
    periods_per_year: int = 365
) -> float:
    """Calculate annualized volatility of a return series."""
    r = returns.dropna()
    if len(r) < 2:
        return float("nan")
    return float(r.std(ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 365
) -> float:
    """Calculate the Sharpe ratio of a return series."""
    r = returns.dropna()
    if len(r) < 2:
        return float("nan")

    rf_per_period = risk_free_rate / periods_per_year
    excess = r - rf_per_period
    denom = excess.std(ddof=1)
    if denom == 0:
        return float("nan")
    return float(excess.mean() / denom * np.sqrt(periods_per_year))


def historical_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Calculate historical Value at Risk (VaR)."""
    r = returns.dropna()
    if len(r) == 0:
        return float("nan")
    return float(np.quantile(r, 1 - confidence))


def correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the correlation matrix between asset returns."""
    return returns_df.corr()


def covariance_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the covariance matrix between asset returns."""
    return returns_df.cov()


def portfolio_volatility(
    returns_df: pd.DataFrame,
    weights: dict[str, float],
    periods_per_year: int = 365
) -> float:
    """Calculate annualized volatility of the entire portfolio."""
    w = np.array([weights.get(col, 0) for col in returns_df.columns])
    cov = covariance_matrix(returns_df)
    portfolio_var = np.dot(w.T, np.dot(cov, w))
    return float(np.sqrt(portfolio_var * periods_per_year))
