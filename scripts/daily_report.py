import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from memory.audit_log import get_recent_runs, get_recent_alerts
from trading.portfolio import get_portfolio, get_recent_trades, get_open_positions
from tools.telegram import send_message


def generate_daily_report() -> str:
    today     = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    portfolio  = get_portfolio()
    runs       = get_recent_runs(100)
    alerts     = get_recent_alerts(100)
    trades     = get_recent_trades(100)
    positions  = get_open_positions()

    # filter to today only
    runs_today = [
        r for r in runs
        if r["triggered_at"][:10] == str(today)
    ]
    alerts_today = [
        a for a in alerts
        if a["sent_at"][:10] == str(today)
    ]
    trades_today = [
        t for t in trades
        if t["closed_at"][:10] == str(today)
    ]

    pnl_today  = sum(t["pnl"] for t in trades_today)
    wins_today = len([t for t in trades_today if t["pnl"] >= 0])
    loss_today = len([t for t in trades_today if t["pnl"] < 0])

    cost_today = sum(
        r["total_cost_usd"] for r in runs_today
    )

    report = f"""📊 <b>DAILY TRADING REPORT</b>
{today.strftime("%B %d, %Y")}

💼 <b>Portfolio</b>
  Total Value:    ${portfolio['total_value']:,.2f}
  Cash Balance:   ${portfolio['cash_balance']:,.2f}
  Total P&L:      ${portfolio['total_pnl']:+,.2f} ({portfolio['total_pnl_pct']:+.2f}%)
  Win Rate:       {portfolio['win_rate']}%
  Open Positions: {portfolio['open_positions']}

📈 <b>Today's Activity</b>
  Pipeline runs:  {len(runs_today)}
  Alerts sent:    {len(alerts_today)}
  Trades closed:  {len(trades_today)}
  Today's P&L:    ${pnl_today:+,.2f}
  Wins/Losses:    {wins_today}W / {loss_today}L
  AI cost today:  ${cost_today:.4f}

📱 <b>Open Positions</b>"""

    if not positions:
        report += "\n  No open positions"
    else:
        for p in positions:
            report += f"\n  • {p['symbol']} {p['direction']} @ ${p['entry_price']:,.2f}"

    report += f"""

⏰ Generated at {datetime.utcnow().strftime("%H:%M UTC")}
⚠️ <i>Paper trading — not real money</i>"""

    return report


if __name__ == "__main__":
    print("Generating daily report...")
    report = generate_daily_report()
    print(report)
    print("\nSending to Telegram...")
    from tools.telegram import send_message
    send_message(report)
    print("Done.")