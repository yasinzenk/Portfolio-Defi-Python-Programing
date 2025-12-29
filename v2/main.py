"""
CLI entry point for the DeFi portfolio analyzer (V2).

Subcommands:
  analyze   -> compute metrics and export results
  optimize  -> compute optimal allocations (Markowitz)
  visualize -> generate plots
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path
from typing import Dict, List

import pandas as pd

from config import load_config
from data_fetcher import CryptoCompareClient
from data_loader import load_portfolio_from_json
from logger_config import setup_logging
from optimizer import efficient_frontier, max_sharpe, min_variance, target_return
from output_writer import (
    write_allocation_csv,
    write_allocation_json,
    write_dataframe_csv,
    write_dataframe_json,
    write_metrics_csv,
    write_metrics_json,
)
from report_writer import write_html_report
from risk_analyzer import (
    annualized_volatility,
    correlation_matrix,
    historical_var,
    portfolio_volatility,
    prices_to_returns,
    sharpe_ratio,
)
from visualizer import (
    plot_allocation_pie,
    plot_correlation_heatmap,
    plot_efficient_frontier,
    plot_risk_bars,
)

logger = logging.getLogger(__name__)


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add shared CLI arguments for all subcommands."""
    parser.add_argument("--portfolio", help="Path to the portfolio JSON file")
    parser.add_argument("--days", type=int, help="Historical window in days")
    parser.add_argument(
        "--rf",
        type=float,
        help="Annual risk-free rate (e.g. 0.02)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        help="VaR confidence level (e.g. 0.95)",
    )
    parser.add_argument("--outdir", help="Directory to save outputs")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print readable tables in the console output",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use cache only and avoid network calls",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Bypass cache and refresh from the API",
    )


def resolve_existing_path(path_str: str, base_dir: Path) -> Path:
    """
    Resolve a path relative to the version directory when possible.

    This makes root-level execution work with relative paths like
    ``data/sample_portfolio.json``.
    """
    path = Path(path_str)
    if path.is_absolute():
        return path

    candidate = base_dir / path
    if candidate.exists():
        return candidate

    return path


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="V2 - DeFi Portfolio Analyzer",
    )
    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce console output (WARNING and above)",
    )
    log_group.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose console output (DEBUG)",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Set console log level (DEBUG, INFO, WARNING, ERROR)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to the YAML configuration file (default: v2/config.yml)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Compute metrics")
    add_common_args(analyze)
    analyze.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format for metrics/allocation",
    )
    analyze.set_defaults(func=run_analyze)

    optimize = subparsers.add_parser("optimize", help="Optimize allocation")
    add_common_args(optimize)
    optimize.add_argument(
        "--mode",
        choices=["min-vol", "max-sharpe", "target-return"],
        default="max-sharpe",
        help="Optimization objective",
    )
    optimize.add_argument(
        "--target-return",
        type=float,
        default=None,
        help="Target return for target-return mode",
    )
    optimize.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format for allocation",
    )
    optimize.set_defaults(func=run_optimize)

    visualize = subparsers.add_parser("visualize", help="Generate plots")
    add_common_args(visualize)
    visualize.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format for frontier export",
    )
    visualize.add_argument(
        "--report",
        action="store_true",
        help="Generate a static HTML report in the output directory",
    )
    visualize.set_defaults(func=run_visualize)

    return parser


def resolve_params(args: argparse.Namespace, cfg, base_dir: Path) -> Dict[str, object]:
    """Resolve CLI overrides, config defaults, and normalized paths."""
    portfolio_path = args.portfolio or cfg.data.default_portfolio_path
    portfolio_path = resolve_existing_path(portfolio_path, base_dir)
    days = args.days if args.days is not None else cfg.risk.days
    rf = args.rf if args.rf is not None else cfg.risk.risk_free_rate
    confidence = args.confidence if args.confidence is not None else cfg.risk.confidence
    outdir = args.outdir or cfg.visualization.output_dir

    return {
        "portfolio_path": portfolio_path,
        "days": days,
        "rf": rf,
        "confidence": confidence,
        "outdir": outdir,
    }


