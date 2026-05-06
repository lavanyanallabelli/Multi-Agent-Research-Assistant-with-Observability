import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.telegram import send_message
from agents.risk import record_alert
# from memory.state import PipelineState


def notification_agent(state: dict) -> dict:
    print("\n[NotificationAgent] Sending alert...")

    # Debug — print exactly what we received
    # print(f"  risk_check: {state.get('risk_check')}")
    # print(f"  alert_message exists: {state.get('alert_message') is not None}")
    # print(f"  decision: {state.get('decision')}")

    # ── Check risk passed ─────────────────────────────────
    risk = state.get("risk_check")
    if not risk or not risk.get("passed"):
        reason = risk.get("reason", "Risk check failed") if risk else "No risk check"
        print(f"  Blocked: {reason}")
        state["alert_sent"] = False
        return dict(state)
        # return state
        # return {
        # "alert_sent": state.get("alert_sent", False),
        # "errors":     state.get("errors", []),
    # }

    # ── Check alert message exists ────────────────────────
    alert = state.get("alert_message")
    if not alert:
        print("  No alert message to send — skipping")
        state["alert_sent"] = False
        # return state
        # return {
        # "alert_sent": state.get("alert_sent", False),
        # "errors":     state.get("errors", []),
    # }
        return dict(state)
    # Check action is not HOLD
    if alert.get("action") == "HOLD":
        print("  Action is HOLD — skipping")
        state["alert_sent"] = False
        return dict(state)

    print(f"  Attempting to send to Telegram...")

    # ── Send to Telegram ──────────────────────────────────
    success = send_message(alert["text"])

    if success:
        print(f"  Alert sent for {alert['symbol']} — {alert['action']} @ {alert['confidence']}%")
        record_alert(alert["symbol"])
        state["alert_sent"] = True
    else:
        print("  Failed to send alert")
        state["alert_sent"] = False
        state["errors"].append("[NotificationAgent] Telegram send failed")
    return dict(state)
     # return state
    # return {
        # "alert_sent": state.get("alert_sent", False),
        # "errors":     state.get("errors", []),
    # }