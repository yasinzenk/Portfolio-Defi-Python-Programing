"""

Data fetching module for cryptocurrency prices.

This module provides clients for fetching real-time and historical
cryptocurrency data from external APIs.

Classes:
    CryptoCompareClient: Client for the CryptoCompare API.
Example:
    >>> from data_fetcher import CryptoCompareClient
    >>> client = CryptoCompareClient()
    >>> price = client.get_current_price("ETH")
    >>> print(f"Current ETH price: ${price:.2f}")

"""

import os
import time
import requests
import pandas as pd
from datetime import datetime

class CryptoCompareClient:
    """
    Client for the CryptoCompare API

    Attributes:
        base_url: Base URL for the CryptoCompare API
        api_key: Optional API key for authentication
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts

    Example:
        >>> client = CryptoCompareClient()
        >>> price = client.get_current_price("ETH")
        >>> print(f"Current ETH price: ${price:.2f}")

    """
    BASE_URL = "https://min-api.cryptocompare.com/data"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 15,
        max_retries: int = 2
    ):
        """
        Initialize the CryptoCompare client.

        Args:
            api_key: Optional API key. If not provided, reads from
                     CRYPTOCOMPARE_API_KEY environment variable.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts on failure.
        """
        self.api_key = api_key or os.getenv("CRYPTOCOMPARE_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """
        Make a GET request to the CryptoCompare API.

        Args:
            endpoint: API endpoint path (without base URL).
            params: Optional query parameters.

        Returns:
            JSON response as dictionary.

        Raises:
            RuntimeError: If the request fails after all retries.
        """
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

                # CryptoCompare returns error in Response field
                if data.get("Response") == "Error":
                    raise ValueError(data.get("Message", "Unknown error"))

                return data

            except Exception as e:
                last_error = e
                wait_time = (2 ** attempt) * 0.5
                time.sleep(wait_time)

        raise RuntimeError(f"CryptoCompare request failed: {url} ({last_error})")
    
    def get_current_price(self, symbol: str, vs_currency: str = "USD") -> float:
        """
        Get the current price of a cryptocurrency.

        Args:
            symbol: Cryptocurrency symbol (e.g., "ETH", "BTC").
            vs_currency: Base currency (default: "USD").

        Returns:
            Current price as float.

        Raises:
            RuntimeError: If the request fails after all retries.
        """
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
        """
        Get historical daily prices for a cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., "ETH", "BTC").
            vs_currency: Target currency for prices (default: "USD").
            days: Number of historical days to retrieve.
            
        Returns:
            DataFrame with columns ['date', 'price'] indexed by date.
            
        Raises:
            ValueError: If no data is returned for the symbol.
            
        Example:
            >>> df = client.get_historical_daily("ETH", days=30)
            >>> print(df.head())
        """
        data = self._get("/v2/histoday", params={
            "fsym": symbol.upper(),
            "tsym": vs_currency.upper(),
            "limit": days
        })
        
        prices = data.get("Data", {}).get("Data", [])
        
        if not prices:
            raise ValueError(f"No historical data for symbol={symbol}")
        
        # Convert to DataFrame
        records = []
        for point in prices:
            records.append({
                "date": datetime.fromtimestamp(point["time"]).date(),
                "price": point["close"]
            })
        
        df = pd.DataFrame(records)
        df = df.set_index("date")
        
        return df