# DeFi Portfolio Analyzer

A Python project for analyzing DeFi portfolios with modular architecture and incremental development.

## Versions

This project follows an incremental development approach:

| Version | Description | Features |
|---------|-------------|----------|
| [v0](v0/) | Core portfolio analyzer | Static price data, allocation weights |
| [v1](v1/) | Risk analyzer | Live prices, volatility, Sharpe ratio, VaR, correlation |
| [v2](v2/) | Advanced CLI | Config, caching, optimizer, visualizations, exports |

Each version is independently runnable with its own README.

## Installation

From the project root:

```bash
pip install -r requirements.txt
```

V0 uses the standard library only; dependencies are for V1/V2.

## Quick Start (from project root)

### V0 (Static Prices)

```bash
python v0/main.py --portfolio data/sample_portfolio.json
```

### V1 (Real-Time Data)

```bash
python v1/main.py --portfolio data/sample_portfolio.json --days 30
```

### V2 (Config, Optimization, Visuals)

```bash
python v2/main.py analyze --portfolio data/sample_portfolio.json --format csv --outdir outputs --pretty
python v2/main.py optimize --portfolio data/sample_portfolio.json --mode max-sharpe --format json --outdir outputs --pretty
python v2/main.py visualize --portfolio data/sample_portfolio.json --outdir figures --report
```

Note: relative paths like `data/sample_portfolio.json` are resolved against the
version folder (v0/v1/v2) when using the root-level commands above.
`--pretty` only affects console readability; CSV/JSON exports are unchanged.
If `--outdir` is omitted in v2, the default output directory comes from `v2/config.yml`
(typically `figures/`).

## API Key (V1/V2)

CryptoCompare works without an API key for basic usage, but rate limits apply.
To increase limits, set the `CRYPTOCOMPARE_API_KEY` environment variable.

## Expected Results

- V0: console summary and `portfolio_analyzer_v0.log` in the current directory.
- V1: console metrics/correlation and `portfolio_analyzer.log`.
- V2: exports/plots under the chosen output directory (`--outdir` or config default),
  `cache/` (historical data cache), and `portfolio_analyzer_v2.log`.
- Report PDF: `report.pdf` at the repository root.

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
├── v2/                    # Config + optimization + visualizations
│   ├── main.py
│   ├── config.py
│   ├── config.yml
│   ├── logger_config.py
│   ├── cache.py
│   ├── optimizer.py
│   ├── visualizer.py
│   ├── output_writer.py
│   ├── report_writer.py
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
- V1/V2: See `requirements.txt` (or `v1/requirements.txt`, `v2/requirements.txt`)

## Testing

```bash
pytest v1/tests/ -v
pytest v2/tests/ -v
```

## License

Academic project.
