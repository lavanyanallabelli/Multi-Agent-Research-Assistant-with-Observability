import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from trading.algorithm import (
    calculate_position_size,
    calculate_exit_levels,
    should_open_trade,
    should_close_trade,
    get_direction,
)
from trading.portfolio import (
    open_position,
    close_position,
    get_open_positions,
    get_portfolio,
)
from tools.telegram import send_message
from memory.audit_log import log_signal


def execute_signal(state: dict) -> dict:
    """
    Called after decision agent fires.
    Opens a new paper trade if conditions are met.
    """
    print("\n[PaperTrader] Evaluating signal...")

    decision = state.get("decision")
    if not decision:
        print("  No decision — skipping")
        return dict(state)

    symbol     = decision.get("symbol")
    action     = decision.get("action")
    confidence = decision.get("confidence")

    asset_data = {a["symbol"]: a for a in state.get("all_asset_data", [])}
    asset      = asset_data.get(symbol, {})
    price      = asset.get("price", 0)

    if not price:
        print(f"  No price data for {symbol} — skipping")
        return dict(state)

     # ── SELL signal — check if we own this asset first ──
    if action == "SELL":
        from trading.portfolio import get_open_position_for
        existing = get_open_position_for(symbol)
        if not existing:
            print(f"  [PaperTrader] SELL signal for {symbol} but no open position — skipping")
            state["paper_trade_opened"] = False
            return dict(state)

        # close the existing position
        from trading.portfolio import close_position
        trade = close_position(
            position_id=existing["id"],
            exit_price=price,
            exit_reason="SELL_SIGNAL",
        )

        emoji = "✅" if trade["pnl"] >= 0 else "❌"
        msg = f"""{emoji} <b>PAPER TRADE CLOSED — {symbol}</b>
📊 Direction: {trade['direction']}
📈 Entry: ${trade['entry_price']:,.2f}
📉 Exit: ${trade['exit_price']:,.2f}
💵 P&L: ${trade['pnl']:+,.2f} ({trade['pnl_pct']:+.2f}%)
🔔 Reason: SELL signal fired

⚠️ <i>Paper trading — not real money</i>"""

        send_message(msg)
        print(f"  [PaperTrader] Position closed — {symbol} @ ${price:,.2f}")
        state["paper_trade_opened"] = False
        return dict(state)
        
 # ── BUY signal — check if we should open a trade ──
    # check if we should open a trade
    can_trade, reason = should_open_trade(symbol, action, confidence, price)
    if not can_trade:
        print(f"  Trade blocked: {reason}")
        return dict(state)

    portfolio = get_portfolio()
    cash      = portfolio["cash_balance"]
    direction = get_direction(action)
    sizing    = calculate_position_size(price, cash)
    levels    = calculate_exit_levels(price, direction)

    # log signal to database first
    signal_id = log_signal(state, state.get("run_id", ""))

    # open the position
    position_id = open_position(
        symbol=symbol,
        direction=direction,
        entry_price=price,
        quantity=sizing["quantity"],
        stop_loss=levels["stop_loss"],
        take_profit=levels["take_profit"],
        signal_id=signal_id,
    )

    # send telegram alert
    # send telegram alert
    emoji          = "🟢" if action == "BUY" else "🔴"
    direction_label = "LONG" if action == "BUY" else "SHORT"
    portfolio      = get_portfolio()

    msg = f"""{emoji} <b>PAPER TRADE OPENED — {symbol}</b>

📊 Direction:       {direction_label}
💰 Entry Price:     ${price:,.2f}
📦 Quantity:        {sizing['quantity']:.6f}
💵 Position Value:  ${sizing['position_size']:,.2f}
🛑 Stop Loss:       ${levels['stop_loss']:,.2f} (-{3}%)
🎯 Take Profit:     ${levels['take_profit']:,.2f} (+{6}%)
🎯 Confidence:      {confidence}%

💼 Portfolio after trade:
  Cash remaining: ${portfolio['cash_balance']:,.2f}
  Open positions: {portfolio['open_positions']}

⚠️ <i>Paper trading — not real money</i>"""

    send_message(msg)
    print(f"  [PaperTrader] Trade opened — {direction} {symbol} "
          f"@ ${price:,.2f}")

    state["paper_trade_opened"] = True
    state["paper_trade_id"]     = position_id
    return dict(state)


def monitor_positions(asset_data_list: list[dict]) -> list[dict]:
    """
    Called every pipeline run.
    Checks all open positions against current prices.
    Closes positions that hit stop loss or take profit.
    """
    print("\n[PaperTrader] Monitoring open positions...")

    open_positions = get_open_positions()
    if not open_positions:
        print("  No open positions to monitor")
        return []

    asset_prices = {a["symbol"]: a["price"] for a in asset_data_list}
    closed_trades = []

    for position in open_positions:
        symbol        = position["symbol"]
        current_price = asset_prices.get(symbol)

        if not current_price:
            print(f"  No price for {symbol} — skipping")
            continue

        should_close, reason = should_close_trade(position, current_price)

        if should_close:
            trade = close_position(
                position_id=position["id"],
                exit_price=current_price,
                exit_reason=reason,
            )
            closed_trades.append(trade)

            # send telegram alert
            emoji  = "✅" if trade["pnl"] >= 0 else "❌"
            msg = f"""{emoji} <b>PAPER TRADE CLOSED — {symbol}</b>

📊 Direction: {trade['direction']}
📈 Entry: ${trade['entry_price']:,.2f}
📉 Exit: ${trade['exit_price']:,.2f}
💵 P&L: ${trade['pnl']:+,.2f} ({trade['pnl_pct']:+.2f}%)
🔔 Reason: {reason}

⚠️ <i>Paper trading — not real money</i>"""

            send_message(msg)
        else:
            entry  = position["entry_price"]
            pnl    = (current_price - entry) * position["quantity"]
            pnl_pct = ((current_price - entry) / entry) * 100
            print(f"  {symbol}: ${current_price:,.2f} | "
                  f"P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%) | "
                  f"SL: ${position['stop_loss']:,.2f} | "
                  f"TP: ${position['take_profit']:,.2f}")

    return closed_trades