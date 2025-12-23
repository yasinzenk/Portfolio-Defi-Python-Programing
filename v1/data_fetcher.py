"""
Data fetching module for cryptocurrency prices.

Provides clients for fetching real-time and historical cryptocurrency
data from external APIs.
"""

import os
import time
from datetime import datetime

import pandas as pd
import requests


class CryptoCompareClient:
    """
    Client for the CryptoCompare API.

    No API key required for basic usage (100 calls/hour free tier).
    """

    BASE_URL = "https://min-api.cryptocompare.com/data"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 15,
        max_retries: int = 2
    ):
        """Initialize the CryptoCompare client."""
        self.api_key = api_key or os.getenv("CRYPTOCOMPARE_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make a GET request to the CryptoCompare API."""
        url = f"{self.BASE_URL}{endpoint}"
        headers = {}

        if self.api_key:
            headers["authorization"] = f"Apikey {self.api_key}"

        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                if data.get("Response") == "Error":
                    raise ValueError(data.get("Message", "Unknown error"))

                return data

            except Exception as e:
                last_error = e
                wait_time = (2 ** attempt) * 0.5
                time.sleep(wait_time)

        raise RuntimeError(
            f"CryptoCompare request failed: {url} ({last_error})"
        )

    def get_current_price(self, symbol: str, vs_currency: str = "USD") -> float:
        """Get the current price of a cryptocurrency."""
        params = {
            "fsym": symbol.upper(),
            "tsyms": vs_currency.upper()
        }
        data = self._get("/price", params=params)

        if vs_currency.upper() not in data:
            raise ValueError(f"No price data for symbol={symbol}")

        return float(data[vs_currency.upper()])

    def get_historical_daily(
        self,
        symbol: str,
        vs_currency: str = "USD",
        days: int = 180
    ) -> pd.DataFrame:
        """Get historical daily prices for a cryptocurrency."""
        data = self._get("/v2/histoday", params={
            "fsym": symbol.upper(),
            "tsym": vs_currency.upper(),
            "limit": days
        })

        prices = data.get("Data", {}).get("Data", [])

        if not prices:
            raise ValueError(f"No historical data for symbol={symbol}")

        records = []
        for point in prices:
            records.append({
                "date": datetime.fromtimestamp(point["time"]).date(),
                "price": point["close"]
            })

        df = pd.DataFrame(records)
        df = df.set_index("date")

        return df
