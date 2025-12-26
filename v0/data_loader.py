"""
Portfolio data loading module.

This module provides functions for loading and validating portfolio
definitions stored as JSON files on disk.

In V0, asset prices are expected to be provided directly in the JSON
file (no external price fetching). The loader converts the raw JSON
structure into a Portfolio instance composed of Asset objects.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from portfolio_core import Portfolio

logger = logging.getLogger(__name__)


def load_portfolio_from_json(path: str | Path) -> "Portfolio":
    """
    Load a portfolio from a JSON file.

    The JSON file is expected to contain:
      - a ``name`` field (string, optional)
      - an ``assets`` field (list of objects), where each asset has:
        - ``symbol`` (string)
        - ``amount`` (number)
        - ``price`` (number)

    Args:
        path: Path to the JSON file containing the portfolio data.
            Can be a string or a :class:`pathlib.Path` instance.

    Returns:
        A :class:`portfolio_core.Portfolio` instance populated with
        :class:`portfolio_core.Asset` objects.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid JSON file, if the file
            format is not ``.json``, or if the structure of the data
            is invalid (e.g. ``assets`` is not a list).
        KeyError: If a required asset field is missing.
    """
    from portfolio_core import Asset, Portfolio  # local import to avoid cycles

    path = Path(path)
    logger.info("Loading portfolio from %s", path)

    if not path.exists():
        logger.error("Portfolio file not found: %s", path)
        raise FileNotFoundError(f"Portfolio file not found: {path}")

    if path.suffix.lower() != ".json":
        logger.error("Invalid file format: %s", path.suffix)
        raise ValueError(
            f"Invalid file format: {path.suffix}. Only .json files supported."
        )

    try:
        data: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON file: %s", exc)
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    name: str = data.get("name", "portfolio")

    assets_data: List[Dict[str, Any]] = data.get("assets", [])
    if not isinstance(assets_data, list):
        logger.error("The 'assets' field must be a list.")
        raise ValueError("The 'assets' field must be a list.")
    if len(assets_data) == 0:
        logger.error("The portfolio must contain at least one asset.")
        raise ValueError("The portfolio must contain at least one asset.")

    portfolio = Portfolio(name=name)

    for i, item in enumerate(assets_data):
        if not isinstance(item, dict):
            logger.error("Asset #%d: must be a JSON object", i)
            raise ValueError(f"Asset #{i}: must be a JSON object")

        try:
            symbol: str = str(item["symbol"])
            amount: float = float(item["amount"])
            price: float = float(item["price"])
        except KeyError as exc:
            logger.error("Asset #%d: missing field %s", i, exc)
            raise KeyError(f"Asset #{i}: missing field {exc}") from exc
        except (TypeError, ValueError) as exc:
            logger.error("Asset #%d: invalid value - %s", i, exc)
            raise ValueError(f"Asset #{i}: invalid value - {exc}") from exc

        portfolio.add_asset(Asset(symbol=symbol, amount=amount, price=price))

    logger.info("Successfully loaded portfolio with %d assets", len(portfolio.assets))
    return portfolio


def validate_portfolio_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate portfolio data without creating a Portfolio object.

    This function performs a static validation of a dictionary that is
    expected to represent a portfolio definition. It is useful for
    checking user input or testing JSON structures before loading them.

    Args:
        data: Dictionary containing the portfolio data.

    Returns:
        List of human-readable validation error messages.
        The list is empty if the data is considered valid.
    """
    errors: List[str] = []

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

        for field in ["symbol", "amount", "price"]:
            if field not in asset:
                errors.append(f"Asset #{i}: missing field '{field}'")

    return errors
