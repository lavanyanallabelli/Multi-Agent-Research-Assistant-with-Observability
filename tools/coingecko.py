import requests #makes HTTP calls to APIs
import time #used for time.sleep() to pause b/w API calls
import sys
import os
#__file__ — the current file's path, like D:\project\tools\coingecko.py
#os.path.dirname(__file__) — goes up one level → D:\project\tools
#os.path.dirname(os.path.dirname(__file__)) — goes up one more level → D:\project
#sys.path.insert(0, ...) — tells Python "look here first when importing"

#So when you write from config import COINGECKO_API_KEY, Python knows to look in D:\project\config.py
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import COINGECKO_API_KEY

BASE_URL = "https://api.coingecko.com/api/v3"
#every request to CoinGecko needs this header to prove who you are. It's like showing your ID at the door.
HEADERS = {"x-cg-demo-api-key": COINGECKO_API_KEY}

def get_price(coingecko_id: str) -> dict: #takes a coin id and return a dictionary with price data
    url = f"{BASE_URL}/simple/price"
    #these get added to the URL automatically by requests
    params = {
        "ids": coingecko_id, #which coin you wnat
        "vs_currencies": "usd", #convert to USD
        "include_24hr_vol": "true", #also give me the 24h trading volume
        "include_24hr_change": "true", #also give me the % change in the last 24th
    }
    
    #makes the actual http get request to the API
    resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
    resp.raise_for_status() #raises an error if the request failed
    coin = resp.json().get(coingecko_id, {}) # CoinGecko returns data like this:
    return {
        "price_usd": coin.get("usd", 0),
        "volume_24h": coin.get("usd_24h_vol", 0),
        "price_change_24h": coin.get("usd_24h_change", 0),
    }

def get_ohlcv(coingecko_id: str, days: int = 30) -> list[dict]:
    url = f"{BASE_URL}/coins/{coingecko_id}/ohlc"
    params = {"vs_currency": "usd", "days": days}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
    resp.raise_for_status()
    candles = []
    for row in resp.json(): # loops through each candle array.
        candles.append({
            "t": row[0] //1000,  #timestamp
            "o": row[1], #open
            "h": row[2], #high
            "l": row[3], #low
            "c": row[4], #close
            "v": 0, #volume v": 0 — CoinGecko's free OHLC endpoint doesn't include volume per candle. We set it to 0 for now and use the 24h volume from get_price() instead.
        })

    return candles

def get_full_asset_data(symbol: str, coingecko_id: str) -> dict:
    price_data = get_price(coingecko_id)
    time.sleep(0.5)
    ohlcv = get_ohlcv(coingecko_id, days=30)
    return {
        "symbol": symbol,
        "asset_type": "crypto",
        "price": price_data["price_usd"],
        "volume_24h": price_data["volume_24h"],
        "price_change_24h": price_data["price_change_24h"],
        "ohlcv": ohlcv,
    }

def get_market_chart(coingecko_id: str, days: int = 90) -> list[dict]:
    """
    Uses /market_chart endpoint which returns daily candles
    for the past N days on free tier.
    Returns more data than /ohlc endpoint.
    """
    url    = f"{BASE_URL}/coins/{coingecko_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days":        str(days),
        "interval":    "daily",
    }
    resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
    resp.raise_for_status()
    data   = resp.json()
    prices = data.get("prices", [])
    candles = []
    for i in range(1, len(prices)):
        prev  = prices[i - 1]
        curr  = prices[i]
        candles.append({
            "t": curr[0] // 1000,
            "o": prev[1],
            "h": max(prev[1], curr[1]),
            "l": min(prev[1], curr[1]),
            "c": curr[1],
            "v": 0,
        })
    return candles