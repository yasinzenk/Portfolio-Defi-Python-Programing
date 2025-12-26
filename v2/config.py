"""
Configuration management for the DeFi Portfolio Analyzer (V2).

This module loads application configuration from a YAML file and exposes
a typed Config object to the rest of the codebase. It centralizes all
tunable parameters (paths, risk settings, optimization constraints, etc.)
so that behavior can be changed without modifying the Python code.

Typical usage:

    from config import load_config

    cfg = load_config()  # defaults to "config.yml"
    days = cfg.risk.days
    rf = cfg.risk.risk_free_rate
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses for strongly-typed configuration sections
# ---------------------------------------------------------------------------


@dataclass
class AppConfig:
    """Application-level settings."""
    name: str
    log_file: str


@dataclass
class DataConfig:
    """Data input/output settings."""
    default_portfolio_path: str
    cache_dir: str


@dataclass
class RiskConfig:
    """Risk analysis parameters."""
    days: int
    risk_free_rate: float
    confidence: float


@dataclass
class OptimizationConfig:
    """Portfolio optimization parameters."""
    target_return: float
    max_weight_per_asset: float
    short_selling_allowed: bool


@dataclass
class VisualizationConfig:
    """Visualization and plotting settings."""
    theme: str
    output_dir: str


@dataclass
class Config:
    """Top-level configuration object aggregating all sections."""
    app: AppConfig
    data: DataConfig
    risk: RiskConfig
    optimization: OptimizationConfig
    visualization: VisualizationConfig


# ---------------------------------------------------------------------------
# Default configuration (used as a base and overridden by YAML)
# ---------------------------------------------------------------------------


def _default_config_dict() -> Dict[str, Any]:
    """
    Return a dictionary with default configuration values.

    These defaults are used when some keys are missing in the YAML file.
    """
    return {
        "app": {
            "name": "DeFi Portfolio Risk Analyzer V2",
            "log_file": "portfolio_analyzer_v2.log",
        },
        "data": {
            "default_portfolio_path": "data/sample_portfolio_v2.json",
            "cache_dir": "cache",
        },
        "risk": {
            "days": 30,
            "risk_free_rate": 0.02,
            "confidence": 0.95,
        },
        "optimization": {
            "target_return": 0.10,
            "max_weight_per_asset": 0.30,
            "short_selling_allowed": False,
        },
        "visualization": {
            "theme": "plotly_dark",
            "output_dir": "figures",
        },
    }


# ---------------------------------------------------------------------------
# YAML loading and validation helpers
# ---------------------------------------------------------------------------


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Shallow-merge two dictionaries of configuration.

    Values from `override` take precedence over `base`. Nested dictionaries
    are merged one level deep, other values are replaced.

    Args:
        base: Base configuration dictionary.
        override: Dictionary with user-provided values that override base.

    Returns:
        A new dictionary representing the merged configuration.
    """
    merged: Dict[str, Any] = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            inner = dict(merged[key])
            inner.update(value)
            merged[key] = inner
        else:
            merged[key] = value
    return merged


def _load_yaml(path: Path) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        The YAML content as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed as valid YAML.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML config file: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Top-level YAML structure must be a mapping (dict).")

    return data


# ---------------------------------------------------------------------------
# Load config
# ---------------------------------------------------------------------------


def load_config(path: str | Path = "config.yml") -> Config:
    """
    Load application configuration from a YAML file into a Config object.

    The function reads the specified YAML file, merges it with built-in
    defaults, performs minimal validation, and returns a strongly-typed
    Config instance. Missing sections or keys fall back to default values.

    Args:
        path: Path to the YAML configuration file. Defaults to ``config.yml``
            in the current working directory.

    Returns:
        A :class:`Config` instance containing all configuration sections.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the YAML file is invalid or has an unexpected
            top-level structure.
    """
    cfg_path = Path(path)
    logger.info("Loading configuration from %s", cfg_path)

    defaults = _default_config_dict()
    user_conf: Dict[str, Any] = {}

    if cfg_path.exists():
        user_conf = _load_yaml(cfg_path)
    else:
        logger.warning(
            "Config file %s not found. Using built-in defaults only.", cfg_path
        )

    merged = _merge_dicts(defaults, user_conf)

    # Build strongly-typed sections
    app_cfg = AppConfig(
        name=str(merged["app"]["name"]),
        log_file=str(merged["app"]["log_file"]),
    )

    data_cfg = DataConfig(
        default_portfolio_path=str(merged["data"]["default_portfolio_path"]),
        cache_dir=str(merged["data"]["cache_dir"]),
    )

    risk_cfg = RiskConfig(
        days=int(merged["risk"]["days"]),
        risk_free_rate=float(merged["risk"]["risk_free_rate"]),
        confidence=float(merged["risk"]["confidence"]),
    )

    optimization_cfg = OptimizationConfig(
        target_return=float(merged["optimization"]["target_return"]),
        max_weight_per_asset=float(merged["optimization"]["max_weight_per_asset"]),
        short_selling_allowed=bool(merged["optimization"]["short_selling_allowed"]),
    )

    visualization_cfg = VisualizationConfig(
        theme=str(merged["visualization"]["theme"]),
        output_dir=str(merged["visualization"]["output_dir"]),
    )

    config = Config(
        app=app_cfg,
        data=data_cfg,
        risk=risk_cfg,
        optimization=optimization_cfg,
        visualization=visualization_cfg,
    )

    logger.debug("Configuration loaded: %s", config)
    return config
