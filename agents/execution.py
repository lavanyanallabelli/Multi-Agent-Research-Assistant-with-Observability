import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import LIVE_TRADING
from trading.alpaca import buy_stock, sell_stock


def execution_agent(state: dict) -> dict:
    print("\n[ExecutionAgent] Processing trade execution...")

    decision = state.get("decision")
    if not decision:
        print("  No decision found — skipping execution")
        state["execution_result"] = {"status": "skipped", "reason": "No decision"}
        return dict(state)

    symbol     = decision.get("symbol", "")
    action     = decision.get("action", "HOLD")
    asset_type = state.get("all_asset_data", [{}])
    
    # find asset type for this symbol
    asset_type = next(
        (a.get("asset_type") for a in state.get("all_asset_data", []) if a.get("symbol") == symbol),
        "unknown"
    )

    # only execute for stocks
    if asset_type != "stock":
        print(f"  {symbol}: asset_type is '{asset_type}' — Alpaca supports stocks only, skipping")
        state["execution_result"] = {"status": "skipped", "reason": "Crypto not supported by Alpaca"}
        return dict(state)

    if action == "HOLD":
        print(f"  {symbol}: HOLD — no execution needed")
        state["execution_result"] = {"status": "skipped", "reason": "Action is HOLD"}
        return dict(state)

    # calculate qty based on fixed $1000 per trade
    price = decision.get("price") or next(
        (a.get("price") for a in state.get("all_asset_data", []) if a.get("symbol") == symbol),
        None
    )

    if not price or price <= 0:
        print(f"  {symbol}: Could not determine price — skipping execution")
        state["execution_result"] = {"status": "skipped", "reason": "Price unavailable"}
        return dict(state)

    qty = round(1000 / price, 4)

    print(f"  {symbol}: {action} | price=${price} | qty={qty} | live={LIVE_TRADING}")

    if action == "BUY":
        result = buy_stock(symbol, qty)
    elif action == "SELL":
        result = sell_stock(symbol, qty)
    else:
        result = {"status": "skipped", "reason": f"Unknown action {action}"}

    state["execution_result"] = result
    print(f"  Execution result: {result}")
    return dict(state)