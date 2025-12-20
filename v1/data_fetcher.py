import time
import requests
import pandas as pd

class CoingeckoClient:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self, timeout: int = 15, max_retries: int = 2, sleep_s: float = 0.5):
        self.timeout = timeout
        self.max_retries = max_retries
        self.sleep_s = sleep_s

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        last_err = None

        for attempt in range(self.max_retries + 1):
            try:
                r = requests.get(url, params=params, timeout=self.timeout)

                # Handle rate limit (429)
                if r.status_code == 429:
                    wait = (2 ** attempt) * 2  # 2s, 4s, 8s...
                    time.sleep(wait)
                    continue

                r.raise_for_status()
                return r.json()

            except Exception as e:
                last_err = e
                time.sleep((2 ** attempt) * self.sleep_s)

        raise RuntimeError(f"Coingecko request failed: {url} ({last_err})")
    
    def get_market_chart(self, coin_id: str, vs_currency: str="usd", days: int=90) -> pd.DataFrame:
        data = self._get(
            f"/coins/{coin_id}/market_chart",
            params={"vs_currency" : vs_currency, "days": days, "interval": "daily"}
        )
        prices = data.get("prices",[])
        if not prices:
            raise ValueError(f"No prices returned for coin_id={coin_id}")
        
        df = pd.DataFrame(prices, columns=["timestamp_ms", "price"])
        df["date"] = pd.to_datetime(df["timestamp_ms"], unit="ms").dt.date
        df = df.drop(columns=["timestamp_ms"]).drop_duplicates(subset=["date"]).set_index("date")
        return df
    
    def get_current_price(self, coin_id: str, vs_currency: str = "usd") -> float:
        data = self._get(
            "/simple/price",
            params={"ids": coin_id, "vs_currencies": vs_currency},
        )
        if coin_id not in data or vs_currency not in data[coin_id]:
            raise ValueError(f"No current price for coin_id={coin_id}")
        return float(data[coin_id][vs_currency])

class DefiLlamaClient:
    BASE_URL = "https://api.llama.fi"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def get_protocol(self, protocol_slug: str) -> dict:
        url = f"{self.BASE_URL}/protocol/{protocol_slug}"
        r = requests.get(url, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
    
    def get_protocol_tvl(self, protocol_slug: str) -> float | None:
        """Return latest TVL if available."""
        data = self.get_protocol(protocol_slug)
        tvl = data.get("tvl")
        return float(tvl) if tvl is not None else None
    
