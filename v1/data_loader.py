"""
Portfolio data loading module.

Provides functions for loading portfolios from JSON files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from portfolio_core import Portfolio


def load_portfolio_from_json(path: str | Path) -> "Portfolio":
    """
    Load a portfolio from a JSON file.

    Args:
        path: Path to the JSON file containing portfolio data.

    Returns:
        The loaded Portfolio object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid JSON file.
        KeyError: If the file is missing required fields.
    """
    from portfolio_core import Asset, Portfolio

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Portfolio file not found: {path}")

    if path.suffix.lower() != ".json":
        raise ValueError(
            f"Invalid file format: {path.suffix}. Only .json files supported."
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file: {e}")

    name = data.get("name", "portfolio")

    assets = data.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError("The 'assets' field must be a list.")
    if len(assets) == 0:
        raise ValueError("The portfolio must contain at least one asset.")

    portfolio = Portfolio(name=name)

    for i, item in enumerate(assets):
        try:
            symbol = str(item["symbol"])
            amount = float(item["amount"])
        except KeyError as e:
            raise KeyError(f"Asset #{i}: missing field {e}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Asset #{i}: invalid value - {e}")

        crypto_id = item.get("crypto_id")
        portfolio.add_asset(Asset(
            symbol=symbol,
            amount=amount,
            price=None,
            crypto_id=crypto_id
        ))

    return portfolio


def validate_portfolio_data(data: dict) -> list[str]:
    """
    Validate portfolio data without creating a Portfolio object.

    Args:
        data: Dictionary containing the portfolio data.

    Returns:
        List of validation errors (empty if valid).
    """
    errors = []

    if "name" not in data:
        errors.append("'name' field is missing (optional but recommended)")

    if "assets" not in data:
        errors.append("'assets' field is missing (required)")
        return errors

    assets = data["assets"]
    if not isinstance(assets, list):
        errors.append("'assets' field must be a list")
        return errors

    if len(assets) == 0:
        errors.append("The portfolio must contain at least one asset.")

    for i, asset in enumerate(assets):
        if not isinstance(asset, dict):
            errors.append(f"Asset #{i}: must be a JSON object")
            continue

        for field in ["symbol", "amount", "crypto_id"]:
            if field not in asset:
                errors.append(f"Asset #{i}: missing field '{field}'")

    return errors
