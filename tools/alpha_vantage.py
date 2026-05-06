import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import ALPHA_VANTAGE_API_KEY

BASE_URL = "https://www.alphavantage.co/query"

def get_quote(symbol: str) -> dict:
    params = {
        "function": "GLOBAL_QUOTE", #this tells Alpha Vantage which data you want. Think of it like choosing from a menu. GLOBAL_QUOTE means "give me the current price snapshot for this stock."
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()

    #Alpha Vantage doesn't give you the percentage change directly like CoinGecko does. So we calculate it ourselves:
    q = resp.json().get("Global Quote", {})
    price = float(q.get("05. price", 0))
    prev = float(q.get("08. previous close", price))
    change = ((price - prev) / prev *100) if prev else 0
    return {
        "price_usd": price,
        "volume_24h": float(q.get("06. volume", 0)), #Alpha Vantage doesn't provide volume data for stocks
        "price_change_24h": round(change, 2),
    }

def get_ohlcv(symbol: str) -> list[dict]:
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": ALPHA_VANTAGE_API_KEY,
        
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    ts = resp.json().get("Time Series (Daily)", {})
    candles = []
    for date_str, row in sorted(ts.items()):
        candles.append({
            "t": date_str,
            "o": float(row["1. open"]),
            "h": float(row["2. high"]),
            "l": float(row["3. low"]),
            "c": float(row["4. close"]),
            "v": float(row["5. volume"]),
        })
    return candles

def get_full_asset_data(symbol: str) -> dict:
    quote = get_quote(symbol)
    ohlcv = get_ohlcv(symbol)
    return {
        "symbol": symbol,
        "asset_type": "stock",
        "price": quote["price_usd"],
        "volume_24h": quote["volume_24h"],
        "price_change_24h": quote["price_change_24h"],
        "ohlcv": ohlcv,
    }