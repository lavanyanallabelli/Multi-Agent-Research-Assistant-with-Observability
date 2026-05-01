import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
import openai
from config import (OPENAI_API_KEY, COINGECKO_API_KEY, ALPHA_VANTAGE_API_KEY, NEWS_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DATABASE_URL)

def check(name, fn):
    try:
        fn()
        print(f" [OK] {name}")
    except Exception as e:
        print(f" [FAIL] {name}: {e}")

def test_openai():
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    msg = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=10,
        messages=[{"role": "user", "content": "Say OK"}],
    )
    assert msg.choices[0].message.content

def test_coingecko():
    resp = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        headers={"x-cg-demo-api-key": COINGECKO_API_KEY},
        params={"ids": "bitcoin", "vs_currencies": "usd"},
        timeout=10,
    )
    resp.raise_for_status()
    assert resp.json()["bitcoin"]["usd"] > 0

def test_alpha_vantage():
    resp = requests.get(
        "https://www.alphavantage.co/query",
        params={
            "function": "GLOBAL_QUOTE",
            "symbol": "AAPL",
            "apikey": ALPHA_VANTAGE_API_KEY
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    assert "Global Quote" in data and data["Global Quote"]

def test_newsapi():
    resp = requests.get(
        "https://newsapi.org/v2/everything",
        params={"q": "Bitcoin", "pageSize": 1, "apiKey": NEWS_API_KEY},
        timeout=10,
    )
    resp.raise_for_status()
    assert resp.json().get("status") == "ok"

def test_telegram():
    resp = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe",
        timeout=10,
    )
    data = resp.json()
    assert data.get("ok"), f"Bad response: {data}"
    print(f"      Bot name: @{data['result']['username']}")

if __name__ == "__main__":
    print("\n=== API Key Verification ===\n")
    check("OpenAI",             test_openai)
    check("CoinGecko",             test_coingecko)
    check("Alpha Vantage (stocks)",test_alpha_vantage)
    check("NewsAPI",               test_newsapi)
    check("Telegram",              test_telegram)
    print("\nDone. Fix any [FAIL] before continuing.\n")