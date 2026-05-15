import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import LIVE_TRADING
from memory.audit_log import get_system_settings
from trading.alpaca import buy_stock, sell_stock, get_position


def execution_agent(state: dict) -> dict:
    print("\n[ExecutionAgent] Processing trade execution...")

    decision = state.get("decision")
    if not decision:
        print("  No decision found — skipping execution")
        state["execution_result"] = {"status": "skipped", "reason": "No decision"}
        return dict(state)

    symbol = decision.get("symbol", "")
    action = decision.get("action", "HOLD")
    asset_type = next(
        (a.get("asset_type") for a in state.get("all_asset_data", []) if a.get("symbol") == symbol),
        "unknown",
    )

    if action == "HOLD":
        print(f"  {symbol}: HOLD — no execution needed")
        state["execution_result"] = {"status": "skipped", "reason": "Action is HOLD"}
        return dict(state)

    if asset_type != "stock":
        print(f"  {symbol}: asset_type is '{asset_type}' — Alpaca supports stocks only, skipping")
        state["execution_result"] = {"status": "skipped", "reason": "Crypto not supported by Alpaca"}
        return dict(state)

    if action == "BUY":
        price = decision.get("price") or next(
            (a.get("price") for a in state.get("all_asset_data", []) if a.get("symbol") == symbol),
            None,
        )
        if not price or float(price) <= 0:
            print(f"  {symbol}: Could not determine price — skipping execution")
            state["execution_result"] = {"status": "skipped", "reason": "Price unavailable"}
            return dict(state)
        price = float(price)
        qty = round(get_system_settings().get('alpaca_trade_size', 1000.0) / price, 4)
        print(f"  {symbol}: BUY | price=${price:.4f} | qty={qty} | live={LIVE_TRADING}")
        result = buy_stock(symbol, qty)
        state["execution_result"] = result
        print(f"  Execution result: {result}")
        return dict(state)

    if action == "SELL":
        position = get_position(symbol)
        if position.get("status") == "no_position":
            print(f"  {symbol}: No Alpaca position to sell — skipping")
            state["execution_result"] = {"status": "skipped", "reason": "No position to sell"}
            return dict(state)
        qty = abs(float(position["qty"]))
        print(f"  {symbol}: SELL | qty={qty} | live={LIVE_TRADING}")
        result = sell_stock(symbol, qty)
        state["execution_result"] = result
        print(f"  Execution result: {result}")
        return dict(state)

    state["execution_result"] = {"status": "skipped", "reason": f"Unknown action {action}"}
    return dict(state)
