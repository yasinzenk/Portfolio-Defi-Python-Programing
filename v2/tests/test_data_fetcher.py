"""
Tests for the CryptoCompare data fetcher client.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
import pandas as pd

import data_fetcher
from data_fetcher import CryptoCompareClient
from cache import save_series


class DummyResponse:
    """Simple response stub for requests.get."""

    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        """Return the JSON payload."""
        return self._payload

    def raise_for_status(self) -> None:
        """Raise an error for non-2xx status codes."""
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")


def test_get_current_price_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return the expected price from a successful API response."""
    def fake_get(url: str, params=None, headers=None, timeout=None) -> DummyResponse:
        return DummyResponse({"USD": 123.45})

    monkeypatch.setattr(data_fetcher.requests, "get", fake_get)

    client = CryptoCompareClient(timeout=1, max_retries=0)
    price = client.get_current_price("eth", "usd")
    assert price == 123.45


def test_get_raises_on_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise ValueError when the API returns an error payload."""
    def fake_get(url: str, params=None, headers=None, timeout=None) -> DummyResponse:
        return DummyResponse({"Response": "Error", "Message": "Limit exceeded"})

    monkeypatch.setattr(data_fetcher.requests, "get", fake_get)

    client = CryptoCompareClient(timeout=1, max_retries=0)
    with pytest.raises(ValueError):
        client.get_current_price("eth", "usd")


def test_get_historical_daily_returns_df(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return a DataFrame indexed by date with a price column."""
    payload = {
        "Data": {
            "Data": [
                {"time": 1704067200, "close": 100.0},
                {"time": 1704153600, "close": 110.0},
            ]
        }
    }

    def fake_get(url: str, params=None, headers=None, timeout=None) -> DummyResponse:
        return DummyResponse(payload)

    monkeypatch.setattr(data_fetcher.requests, "get", fake_get)

    client = CryptoCompareClient(timeout=1, max_retries=0, cache_dir=None)
    df = client.get_historical_daily("eth", "usd", days=2)

    assert list(df.columns) == ["price"]
    assert len(df) == 2
    assert isinstance(df.index[0], date)
    assert df.iloc[0]["price"] == 100.0


def test_offline_uses_cached_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use cached data in offline mode without network calls."""
    series = pd.Series(
        [100.0, 101.0],
        index=[date.today() - timedelta(days=1), date.today()],
        name="price",
    )
    cache_path = tmp_path / "ETH_USD_2.json"
    save_series(cache_path, series)

    def fail_get(*args, **kwargs):
        raise RuntimeError("network call not expected")

    monkeypatch.setattr(data_fetcher.requests, "get", fail_get)

    client = CryptoCompareClient(
        timeout=1,
        max_retries=0,
        cache_dir=tmp_path,
        cache_ttl_seconds=3600,
        offline=True,
    )
    df = client.get_historical_daily("ETH", "USD", days=2)
    assert df["price"].iloc[-1] == 101.0


def test_offline_cache_miss_raises(tmp_path: Path) -> None:
    """Raise when offline mode has no cached data."""
    client = CryptoCompareClient(
        timeout=1,
        max_retries=0,
        cache_dir=tmp_path,
        cache_ttl_seconds=3600,
        offline=True,
    )
    with pytest.raises(FileNotFoundError):
        client.get_historical_daily("ETH", "USD", days=2)


def test_refresh_cache_bypasses_cached_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bypass cache when refresh_cache is enabled."""
    series = pd.Series(
        [100.0, 101.0],
        index=[date.today() - timedelta(days=1), date.today()],
        name="price",
    )
    cache_path = tmp_path / "ETH_USD_2.json"
    save_series(cache_path, series)

    payload = {
        "Data": {
            "Data": [
                {"time": 1704067200, "close": 200.0},
                {"time": 1704153600, "close": 210.0},
            ]
        }
    }

    def fake_get(url: str, params=None, headers=None, timeout=None) -> DummyResponse:
        return DummyResponse(payload)

    monkeypatch.setattr(data_fetcher.requests, "get", fake_get)

    client = CryptoCompareClient(
        timeout=1,
        max_retries=0,
        cache_dir=tmp_path,
        cache_ttl_seconds=3600,
        refresh_cache=True,
    )
    df = client.get_historical_daily("ETH", "USD", days=2)
    assert df["price"].iloc[0] == 200.0
