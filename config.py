import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")
COINGECKO_API_KEY     = os.getenv("COINGECKO_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
NEWS_API_KEY          = os.getenv("NEWS_API_KEY", "")
TELEGRAM_BOT_TOKEN    = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID      = os.getenv("TELEGRAM_CHAT_ID", "")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///trading.db")

# Assets to monitor
CRYPTO_ASSETS = [
    {"symbol": "BTC", "coingecko_id": "bitcoin"},
    {"symbol": "ETH", "coingecko_id": "ethereum"},
    {"symbol": "SOL", "coingecko_id": "solana"},
    {"symbol": "BNB", "coingecko_id": "binancecoin"},
]

STOCK_ASSETS = [
    {"symbol": "AAPL"},
    {"symbol": "NVDA"},
    {"symbol": "TSLA"},
]

ALL_ASSETS = CRYPTO_ASSETS + STOCK_ASSETS

# App settings
SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL_MINUTES", 15))
MAX_ALERTS_PER_DAY    = int(os.getenv("MAX_ALERTS_PER_DAY", 5))
ALERT_COOLDOWN_HOURS  = int(os.getenv("ALERT_COOLDOWN_HOURS", 2))
TOP_N_OPPORTUNITIES   = 2
MIN_CONFIDENCE_SCORE  = 60

# LLM
OPENAI_MODEL = "gpt-4o-mini"
MAX_TOKENS   = 1000