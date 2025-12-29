"""
Visualization utilities for the DeFi portfolio analyzer.

This module provides minimal matplotlib helpers to save static charts
to disk for the CLI outputs.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def plot_risk_bars(metrics_df: pd.DataFrame, output_path: str | Path) -> Path:
    """
    Save a simple bar chart for volatility and Sharpe ratio per asset.

    Args:
        metrics_df: DataFrame indexed by asset with columns ``vol_ann`` and ``sharpe``.
        output_path: Destination path for the PNG file.

    Returns:
        The output path as a :class:`pathlib.Path`.
    """
    required = {"vol_ann", "sharpe"}
    missing = required.difference(metrics_df.columns)
    if missing:
        raise ValueError(f"Missing columns in metrics_df: {sorted(missing)}")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    assets = metrics_df.index.tolist()
    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    axes[0].bar(assets, metrics_df["vol_ann"].values, color="#4C78A8")
    axes[0].set_title("Annualized Volatility")
    axes[0].set_ylabel("Volatility")
    axes[0].grid(axis="y", alpha=0.3)

    axes[1].bar(assets, metrics_df["sharpe"].values, color="#F58518")
    axes[1].set_title("Sharpe Ratio")
    axes[1].set_ylabel("Sharpe")
    axes[1].set_xlabel("Asset")
    axes[1].grid(axis="y", alpha=0.3)
    axes[1].tick_params(axis="x", rotation=45)

    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    return output_path


def plot_correlation_heatmap(corr_df: pd.DataFrame, output_path: str | Path) -> Path:
    """
    Save a heatmap of the correlation matrix.

    Args:
        corr_df: Square correlation matrix with asset labels as index/columns.
        output_path: Destination path for the PNG file.

    Returns:
        The output path as a :class:`pathlib.Path`.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.imshow(corr_df.values, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_title("Correlation Matrix")

    labels = list(corr_df.columns)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)

    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    return output_path


def plot_allocation_pie(weights: dict[str, float], output_path: str | Path) -> Path:
    """
    Save a pie chart of portfolio allocation.

    Args:
        weights: Mapping of asset to portfolio weight.
        output_path: Destination path for the PNG file.

    Returns:
        The output path as a :class:`pathlib.Path`.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    labels = list(weights.keys())
    values = list(weights.values())

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(values, labels=labels, autopct="%1.1f%%")
    ax.set_title("Allocation")
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    return output_path


def plot_efficient_frontier(frontier_df: pd.DataFrame, output_path: str | Path) -> Path:
    """
    Save the efficient frontier scatter plot.

    Args:
        frontier_df: DataFrame with columns ``target_return`` and ``volatility``.
        output_path: Destination path for the PNG file.

    Returns:
        The output path as a :class:`pathlib.Path`.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(frontier_df["volatility"], frontier_df["target_return"], marker="o")
    ax.set_title("Efficient Frontier")
    ax.set_xlabel("Volatility")
    ax.set_ylabel("Return")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    return output_path
