"""
CLI entry point for the DeFi portfolio risk analyzer (V1).

Usage:
    python main.py --portfolio <path_to_portfolio.json>

Example:
    python main.py --portfolio ../data/sample_portfolio.json
"""

import argparse
import pandas as pd
import time

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


def main() -> None:
    """
    Main function : parse arguments, fetch market data, compute risk metrics
    and display portfolio summary.
    """
    parser = argparse.ArgumentParser(
        description="V1 - DeFi Portfolio Risk Analyzer (tokens)",
        epilog="Example: python main.py --portfolio ../data/sample_portfolio.json --days 180"
    )
    parser.add_argument(
        "--portfolio",
        required=True,
        help="Path to the portfolio JSON file"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=180,
        help="Historical window in days (Coingecko)"
    )
    parser.add_argument(
        "--rf",
        type=float,
        default=0.02,
        help="Risk-free rate (annual, e.g. 0.02 for 2%)"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.95,
        help="VaR confidence level (e.g. 0.95)"
    )
    args = parser.parse_args()

    # Loading of the portfolio
    portfolio = load_portfolio_from_json(args.portfolio)

    api_client = CryptoCompareClient()

    # Fetch current prices to compute portfolio value/weights
    print("Fetching current prices...")
    updated_assets = []
    for asset in portfolio.assets:
        crypto_id = asset.crypto_id
        if not crypto_id:
            raise ValueError(
                f"Missing 'crypto_id' for asset '{asset.symbol}'. "
                "Add it in your JSON file."
            )
        
        current_price = api_client.get_current_price(symbol=crypto_id)
        updated_assets.append(
            type(asset)(
                symbol=asset.symbol,
                amount=asset.amount,
                price=current_price,
                crypto_id=crypto_id,
            )
        )
        time.sleep(0.5)  # Respectful delay between requests

    # Replace portfolio assets with priced versions
    portfolio.assets = updated_assets

    # Fetch historical prices
    print(f"Fetching {args.days} days of historical data...")
    price_series = {}

    for asset in portfolio.assets:
        crypto_id = asset.crypto_id
        # Validation already done above, but let's be safe
        if not crypto_id:
            raise ValueError(f"Missing 'crypto_id' for asset '{asset.symbol}'.")

        df = api_client.get_historical_daily(
            symbol=crypto_id, 
            days=args.days
        )
        time.sleep(0.5)  # Respectful delay
        price_series[asset.symbol] = df["price"]

    # Align all assets on common dates
    prices_df = pd.DataFrame(price_series).dropna(how="any")
    returns_df = prices_to_returns(prices_df)

    # Metrics computation (portfolio core)
    total = portfolio.total_value()
    weights = portfolio.weights()

    # Summary (same style as V0)
    print(f"\n{'='*40}")
    print(f"Portfolio: {portfolio.name}")
    print(f"{'='*40}")
    print(f"Total value: ${total:,.2f}")
    print(f"Number of assets: {len(portfolio.assets)}")
    print(f"Aligned history points: {len(prices_df)} days")
    print(f"{'='*40}\n")

    print("Allocation:")
    print("-" * 30)
    for sym, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(w * 100)
        print(f"  {sym:8} {w*100:6.2f}% {bar}")
    print()

    # Risk metrics per asset
    print("Risk metrics (per asset):")
    print("-" * 40)
    rows = []
    for sym in returns_df.columns:
        r = returns_df[sym]
        rows.append({
            "asset": sym,
            "vol_ann": annualized_volatility(r),
            "sharpe": sharpe_ratio(r, risk_free_rate=args.rf),
            "VaR": historical_var(r, confidence=args.confidence),
        })

    metrics_df = pd.DataFrame(rows).set_index("asset").round(4)
    print(metrics_df.to_string())
    print()

    # Portfolio-level volatility
    port_vol = portfolio_volatility(returns_df, weights)
    print(f"\nPortfolio volatility (annualized): {port_vol:.2%}")

    # Correlation matrix
    print("Correlation matrix:")
    print("-" * 40)
    corr = correlation_matrix(returns_df).round(3)
    print(corr.to_string())
    print()


if __name__ == "__main__":
    main()
