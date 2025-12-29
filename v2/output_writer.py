"""
Output helpers for CSV/JSON exports.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _ensure_parent(path: Path) -> None:
    """Create parent directories for the given path if missing."""
    path.parent.mkdir(parents=True, exist_ok=True)


def write_metrics_csv(metrics_df: pd.DataFrame, path: str | Path) -> Path:
    """
    Write metrics DataFrame to CSV.
    """
    path = Path(path)
    _ensure_parent(path)
    metrics_df.to_csv(path)
    return path


def write_metrics_json(metrics_df: pd.DataFrame, path: str | Path) -> Path:
    """
    Write metrics DataFrame to JSON (records).
    """
    path = Path(path)
    _ensure_parent(path)
    records = metrics_df.reset_index().to_dict(orient="records")
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return path


def write_allocation_csv(weights: dict[str, float], path: str | Path) -> Path:
    """
    Write allocation weights to CSV.
    """
    path = Path(path)
    _ensure_parent(path)
    df = pd.DataFrame(list(weights.items()), columns=["asset", "weight"])
    df.to_csv(path, index=False)
    return path


def write_allocation_json(weights: dict[str, float], path: str | Path) -> Path:
    """
    Write allocation weights to JSON.
    """
    path = Path(path)
    _ensure_parent(path)
    path.write_text(json.dumps(weights, indent=2), encoding="utf-8")
    return path


def write_dataframe_csv(df: pd.DataFrame, path: str | Path) -> Path:
    """
    Write a DataFrame to CSV, keeping index values.
    """
    path = Path(path)
    _ensure_parent(path)
    df.to_csv(path)
    return path


def write_dataframe_json(
    df: pd.DataFrame,
    path: str | Path,
    orient: str = "split",
) -> Path:
    """
    Write a DataFrame to JSON.

    Args:
        df: DataFrame to serialize.
        path: Destination path.
        orient: pandas JSON orientation (default: "split").
    """
    path = Path(path)
    _ensure_parent(path)
    path.write_text(df.to_json(orient=orient, indent=2), encoding="utf-8")
    return path
