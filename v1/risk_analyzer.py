import numpy as np
import pandas as pd

def prices_to_returns(prices_df: pd.DataFrame) -> pd.DataFrame:
    # simple returns
    return prices_df.pct_change().dropna(how="all")


def annualized_volatility(returns: pd.Series, periods_per_year: int = 365) -> float:
    r = returns.dropna()
    if len(r) < 2:
        return float("nan")
    return float(r.std(ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02, periods_per_year: int = 365) -> float:
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
    r = returns.dropna()
    if len(r) == 0:
        return float("nan")
    return float(np.quantile(r, 1 - confidence))


def correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    return returns_df.corr()


def covariance_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    return returns_df.cov()