"""
CLI entry point for the DeFi portfolio risk analyzer (V2).

Usage:
    python main.py --portfolio <path_to_portfolio.json> [--days DAYS] [--rf RF] [--confidence CONFIDENCE] [--config CONFIG]

Example:
    python main.py --portfolio data/sample_portfolio.json --days 30
"""

from __future__ import annotations

import argparse
import logging
import time
from typing import Dict, List

import pandas as pd

from logger_config import setup_logging
from data_loader import load_portfolio_from_json
from data_fetcher import CryptoCompareClient
from risk_analyzer import (
    prices_to_returns,
    annualized_volatility,
    sharpe_ratio,
    historical_var,
    correlation_matrix,
    portfolio_volatility,
)
from config import load_config

logger = logging.getLogger(__name__)


def main() -> None:
    """Parse arguments, fetch market data, compute risk metrics."""
    # ------------------------------------------------------------------
    # Argument parsing
    # ------------------------------------------------------------------
    parser = argparse.ArgumentParser(
        description="V2 - DeFi Portfolio Risk Analyzer",
        epilog="Example: python main.py --portfolio data/sample_portfolio.json --days 30",
    )
    parser.add_argument(
        "--portfolio",
        help="Path to the portfolio JSON file (overrides config.data.default_portfolio_path)",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Historical window in days (overrides config.risk.days)",
    )
    parser.add_argument(
        "--rf",
        type=float,
        help="Annual risk-free rate, e.g. 0.02 for 2%% (overrides config.risk.risk_free_rate)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        help="VaR confidence level, e.g. 0.95 for 95%% (overrides config.risk.confidence)",
    )
    parser.add_argument(
        "--config",
        default="config.yml",
        help="Path to the YAML configuration file (default: config.yml)",
    )

    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load configuration
    # ------------------------------------------------------------------
    cfg = load_config(args.config)

    # Initialize logging (console + file) using config
    logger_obj = setup_logging(log_level="INFO", log_file=cfg.app.log_file)
    # Use module-level logger variable
    global logger
    logger = logger_obj

    logger.info("=" * 50)
    logger.info(cfg.app.name)
    logger.info("=" * 50)

    logger.debug(
        "Arguments: portfolio=%s, days=%s, rf=%s, confidence=%s, config=%s",
        args.portfolio,
        args.days,
        args.rf,
        args.confidence,
        args.config,
    )

    # Resolve effective parameters (CLI overrides YAML)
    portfolio_path: str = args.portfolio or cfg.data.default_portfolio_path
    days: int = args.days if args.days is not None else cfg.risk.days
    rf: float = args.rf if args.rf is not None else cfg.risk.risk_free_rate
    confidence: float = (
        args.confidence if args.confidence is not None else cfg.risk.confidence
    )

    logger.info("Using portfolio file: %s", portfolio_path)
    logger.info("Risk parameters: days=%d, rf=%.4f, confidence=%.3f", days, rf, confidence)

    # ------------------------------------------------------------------
    # Load portfolio
    # ------------------------------------------------------------------
    try:
        portfolio = load_portfolio_from_json(portfolio_path)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        logger.error("Failed to load portfolio: %s", exc)
        raise

    api_client = CryptoCompareClient()

    # ------------------------------------------------------------------
    # Fetch current prices
    # ------------------------------------------------------------------
    logger.info("Fetching current prices...")
    updated_assets: List[type(portfolio.assets[0])] = []
    for asset in portfolio.assets:
        crypto_id = asset.crypto_id
        if not crypto_id:
            logger.error("Missing 'crypto_id' for asset '%s'", asset.symbol)
            raise ValueError(
                f"Missing 'crypto_id' for asset '{asset.symbol}'. "
                "Add it in your JSON file."
            )

        try:
            current_price = api_client.get_current_price(symbol=crypto_id)
            updated_assets.append(
                type(asset)(
                    symbol=asset.symbol,
                    amount=asset.amount,
                    price=current_price,
                    crypto_id=crypto_id,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch price for %s: %s", asset.symbol, exc)
            raise

        time.sleep(0.5)

    portfolio.assets = updated_assets
    logger.info("Successfully fetched current prices for %d assets", len(updated_assets))

    # ------------------------------------------------------------------
    # Fetch historical prices
    # ------------------------------------------------------------------
    logger.info("Fetching %d days of historical data...", days)
    price_series: Dict[str, pd.Series] = {}

    for asset in portfolio.assets:
        crypto_id = asset.crypto_id
        if not crypto_id:
            logger.error("Missing 'crypto_id' for asset '%s'", asset.symbol)
            raise ValueError(f"Missing 'crypto_id' for asset '{asset.symbol}'.")

        try:
            df_hist = api_client.get_historical_daily(
                symbol=crypto_id,
                days=days,
            )
            price_series[asset.symbol] = df_hist["price"]
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch historical data for %s: %s", asset.symbol, exc)
            raise

        time.sleep(0.5)

    # ------------------------------------------------------------------
    # Align time series and compute returns
    # ------------------------------------------------------------------
    logger.info("Aligning %d assets on common dates...", len(price_series))
    prices_df = pd.DataFrame(price_series).dropna(how="any")
    returns_df = prices_to_returns(prices_df)
    logger.info("Aligned to %d common dates", len(prices_df))

    if len(prices_df) < 2:
        logger.error("Not enough data points after alignment for analysis")
        raise ValueError("Not enough data points after alignment")

    # ------------------------------------------------------------------
    # Portfolio-level quantities
    # ------------------------------------------------------------------
    total_value: float = portfolio.total_value()
    weights: Dict[str, float] = portfolio.weights()

    logger.debug("Total portfolio value: %.4f", total_value)
    logger.debug("Computed weights for %d assets", len(weights))

    # ------------------------------------------------------------------
    # Portfolio summary
    # ------------------------------------------------------------------
    logger.info("")
    logger.info("=" * 50)
    logger.info("Portfolio: %s", portfolio.name)
    logger.info("=" * 50)
    logger.info(f"Total value: ${total_value:,.2f}")
    logger.info("Number of assets: %d", len(portfolio.assets))
    logger.info("Aligned history points: %d days", len(prices_df))
    logger.info("=" * 50)
    logger.info("")

    # ------------------------------------------------------------------
    # Allocation
    # ------------------------------------------------------------------
    logger.info("Allocation:")
    logger.info("-" * 50)
    for symbol, weight in sorted(
        weights.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        bar = "#" * int(weight * 50)
        logger.info("  %-8s %6.2f%% %s", symbol, weight * 100, bar)
    logger.info("")

    # ------------------------------------------------------------------
    # Risk metrics per asset
    # ------------------------------------------------------------------
    logger.info("Risk metrics (per asset):")
    logger.info("-" * 74)

    rows: list[dict[str, float | str]] = []
    for symbol in returns_df.columns:
        r = returns_df[symbol]
        vol = annualized_volatility(r)
        sharpe = sharpe_ratio(r, risk_free_rate=rf)
        var = historical_var(r, confidence=confidence)

        rows.append(
            {
                "asset": symbol,
                "vol_ann": vol,
                "sharpe": sharpe,
                "VaR": var,
            }
        )

        logger.debug(
            "Metrics for %s: vol_ann=%.6f sharpe=%.6f VaR=%.6f",
            symbol,
            vol,
            sharpe,
            var,
        )

    metrics_df = pd.DataFrame(rows).set_index("asset").round(4)

    header = f"{'asset':8} {'vol_ann':>10} {'sharpe':>10} {'VaR':>10}"
    logger.info("  %s", header)
    logger.info("  %s", "-" * len(header))

    for asset_name, row in metrics_df.iterrows():
        logger.info(
            "  %-8s %10.4f %10.4f %10.4f",
            asset_name,
            row["vol_ann"],
            row["sharpe"],
            row["VaR"],
        )

    logger.info("")

    # ------------------------------------------------------------------
    # Portfolio-level volatility
    # ------------------------------------------------------------------
    port_vol = portfolio_volatility(returns_df, weights)
    logger.info("Portfolio volatility (annualized): %.2f%%", port_vol * 100)
    logger.debug("Portfolio volatility (decimal): %.6f", port_vol)
    logger.info("")

    # ------------------------------------------------------------------
    # Correlation matrix
    # ------------------------------------------------------------------
    logger.info("Correlation matrix:")
    logger.info("-" * 74)

    corr = correlation_matrix(returns_df).round(3)
    assets = list(corr.columns)

    corr_header = "asset    " + " ".join(f"{a:>8}" for a in assets)
    logger.info("  %s", corr_header)
    logger.info("  %s", "-" * len(corr_header))

    for idx, row in corr.iterrows():
        row_vals = " ".join(f"{val:8.3f}" for val in row.values)
        logger.info("  %-8s %s", idx, row_vals)

    logger.info("")
    logger.info("=" * 50)
    logger.info("DeFi Portfolio Risk Analyzer V2 - Complete")
    logger.info("=" * 50)
    logger.info("Results saved to: %s", cfg.app.log_file)


if __name__ == "__main__":
    main()

