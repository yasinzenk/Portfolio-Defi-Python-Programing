"""
Unit tests for the configuration loader (config.py) in V2.

These tests verify that:
- Defaults are used when the YAML file is missing.
- User-provided values in YAML override defaults correctly.
- Invalid YAML raises a ValueError.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from config import load_config


def test_load_config_uses_defaults_when_file_missing(tmp_path: Path) -> None:
    """
    When the config file does not exist, load_config should fall back
    to built-in defaults without raising, and return a Config object
    with those default values.
    """
    missing_path = tmp_path / "non_existing_config.yml"
    assert not missing_path.exists()

    cfg = load_config(missing_path)

    # Check a few representative defaults
    assert cfg.app.name == "DeFi Portfolio Risk Analyzer V2"
    assert cfg.app.log_file == "portfolio_analyzer_v2.log"

    assert cfg.data.default_portfolio_path == "data/sample_portfolio_v2.json"
    assert cfg.data.cache_dir == "cache"

    assert cfg.risk.days == 30
    assert cfg.risk.risk_free_rate == 0.02
    assert cfg.risk.confidence == 0.95

    assert cfg.optimization.target_return == 0.10
    assert cfg.optimization.max_weight_per_asset == 0.30
    assert cfg.optimization.short_selling_allowed is False

    assert cfg.visualization.theme == "plotly_dark"
    assert cfg.visualization.output_dir == "figures"


def test_load_config_overrides_defaults(tmp_path: Path) -> None:
    """
    User-provided YAML values must override the built-in defaults, while
    unspecified keys should still come from the defaults.
    """
    yaml_content = """
app:
  log_file: "custom.log"

risk:
  days: 42
  risk_free_rate: 0.01

optimization:
  max_weight_per_asset: 0.25
"""

    cfg_path = tmp_path / "config_override.yml"
    cfg_path.write_text(yaml_content, encoding="utf-8")

    cfg = load_config(cfg_path)

    # Overridden values
    assert cfg.app.log_file == "custom.log"
    assert cfg.risk.days == 42
    assert cfg.risk.risk_free_rate == 0.01
    assert cfg.optimization.max_weight_per_asset == 0.25

    # Values still coming from defaults
    assert cfg.app.name == "DeFi Portfolio Risk Analyzer V2"
    assert cfg.risk.confidence == 0.95
    assert cfg.data.default_portfolio_path == "data/sample_portfolio_v2.json"
    assert cfg.optimization.target_return == 0.10
    assert cfg.visualization.theme == "plotly_dark"


def test_load_config_invalid_yaml_raises_value_error(tmp_path: Path) -> None:
    """
    Invalid YAML content should cause load_config to raise a ValueError.
    """
    invalid_yaml = "this: is: not: valid: yaml: ["
    cfg_path = tmp_path / "invalid_config.yml"
    cfg_path.write_text(invalid_yaml, encoding="utf-8")

    with pytest.raises(ValueError):
        load_config(cfg_path)
