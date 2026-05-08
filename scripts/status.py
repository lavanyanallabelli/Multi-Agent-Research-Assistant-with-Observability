import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from memory.audit_log import get_recent_runs, get_recent_alerts
from datetime import datetime
import json


def print_status():
    print("\n" + "="*50)
    print("SWING TRADING ASSISTANT — STATUS")
    print("="*50)

    print("\n📊 Recent Pipeline Runs:")
    runs = get_recent_runs(5)
    if not runs:
        print("  No runs yet")
    for run in runs:
        alert_icon = "✅" if run["alert_sent"] else "⬜"
        print(f"  {alert_icon} {run['triggered_at'][:16]} | "
              f"Top: {run['top_assets']} | "
              f"{run['action'] or 'NO ACTION'} {run['symbol'] or ''} "
              f"{run['confidence'] or ''}% | "
              f"${run['total_cost_usd']:.6f}")

    print("\n📱 Recent Alerts Sent:")
    alerts = get_recent_alerts(5)
    if not alerts:
        print("  No alerts sent yet")
    for alert in alerts:
        emoji = "🟢" if alert["action"] == "BUY" else "🔴"
        print(f"  {emoji} {alert['sent_at'][:16]} | "
              f"{alert['symbol']} {alert['action']} @ "
              f"{alert['confidence']}%")

    print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    print_status()