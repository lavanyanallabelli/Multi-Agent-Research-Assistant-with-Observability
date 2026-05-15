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

# Paper Trading
PAPER_TRADING_BALANCE      = 10000.0  # starting virtual balance
PAPER_TRADING_RISK_PCT     = 2.0      # risk % per trade
PAPER_TRADING_MAX_POSITIONS = 3       # max open trades at once
PAPER_TRADING_STOP_LOSS_PCT = 3.0     # stop loss % below entry
PAPER_TRADING_TP_PCT        = 6.0     # take profit % above entry
CIRCUIT_BREAKER_PCT         = 15.0    # pause trading if portfolio drops this %
LIVE_TRADING                = False   # False = paper, True = live

ALPACA_API_KEY    = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL   = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
ALPACA_TRADE_SIZE = float(os.getenv("ALPACA_TRADE_SIZE", 1000))