# DeFi Portfolio Risk Analyzer – V2

This repository contains three versions of a DeFi portfolio analyzer:

- **V0**: Minimal version (local prices in JSON, simple CLI).
- **V1**: Adds real-time market data and risk metrics.
- **V2**: Builds on V1 with YAML configuration, better logging, and extended architecture (ready for optimization, visualization, caching, and tests).

---

## Installation

From the project root:

```bash
pip install -r v1/requirements.txt
pip install -r v2/requirements.txt
```

Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate # macOS / Linux

.venv\Scripts\activate # Windows
```

## V2 – DeFi Portfolio Risk Analyzer (Config-Driven)

### Overview

V2 extends V1 by:

- Introducing a **YAML configuration file** (`config.yml`).
- Adding a **`config.py` module** with typed dataclasses.
- Integrating configuration into `main.py` (CLI overrides YAML).
- Reusing structured logging (`logger_config.py`).
- Providing dedicated unit tests for configuration.

It keeps V1’s features (data loading, API, risk metrics) and prepares the codebase for further enhancements (Markowitz optimizer, Plotly visualizations, caching, more subcommands).

### Usage

From `v2/`:

```bash
python main.py --portfolio data/sample_portfolio.json
```

Explicitly overriding parameters and config file:

python main.py
--portfolio data/sample_portfolio.json
--days 30
--rf 0.02
--confidence 0.95
--config config.yml

### Configuration (config.yml)

Sections:

- `app`: high-level app settings (name, log file).
- `data`: default portfolio path, cache directory.
- `risk`: default risk parameters used when CLI overrides are absent.
- `optimization`: parameters reserved for Markowitz optimizer (V2+).
- `visualization`: defaults for future Plotly charts.

### Project Structure – V2

v2/
├── main.py # CLI entry point (uses YAML config + logging)
├── config.py # YAML configuration loader (Config dataclasses)
├── logger_config.py # Logging configuration (console + file handlers)
├── portfolio_core.py # Asset and Portfolio classes
├── data_loader.py # JSON loading utilities
├── data_fetcher.py # CryptoCompare API client
├── risk_analyzer.py # Risk metrics calculations
├── data/
│ └── sample_portfolio_v2.json
├── tests/
│ ├── test_portfolio_core.py
│ ├── test_risk_analyzer.py
│ ├── test_data_loader.py
│ └── test_config.py
├── requirements.txt
└── README.md

### Running Tests (V2)

From `v2/`:

```bash
pip install pytest
pytest tests/ -v
```

Tests cover:

- `portfolio_core` (Asset, Portfolio).
- `risk_analyzer` (returns, volatility, Sharpe, VaR, correlation, portfolio vol).
- `data_loader` (JSON loading, validation).
- `config` (defaults, overrides, invalid YAML).

---

## Notes on Versioning

- **V0** lives in `v0/` and provides the minimal baseline (local prices, simple CLI, first tests & logging).
- **V1** focuses on real-time data and risk analytics.
- **V2** focuses on architecture & configuration improvements, and prepares the ground for:
  - Markowitz portfolio optimization (`optimizer.py`),
  - visualization (`visualizer.py` with Plotly),
  - additional CLI subcommands (`analyze`, `optimize`, `visualize`),
  - more comprehensive unit tests.

All versions can be run independently from their respective subfolders, using the same virtual environment.