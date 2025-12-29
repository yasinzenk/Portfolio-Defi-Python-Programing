# V1 - DeFi Portfolio Risk Analyzer

A portfolio analyzer that fetches real-time cryptocurrency prices and calculates risk metrics.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py --portfolio data/sample_portfolio.json --days 30
```

From the project root:

```bash
python v1/main.py --portfolio data/sample_portfolio.json --days 30
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--portfolio` | (required) | Path to portfolio JSON file |
| `--days` | 30 | Historical data window in days |
| `--rf` | 0.02 | Annual risk-free rate (2%) |
| `--confidence` | 0.95 | VaR confidence level (95%) |

## Portfolio JSON Format

```json
{
    "name": "my_portfolio",
    "assets": [
        {"symbol": "ETH", "crypto_id": "ETH", "amount": 1.5},
        {"symbol": "BTC", "crypto_id": "BTC", "amount": 0.1}
    ]
}
```

Required fields per asset:
- `symbol`: Display name
- `crypto_id`: CryptoCompare symbol (usually same as symbol)
- `amount`: Quantity held

## API Information

Uses the CryptoCompare API for price data.

- No API key required for basic usage
- Free tier: ~100 calls/hour
- For higher limits: set `CRYPTOCOMPARE_API_KEY` environment variable

## Project Structure

```
v1/
├── main.py           # CLI entry point
├── portfolio_core.py # Asset and Portfolio classes
├── data_loader.py    # JSON loading utilities
├── data_fetcher.py   # CryptoCompare API client
├── risk_analyzer.py  # Risk metrics calculations
├── data/
│   └── sample_portfolio.json
├── tests/
│   ├── test_portfolio_core.py
│   ├── test_risk_analyzer.py
│   └── test_data_loader.py
├── requirements.txt
└── README.md
```

## Risk Metrics

| Metric | Description |
|--------|-------------|
| Volatility | Annualized standard deviation of returns |
| Sharpe Ratio | Risk-adjusted return measure |
| VaR | Value at Risk at specified confidence level |
| Correlation | Pairwise correlation between assets |
| Portfolio Vol | Overall portfolio volatility with diversification |

## Running Tests

```bash
pytest tests/ -v
```

From the project root:

```bash
pytest v1/tests/ -v
```
