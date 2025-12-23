# DeFi Portfolio Analyzer

A Python project for analyzing DeFi portfolios with modular architecture and incremental development.

## Versions

This project follows an incremental development approach:

| Version | Description | Features |
|---------|-------------|----------|
| [v0](v0/) | Core portfolio analyzer | Static price data, allocation weights |
| [v1](v1/) | Risk analyzer | Real-time API prices, volatility, Sharpe ratio, VaR |

Each version is independently runnable with its own README.

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### V0 (Static Prices)

```bash
cd v0
python main.py --portfolio data/sample_portfolio.json
```

### V1 (Real-Time Data)

```bash
cd v1
pip install -r requirements.txt
python main.py --portfolio data/sample_portfolio.json --days 30
```

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
- V1: See `v1/requirements.txt`

## Testing (V1)

```bash
cd v1
pip install pytest
pytest tests/ -v
```

## License

Academic project.
