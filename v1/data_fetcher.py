"""
Data fetching utilities for cryptocurrency prices.

This module provides a thin client around the CryptoCompare HTTP API
to retrieve both current and historical price data for cryptocurrencies.
It is used by the portfolio analyzer to populate asset prices and build
return series.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional, List

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class CryptoCompareClient:
    """
    Client for the CryptoCompare REST API.

    The client supports fetching current spot prices as well as
    historical daily OHLC data for a given symbol and quote currency.
    A free tier (no API key) is sufficient for small academic projects.
    """

    BASE_URL: str = "https://min-api.cryptocompare.com/data"

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 15,
        max_retries: int = 2,
    ) -> None:
        """
        Initialize a new CryptoCompareClient instance.

        Args:
            api_key: Optional API key. If not provided, the value is read
                from the ``CRYPTOCOMPARE_API_KEY`` environment variable.
                If still missing, unauthenticated public access is used.
            timeout: HTTP request timeout in seconds.
            max_retries: Maximum number of retry attempts for failed
                requests (excluding the initial attempt).

        Example:
            >>> client = CryptoCompareClient(timeout=10, max_retries=1)
            >>> price = client.get_current_price("ETH", "USD")
        """
        self.api_key: Optional[str] = api_key or os.getenv("CRYPTOCOMPARE_API_KEY")
        self.timeout: int = timeout
        self.max_retries: int = max_retries

        logger.debug(
            "CryptoCompareClient initialized (timeout=%s, max_retries=%s)",
            self.timeout,
            self.max_retries,
        )

    def _get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a GET request to a CryptoCompare API endpoint.

        This method handles retries with exponential backoff and basic
        error checking on the JSON response.

        Args:
            endpoint: Endpoint path (e.g. ``"/price"`` or ``"/v2/histoday"``).
            params: Optional dictionary of query string parameters.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            RuntimeError: If all retry attempts fail.
            ValueError: If the API returns a structured error payload.
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers: Dict[str, str] = {}

        if self.api_key:
            headers["authorization"] = f"Apikey {self.api_key}"

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug("API GET %s (attempt %d)", url, attempt + 1)
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data: Dict[str, Any] = response.json()

                if data.get("Response") == "Error":
                    # CryptoCompare-specific error format
                    raise ValueError(data.get("Message", "Unknown error"))

                return data

            except Exception as exc:  # noqa: BLE001
                last_error = exc
                wait_time: float = (2**attempt) * 0.5
                if attempt < self.max_retries:
                    logger.warning(
                        "API request failed (%s). Retrying in %.1fs...",
                        exc,
                        wait_time,
                    )
                    time.sleep(wait_time)
                else:
                    logger.error("API request failed after retries: %s", exc)

        raise RuntimeError(f"CryptoCompare request failed: {url} ({last_error})")

    def get_current_price(self, symbol: str, vs_currency: str = "USD") -> float:
        """
        Fetch the current spot price for a given cryptocurrency.

        Args:
            symbol: Asset ticker recognized by CryptoCompare (e.g. ``"ETH"``).
            vs_currency: Quote currency ticker (e.g. ``"USD"``).

        Returns:
            Current price as a float.

        Raises:
            ValueError: If no price data is returned by the API.
        """
        params: Dict[str, str] = {
            "fsym": symbol.upper(),
            "tsyms": vs_currency.upper(),
        }
        logger.info("Fetching current price for %s in %s", symbol, vs_currency)
        data = self._get("/price", params=params)

        key = vs_currency.upper()
        if key not in data:
            logger.error("No price data returned for %s", symbol)
            raise ValueError(f"No price data for symbol={symbol}")

        price = float(data[key])
        logger.debug("Current price for %s: %.6f", symbol, price)
        return price

    def get_historical_daily(
        self,
        symbol: str,
        vs_currency: str = "USD",
        days: int = 180,
    ) -> pd.DataFrame:
        """
        Fetch historical daily closing prices for a cryptocurrency.

        Data is returned as a :class:`pandas.DataFrame` indexed by date,
        with a single ``'price'`` column corresponding to the daily
        close value.

        Args:
            symbol: Asset ticker (e.g. ``"ETH"``).
            vs_currency: Quote currency ticker (default: ``"USD"``).
            days: Number of calendar days of history to request.

        Returns:
            DataFrame with index as ``datetime.date`` objects and a
            single ``price`` column.

        Raises:
            ValueError: If the API does not return any price data.
        """
        logger.info("Fetching %d days of historical data for %s", days, symbol)

        data = self._get(
            "/v2/histoday",
            params={
                "fsym": symbol.upper(),
                "tsym": vs_currency.upper(),
                "limit": days,
            },
        )

        prices: List[Dict[str, Any]] = data.get("Data", {}).get("Data", [])

        if not prices:
            logger.error("No historical data returned for %s", symbol)
            raise ValueError(f"No historical data for symbol={symbol}")

        records: List[Dict[str, Any]] = []
        for point in prices:
            records.append(
                {
                    "date": datetime.fromtimestamp(point["time"]).date(),
                    "price": point["close"],
                }
            )

        df = pd.DataFrame(records)
        df = df.set_index("date")

        logger.info("Successfully fetched %d data points for %s", len(df), symbol)
        return df
