import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import LIVE_TRADING

# ── Placeholder — activate after getting Alpaca API keys ──
# pip install alpaca-trade-api
# Add to .env:
#   ALPACA_API_KEY=your_key
#   ALPACA_SECRET_KEY=your_secret
#   ALPACA_BASE_URL=https://paper-api.alpaca.markets


def buy_stock(symbol: str, qty: float) -> dict:
    if not LIVE_TRADING:
        print(f"  [Alpaca] PAPER MODE — would BUY {qty} {symbol}")
        return {"status": "paper", "symbol": symbol, "qty": qty}
    # TODO: implement live trading after SSN verification
    raise NotImplementedError("Alpaca live trading not configured yet")


def sell_stock(symbol: str, qty: float) -> dict:
    if not LIVE_TRADING:
        print(f"  [Alpaca] PAPER MODE — would SELL {qty} {symbol}")
        return {"status": "paper", "symbol": symbol, "qty": qty}
    raise NotImplementedError("Alpaca live trading not configured yet")


def get_account() -> dict:
    if not LIVE_TRADING:
        return {"status": "paper_mode", "message": "Alpaca not connected yet"}
    raise NotImplementedError("Alpaca live trading not configured yet")