"""
CLI entry point for the DeFi portfolio core.

Usage:
    python main.py --portfolio <path_to_portfolio.json>

Example:
    python main.py --portfolio ../data/sample_portfolio.json

"""

import argparse
from data_loader import load_portfolio_from_json

def main() -> None:
    """
    Main function : parse arguments and display portfolio summary.
    """
    parser = argparse.ArgumentParser(
        description="V0 - DeFi Portfolio Core",
        epilog="Example: python main.py --portfolio ../data/sample_portfolio.json"
    )
    parser.add_argument(
        "--portfolio",
        required=True,
        help="Path to the portfolio JSON file"
    )
    args = parser.parse_args()

    # Chargement du portfolio
    portfolio = load_portfolio_from_json(args.portfolio)

    # Calcul des métriques
    total = portfolio.total_value()
    weights = portfolio.weights()

    # Affichage du résumé
    print(f"\n{'='*40}")
    print(f"Portfolio: {portfolio.name}")
    print(f"{'='*40}")
    print(f"Total value: ${total:,.2f}")
    print(f"Number of assets: {len(portfolio.assets)}")
    print(f"{'='*40}\n")

    print("Allocation (from highest to lowest):")
    print("-" * 30)
    for sym, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(w * 20)  # Barre visuelle
        print(f"  {sym:8} {w*100:6.2f}% {bar}")
    print()


if __name__ == "__main__":
    main()