import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# from memory.state import PipelineState
from config import MAX_ALERTS_PER_DAY, ALERT_COOLDOWN_HOURS, MIN_CONFIDENCE_SCORE

# In-memory tracking (resets when app restarts)
# Will be replaced by database in a later step
_alerts_sent_today = []


def risk_agent(state: dict) -> dict:
    print("\n[RiskAgent] Running risk checks...")

    decision = state.get("decision")

    # If no decision made yet, skip risk check
    if not decision:
        print("  No decision to check yet — skipping")
        state["risk_check"] = {"passed": True, "reason": "No decision yet"}
        # 
        # return {"risk_check": {"passed": True, "reason": "All checks passed"}}
        return dict(state)

    symbol     = decision.get("symbol", "")
    action     = decision.get("action", "HOLD")
    confidence = decision.get("confidence", 0)

    # ── Check 1: HOLD signals don't need alerts ───────────
    if action == "HOLD":
        print(f"  {symbol}: Action is HOLD — no alert needed")
        state["risk_check"] = {"passed": False, "reason": "Action is HOLD"}
       
        # return {"risk_check": {"passed": True, "reason": "All checks passed"}}
        return dict(state)

    # ── Check 2: Confidence too low ───────────────────────
    if confidence < MIN_CONFIDENCE_SCORE:
        print(f"  {symbol}: Confidence {confidence}% below minimum {MIN_CONFIDENCE_SCORE}%")
        state["risk_check"] = {
            "passed": False,
            "reason": f"Confidence {confidence}% below minimum {MIN_CONFIDENCE_SCORE}%"
        }
        # 
        # return {"risk_check": {"passed": True, "reason": "All checks passed"}}
        return dict(state)

    # ── Check 3: Daily alert limit ────────────────────────
    today        = datetime.utcnow().date()
    alerts_today = [a for a in _alerts_sent_today if a["date"] == today]
    if len(alerts_today) >= MAX_ALERTS_PER_DAY:
        print(f"  Daily limit of {MAX_ALERTS_PER_DAY} alerts reached")
        state["risk_check"] = {
            "passed": False,
            "reason": f"Daily alert limit of {MAX_ALERTS_PER_DAY} reached"
        }
        # 
        # return {"risk_check": {"passed": True, "reason": "All checks passed"}}
        return dict(state)

    # ── Check 4: Cooldown per symbol ──────────────────────
    cutoff         = datetime.utcnow() - timedelta(hours=ALERT_COOLDOWN_HOURS)
    recent_same    = [
        a for a in _alerts_sent_today
        if a["symbol"] == symbol and a["timestamp"] > cutoff
    ]
    if recent_same:
        last_sent = recent_same[-1]["timestamp"].strftime("%H:%M UTC")
        print(f"  {symbol}: Already alerted at {last_sent} — cooldown active")
        state["risk_check"] = {
            "passed": False,
            "reason": f"{symbol} already alerted within {ALERT_COOLDOWN_HOURS}h cooldown"
        }
        # 
        # return {"risk_check": {"passed": True, "reason": "All checks passed"}}
        return dict(state)

    # ── All checks passed ─────────────────────────────────
    print(f"  {symbol}: All risk checks passed")
    state["risk_check"] = {"passed": True, "reason": "All checks passed"}
    # 
    return dict(state)


def record_alert(symbol: str) -> None:
    """Call this after an alert is successfully sent."""
    _alerts_sent_today.append({
        "symbol":    symbol,
        "date":      datetime.utcnow().date(),
        "timestamp": datetime.utcnow(),
    })