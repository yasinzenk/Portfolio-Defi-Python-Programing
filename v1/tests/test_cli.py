"""CLI integration tests for the V1 entry point."""

from __future__ import annotations

import json
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

import main as v1_main


class FakeClient:
    """Deterministic client stub for CLI tests."""

    def get_current_price(self, symbol: str, vs_currency: str = "USD") -> float:
        """Return a fixed price by symbol."""
        return 100.0 if symbol.upper() == "ETH" else 200.0

    def get_historical_daily(
        self,
        symbol: str,
        vs_currency: str = "USD",
        days: int = 30,
    ) -> pd.DataFrame:
        """Return a small deterministic price series."""
        dates = [date.today() - timedelta(days=4 - i) for i in range(5)]
        prices = [100.0, 101.0, 102.0, 103.0, 104.0]
        return pd.DataFrame({"price": prices}, index=dates)


def _write_portfolio(tmp_path: Path) -> Path:
    """Write a minimal portfolio JSON file and return its path."""
    payload = {
        "name": "test_portfolio",
        "assets": [
            {"symbol": "ETH", "crypto_id": "ETH", "amount": 1.0},
            {"symbol": "BTC", "crypto_id": "BTC", "amount": 2.0},
        ],
    }
    path = tmp_path / "portfolio.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _fake_setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Return a logger without file handlers to avoid side effects."""
    logger = logging.getLogger("v1_test_logger")
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    logger.setLevel(log_level)
    return logger


def test_cli_runs(monkeypatch, tmp_path: Path) -> None:
    """Run the V1 CLI and ensure it completes without errors."""
    portfolio_path = _write_portfolio(tmp_path)

    monkeypatch.setattr(v1_main, "CryptoCompareClient", lambda: FakeClient())
    monkeypatch.setattr(v1_main, "setup_logging", _fake_setup_logging)
    monkeypatch.setattr(v1_main.time, "sleep", lambda *_: None)

    argv = [
        "main.py",
        "--portfolio",
        str(portfolio_path),
        "--days",
        "30",
    ]
    monkeypatch.setattr(sys, "argv", argv)

    v1_main.main()
