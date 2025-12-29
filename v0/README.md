# V0 - DeFi Portfolio Analyzer

A simple portfolio analyzer that calculates allocation weights from static price data.

## Installation

No external dependencies required. Uses Python 3.10+ standard library only.

## Usage

```bash
python main.py --portfolio data/sample_portfolio.json
```

## Portfolio JSON Format

```json
{
    "name": "my_portfolio",
    "assets": [
        {"symbol": "ETH", "amount": 1.5, "price": 3000.0},
        {"symbol": "BTC", "amount": 0.1, "price": 95000.0}
    ]
}
```

Required fields per asset:
- `symbol`: Asset ticker
- `amount`: Quantity held
- `price`: Price in USD

## Project Structure

```
v0/
├── main.py           # CLI entry point
├── portfolio_core.py # Asset and Portfolio classes
├── data_loader.py    # JSON loading utilities
└── data/
    └── sample_portfolio.json
```

## Output Example

```
========================================
Portfolio: sample_portfolio
========================================
Total value: $10,850.00
Number of assets: 4
========================================

Allocation:
------------------------------
  BTC       43.78% #####################
  ETH       41.47% ####################
  AAVE      13.82% ######
  UNI        0.92%
```
