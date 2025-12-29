"""
CLI entry point for the DeFi portfolio analyzer (V0).

Usage:
    python main.py --portfolio <path_to_portfolio.json>

Example:
    python main.py --portfolio data/sample_portfolio.json

Version 0 focuses on validating the data model and I/O pipeline:
it loads a portfolio from a JSON file, computes total value and
allocation weights, and prints a simple summary to the console.
"""

from __future__ import annotations

import argparse
import logging
from typing import Dict

from logger_config import setup_logging
from data_loader import load_portfolio_from_json

logger = logging.getLogger(__name__)


def main() -> None:
    """
    Parse command-line arguments, load the portfolio, and display a summary.

    This entry point:
      1. Parses the ``--portfolio`` argument.
      2. Loads the portfolio from the provided JSON file.
      3. Computes total portfolio value and per-asset weights.
      4. Prints a simple allocation report to the console.

    V0 does not fetch any external market data and assumes that prices
    are already present in the JSON file.

    Raises:
        FileNotFoundError: If the portfolio file does not exist.
        ValueError: If the portfolio JSON is invalid or has wrong types.
        KeyError: If required fields are missing in the JSON file.
    """
    # ------------------------------------------------------------------
    # Logging setup
    # ------------------------------------------------------------------
    setup_logging(log_level="INFO")

    # ------------------------------------------------------------------
    # Argument parsing
    # ------------------------------------------------------------------
    parser = argparse.ArgumentParser(
        description="V0 - DeFi Portfolio Analyzer",
        epilog="Example: python main.py --portfolio data/sample_portfolio.json",
    )
    parser.add_argument(
        "--portfolio",
        required=True,
        help="Path to the portfolio JSON file",
    )
    args = parser.parse_args()

    logger.debug("Arguments: portfolio=%s", args.portfolio)

    # Basic sanity check on CLI argument
    assert args.portfolio, "--portfolio must be a non-empty path"

    # ------------------------------------------------------------------
    # Load portfolio
    # ------------------------------------------------------------------
    portfolio = load_portfolio_from_json(args.portfolio)
    logger.info(
        "Loaded portfolio '%s' with %d assets",
        portfolio.name,
        len(portfolio.assets),
    )

    # ------------------------------------------------------------------
    # Compute basic metrics
    # ------------------------------------------------------------------
    total: float = portfolio.total_value()
    weights: Dict[str, float] = portfolio.weights()

    logger.debug("Total portfolio value: %.4f", total)
    logger.debug("Computed weights for %d assets", len(weights))

    # ------------------------------------------------------------------
    # Summary output (console)
    # ------------------------------------------------------------------
    logger.info("")
    logger.info("=" * 40)
    logger.info("Portfolio: %s", portfolio.name)
    logger.info("=" * 40)
    logger.info(f"Total value: ${total:,.2f}")
    logger.info("Number of assets: %d", len(portfolio.assets))
    logger.info("=" * 40)
    logger.info("")

    logger.info("Allocation:")
    logger.info("-" * 30)
    for sym, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        bar = "#" * int(w * 50)
        logger.info("  %-8s %6.2f%% %s", sym, w * 100, bar)
    logger.info("")


if __name__ == "__main__":
    main()

