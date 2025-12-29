# DeFi Portfolio Analyzer

A Python project for analyzing DeFi portfolios with modular architecture and incremental development.

## Versions

This project follows an incremental development approach:

| Version | Description | Features |
|---------|-------------|----------|
| [v0](v0/) | Core portfolio analyzer | Static price data, allocation weights |
| [v1](v1/) | Risk analyzer | Live prices, volatility, Sharpe ratio, VaR, correlation |

Each version is independently runnable with its own README.

## Installation

From the project root:

```bash
pip install -r requirements.txt
```

V0 uses the standard library only; dependencies are for V1.

## Quick Start (from project root)

### V0 (Static Prices)

```bash
python v0/main.py --portfolio data/sample_portfolio.json
```

### V1 (Real-Time Data)

```bash
python v1/main.py --portfolio data/sample_portfolio.json --days 30
```

## API Key (V1)

CryptoCompare works without an API key for basic usage, but rate limits apply.
To increase limits, set the `CRYPTOCOMPARE_API_KEY` environment variable.

## Expected Results

- V0: console summary and `portfolio_analyzer_v0.log` in the current directory.
- V1: console metrics/correlation and `portfolio_analyzer.log`.

## Project Structure

```
.
├── v0/                    # Basic portfolio analyzer
│   ├── main.py
│   ├── portfolio_core.py
│   ├── data_loader.py
│   ├── data/
│   └── README.md
│
├── v1/                    # Risk analyzer with API
│   ├── main.py
│   ├── portfolio_core.py
│   ├── data_loader.py
│   ├── data_fetcher.py
│   ├── risk_analyzer.py
│   ├── tests/
│   ├── data/
│   └── README.md
│
└── README.md              # This file
```

## Requirements

- Python 3.10+
- V0: No external dependencies (stdlib only)
- V1: See `requirements.txt` (or `v1/requirements.txt`)

## Testing

```bash
pytest v1/tests/ -v
```

## License

Academic project.