def validate_cache_flags(args: argparse.Namespace) -> None:
    """Validate that cache-related flags are not in conflict."""
    if args.offline and args.refresh_cache:
        raise ValueError("Cannot use --offline and --refresh-cache together.")


def resolve_log_level(args: argparse.Namespace) -> str:
    """Resolve the desired console log level from CLI flags."""
    if args.quiet:
        return "WARNING"
    if args.verbose:
        return "DEBUG"
    if args.log_level:
        return str(args.log_level).upper()
    return "INFO"


def build_bounds(cfg, num_assets: int) -> list[tuple[float, float]]:
    """Build per-asset bounds from optimization constraints."""
    max_weight = float(cfg.optimization.max_weight_per_asset)
    if cfg.optimization.short_selling_allowed:
        lower = -max_weight
        upper = max_weight
    else:
        lower = 0.0
        upper = max_weight
    return [(lower, upper)] * num_assets


def _format_table(
    headers: list[str],
    rows: list[list[str]],
    align: list[str] | None = None,
) -> list[str]:
    """Format a simple ASCII table for console output."""
    if align is None:
        align = ["left"] * len(headers)

    safe_rows = [[str(cell) for cell in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in safe_rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def format_row(row: list[str]) -> str:
        cells = []
        for idx, cell in enumerate(row):
            if align[idx] == "right":
                cells.append(cell.rjust(widths[idx]))
            else:
                cells.append(cell.ljust(widths[idx]))
        return " | ".join(cells)

    separator = "-+-".join("-" * width for width in widths)
    lines = [format_row(headers), separator]
    lines.extend(format_row(row) for row in safe_rows)
    return lines


def _log_table(
    title: str,
    headers: list[str],
    rows: list[list[str]],
    align: list[str] | None = None,
) -> None:
    """Log a title followed by a formatted table."""
    logger.info(title)
    for line in _format_table(headers, rows, align):
        logger.info(line)


def load_portfolio_with_prices(
    client: CryptoCompareClient,
    portfolio_path: str,
    days: int,
    offline: bool = False,
) -> object:
    """Load a portfolio JSON file and attach prices."""
    portfolio = load_portfolio_from_json(portfolio_path)

    updated_assets: List[type(portfolio.assets[0])] = []
    for asset in portfolio.assets:
        crypto_id = asset.crypto_id
        if not crypto_id:
            raise ValueError(f"Missing 'crypto_id' for asset '{asset.symbol}'.")

        if offline:
            history = client.get_historical_daily(symbol=crypto_id, days=days)
            current_price = float(history["price"].iloc[-1])
        else:
            current_price = client.get_current_price(symbol=crypto_id)
        updated_assets.append(
            type(asset)(
                symbol=asset.symbol,
                amount=asset.amount,
                price=current_price,
                crypto_id=crypto_id,
            )
        )
        if not offline:
            time.sleep(0.5)

    portfolio.assets = updated_assets
    return portfolio


def fetch_returns_df(
    client: CryptoCompareClient,
    portfolio,
    days: int,
    offline: bool = False,
) -> pd.DataFrame:
    """Fetch historical prices and return aligned return series."""
    price_series: Dict[str, pd.Series] = {}

    for asset in portfolio.assets:
        crypto_id = asset.crypto_id
        if not crypto_id:
            raise ValueError(f"Missing 'crypto_id' for asset '{asset.symbol}'.")

        df_hist = client.get_historical_daily(symbol=crypto_id, days=days)
        price_series[asset.symbol] = df_hist["price"]
        if not offline:
            time.sleep(0.5)

    prices_df = pd.DataFrame(price_series).dropna(how="any")
    if len(prices_df) < 2:
        raise ValueError("Not enough data points after alignment")

    return prices_to_returns(prices_df)


def build_metrics_df(
    returns_df: pd.DataFrame,
    rf: float,
    confidence: float,
) -> pd.DataFrame:
    """Build a metrics DataFrame (volatility, Sharpe, VaR) per asset."""
    rows: list[dict[str, float | str]] = []
    for symbol in returns_df.columns:
        r = returns_df[symbol]
        rows.append(
            {
                "asset": symbol,
                "vol_ann": annualized_volatility(r),
                "sharpe": sharpe_ratio(r, risk_free_rate=rf),
                "VaR": historical_var(r, confidence=confidence),
            }
        )
    return pd.DataFrame(rows).set_index("asset").round(4)


def run_analyze(args: argparse.Namespace, cfg, base_dir: Path) -> None:
    """Run the analyze subcommand and export metrics/allocation."""
    params = resolve_params(args, cfg, base_dir)
    validate_cache_flags(args)
    client = CryptoCompareClient(
        cache_dir=cfg.data.cache_dir,
        cache_ttl_seconds=cfg.data.cache_ttl_seconds,
        offline=args.offline,
        refresh_cache=args.refresh_cache,
    )

    portfolio = load_portfolio_with_prices(
        client,
        params["portfolio_path"],
        params["days"],
        offline=args.offline,
    )
    returns_df = fetch_returns_df(
        client,
        portfolio,
        params["days"],
        offline=args.offline,
    )
    metrics_df = build_metrics_df(returns_df, params["rf"], params["confidence"])

    weights = portfolio.weights()
    corr = correlation_matrix(returns_df).round(3)

    logger.info("Portfolio: %s", portfolio.name)
    logger.info("Total value: %.2f", portfolio.total_value())
    logger.info("Portfolio volatility: %.4f", portfolio_volatility(returns_df, weights))

    outdir = Path(params["outdir"])
    if args.format == "csv":
        write_metrics_csv(metrics_df, outdir / "metrics.csv")
        write_allocation_csv(weights, outdir / "allocation.csv")
        write_dataframe_csv(corr, outdir / "correlation.csv")
    else:
        write_metrics_json(metrics_df, outdir / "metrics.json")
        write_allocation_json(weights, outdir / "allocation.json")
        write_dataframe_json(corr, outdir / "correlation.json", orient="split")

    logger.info("Saved outputs to: %s", outdir)

    if args.pretty:
        logger.info("")
        metrics_rows = []
        for asset, row in metrics_df.iterrows():
            metrics_rows.append(
                [
                    asset,
                    f"{row['vol_ann']:.4f}",
                    f"{row['sharpe']:.4f}",
                    f"{row['VaR']:.4f}",
                ]
            )
        _log_table(
            "Metrics (per asset):",
            ["asset", "vol_ann", "sharpe", "VaR"],
            metrics_rows,
            ["left", "right", "right", "right"],
        )
        logger.info("")

        allocation_rows = []
        for symbol, weight in sorted(
            weights.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            allocation_rows.append([symbol, f"{weight * 100:.2f}%"])
        _log_table(
            "Allocation:",
            ["asset", "weight"],
            allocation_rows,
            ["left", "right"],
        )
        logger.info("")

    logger.info("Correlation matrix:")
    for idx, row in corr.iterrows():
        row_vals = " ".join(f"{val:8.3f}" for val in row.values)
        logger.info("  %-8s %s", idx, row_vals)


def run_optimize(args: argparse.Namespace, cfg, base_dir: Path) -> None:
    """Run the optimize subcommand and export optimal allocation."""
    params = resolve_params(args, cfg, base_dir)
    validate_cache_flags(args)
    client = CryptoCompareClient(
        cache_dir=cfg.data.cache_dir,
        cache_ttl_seconds=cfg.data.cache_ttl_seconds,
        offline=args.offline,
        refresh_cache=args.refresh_cache,
    )

    portfolio = load_portfolio_with_prices(
        client,
        params["portfolio_path"],
        params["days"],
        offline=args.offline,
    )
    returns_df = fetch_returns_df(
        client,
        portfolio,
        params["days"],
        offline=args.offline,
    )
    bounds = build_bounds(cfg, returns_df.shape[1])

    if args.mode == "min-vol":
        result = min_variance(returns_df, bounds=bounds)
    elif args.mode == "max-sharpe":
        result = max_sharpe(
            returns_df,
            risk_free_rate=params["rf"],
            bounds=bounds,
        )
    else:
        target = args.target_return
        if target is None:
            target = cfg.optimization.target_return
        result = target_return(returns_df, target, bounds=bounds)

    outdir = Path(params["outdir"])
    if args.format == "csv":
        write_allocation_csv(result.weights, outdir / "optimal_allocation.csv")
    else:
        write_allocation_json(result.weights, outdir / "optimal_allocation.json")

    logger.info("Optimization mode: %s", args.mode)
    logger.info("Expected return: %.4f", result.expected_return)
    logger.info("Volatility: %.4f", result.volatility)
    logger.info("Sharpe: %.4f", result.sharpe)
    logger.info("Saved outputs to: %s", outdir)

    if args.pretty:
        logger.info("")
        allocation_rows = []
        for symbol, weight in sorted(
            result.weights.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            allocation_rows.append([symbol, f"{weight * 100:.2f}%"])
        _log_table(
            "Optimal allocation:",
            ["asset", "weight"],
            allocation_rows,
            ["left", "right"],
        )
        logger.info("")


def run_visualize(args: argparse.Namespace, cfg, base_dir: Path) -> None:
    """Run the visualize subcommand and save plots."""
    params = resolve_params(args, cfg, base_dir)
    validate_cache_flags(args)
    client = CryptoCompareClient(
        cache_dir=cfg.data.cache_dir,
        cache_ttl_seconds=cfg.data.cache_ttl_seconds,
        offline=args.offline,
        refresh_cache=args.refresh_cache,
    )

    portfolio = load_portfolio_with_prices(
        client,
        params["portfolio_path"],
        params["days"],
        offline=args.offline,
    )
    returns_df = fetch_returns_df(
        client,
        portfolio,
        params["days"],
        offline=args.offline,
    )
    metrics_df = build_metrics_df(returns_df, params["rf"], params["confidence"])

    weights = portfolio.weights()
    mean_returns = returns_df.mean() * 365
    weights_series = pd.Series(weights).reindex(mean_returns.index).fillna(0.0)
    portfolio_return = float(mean_returns @ weights_series)
    portfolio_vol = portfolio_volatility(returns_df, weights)
    portfolio_sharpe = (
        (portfolio_return - params["rf"]) / portfolio_vol
        if portfolio_vol > 0
        else float("nan")
    )
    corr = correlation_matrix(returns_df)
    bounds = build_bounds(cfg, returns_df.shape[1])
    frontier = efficient_frontier(returns_df, num_points=20, bounds=bounds)

    outdir = Path(params["outdir"])
    plot_risk_bars(metrics_df, outdir / "risk_bars.png")
    plot_correlation_heatmap(corr, outdir / "correlation_heatmap.png")
    plot_allocation_pie(weights, outdir / "allocation.png")
    plot_efficient_frontier(frontier, outdir / "frontier.png")

    if args.format == "csv":
        write_dataframe_csv(frontier, outdir / "frontier.csv")
    else:
        write_dataframe_json(frontier, outdir / "frontier.json", orient="records")

    if args.report:
        report_path = outdir / "report.html"
        image_paths = {
            "risk_bars": outdir / "risk_bars.png",
            "correlation_heatmap": outdir / "correlation_heatmap.png",
            "allocation": outdir / "allocation.png",
            "frontier": outdir / "frontier.png",
        }
        write_html_report(
            report_path,
            cfg.app.name,
            portfolio.name,
            portfolio.total_value(),
            portfolio_vol,
            portfolio_return,
            portfolio_sharpe,
            params,
            metrics_df,
            weights,
            corr.round(3),
            frontier,
            image_paths,
        )

    logger.info("Plots saved to: %s", outdir)


def main() -> None:
    """CLI entry point for V2."""
    parser = build_parser()
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    config_path = (
        resolve_existing_path(args.config, base_dir)
        if args.config is not None
        else base_dir / "config.yml"
    )
    cfg = load_config(config_path)
    log_level = resolve_log_level(args)
    logger_obj = setup_logging(log_level=log_level, log_file=cfg.app.log_file)
    global logger
    logger = logger_obj

    logger.info(cfg.app.name)
    logger.info("=" * 50)

    args.func(args, cfg, base_dir)

if __name__ == "__main__":
    main()
