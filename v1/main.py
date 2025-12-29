"""
CLI entry point for the DeFi portfolio risk analyzer (V1).

Usage:
    python main.py --portfolio <path_to_portfolio.json> [--days DAYS] [--rf RF] [--confidence CONFIDENCE]

Example:
    python main.py --portfolio data/sample_portfolio.json --days 30
"""

import argparse
import logging
import time
from pathlib import Path

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
from visualizer import plot_correlation_heatmap, plot_risk_bars


def main() -> None:
    """Parse arguments, fetch market data, compute risk metrics."""
    # Initialize logging (console + file)
    logger = setup_logging(log_level="INFO")
    logger.info("=" * 50)
    logger.info("DeFi Portfolio Risk Analyzer V1 - Starting")
    logger.info("=" * 50)

    # ------------------------------------------------------------------
    # Argument parsing
    # ------------------------------------------------------------------
    parser = argparse.ArgumentParser(
        description="V1 - DeFi Portfolio Risk Analyzer",
        epilog="Example: python main.py --portfolio data/sample_portfolio.json",
    )
    parser.add_argument(
        "--portfolio",
        required=True,
        help="Path to the portfolio JSON file",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Historical window in days",
    )
    parser.add_argument(
        "--rf",
        type=float,
        default=0.02,
        help="Annual risk-free rate, e.g. 0.02 for 2%% (default: 0.02)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.95,
        help="VaR confidence level, e.g. 0.95 for 95%% (default: 0.95)",
    )
    parser.add_argument(
        "--plots",
        action="store_true",
        help="Generate simple PNG visualizations (risk bars and correlation heatmap)",
    )
    parser.add_argument(
        "--outdir",
        default="outputs",
        help="Directory to save visualization files (default: outputs)",
    )

    args = parser.parse_args()
    logger.debug(
        "Arguments: portfolio=%s, days=%d, rf=%.4f, confidence=%.3f",
        args.portfolio,
        args.days,
        args.rf,
        args.confidence,
    )

    # ------------------------------------------------------------------
    # Load portfolio
    # ------------------------------------------------------------------
    try:
        portfolio = load_portfolio_from_json(args.portfolio)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        logger.error("Failed to load portfolio: %s", exc)
        raise

    api_client = CryptoCompareClient()

    # ------------------------------------------------------------------
    # Fetch current prices
    # ------------------------------------------------------------------
    logger.info("Fetching current prices...")
    updated_assets = []
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

        # Simple rate limiting to avoid hitting the API too aggressively
        time.sleep(0.5)

    portfolio.assets = updated_assets
    logger.info("Successfully fetched current prices for %d assets", len(updated_assets))

    # ------------------------------------------------------------------
    # Fetch historical prices
    # ------------------------------------------------------------------
    logger.info("Fetching %d days of historical data...", args.days)
    price_series: dict[str, pd.Series] = {}

    for asset in portfolio.assets:
        crypto_id = asset.crypto_id
        if not crypto_id:
            logger.error("Missing 'crypto_id' for asset '%s'", asset.symbol)
            raise ValueError(f"Missing 'crypto_id' for asset '{asset.symbol}'.")

        try:
            df_hist = api_client.get_historical_daily(
                symbol=crypto_id,
                days=args.days,
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
    total_value = portfolio.total_value()
    weights = portfolio.weights()

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
        sharpe = sharpe_ratio(r, risk_free_rate=args.rf)
        var = historical_var(r, confidence=args.confidence)

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

    # Header row 
    corr_header = "asset    " + " ".join(f"{a:>8}" for a in assets)
    logger.info("  %s", corr_header)
    logger.info("  %s", "-" * len(corr_header))

    # Each row: asset name + correlation values
    for idx, row in corr.iterrows():
        row_vals = " ".join(f"{val:8.3f}" for val in row.values)
        logger.info("  %-8s %s", idx, row_vals)

    logger.info("")
    if args.plots:
        output_dir = Path(args.outdir)
        bars_path = plot_risk_bars(metrics_df, output_dir / "risk_bars.png")
        heatmap_path = plot_correlation_heatmap(
            corr, output_dir / "correlation_heatmap.png"
        )
        logger.info("Plots saved to: %s", output_dir)
        logger.debug("Plot files: %s, %s", bars_path, heatmap_path)

    logger.info("=" * 50)
    logger.info("DeFi Portfolio Risk Analyzer V1 - Complete")
    logger.info("=" * 50)
    logger.info("Results saved to: portfolio_analyzer.log")


if __name__ == "__main__":
    main()
