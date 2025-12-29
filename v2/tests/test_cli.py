"""
CLI integration tests for the V2 entry point.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

import main as v2_main
from config import (
    AppConfig,
    Config,
    DataConfig,
    OptimizationConfig,
    RiskConfig,
    VisualizationConfig,
)
from optimizer import OptimizationResult


class FakeClient:
    """Deterministic client stub for CLI tests."""

    def __init__(self, *args, **kwargs) -> None:
        pass

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
        dates = [date.today() - timedelta(days=2 - i) for i in range(3)]
        prices = [100.0, 101.0, 102.0]
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


def _make_config(
    tmp_path: Path,
    portfolio_path: Path,
    max_weight: float = 0.6,
    short_allowed: bool = False,
) -> Config:
    """Return a Config instance for CLI tests."""
    return Config(
        app=AppConfig(
            name="Test App",
            log_file=str(tmp_path / "test.log"),
        ),
        data=DataConfig(
            default_portfolio_path=str(portfolio_path),
            cache_dir=str(tmp_path / "cache"),
            cache_ttl_seconds=3600,
        ),
        risk=RiskConfig(
            days=30,
            risk_free_rate=0.02,
            confidence=0.95,
        ),
        optimization=OptimizationConfig(
            target_return=0.10,
            max_weight_per_asset=max_weight,
            short_selling_allowed=short_allowed,
        ),
        visualization=VisualizationConfig(
            theme="default",
            output_dir=str(tmp_path / "figures"),
        ),
    )


def test_cli_analyze_writes_outputs(monkeypatch, tmp_path: Path) -> None:
    """Run the analyze command and verify output files are created."""
    portfolio_path = _write_portfolio(tmp_path)
    cfg = _make_config(tmp_path, portfolio_path)
    outdir = tmp_path / "outputs"

    monkeypatch.setattr(v2_main, "CryptoCompareClient", FakeClient)
    monkeypatch.setattr(v2_main, "load_config", lambda _: cfg)
    monkeypatch.setattr(v2_main.time, "sleep", lambda *_: None)

    argv = [
        "main.py",
        "analyze",
        "--portfolio",
        str(portfolio_path),
        "--format",
        "csv",
        "--outdir",
        str(outdir),
    ]
    monkeypatch.setattr(sys, "argv", argv)

    v2_main.main()

    assert (outdir / "metrics.csv").exists()
    assert (outdir / "allocation.csv").exists()
    assert (outdir / "correlation.csv").exists()


def test_cli_optimize_applies_bounds(monkeypatch, tmp_path: Path) -> None:
    """Ensure optimization passes config-based bounds to the optimizer."""
    portfolio_path = _write_portfolio(tmp_path)
    cfg = _make_config(tmp_path, portfolio_path, max_weight=0.4)
    outdir = tmp_path / "outputs"
    captured: dict[str, object] = {}

    def fake_max_sharpe(returns_df, risk_free_rate=0.0, bounds=None):
        captured["bounds"] = bounds
        weights = {col: 1 / len(returns_df.columns) for col in returns_df.columns}
        return OptimizationResult(
            weights=weights,
            expected_return=0.1,
            volatility=0.2,
            sharpe=0.3,
        )

    monkeypatch.setattr(v2_main, "CryptoCompareClient", FakeClient)
    monkeypatch.setattr(v2_main, "load_config", lambda _: cfg)
    monkeypatch.setattr(v2_main.time, "sleep", lambda *_: None)
    monkeypatch.setattr(v2_main, "max_sharpe", fake_max_sharpe)

    argv = [
        "main.py",
        "optimize",
        "--portfolio",
        str(portfolio_path),
        "--mode",
        "max-sharpe",
        "--format",
        "csv",
        "--outdir",
        str(outdir),
    ]
    monkeypatch.setattr(sys, "argv", argv)

    v2_main.main()

    assert captured["bounds"] == [(0.0, 0.4), (0.0, 0.4)]
    assert (outdir / "optimal_allocation.csv").exists()


def test_cli_visualize_writes_report(monkeypatch, tmp_path: Path) -> None:
    """Run visualize with report output and verify files are created."""
    portfolio_path = _write_portfolio(tmp_path)
    cfg = _make_config(tmp_path, portfolio_path)
    outdir = tmp_path / "figures"

    def fake_frontier(returns_df, num_points=20, bounds=None):
        return pd.DataFrame(
            {
                "target_return": [0.1, 0.2],
                "volatility": [0.2, 0.3],
            }
        )

    monkeypatch.setattr(v2_main, "CryptoCompareClient", FakeClient)
    monkeypatch.setattr(v2_main, "load_config", lambda _: cfg)
    monkeypatch.setattr(v2_main.time, "sleep", lambda *_: None)
    monkeypatch.setattr(v2_main, "efficient_frontier", fake_frontier)

    argv = [
        "main.py",
        "visualize",
        "--portfolio",
        str(portfolio_path),
        "--outdir",
        str(outdir),
        "--format",
        "csv",
        "--report",
    ]
    monkeypatch.setattr(sys, "argv", argv)

    v2_main.main()

    assert (outdir / "frontier.csv").exists()
    report_path = outdir / "report.html"
    assert report_path.exists()
    assert "Glossary" in report_path.read_text(encoding="utf-8")
