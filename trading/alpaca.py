import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import LIVE_TRADING

ALPACA_API_KEY    = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL   = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")


def _get_client():
    from alpaca.trading.client import TradingClient
    return TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=not LIVE_TRADING)


def buy_stock(symbol: str, qty: float) -> dict:
    try:
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        client = _get_client()
        order  = client.submit_order(
            MarketOrderRequest(
                symbol       = symbol,
                qty          = qty,
                side         = OrderSide.BUY,
                time_in_force= TimeInForce.DAY,
            )
        )
        print(f"  [Alpaca] BUY order submitted — {qty} {symbol} | order_id: {order.id}")
        return {
            "status":   "submitted",
            "symbol":   symbol,
            "qty":      qty,
            "order_id": str(order.id),
            "side":     "BUY",
        }
    except Exception as e:
        print(f"  [Alpaca] BUY failed for {symbol}: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}


def sell_stock(symbol: str, qty: float) -> dict:
    try:
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        client = _get_client()
        order  = client.submit_order(
            MarketOrderRequest(
                symbol       = symbol,
                qty          = qty,
                side         = OrderSide.SELL,
                time_in_force= TimeInForce.DAY,
            )
        )
        print(f"  [Alpaca] SELL order submitted — {qty} {symbol} | order_id: {order.id}")
        return {
            "status":   "submitted",
            "symbol":   symbol,
            "qty":      qty,
            "order_id": str(order.id),
            "side":     "SELL",
        }
    except Exception as e:
        print(f"  [Alpaca] SELL failed for {symbol}: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}


def get_account() -> dict:
    try:
        client  = _get_client()
        account = client.get_account()
        return {
            "status":           "connected",
            "paper":            not LIVE_TRADING,
            "buying_power":     float(account.buying_power),
            "cash":             float(account.cash),
            "portfolio_value":  float(account.portfolio_value),
            "equity": float(getattr(account, "equity", None) or account.portfolio_value),
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "paper": not LIVE_TRADING}


def get_position(symbol: str) -> dict:
    try:
        client   = _get_client()
        position = client.get_open_position(symbol)
        return {
            "symbol":   symbol,
            "qty":      float(position.qty),
            "avg_cost": float(position.avg_entry_price),
            "market_value": float(position.market_value),
            "unrealized_pl": float(position.unrealized_pl),
        }
    except Exception as e:
        return {"status": "no_position", "symbol": symbol}

def close_position(symbol: str) -> dict:
    try:
        client = _get_client()
        order = client.close_position(symbol)
        print(f"  [Alpaca] CLOSE order submitted for {symbol} | order_id: {order.id}")
        return {
            "status": "submitted",
            "symbol": symbol,
            "order_id": str(order.id)
        }
    except Exception as e:
        print(f"  [Alpaca] CLOSE failed for {symbol}: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}


def get_all_positions() -> dict:
    """
    All open stock positions at Alpaca.
    Returns {"status": "ok", "positions": [...]} or {"status": "error", "error": str, "positions": []}.
    """
    try:
        client    = _get_client()
        positions = client.get_all_positions()
        rows = []
        for p in positions:
            plpc = getattr(p, "unrealized_plpc", None)
            try:
                plpc_pct = round(float(plpc) * 100, 2) if plpc is not None else None
            except (TypeError, ValueError):
                plpc_pct = None
            rows.append({
                "symbol":          p.symbol,
                "qty":             float(p.qty),
                "avg_cost":        float(p.avg_entry_price),
                "market_value":    float(p.market_value),
                "unrealized_pl":   float(p.unrealized_pl),
                "unrealized_plpc": plpc_pct,
                "side":            p.side.value if hasattr(p.side, "value") else str(p.side),
            })
        return {"status": "ok", "positions": rows}
    except Exception as e:
        return {"status": "error", "error": str(e), "positions": []}


# import sys
# import os
# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# 
# from config import LIVE_TRADING

# ── Placeholder — activate after getting Alpaca API keys ──
# pip install alpaca-trade-api
# Add to .env:
#   ALPACA_API_KEY=your_key
#   ALPACA_SECRET_KEY=your_secret
#   ALPACA_BASE_URL=https://paper-api.alpaca.markets


# def buy_stock(symbol: str, qty: float) -> dict:
    # if not LIVE_TRADING:
        # print(f"  [Alpaca] PAPER MODE — would BUY {qty} {symbol}")
        # return {"status": "paper", "symbol": symbol, "qty": qty}
    # : implement live trading after SSN verification
    # raise NotImplementedError("Alpaca live trading not configured yet")
# 
# 
# def sell_stock(symbol: str, qty: float) -> dict:
    # if not LIVE_TRADING:
        # print(f"  [Alpaca] PAPER MODE — would SELL {qty} {symbol}")
        # return {"status": "paper", "symbol": symbol, "qty": qty}
    # raise NotImplementedError("Alpaca live trading not configured yet")
# 
# 
# def get_account() -> dict:
    # if not LIVE_TRADING:
        # return {"status": "paper_mode", "message": "Alpaca not connected yet"}
    # raise NotImplementedError("Alpaca live trading not configured yet")