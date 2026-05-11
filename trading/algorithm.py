import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    PAPER_TRADING_BALANCE,
    PAPER_TRADING_RISK_PCT,
    PAPER_TRADING_MAX_POSITIONS,
    PAPER_TRADING_STOP_LOSS_PCT,
    PAPER_TRADING_TP_PCT,
)
from trading.portfolio import (
    get_portfolio,
    count_open_positions,
    get_open_position_for,
)


def calculate_position_size(
    entry_price: float,
    cash_balance: float,
) -> dict:
    """
    Calculates how much to buy based on 2% risk rule.

    Example:
        Portfolio: $10,000
        Risk per trade: 2% = $200 max loss
        Stop loss: 3% below entry
        Position size = $200 / 3% = $6,666
        Quantity = $6,666 / entry_price
    """
    risk_amount   = cash_balance * (PAPER_TRADING_RISK_PCT / 100)
    stop_loss_pct = PAPER_TRADING_STOP_LOSS_PCT / 100
    position_size = risk_amount / stop_loss_pct

    # never use more than 30% of cash in one trade
    max_size      = cash_balance * 0.30
    position_size = min(position_size, max_size)

    quantity      = position_size / entry_price

    return {
        "position_size": round(position_size, 2),
        "quantity":       round(quantity, 6),
        "risk_amount":    round(risk_amount, 2),
    }


def calculate_exit_levels(
    entry_price: float,
    direction: str,
) -> dict:
    """
    Calculates stop loss and take profit prices.

    LONG:
        stop_loss   = entry - 3%
        take_profit = entry + 6%

    SHORT:
        stop_loss   = entry + 3%
        take_profit = entry - 6%
    """
    sl_pct = PAPER_TRADING_STOP_LOSS_PCT / 100
    tp_pct = PAPER_TRADING_TP_PCT / 100

    if direction == "LONG":
        stop_loss   = entry_price * (1 - sl_pct)
        take_profit = entry_price * (1 + tp_pct)
    else:
        stop_loss   = entry_price * (1 + sl_pct)
        take_profit = entry_price * (1 - tp_pct)

    return {
        "stop_loss":   round(stop_loss, 4),
        "take_profit": round(take_profit, 4),
    }


def should_open_trade(
    symbol: str,
    action: str,
    confidence: int,
    current_price: float,
) -> tuple[bool, str]:
    """
    Decides whether to open a trade.
    Returns (should_trade, reason).
    """
    portfolio = get_portfolio()

    # check 1 — max positions
    open_count = count_open_positions()
    if open_count >= PAPER_TRADING_MAX_POSITIONS:
        return False, f"Max positions reached ({open_count}/{PAPER_TRADING_MAX_POSITIONS})"

    # check 2 — already have position in this asset
    existing = get_open_position_for(symbol)
    if existing:
        return False, f"Already have open position in {symbol}"

    # check 3 — enough cash
    cash          = portfolio["cash_balance"]
    sizing        = calculate_position_size(current_price, cash)
    if sizing["position_size"] < 10:
        return False, f"Not enough cash — position size ${sizing['position_size']:.2f}"

    # check 4 — action must be BUY or SELL not HOLD
    if action == "HOLD":
        return False, "Action is HOLD"

    return True, "All checks passed"


def should_close_trade(
    position: dict,
    current_price: float,
) -> tuple[bool, str]:
    """
    Checks if an open position should be closed.
    Returns (should_close, reason).
    """
    direction   = position["direction"]
    stop_loss   = position["stop_loss"]
    take_profit = position["take_profit"]

    if direction == "LONG":
        if current_price <= stop_loss:
            return True, "STOP_LOSS"
        if current_price >= take_profit:
            return True, "TAKE_PROFIT"

    elif direction == "SHORT":
        if current_price >= stop_loss:
            return True, "STOP_LOSS"
        if current_price <= take_profit:
            return True, "TAKE_PROFIT"

    return False, "HOLD"


def get_direction(action: str) -> str:
    """Maps BUY → LONG, SELL → SHORT."""
    return "LONG" if action == "BUY" else "SHORT"