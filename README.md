# DeFi Portfolio Analyzer

A Python project for analyzing DeFi portfolios with modular architecture.

## Version

| Version | Description | Features |
|---------|-------------|----------|
| [v0](v0/) | Core portfolio analyzer | Static price data, allocation weights |

## Installation

From the project root:

```bash
pip install -r requirements.txt
```

V0 uses the standard library only; no external dependencies required.

## Quick Start (from project root)

### V0 (Static Prices)

```bash
python v0/main.py --portfolio data/sample_portfolio.json
```

## Expected Results

- V0: console summary and `portfolio_analyzer_v0.log` in the current directory.

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
└── README.md              # This file
```

## Requirements

- Python 3.10+
- V0: No external dependencies (stdlib only)

## License

Academic project.
