# Project Structure Portfolio (VO)

## Core Architecture
1. Asset class
Represents a single asset or DeFi protocol position.

- Attributes
  - symbol : asset ticker (e.g. ETH, AAVE)
  - amount : quantity held
  - price : unit price (static in V0)

- Methods
  - market_value() → returns the total value of the position

1. Portfolio class
Represents a portfolio composed of multiple assets.

- Attributes
  - name : portfolio name
  - assets : list of Asset objects

- Methods
  - add_asset(asset) → add an asset to the portfolio
  - total_value() → compute total portfolio value
  - weights() → compute allocation weights per asset
  - load_portfolio() function

Utility function to load a portfolio from a JSON file.
- Read and validate JSON input
- Instantiate Portfolio and Asset objects
- Return a ready-to-use Portfolio

## CLI (main.py)

The CLI loads a portfolio file and prints:
- portfolio name
- total value
- asset allocation in %

## Input Format
```bash
{
  "name": "defi_test_portfolio",
  "assets": [
    { "symbol": "ETH", "amount": 1.5, "price": 2200 },
    { "symbol": "AAVE", "amount": 15, "price": 95 },
    { "symbol": "USDC", "amount": 2000, "price": 1.0 }
  ]
}
```
## How to run
```bash
cd v0
python main.py --portfolio ../data/sample_portfolio.json
```

## 💡 Next Improvements
- V1: Fetch real DeFi data (Coingecko, DefiLlama), compute returns and risk metrics
- V2: Portfolio optimization (Markowitz), advanced visualizations, full CLI