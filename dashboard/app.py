import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from memory.audit_log import get_recent_runs, get_recent_alerts
from backtesting.backtest import run_backtest
from config import CRYPTO_ASSETS
from datetime import datetime


def print_header():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print("\n" + "="*60)
    print("   SWING TRADING ASSISTANT — DASHBOARD")
    print(f"   {now}")
    print("="*60)


def print_performance():
    runs   = get_recent_runs(50)
    alerts = get_recent_alerts(50)

    total_runs      = len(runs)
    total_alerts    = len(alerts)
    total_cost      = sum(r["total_cost_usd"] for r in runs)
    total_tokens    = sum(r["total_tokens"] for r in runs)

    buy_alerts  = [a for a in alerts if a["action"] == "BUY"]
    sell_alerts = [a for a in alerts if a["action"] == "SELL"]
    avg_conf    = (
        sum(a["confidence"] for a in alerts) / len(alerts)
        if alerts else 0
    )

    print("\n📊 PERFORMANCE SUMMARY")
    print("-"*40)
    print(f"  Total pipeline runs:   {total_runs}")
    print(f"  Total alerts sent:     {total_alerts}")
    print(f"  BUY alerts:            {len(buy_alerts)}")
    print(f"  SELL alerts:           {len(sell_alerts)}")
    print(f"  Avg confidence:        {avg_conf:.1f}%")
    print(f"  Total tokens used:     {total_tokens:,}")
    print(f"  Total cost:            ${total_cost:.4f}")
    if total_runs > 0:
        print(f"  Avg cost per run:      ${total_cost/total_runs:.6f}")


def print_recent_runs():
    runs = get_recent_runs(5)
    print("\n⏱️  RECENT PIPELINE RUNS")
    print("-"*40)
    if not runs:
        print("  No runs yet")
        return
    for run in runs:
        alert_icon = "✅" if run["alert_sent"] else "⬜"
        action     = run["action"] or "NO ACTION"
        symbol     = run["symbol"] or ""
        conf       = f"{run['confidence']}%" if run["confidence"] else ""
        print(f"  {alert_icon} {run['triggered_at'][:16]} | "
              f"{run['top_assets']} | "
              f"{action} {symbol} {conf} | "
              f"${run['total_cost_usd']:.6f}")


def print_recent_alerts():
    alerts = get_recent_alerts(10)
    print("\n📱 RECENT ALERTS")
    print("-"*40)
    if not alerts:
        print("  No alerts sent yet")
        return
    for alert in alerts:
        emoji = "🟢" if alert["action"] == "BUY" else "🔴"
        print(f"  {emoji} {alert['sent_at'][:16]} | "
              f"{alert['symbol']:6} {alert['action']:4} | "
              f"Confidence: {alert['confidence']}%")


def print_backtest_summary():
    print("\n🧪 BACKTEST ACCURACY (90 days)")
    print("-"*40)
    for asset in CRYPTO_ASSETS:
        result = run_backtest(
            symbol=asset["symbol"],
            coingecko_id=asset["coingecko_id"],
            days=90,
            hold_days=3,
        )
        if result and result.get("total_signals", 0) > 0:
            accuracy = result["accuracy"]
            signals  = result["total_signals"]
            bar      = "█" * int(accuracy / 10)
            print(f"  {asset['symbol']:6} {bar:10} {accuracy}% "
                  f"({signals} signals)")
        else:
            print(f"  {asset['symbol']:6} No signals")


def run_dashboard(show_backtest: bool = False):
    print_header()
    print_performance()
    print_recent_runs()
    print_recent_alerts()
    if show_backtest:
        print_backtest_summary()
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backtest",
        action="store_true",
        help="Include backtest accuracy (takes ~30 seconds)"
    )
    args = parser.parse_args()
    run_dashboard(show_backtest=args.backtest)