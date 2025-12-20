"""
Portfolio data loading module.
This module provides functions for loading portfolios from different sources (JSON for V0, API in V1).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from portfolio_core import Portfolio


def load_portfolio_from_json(path: str | Path) -> "Portfolio":
    """
    Loads a portfolio from a JSON file.

    Args:
        path: Path to the JSON file containing the portfolio data.

    Returns:
        Portfolio: The loaded portfolio object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid JSON file.
        KeyError: If the file is missing required fields.
    
    Example:
        >>> portfolio = load_portfolio_from_json("data/portfolio.json")
        >>> print(portfolio)
    """

    from portfolio_core import Asset, Portfolio

    path = Path(path)

    # Verification if the file exists
    if not path.exists():
        raise FileNotFoundError(f"Portfolio file not found: {path}")

    # Verification if the file is a JSON file
    if path.suffix.lower() != ".json":
        raise ValueError(
            f"Invalid file format: {path.suffix}. V0 supports only .json files"
        )
    
    # Lecture and parsing the JSON file
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file in {path}: {e}")
    
    # Extracting the portfolio name
    name = data.get("name", "portfolio")

    # Validation of the assets list
    assets = data.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError("The 'assets' field must be a list.")
    if len(assets) == 0:
        raise ValueError("The portfolio must contain at least one asset.")

    # Creation of the portfolio
    portfolio = Portfolio(name=name)
    
    # Adding each asset to the portfolio
    for i, item in enumerate(assets):
        try:
            symbol = str(item["symbol"])
            amount = float(item["amount"])
        except KeyError as e:
            raise KeyError(f"Asset #{i}: missing field {e}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Asset #{i}: invalid value - {e}")
        
        coingecko_id = item.get("coingecko_id")
        portfolio.add_asset(Asset(symbol=symbol, amount=amount, price=None, coingecko_id=coingecko_id))
    
    return portfolio

def validate_portfolio_data(data: dict) -> list[str]:
    """
    Validate the portfolio data without creating the portfolio object.

    Args:
        data: Dictionary containing the portfolio data.

    Returns:
        List of validation errors.
    """

    errors = []
    
    if "name" not in data:
        errors.append("'name' field is missing (optional but recommended)")
    
    if "assets" not in data:
        errors.append("'assets' field is missing (obligatory)")
        return errors  # No need to continue if assets is missing

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

        for field in ["symbol", "amount", "coingecko_id"]:
            if field not in asset:
                errors.append(f"Asset #{i}: missing field {field}")

    return errors