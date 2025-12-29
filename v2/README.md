# DeFi Portfolio Risk Analyzer - V2

V2 extends V1 with configuration, caching, optimization, visualization,
and export features while keeping all V1 risk analytics.

## Installation

Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
.venv\Scripts\activate     # Windows
```

From the project root:

```bash
pip install -r requirements.txt
```

## Usage (from project root)

Analyze and export metrics:

```bash
python v2/main.py analyze --portfolio data/sample_portfolio.json --format csv --outdir outputs --pretty
```

Optimize allocation (max Sharpe):

```bash
python v2/main.py optimize --portfolio data/sample_portfolio.json --mode max-sharpe --format json --outdir outputs --pretty
```

Visualize:

```bash
python v2/main.py visualize --portfolio data/sample_portfolio.json --outdir figures --report
```

From `v2/`, you can run the same commands without the `v2/` prefix.
Relative paths like `data/sample_portfolio.json` are resolved against `v2/`.
`--pretty` is optional and only affects console readability.

## API Information

CryptoCompare works without an API key for basic usage, but rate limits apply.
To increase limits, set the `CRYPTOCOMPARE_API_KEY` environment variable.

## CLI Options (V2)

Common options:
- `--portfolio`: path to portfolio JSON (defaults to config value)
- `--days`: historical window in days
- `--rf`: risk-free rate
- `--confidence`: VaR confidence level
- `--outdir`: output directory for files
- `--pretty`: print readable tables in the console output
- `--offline`: use cache only (no network calls)
- `--refresh-cache`: bypass cache and refresh from API

Global options:
- `--log-level`: set console log level (DEBUG, INFO, WARNING, ERROR)
- `--quiet`: shortcut for WARNING output
- `--verbose`: shortcut for DEBUG output

Optimize options:
- `--mode`: `min-vol`, `max-sharpe`, `target-return`
- `--target-return`: required for `target-return` mode

Analyze/optimize export options:
- `--format`: `csv` or `json`

Visualize options:
- `--format`: `csv` or `json` for frontier export
- `--report`: generate `report.html` with tables, charts, and interpretation

## Configuration (config.yml)

Sections:
- `app`: app name and log file
- `data`: default portfolio path, cache directory, cache TTL
- `risk`: defaults for days, risk-free rate, confidence
- `optimization`: default target return and constraints
- `visualization`: output directory (theme reserved for future use)

`data.cache_ttl_seconds` controls cache freshness for historical prices.
`optimization.max_weight_per_asset` and `optimization.short_selling_allowed`
are used as per-asset bounds during optimization.

## Caching

Historical price series are cached as JSON in `cache/` with a timestamp.
The cache directory is created automatically when running the CLI.
Use `--offline` to rely on cache only, or `--refresh-cache` to force a refresh.

## Output Files

Analyze:
- `outputs/metrics.csv` or `outputs/metrics.json`
- `outputs/allocation.csv` or `outputs/allocation.json`
- `outputs/correlation.csv` or `outputs/correlation.json`

Optimize:
- `outputs/optimal_allocation.csv` or `outputs/optimal_allocation.json`

Visualize:
- `figures/risk_bars.png`
- `figures/correlation_heatmap.png`
- `figures/allocation.png`
- `figures/frontier.png`
- `figures/frontier.csv` or `figures/frontier.json`
- `figures/report.html` (if `--report` is used; includes interpretation and glossary)

## Expected Results

- Console output with metrics and allocation summaries.
- `outputs/` for CSV/JSON exports.
- `figures/` for plots.
- `cache/` for cached historical prices.
- `portfolio_analyzer_v2.log` in the current directory.

## Glossary (non-finance friendly)

- Volatility: how much prices fluctuate over time.
- Sharpe: return adjusted for risk (higher is better).
- VaR: worst expected loss at a given confidence level.
- Correlation: how assets move together.
- Efficient frontier: best risk/return trade-offs under constraints.

## Project Structure (V2)

```
v2/
├── main.py
├── config.py
├── config.yml
├── logger_config.py
├── cache.py
├── output_writer.py
├── optimizer.py
├── visualizer.py
├── portfolio_core.py
├── data_loader.py
├── data_fetcher.py
├── risk_analyzer.py
├── data/
│   └── sample_portfolio.json
├── tests/
│   ├── test_cli.py
│   ├── test_data_fetcher.py
│   ├── test_cache.py
│   ├── test_config.py
│   ├── test_data_loader.py
│   ├── test_optimizer.py
│   ├── test_portfolio_core.py
│   ├── test_risk_analyzer.py
│   └── test_visualizer.py
├── requirements.txt
└── README.md
```

## Running Tests (V2)

From `v2/`:

```bash
pytest tests/ -v
```

From the project root:

```bash
pytest v2/tests/ -v
```

## Notes on Versioning

- **V0**: minimal baseline (local prices, simple CLI).
- **V1**: real-time data + risk analytics.
- **V2**: configuration, caching, optimizer, visualizations, exports, tests.
