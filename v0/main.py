import argparse
from portfolio_core import load_portfolio

def main() -> None:
    parser = argparse.ArgumentParser(description="V0 _ DeFi Portfolio Core")
    parser.add_argument("--portfolio", required=True, help = "Path towards a portfolio JSON")
    args = parser.parse_args()

    portfolio = load_portfolio(args.portfolio)
    total = portfolio.total_value()
    weights = portfolio.weights()

    print(f"\nPortfolio: {portfolio.name}")
    print(f"Total value: {total:.2f}\n")

    print("Allocation:")
    for sym, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        print(f" - {sym}: {w*100:.2f}%")
    print("")

if __name__ == "__main__":
    main()

