import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    MAX_ALERTS_PER_DAY,
    ALERT_COOLDOWN_HOURS,
    MIN_CONFIDENCE_SCORE,
)
from memory.audit_log import total_alerts_today, last_alert_for

# Assets that move together — if one is already signaling
# don't signal the others in the same direction
CORRELATION_GROUPS = [
    ["BTC", "ETH", "SOL", "BNB"],   # crypto moves together
    ["AAPL", "NVDA", "TSLA"],        # tech stocks move together
]

# tracks active signals this run — resets each pipeline run
_active_signals_this_run = []


def get_correlated_symbols(symbol: str) -> list[str]:
    """Returns all symbols correlated with the given symbol."""
    for group in CORRELATION_GROUPS:
        if symbol in group:
            return [s for s in group if s != symbol]
    return []


def risk_agent(state: dict) -> dict:
    print("\n[RiskAgent] Running risk checks...")

    decision = state.get("decision")
    if not decision:
        print("  No decision to check — skipping")
        state["risk_check"] = {"passed": True, "reason": "No decision yet"}
        return dict(state)

    symbol     = decision.get("symbol", "")
    action     = decision.get("action", "HOLD")
    confidence = decision.get("confidence", 0)

    # ── Check 1: HOLD signals don't need alerts ───────────
    if action == "HOLD":
        print(f"  {symbol}: Action is HOLD — no alert needed")
        state["risk_check"] = {"passed": False, "reason": "Action is HOLD"}
        return dict(state)

    # ── Check 2: Confidence too low ───────────────────────
    if confidence < MIN_CONFIDENCE_SCORE:
        print(f"  {symbol}: Confidence {confidence}% below "
              f"minimum {MIN_CONFIDENCE_SCORE}%")
        state["risk_check"] = {
            "passed": False,
            "reason": f"Confidence {confidence}% below minimum "
                      f"{MIN_CONFIDENCE_SCORE}%"
        }
        return dict(state)

    # ── Check 3: Daily alert limit ────────────────────────
    alerts_today = total_alerts_today()
    if alerts_today >= MAX_ALERTS_PER_DAY:
        print(f"  Daily limit of {MAX_ALERTS_PER_DAY} alerts reached")
        state["risk_check"] = {
            "passed": False,
            "reason": f"Daily alert limit of {MAX_ALERTS_PER_DAY} reached"
        }
        return dict(state)

    # ── Check 4: Cooldown per symbol ──────────────────────
    last_alert = last_alert_for(symbol)
    if last_alert:
        cutoff  = datetime.utcnow() - timedelta(hours=ALERT_COOLDOWN_HOURS)
        if last_alert > cutoff:
            last_sent = last_alert.strftime("%H:%M UTC")
            print(f"  {symbol}: Already alerted at {last_sent} "
                  f"— cooldown active")
            state["risk_check"] = {
                "passed": False,
                "reason": f"{symbol} already alerted within "
                          f"{ALERT_COOLDOWN_HOURS}h cooldown"
            }
            return dict(state)

    # ── Check 5: Correlation filter ───────────────────────
    correlated = get_correlated_symbols(symbol)
    technical  = state.get("technical_signals", {})

    conflicting = []
    for corr_symbol in correlated:
        corr_signal = technical.get(corr_symbol, {})
        corr_action = corr_signal.get("signal", "HOLD")
        if corr_action == action:
            conflicting.append(corr_symbol)

    if len(conflicting) >= 2:
        print(f"  {symbol}: Correlation filter triggered — "
              f"{conflicting} already showing same signal")
        state["risk_check"] = {
            "passed": False,
            "reason": f"Correlated assets {conflicting} already "
                      f"showing {action} signal — avoiding overexposure"
        }
        return dict(state)

    # ── All checks passed ─────────────────────────────────
    print(f"  {symbol}: All risk checks passed ✅")
    state["risk_check"] = {"passed": True, "reason": "All checks passed"}
    return dict(state)


def record_alert(symbol: str) -> None:
    """Call this after an alert is successfully sent."""
    _active_signals_this_run.append({
        "symbol":    symbol,
        "timestamp": datetime.utcnow(),
    })