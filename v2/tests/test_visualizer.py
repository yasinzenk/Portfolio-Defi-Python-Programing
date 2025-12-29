"""Tests for visualization helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from visualizer import (
    plot_allocation_pie,
    plot_correlation_heatmap,
    plot_efficient_frontier,
    plot_risk_bars,
)


def test_plot_risk_bars(tmp_path: Path) -> None:
    """Ensure risk bar plot saves to disk."""
    metrics = pd.DataFrame(
        {"vol_ann": [0.2, 0.3], "sharpe": [0.5, 0.8]},
        index=["ETH", "BTC"],
    )
    out = plot_risk_bars(metrics, tmp_path / "risk_bars.png")
    assert out.exists()


def test_plot_correlation_heatmap(tmp_path: Path) -> None:
    """Ensure correlation heatmap saves to disk."""
    corr = pd.DataFrame(
        [[1.0, 0.2], [0.2, 1.0]],
        index=["ETH", "BTC"],
        columns=["ETH", "BTC"],
    )
    out = plot_correlation_heatmap(corr, tmp_path / "corr.png")
    assert out.exists()


def test_plot_allocation_pie(tmp_path: Path) -> None:
    """Ensure allocation pie chart saves to disk."""
    weights = {"ETH": 0.6, "BTC": 0.4}
    out = plot_allocation_pie(weights, tmp_path / "allocation.png")
    assert out.exists()


def test_plot_efficient_frontier(tmp_path: Path) -> None:
    """Ensure efficient frontier plot saves to disk."""
    frontier = pd.DataFrame(
        {"target_return": [0.1, 0.12, 0.14], "volatility": [0.2, 0.22, 0.25]}
    )
    out = plot_efficient_frontier(frontier, tmp_path / "frontier.png")
    assert out.exists()
