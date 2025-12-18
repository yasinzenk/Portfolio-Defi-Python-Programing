from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class Asset:
    symbol: str
    amount: float
    price: float

    def market_value(self) -> float:
        return self.amount * self.price
    
class Portfolio:
    def __init__(self, name: str):
        self.name = name
        self.assets : List[Asset] = []
    
    def add_asset(self, asset: Asset) -> None:
        self.assets.append(asset)
    
    def total_value(self) -> float:
        return sum(a.market_value() for a in self.assets)
    
    def weights(self) -> Dict[str, float]:
        total = self.total_value()
        if total <= 0:
            return {a.symbol: 0.0 for a in self.assets}

        values : Dict[str, float] = {}
        for a in self.assets:
            values[a.symbol] = values.get(a.symbol, 0.0) + a.market_value()
        return {sym: val/total for sym, val in values.items()}

def load_portfolio(path: str | Path) -> Portfolio:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Portfolio file not found:{path}")
    
    if path.suffix.lower() != ".json":
        raise ValueError("V0 only supports .json files for the moment (CSV possible in V1).")
    
    data = json.loads(path.read_text(encoding="utf-8"))

    name = data.get("name", "portfolio")
    assets = data.get("assets", [])
    if not isinstance(assets, list) or len(assets) == 0:
        raise ValueError("The field assets must be a non empty list.")

    p = Portfolio(name=name)

    for item in assets:
        symbol = str(str(item["symbol"]))
        amount = float(item["amount"])
        price = float(item["price"])
        p.add_asset(Asset(symbol=symbol, amount=amount, price=price))
    
    return p
    


    

    
