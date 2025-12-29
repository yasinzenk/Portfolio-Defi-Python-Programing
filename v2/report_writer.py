"""
HTML report generation for V2 outputs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd


def _table_html(df: pd.DataFrame) -> str:
    """Return a minimal HTML table for a DataFrame."""
    return df.to_html(border=0, classes="table", justify="left")


def _weights_df(weights: Dict[str, float]) -> pd.DataFrame:
    """Convert allocation weights to a DataFrame."""
    return pd.DataFrame(
        [{"asset": k, "weight": v} for k, v in weights.items()]
    ).set_index("asset")


def _format_percent(value: float | int | None, decimals: int = 2) -> str:
    """Format a numeric ratio as a percentage string."""
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value) * 100:.{decimals}f}%"


def _format_ratio(value: float | int | None, decimals: int = 2) -> str:
    """Format a numeric ratio with fixed decimals."""
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.{decimals}f}"


def _join_assets(assets: list[str], max_items: int = 2) -> str:
    """Join asset names in a short, readable form."""
    if not assets:
        return "n/a"
    trimmed = assets[:max_items]
    if len(trimmed) == 1:
        return trimmed[0]
    return " and ".join(trimmed)


def _describe_portfolio_summary(
    portfolio_return: float,
    portfolio_vol: float,
    portfolio_sharpe: float,
) -> str:
    """Build a sentence describing the baseline portfolio metrics."""
    parts = []
    parts.append(
        "Baseline portfolio (current weights) has an annualized expected "
        f"return of {_format_percent(portfolio_return)} and volatility of "
        f"{_format_percent(portfolio_vol)}."
    )
    if not pd.isna(portfolio_sharpe):
        parts.append(f"Portfolio Sharpe ratio is {_format_ratio(portfolio_sharpe)}.")
    return " ".join(parts)


def _describe_volatility(metrics_df: pd.DataFrame) -> str:
    """Describe the volatility distribution across assets."""
    if "vol_ann" not in metrics_df.columns:
        return "Volatility metrics are not available for this run."
    vol = metrics_df["vol_ann"].dropna()
    if vol.empty:
        return "Volatility metrics could not be computed for the assets."
    q25 = vol.quantile(0.25)
    q75 = vol.quantile(0.75)
    high_assets = vol[vol >= q75].sort_values(ascending=False).index.tolist()
    low_assets = vol[vol <= q25].sort_values().index.tolist()
    return (
        f"Asset volatility ranges from {_format_percent(vol.min())} to "
        f"{_format_percent(vol.max())}, with a median of {_format_percent(vol.median())}. "
        f"Assets above the 75th percentile (>= {_format_percent(q75)}) are "
        f"relatively high-volatility (e.g. {_join_assets(high_assets)}), "
        f"while those below the 25th percentile (<= {_format_percent(q25)}) are "
        f"relatively low-volatility (e.g. {_join_assets(low_assets)})."
    )


def _describe_sharpe(metrics_df: pd.DataFrame) -> str:
    """Describe the Sharpe ratio distribution across assets."""
    if "sharpe" not in metrics_df.columns:
        return "Sharpe ratios are not available for this run."
    sharpe = metrics_df["sharpe"].dropna()
    if sharpe.empty:
        return "Sharpe ratios could not be computed for the assets."
    neg_count = int((sharpe < 0).sum())
    strong_count = int((sharpe >= 2).sum())
    best_asset = sharpe.idxmax()
    worst_asset = sharpe.idxmin()
    return (
        f"Sharpe ratios range from {_format_ratio(sharpe[worst_asset])} "
        f"({worst_asset}) to {_format_ratio(sharpe[best_asset])} ({best_asset}). "
        f"Negative Sharpe values ({neg_count} asset(s)) indicate returns that did not "
        f"compensate risk over the sample. A Sharpe >= 2 is often considered strong; "
        f"{strong_count} asset(s) meet that threshold."
    )


def _describe_var(metrics_df: pd.DataFrame, confidence: float) -> str:
    """Describe Value at Risk (VaR) across assets."""
    if "VaR" not in metrics_df.columns:
        return "VaR metrics are not available for this run."
    var = metrics_df["VaR"].dropna()
    if var.empty:
        return "VaR could not be computed for the assets."
    worst_asset = var.idxmin()
    best_asset = var.idxmax()
    confidence_pct = _format_percent(confidence, decimals=0)
    return (
        f"VaR at {confidence_pct} confidence estimates the worst expected loss over "
        f"the period. The most negative VaR is {_format_percent(var[worst_asset])} "
        f"({worst_asset}), while the least negative is {_format_percent(var[best_asset])} "
        f"({best_asset})."
    )


def _describe_weights(weights: Dict[str, float]) -> str:
    """Describe concentration and diversification of weights."""
    if not weights:
        return "Portfolio weights are not available."
    weights_series = pd.Series(weights).dropna()
    top_asset = weights_series.idxmax()
    max_weight = float(weights_series.max())
    zero_count = int((weights_series <= 0).sum())
    if max_weight >= 0.4:
        concentration = "highly concentrated"
    elif max_weight >= 0.25:
        concentration = "moderately concentrated"
    else:
        concentration = "fairly diversified"
    message = (
        f"Allocation is {concentration}. The largest weight is "
        f"{_format_percent(max_weight)} in {top_asset}."
    )
    if zero_count:
        message += f" {zero_count} asset(s) have zero weight."
    return message


def _describe_correlation(corr: pd.DataFrame) -> str:
    """Describe average correlation and diversification signal."""
    if corr.empty or corr.shape[0] < 2:
        return "Correlation needs at least two assets to interpret."
    mask = ~np.eye(corr.shape[0], dtype=bool)
    values = corr.where(mask).stack()
    if values.empty:
        return "Correlation metrics could not be computed for the assets."
    mean_corr = float(values.mean())
    if mean_corr >= 0.7:
        level = "high"
    elif mean_corr >= 0.4:
        level = "moderate"
    else:
        level = "low"
    return (
        f"Average pairwise correlation is {_format_ratio(mean_corr)}, which is {level}. "
        "Higher correlation means less diversification benefit."
    )


def _describe_frontier(
    frontier: pd.DataFrame,
    portfolio_return: float,
    portfolio_vol: float,
) -> list[str]:
    """Describe the efficient frontier range and baseline comparison."""
    if frontier.empty:
        return ["Efficient frontier could not be computed; no optimization comparison available."]
    min_ret = float(frontier["target_return"].min())
    max_ret = float(frontier["target_return"].max())
    min_vol = float(frontier["volatility"].min())
    max_vol = float(frontier["volatility"].max())
    items = [
        (
            "Efficient frontier spans expected returns from "
            f"{_format_percent(min_ret)} to {_format_percent(max_ret)} "
            f"and volatility from {_format_percent(min_vol)} to {_format_percent(max_vol)} "
            "under the current constraints."
        )
    ]
    if not pd.isna(portfolio_vol):
        if min_vol < portfolio_vol:
            items.append(
                f"Current volatility is {_format_percent(portfolio_vol)}; "
                "the frontier indicates a lower-risk allocation is feasible."
            )
        else:
            items.append(
                f"Current volatility is {_format_percent(portfolio_vol)} and "
                "already near the low end of the frontier range."
            )
    if not pd.isna(portfolio_return):
        if portfolio_return < min_ret:
            items.append(
                "Current expected return is below the frontier range, suggesting "
                "potential improvement under the same constraints."
            )
        elif portfolio_return < max_ret:
            items.append(
                "Higher expected returns appear feasible on the frontier, typically "
                "with higher volatility."
            )
        else:
            items.append(
                "Current expected return is above the frontier range; this can happen "
                "with short samples or estimation noise."
            )
    return items


def _list_html(items: list[str]) -> str:
    """Render a list of sentences as HTML list items."""
    safe_items = [f"<li>{escape(item)}</li>" for item in items if item]
    if not safe_items:
        return '<p class="note">No interpretation available.</p>'
    return "<ul>" + "".join(safe_items) + "</ul>"


def write_html_report(
    out_path: Path,
    app_name: str,
    portfolio_name: str,
    total_value: float,
    portfolio_vol: float,
    portfolio_return: float,
    portfolio_sharpe: float,
    params: Dict[str, object],
    metrics_df: pd.DataFrame,
    weights: Dict[str, float],
    corr: pd.DataFrame,
    frontier: pd.DataFrame,
    image_paths: Dict[str, Path],
) -> Path:
    """
    Write a static HTML report with tables and figures.

    Args:
        out_path: Destination HTML file path.
        app_name: Application title.
        portfolio_name: Portfolio name.
        total_value: Total portfolio value.
        portfolio_vol: Annualized portfolio volatility.
        portfolio_return: Annualized expected return for current weights.
        portfolio_sharpe: Portfolio Sharpe ratio based on current weights.
        params: Runtime parameters (days, rf, confidence).
        metrics_df: Metrics per asset.
        weights: Allocation weights.
        corr: Correlation matrix.
        frontier: Efficient frontier points.
        image_paths: Mapping of figure names to image paths.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    weights_df = _weights_df(weights)
    summary = {
        "Days": params.get("days"),
        "Risk-free rate": params.get("rf"),
        "Confidence": params.get("confidence"),
    }
    summary_df = pd.DataFrame(list(summary.items()), columns=["param", "value"])
    interpretation_items = [
        _describe_portfolio_summary(portfolio_return, portfolio_vol, portfolio_sharpe),
        _describe_volatility(metrics_df),
        _describe_sharpe(metrics_df),
        _describe_var(metrics_df, float(params.get("confidence", 0.95))),
        _describe_weights(weights),
        _describe_correlation(corr),
    ]
    interpretation_items.extend(
        _describe_frontier(frontier, portfolio_return, portfolio_vol)
    )
    interpretation_items.append(
        "Thresholds are relative to this dataset and should be treated as context-specific."
    )
    interpretation_html = _list_html(interpretation_items)
    figures_html = _list_html(
        [
            "Risk bars compare annualized volatility by asset.",
            "Correlation heatmap shows co-movement between assets (warmer means higher correlation).",
            "Allocation pie shows the current portfolio weights.",
            "Efficient frontier shows the best risk/return trade-offs under constraints.",
        ]
    )

    def img_tag(key: str, title: str) -> str:
        path = image_paths.get(key)
        if not path:
            return ""
        title_safe = escape(title)
        src_safe = escape(path.name)
        return (
            f"<h3>{title_safe}</h3>"
            f"<img src=\"{src_safe}\" alt=\"{title_safe}\" />"
        )

    html = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(app_name)} - Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    h1, h2, h3 {{ color: #222; }}
    .table {{ border-collapse: collapse; margin: 8px 0 20px 0; }}
    .table th, .table td {{ border: 1px solid #ddd; padding: 6px 10px; }}
    .summary {{ margin-bottom: 20px; }}
    img {{ max-width: 900px; width: 100%; height: auto; margin-bottom: 16px; }}
    .glossary li {{ margin-bottom: 6px; }}
    .note {{ color: #555; font-size: 0.95em; }}
  </style>
</head>
<body>
  <h1>{escape(app_name)} - Report</h1>
    <div class="summary">
    <p><strong>Portfolio:</strong> {escape(portfolio_name)}</p>
    <p><strong>Total value:</strong> {total_value:,.2f}</p>
    <p><strong>Expected return (annualized):</strong> {_format_percent(portfolio_return)}</p>
    <p><strong>Portfolio volatility (annualized):</strong> {_format_percent(portfolio_vol)}</p>
    <p><strong>Portfolio Sharpe:</strong> {_format_ratio(portfolio_sharpe)}</p>
    <p><strong>Generated:</strong> {escape(datetime.now(timezone.utc).isoformat())}</p>
  </div>

  <h2>Run Parameters</h2>
  {summary_df.to_html(index=False, border=0, classes="table")}

  <h2>Interpretation (auto-generated)</h2>
  {interpretation_html}

  <h2>Metrics (per asset)</h2>
  {_table_html(metrics_df)}

  <h2>Allocation</h2>
  {_table_html(weights_df)}

  <h2>Correlation</h2>
  {_table_html(corr)}

  <h2>Efficient Frontier</h2>
  {_table_html(frontier)}

  <h2>How to read the figures</h2>
  {figures_html}

  <h2>Figures</h2>
  {img_tag("risk_bars", "Risk bars")}
  {img_tag("correlation_heatmap", "Correlation heatmap")}
  {img_tag("allocation", "Allocation pie")}
  {img_tag("frontier", "Efficient frontier")}

  <h2>Glossary (non-finance friendly)</h2>
  <ul class="glossary">
    <li><strong>Volatility:</strong> how much prices fluctuate over time.</li>
    <li><strong>Sharpe:</strong> return adjusted for risk (higher is better).</li>
    <li><strong>VaR:</strong> worst expected loss at a given confidence level.</li>
    <li><strong>Correlation:</strong> how assets move together.</li>
    <li><strong>Efficient frontier:</strong> best risk/return trade-offs under constraints.</li>
  </ul>
  <p class="note">Historical data is not a guarantee of future performance.</p>
</body>
</html>
"""

    out_path.write_text(html.strip(), encoding="utf-8")
    return out_path
