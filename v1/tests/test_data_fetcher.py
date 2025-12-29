"""Tests for the CryptoCompare data fetcher client (V1)."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

import data_fetcher
from data_fetcher import CryptoCompareClient


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


def test_get_api_error_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise RuntimeError when the API returns an error payload."""
    def fake_get(url: str, params=None, headers=None, timeout=None) -> DummyResponse:
        return DummyResponse({"Response": "Error", "Message": "Limit exceeded"})

    monkeypatch.setattr(data_fetcher.requests, "get", fake_get)

    client = CryptoCompareClient(timeout=1, max_retries=0)
    with pytest.raises(RuntimeError):
        client.get_current_price("eth", "usd")


def test_get_historical_daily_returns_df(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    client = CryptoCompareClient(timeout=1, max_retries=0)
    df = client.get_historical_daily("eth", "usd", days=2)

    assert list(df.columns) == ["price"]
    assert len(df) == 2
    assert isinstance(df.index[0], date)
