import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import LIVE_TRADING

# ── Placeholder — activate after paper trading observation ──
# pip install python-binance
# Add to .env:
#   BINANCE_API_KEY=your_key
#   BINANCE_SECRET_KEY=your_secret


def buy_crypto(symbol: str, qty: float) -> dict:
    if not LIVE_TRADING:
        print(f"  [Binance] PAPER MODE — would BUY {qty} {symbol}")
        return {"status": "paper", "symbol": symbol, "qty": qty}
    raise NotImplementedError("Binance live trading not configured yet")


def sell_crypto(symbol: str, qty: float) -> dict:
    if not LIVE_TRADING:
        print(f"  [Binance] PAPER MODE — would SELL {qty} {symbol}")
        return {"status": "paper", "symbol": symbol, "qty": qty}
    raise NotImplementedError("Binance live trading not configured yet")


def get_account() -> dict:
    if not LIVE_TRADING:
        return {"status": "paper_mode", "message": "Binance not connected yet"}
    raise NotImplementedError("Binance live trading not configured yet")