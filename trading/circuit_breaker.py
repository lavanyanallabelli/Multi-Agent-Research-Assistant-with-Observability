import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from trading.portfolio import get_portfolio, get_recent_trades
from tools.telegram import send_message
from config import CIRCUIT_BREAKER_PCT, PAPER_TRADING_BALANCE


def check_circuit_breaker() -> tuple[bool, str]:
    """
    Checks if trading should be paused.
    Returns (is_triggered, reason).

    Triggers if:
    1. Portfolio dropped 15% from starting balance
    2. Lost 3 trades in a row
    3. Lost more than 10% in the last 7 days
    """

    portfolio = get_portfolio()
    total_pnl_pct = portfolio.get("total_pnl_pct", 0)

    # check 1 — total drawdown from starting balance
    if total_pnl_pct <= -CIRCUIT_BREAKER_PCT:
        reason = (f"Total drawdown {total_pnl_pct:.1f}% "
                  f"exceeded limit of -{CIRCUIT_BREAKER_PCT}%")
        return True, reason

    # check 2 — 3 consecutive losing trades
    recent = get_recent_trades(5)
    if len(recent) >= 3:
        last_3 = recent[:3]
        all_losses = all(t["pnl"] < 0 for t in last_3)
        if all_losses:
            total_loss = sum(t["pnl"] for t in last_3)
            reason = (f"3 consecutive losing trades. "
                      f"Total loss: ${total_loss:,.2f}")
            return True, reason

    # check 3 — weekly drawdown
    recent_all = get_recent_trades(50)
    week_ago   = datetime.utcnow() - timedelta(days=7)
    week_trades = [
        t for t in recent_all
        if datetime.fromisoformat(
            t["closed_at"].replace(" ", "T")
        ) > week_ago
    ]
    if week_trades:
        week_pnl     = sum(t["pnl"] for t in week_trades)
        week_pnl_pct = (week_pnl / PAPER_TRADING_BALANCE) * 100
        if week_pnl_pct <= -10.0:
            reason = (f"Weekly loss {week_pnl_pct:.1f}% "
                      f"exceeded -10% limit")
            return True, reason

    return False, "All checks passed"


def trigger_circuit_breaker(reason: str) -> None:
    """
    Called when circuit breaker fires.
    Sends Telegram alert and logs to console.
    """
    print(f"\n[CircuitBreaker] TRIGGERED — {reason}")

    msg = f"""⛔ <b>CIRCUIT BREAKER TRIGGERED</b>

🔴 All trading has been paused automatically.

Reason: {reason}

Portfolio status:
{_portfolio_summary()}

Action required:
Review your strategy before resuming trading.

⚠️ <i>Paper trading paused — no real money affected</i>"""

    send_message(msg)


def _portfolio_summary() -> str:
    p = get_portfolio()
    return (
        f"  Balance: ${p['cash_balance']:,.2f}\n"
        f"  Total P&L: ${p['total_pnl']:+,.2f} "
        f"({p['total_pnl_pct']:+.2f}%)\n"
        f"  Win rate: {p['win_rate']}%\n"
        f"  Total trades: {p['total_trades']}"
    )


def run_circuit_breaker_check() -> bool:
    """
    Main entry point — call this every pipeline run.
    Returns True if trading should be paused.
    """
    triggered, reason = check_circuit_breaker()
    if triggered:
        trigger_circuit_breaker(reason)
        return True
    print(f"  [CircuitBreaker] OK — {reason}")
    return False