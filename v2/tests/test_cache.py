"""Tests for cache helpers."""

from __future__ import annotations

import json
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from cache import (
    load_cached_series,
    load_cached_series_allow_stale,
    save_series,
)


def test_cache_roundtrip(tmp_path: Path) -> None:
    """Ensure cached series round-trips correctly within TTL."""
    series = pd.Series(
        [100.0, 101.5],
        index=[date.today() - timedelta(days=1), date.today()],
        name="price",
    )
    path = tmp_path / "prices.json"
    save_series(path, series)

    loaded = load_cached_series(path, ttl_seconds=3600)
    assert loaded is not None
    assert list(loaded.values) == list(series.values)


def test_cache_ttl_expired(tmp_path: Path) -> None:
    """Ensure expired cache entries are ignored."""
    series = pd.Series([10.0], index=[date.today()], name="price")
    path = tmp_path / "prices.json"
    save_series(path, series)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["timestamp"] = time.time() - 7200
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_cached_series(path, ttl_seconds=3600)
    assert loaded is None


def test_cache_allow_stale_returns_series(tmp_path: Path) -> None:
    """Return cached series even when the TTL is expired."""
    series = pd.Series([10.0], index=[date.today()], name="price")
    path = tmp_path / "prices.json"
    save_series(path, series)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["timestamp"] = time.time() - 7200
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_cached_series_allow_stale(path)
    assert loaded is not None
