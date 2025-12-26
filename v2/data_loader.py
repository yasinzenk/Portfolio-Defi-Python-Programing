"""
Portfolio data loading utilities.

This module provides helper functions to load and validate portfolio
definitions stored as JSON files on disk. It converts raw JSON data
into :class:`portfolio_core.Portfolio` objects or reports validation
errors when the structure is incorrect.
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
    Load a portfolio definition from a JSON file.

    The JSON file is expected to define a portfolio with a ``name`` field
    and an ``assets`` list, where each asset has at least ``symbol``,
    ``amount`` and ``crypto_id`` fields.

    Args:
        path: Path to the JSON file containing portfolio data. Can be
            passed as string or :class:`pathlib.Path`.

    Returns:
        A fully constructed :class:`portfolio_core.Portfolio` instance
        populated with :class:`portfolio_core.Asset` objects. Asset
        prices are initialized to ``None`` so that they can be filled
        later by the data fetching layer.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a JSON file, cannot be parsed,
            or has an invalid structure (e.g. missing or malformed
            ``assets`` field).
        KeyError: If a required asset field (such as ``symbol`` or
            ``amount``) is missing.

    Example:
        >>> from data_loader import load_portfolio_from_json
        >>> portfolio = load_portfolio_from_json("data/sample_portfolio.json")
        >>> portfolio.name
        'defi_portfolio'
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
        raise ValueError("The 'assets' field must be a list.")
    if len(assets_data) == 0:
        raise ValueError("The portfolio must contain at least one asset.")

    portfolio = Portfolio(name=name)

    for i, item in enumerate(assets_data):
        try:
            symbol: str = str(item["symbol"])
            amount: float = float(item["amount"])
        except KeyError as exc:
            raise KeyError(f"Asset #{i}: missing field {exc}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Asset #{i}: invalid value - {exc}") from exc

        crypto_id: str | None = item.get("crypto_id")
        portfolio.add_asset(
            Asset(
                symbol=symbol,
                amount=amount,
                price=None,
                crypto_id=crypto_id,
            )
        )

    logger.info("Successfully loaded portfolio with %d assets", len(portfolio.assets))
    return portfolio


def validate_portfolio_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate the structure of portfolio data.

    This function performs a static validation of a dictionary that is
    expected to represent a portfolio definition, without constructing
    any :class:`portfolio_core.Portfolio` object.

    Args:
        data: Dictionary parsed from a JSON portfolio file.

    Returns:
        A list of human-readable error messages describing issues with
        the structure. The list is empty if the data is considered
        valid.

    Example:
        >>> errors = validate_portfolio_data({"assets": []})
        >>> errors
        ['The portfolio must contain at least one asset.']
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

        for field in ["symbol", "amount", "crypto_id"]:
            if field not in asset:
                errors.append(f"Asset #{i}: missing field '{field}'")

    return errors

