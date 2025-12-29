"""Tests for optimizer helpers and objectives."""

from __future__ import annotations

import numpy as np
import pandas as pd

from optimizer import (
    efficient_frontier,
    max_sharpe,
    min_variance,
    target_return,
)


def _sample_returns() -> pd.DataFrame:
    """Return a small deterministic returns DataFrame."""
    return pd.DataFrame(
        {
            "A": [0.01, 0.02, -0.01, 0.03, 0.00],
            "B": [0.005, -0.002, 0.004, 0.001, 0.003],
        }
    )


def test_min_variance_weights_sum_to_one() -> None:
    """Check min-variance weights sum to one and stay in bounds."""
    returns = _sample_returns()
    result = min_variance(returns)
    total = sum(result.weights.values())
    assert np.isclose(total, 1.0, atol=1e-6)
    assert all(0.0 <= w <= 1.0 for w in result.weights.values())


def test_max_sharpe_weights_sum_to_one() -> None:
    """Check max-Sharpe weights sum to one and stay in bounds."""
    returns = _sample_returns()
    result = max_sharpe(returns, risk_free_rate=0.0)
    total = sum(result.weights.values())
    assert np.isclose(total, 1.0, atol=1e-6)
    assert all(0.0 <= w <= 1.0 for w in result.weights.values())


def test_target_return_feasible() -> None:
    """Ensure target return optimization returns finite outputs."""
    returns = _sample_returns()
    mean_returns = returns.mean() * 365
    target = float(mean_returns.mean())
    result = target_return(returns, target)
    assert np.isfinite(result.expected_return)
    assert np.isfinite(result.volatility)


def test_efficient_frontier_points() -> None:
    """Ensure efficient frontier output has required columns."""
    returns = _sample_returns()
    frontier = efficient_frontier(returns, num_points=5)
    assert {"target_return", "volatility"}.issubset(frontier.columns)
