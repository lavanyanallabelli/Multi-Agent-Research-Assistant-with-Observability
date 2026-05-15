import requests
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# from config import ALPHA_VANTAGE_API_KEY
import yfinance as yf

def get_quote(symbol: str) -> dict:
    try:
        ticker = yf.Ticker(symbol)
        info   = ticker.fast_info
        price  = info.last_price or 0
        prev   = info.previous_close or price
        change = ((price - prev) / prev * 100) if prev else 0
        return {
            "price_usd":        round(price, 4),
            "volume_24h":       info.last_volume or 0,
            "price_change_24h": round(change, 2),
        }
    except Exception as e:
        raise Exception(f"[yfinance] Failed to fetch quote for {symbol}: {e}")



def get_ohlcv(symbol: str) -> list[dict]:
    try:
        ticker  = yf.Ticker(symbol)
        hist    = ticker.history(period="90d", interval="1d")
        if hist.empty:
            raise Exception(f"[yfinance] No OHLCV data for {symbol}")
        candles = []
        for date, row in hist.iterrows():
            candles.append({
                "t": str(date.date()),
                "o": round(row["Open"], 4),
                "h": round(row["High"], 4),
                "l": round(row["Low"], 4),
                "c": round(row["Close"], 4),
                "v": row["Volume"],
            })
        return candles
    except Exception as e:
        raise Exception(f"[yfinance] Failed to fetch OHLCV for {symbol}: {e}")


def get_full_asset_data(symbol: str) -> dict:
    quote = get_quote(symbol)
    ohlcv = get_ohlcv(symbol)
    return {
        "symbol":           symbol,
        "asset_type":       "stock",
        "price":            quote["price_usd"],
        "volume_24h":       quote["volume_24h"],
        "price_change_24h": quote["price_change_24h"],
        "ohlcv":            ohlcv,
    }
# BASE_URL = "https://www.alphavantage.co/query"
# 
# 
# def _get(params: dict, retries: int = 3) -> dict:
    # """
    # Makes the API call with automatic retry on timeout.
    # Tries up to 3 times before giving up.
    # """
    # params["apikey"] = ALPHA_VANTAGE_API_KEY
    # for attempt in range(retries):
        # try:
            # resp = requests.get(BASE_URL, params=params, timeout=30)
            # resp.raise_for_status()
            # return resp.json()
        # except requests.exceptions.Timeout:
            # print(f"  [AlphaVantage] Timeout on attempt {attempt + 1}/{retries}, retrying...")
            # time.sleep(2)
        # except Exception as e:
            # raise e
    # raise Exception(f"[AlphaVantage] Failed after {retries} attempts")
# 
# 
# def get_quote(symbol: str) -> dict:
    # data  = _get({"function": "GLOBAL_QUOTE", "symbol": symbol})
    # q     = data.get("Global Quote", {})
    # price = float(q.get("05. price", 0))
    # prev  = float(q.get("08. previous close", price))
    # change = ((price - prev) / prev * 100) if prev else 0
    # return {
        # "price_usd":        price,
        # "volume_24h":       float(q.get("06. volume", 0)),
        # "price_change_24h": round(change, 2),
    # }
# 
# 
# def get_ohlcv(symbol: str) -> list[dict]:
    # data    = _get({"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": "compact"})
    # ts      = data.get("Time Series (Daily)", {})
    # candles = []
    # for date_str, row in sorted(ts.items()):
        # candles.append({
            # "t": date_str,
            # "o": float(row["1. open"]),
            # "h": float(row["2. high"]),
            # "l": float(row["3. low"]),
            # "c": float(row["4. close"]),
            # "v": float(row["5. volume"]),
        # })
    # return candles
# 
# 
# def get_full_asset_data(symbol: str) -> dict:
    # quote = get_quote(symbol)
    # time.sleep(1)
    # ohlcv = get_ohlcv(symbol)
    # return {
        # "symbol":           symbol,
        # "asset_type":       "stock",
        # "price":            quote["price_usd"],
        # "volume_24h":       quote["volume_24h"],
        # "price_change_24h": quote["price_change_24h"],
        # "ohlcv":            ohlcv,
    # }