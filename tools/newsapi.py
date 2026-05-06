import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import NEWS_API_KEY

BASE_URL = "https://newsapi.org/v2/everything"

def build_query(symbol: str, asset_type: str = "unknown") -> str:

    """ Builds a smart search query for any symbol dynamically"""
    if asset_type == "crypto":
        return f"{symbol} cryptocurrency"
    elif asset_type == "stock":
        return f"{symbol} stock market"
    else:
        return symbol

def get_headlines(symbol: str, asset_type: str = "unknown", max_articles: int = 10) -> list[str]:
    query = build_query(symbol, asset_type)
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max_articles,
        "apiKey": NEWS_API_KEY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    articles = resp.json().get("articles", [])
    headlines = []
    for article in articles:
        title = article.get("title", "")
        desc = article.get("description", "")
        if title:
            headlines.append(f"{title}. {desc}" if desc else title)
    return headlines