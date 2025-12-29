"""
Cache helpers for historical price series.

Stores data as JSON with a timestamp and a list of date/price pairs.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_cached_series(path: Path, ttl_seconds: int) -> pd.Series | None:
    """
    Load a cached price series if it is still fresh.

    Args:
        path: Path to the cache file.
        ttl_seconds: Maximum age of the cache in seconds.

    Returns:
        A pandas Series indexed by date, or None if missing/stale.
    """
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Invalid cache JSON: %s", exc)
        return None

    timestamp = payload.get("timestamp")
    if not isinstance(timestamp, (int, float)):
        return None

    if time.time() - float(timestamp) > ttl_seconds:
        return None

    records = payload.get("prices", [])
    if not isinstance(records, list) or len(records) == 0:
        return None

    dates = [r["date"] for r in records]
    prices = [r["price"] for r in records]
    idx = pd.to_datetime(dates).date
    return pd.Series(prices, index=idx, name="price")


def load_cached_series_allow_stale(path: Path) -> pd.Series | None:
    """
    Load a cached price series without checking freshness.

    Args:
        path: Path to the cache file.

    Returns:
        A pandas Series indexed by date, or None if missing/invalid.
    """
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Invalid cache JSON: %s", exc)
        return None

    records = payload.get("prices", [])
    if not isinstance(records, list) or len(records) == 0:
        return None

    dates = [r["date"] for r in records]
    prices = [r["price"] for r in records]
    idx = pd.to_datetime(dates).date
    return pd.Series(prices, index=idx, name="price")


def save_series(path: Path, series: pd.Series) -> None:
    """
    Save a price series to disk as JSON.

    Args:
        path: Destination path.
        series: pandas Series indexed by date with price values.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    for idx, value in series.items():
        date_str = idx.isoformat()
        records.append({"date": date_str, "price": float(value)})

    payload = {"timestamp": time.time(), "prices": records}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
