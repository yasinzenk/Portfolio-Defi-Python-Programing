"""
Risk analysis module for portfolio metrics.

This module provides functions to calculate common financial risk
metrics from historical price data. All functions are designed to
work with pandas Series and DataFrames.

Functions:
    prices_to_returns: Convert price series to return series.
    annualized_volatility: Calculate annualized volatility.
    sharpe_ratio: Calculate the Sharpe ratio.
    historical_var: Calculate historical Value at Risk.
    correlation_matrix: Calculate correlation between assets.

Example:
    >>> import pandas as pd
    >>> from risk_analyzer import annualized_volatility
    >>> returns = pd.Series([0.01, -0.02, 0.015, -0.005, 0.02])
    >>> vol = annualized_volatility(returns)
    >>> print(f"Annualized volatility: {vol:.2%}")
"""
import numpy as np
import pandas as pd

def prices_to_returns(prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a DataFrame of prices to a DataFrame of simple returns.
    
    Simple returns are calculated as: (P_t - P_{t-1}) / P_{t-1}
    
    Args:
        prices_df: DataFrame where each column is a price series
                   for a different asset, indexed by date.
    
    Returns:
        DataFrame of simple returns with the same structure.
        The first row is dropped as it cannot have a return.
    
    Example:
        >>> prices = pd.DataFrame({
        ...     "ETH": [3000, 3100, 3050],
        ...     "BTC": [60000, 61000, 60500]
        ... })
        >>> returns = prices_to_returns(prices)
        >>> print(returns)
    """
    return prices_df.pct_change().dropna(how="all")


def annualized_volatility(returns: pd.Series, periods_per_year: int = 365) -> float:
    """
    Calculate the annualized volatility of a return series.
    
    Volatility is the standard deviation of returns, scaled to an
    annual basis by multiplying by sqrt(periods_per_year).
    
    Formula: σ_annual = σ_daily × √365
    
    Args:
        returns: Series of periodic returns (typically daily).
        periods_per_year: Number of periods in a year.
                         Use 365 for daily, 52 for weekly, 12 for monthly.
    
    Returns:
        Annualized volatility as a float.
        Returns NaN if fewer than 2 data points are available.
    
    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.015, -0.005])
        >>> vol = annualized_volatility(returns)
        >>> print(f"Volatility: {vol:.2%}")
    """
    r = returns.dropna()
    if len(r) < 2:
        return float("nan")
    return float(r.std(ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02, periods_per_year: int = 365) -> float:
    """
    Calculate the Sharpe ratio of a return series.
    
    The Sharpe ratio measures risk-adjusted return. A higher ratio
    indicates better risk-adjusted performance.
    
    Formula: Sharpe = (R - Rf) / σ × √periods_per_year
    
    Where:
        R  = Mean return
        Rf = Risk-free rate (adjusted per period)
        σ  = Standard deviation of excess returns
    
    Args:
        returns: Series of periodic returns.
        risk_free_rate: Annual risk-free rate (default 2%).
        periods_per_year: Number of periods in a year.
    
    Returns:
        Annualized Sharpe ratio as a float.
        Returns NaN if fewer than 2 points or zero volatility.
    
    Example:
        >>> returns = pd.Series([0.01, 0.02, 0.015, 0.005])
        >>> sr = sharpe_ratio(returns, risk_free_rate=0.03)
        >>> print(f"Sharpe Ratio: {sr:.2f}")
    """
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
    """
    Calculate historical Value at Risk (VaR).
    
    VaR estimates the maximum expected loss over a given period
    at a specified confidence level.
    
    For 95% confidence, VaR represents the 5th percentile of returns,
    meaning there's a 5% chance of experiencing a loss greater than VaR.
    
    Args:
        returns: Series of historical returns.
        confidence: Confidence level (default 0.95 for 95%).
    
    Returns:
        VaR as a negative float (representing a loss).
        Returns NaN if no data is available.
    
    Note:
        A VaR of -0.05 at 95% confidence means there's a 5% chance
        of losing more than 5% in a single period.
    
    Example:
        >>> returns = pd.Series([-0.03, 0.02, -0.01, 0.01, -0.05])
        >>> var = historical_var(returns, confidence=0.95)
        >>> print(f"VaR (95%): {var:.2%}")
    """
    r = returns.dropna()
    if len(r) == 0:
        return float("nan")
    return float(np.quantile(r, 1 - confidence))


def correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the correlation matrix between asset returns.
    
    Correlation measures how assets move together:
        - +1: Perfect positive correlation (move together)
        -  0: No correlation (independent)
        - -1: Perfect negative correlation (move opposite)
    
    Args:
        returns_df: DataFrame of returns, one column per asset.
    
    Returns:
        Square DataFrame with correlation coefficients.
        Diagonal values are always 1.0 (self-correlation).
    
    Example:
        >>> returns = pd.DataFrame({
        ...     "ETH": [0.01, -0.02, 0.015],
        ...     "BTC": [0.02, -0.01, 0.01]
        ... })
        >>> corr = correlation_matrix(returns)
        >>> print(corr)
    """
    return returns_df.corr()


def covariance_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the covariance matrix between asset returns.
    
    Covariance measures how two assets vary together. Unlike
    correlation, covariance is not normalized and depends on
    the scale of the returns.
    
    Args:
        returns_df: DataFrame of returns, one column per asset.
    
    Returns:
        Square DataFrame with covariance values.
    
    Note:
        For portfolio optimization, covariance is preferred over
        correlation as it preserves magnitude information.
    """
    return returns_df.cov()

def portfolio_volatility(
    returns_df: pd.DataFrame, 
    weights: dict[str, float],
    periods_per_year: int = 365
) -> float:
    """
    Calculate the annualized volatility of the entire portfolio.
    
    Uses the covariance matrix to account for diversification effects.
    A well-diversified portfolio will have lower volatility than the
    weighted average of individual asset volatilities.
    
    Args:
        returns_df: DataFrame of returns, one column per asset.
        weights: Dictionary mapping asset symbols to their weights.
        periods_per_year: Number of periods in a year.
    
    Returns:
        Annualized portfolio volatility as a float.
    
    Example:
        >>> weights = {"ETH": 0.6, "BTC": 0.4}
        >>> vol = portfolio_volatility(returns_df, weights)
        >>> print(f"Portfolio volatility: {vol:.2%}")
    """
    # Align weights with DataFrame columns
    w = np.array([weights.get(col, 0) for col in returns_df.columns])
    
    # Get covariance matrix
    cov = covariance_matrix(returns_df)
    
    # Portfolio variance: w^T × Σ × w
    portfolio_var = np.dot(w.T, np.dot(cov, w))
    
    # Annualize
    return float(np.sqrt(portfolio_var * periods_per_year))