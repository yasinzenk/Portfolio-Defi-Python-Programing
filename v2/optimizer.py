"""
Portfolio optimization utilities (Markowitz).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable

import numpy as np
import pandas as pd
from scipy.optimize import minimize

logger = logging.getLogger(__name__)
_SOLVER_OPTIONS = {"maxiter": 2000, "ftol": 1e-9}


@dataclass(frozen=True)
class OptimizationResult:
    """Container for optimization results."""

    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe: float


def _annualized_mean(
    returns_df: pd.DataFrame,
    periods_per_year: int = 365,
) -> pd.Series:
    """Compute annualized mean returns."""
    return returns_df.mean() * periods_per_year


def _annualized_cov(
    returns_df: pd.DataFrame,
    periods_per_year: int = 365,
) -> pd.DataFrame:
    """Compute annualized covariance matrix."""
    return returns_df.cov() * periods_per_year


def _as_bounds(
    bounds: Iterable[tuple[float, float]] | None,
    n: int,
) -> list[tuple[float, float]]:
    """Return per-asset bounds, defaulting to long-only (0, 1)."""
    return list(bounds) if bounds is not None else [(0.0, 1.0)] * n


def _portfolio_volatility(weights: np.ndarray, cov: pd.DataFrame) -> float:
    """Compute portfolio volatility for given weights and covariance."""
    return float(np.sqrt(weights.T @ cov.values @ weights))


def _min_expected_return(
    returns_df: pd.DataFrame,
    bounds: Iterable[tuple[float, float]] | None = None,
) -> float:
    """Compute the minimum feasible expected return under bounds."""
    n = len(returns_df.columns)
    mean_returns = _annualized_mean(returns_df)
    bnds = _as_bounds(bounds, n)
    constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0},)
    x0 = np.repeat(1.0 / n, n)

    result = minimize(
        lambda w: float(w @ mean_returns.values),
        x0,
        bounds=bnds,
        constraints=constraints,
        method="SLSQP",
        options=_SOLVER_OPTIONS,
    )
    if not result.success:
        raise ValueError(f"Min-return optimization failed: {result.message}")
    return float(result.x @ mean_returns.values)


def _max_expected_return(
    returns_df: pd.DataFrame,
    bounds: Iterable[tuple[float, float]] | None = None,
) -> float:
    """Compute the maximum feasible expected return under bounds."""
    n = len(returns_df.columns)
    mean_returns = _annualized_mean(returns_df)
    bnds = _as_bounds(bounds, n)
    constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0},)
    x0 = np.repeat(1.0 / n, n)

    result = minimize(
        lambda w: -float(w @ mean_returns.values),
        x0,
        bounds=bnds,
        constraints=constraints,
        method="SLSQP",
        options=_SOLVER_OPTIONS,
    )
    if not result.success:
        raise ValueError(f"Max-return optimization failed: {result.message}")
    return float(result.x @ mean_returns.values)


def min_variance(
    returns_df: pd.DataFrame,
    bounds: Iterable[tuple[float, float]] | None = None,
) -> OptimizationResult:
    """Compute the minimum-variance portfolio under long-only bounds."""
    assets = list(returns_df.columns)
    n = len(assets)
    mean_returns = _annualized_mean(returns_df)
    cov = _annualized_cov(returns_df)

    constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0},)
    x0 = np.repeat(1.0 / n, n)
    bnds = _as_bounds(bounds, n)

    result = minimize(
        lambda w: w.T @ cov.values @ w,
        x0,
        bounds=bnds,
        constraints=constraints,
        method="SLSQP",
        options=_SOLVER_OPTIONS,
    )
    if not result.success:
        raise ValueError(f"Optimization failed: {result.message}")

    weights = dict(zip(assets, result.x))
    expected_return = float(result.x @ mean_returns.values)
    volatility = _portfolio_volatility(result.x, cov)
    sharpe = (expected_return / volatility) if volatility > 0 else float("nan")
    return OptimizationResult(weights, expected_return, volatility, sharpe)


def max_sharpe(
    returns_df: pd.DataFrame,
    risk_free_rate: float = 0.02,
    bounds: Iterable[tuple[float, float]] | None = None,
) -> OptimizationResult:
    """Compute the maximum Sharpe ratio portfolio."""
    assets = list(returns_df.columns)
    n = len(assets)
    mean_returns = _annualized_mean(returns_df)
    cov = _annualized_cov(returns_df)

    constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0},)
    x0 = np.repeat(1.0 / n, n)
    bnds = _as_bounds(bounds, n)

    def neg_sharpe(w: np.ndarray) -> float:
        port_return = float(w @ mean_returns.values)
        port_vol = _portfolio_volatility(w, cov)
        if port_vol == 0:
            return float("inf")
        return -(port_return - risk_free_rate) / port_vol

    result = minimize(
        neg_sharpe,
        x0,
        bounds=bnds,
        constraints=constraints,
        method="SLSQP",
        options=_SOLVER_OPTIONS,
    )
    if not result.success:
        raise ValueError(f"Optimization failed: {result.message}")

    weights = dict(zip(assets, result.x))
    expected_return = float(result.x @ mean_returns.values)
    volatility = _portfolio_volatility(result.x, cov)
    sharpe = (expected_return - risk_free_rate) / volatility if volatility > 0 else float(
        "nan"
    )
    return OptimizationResult(weights, expected_return, volatility, sharpe)


def target_return(
    returns_df: pd.DataFrame,
    target_return: float,
    bounds: Iterable[tuple[float, float]] | None = None,
) -> OptimizationResult:
    """Minimize variance subject to a target return constraint."""
    assets = list(returns_df.columns)
    n = len(assets)
    mean_returns = _annualized_mean(returns_df)
    cov = _annualized_cov(returns_df)

    constraints = (
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        {"type": "eq", "fun": lambda w: float(w @ mean_returns.values) - target_return},
    )
    x0 = np.repeat(1.0 / n, n)
    bnds = _as_bounds(bounds, n)

    result = minimize(
        lambda w: w.T @ cov.values @ w,
        x0,
        bounds=bnds,
        constraints=constraints,
        method="SLSQP",
        options=_SOLVER_OPTIONS,
    )
    if not result.success:
        raise ValueError(f"Optimization failed: {result.message}")

    weights = dict(zip(assets, result.x))
    expected_return = float(result.x @ mean_returns.values)
    volatility = _portfolio_volatility(result.x, cov)
    sharpe = expected_return / volatility if volatility > 0 else float("nan")
    return OptimizationResult(weights, expected_return, volatility, sharpe)


def efficient_frontier(
    returns_df: pd.DataFrame,
    num_points: int = 20,
    bounds: Iterable[tuple[float, float]] | None = None,
) -> pd.DataFrame:
    """Compute a simple efficient frontier as (return, volatility) points."""
    mean_returns = _annualized_mean(returns_df)
    min_ret = float(mean_returns.min())
    max_ret = float(mean_returns.max())

    try:
        min_ret = _min_expected_return(returns_df, bounds=bounds)
        max_ret = _max_expected_return(returns_df, bounds=bounds)
    except ValueError as exc:
        logger.warning("Falling back to naive target range: %s", exc)

    if min_ret > max_ret:
        min_ret, max_ret = max_ret, min_ret

    targets = np.linspace(min_ret, max_ret, num_points)
    records = []
    skipped = 0
    for target in targets:
        try:
            result = target_return(returns_df, target, bounds=bounds)
            records.append(
                {
                    "target_return": result.expected_return,
                    "volatility": result.volatility,
                }
            )
        except ValueError as exc:
            skipped += 1
            logger.debug("Skipping target %.6f: %s", target, exc)

    if skipped:
        logger.info("Efficient frontier: skipped %d/%d targets", skipped, num_points)

    return pd.DataFrame(records, columns=["target_return", "volatility"])
