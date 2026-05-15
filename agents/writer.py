import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# from memory.state import PipelineState


ACTION_EMOJI = {
    "BUY":  "🟢",
    "SELL": "🔴",
    "HOLD": "🟡",
}

ASSET_EMOJI = {
    "crypto": "🪙",
    "stock":  "📈",
}


def writer_agent(state: dict) -> dict:
    print("\n[WriterAgent] Formatting alert message...")

    decision = state.get("decision")

    if not decision:
        print("  No decision to write — skipping")
        return dict(state)

    if decision["action"] == "HOLD":
        print("  Action is HOLD — no alert needed")
        state["alert_message"] = None
        return dict(state)

    symbol     = decision["symbol"]
    action     = decision["action"]
    confidence = decision["confidence"]
    asset_type = decision["asset_type"]
    reasoning  = decision["reasoning"]
    entry_zone = decision["entry_zone"]
    target     = decision["target"]
    stop_loss  = decision["stop_loss"]

    asset_data = {a["symbol"]: a for a in state["all_asset_data"]}
    asset      = asset_data.get(symbol, {})
    price      = asset.get("price", 0)
    change_24h = asset.get("price_change_24h", 0)

    technical  = state["technical_signals"].get(symbol, {})
    sentiment  = state["sentiment_results"].get(symbol, {})

    action_emoji = ACTION_EMOJI.get(action, "⚪")
    asset_emoji  = ASSET_EMOJI.get(asset_type, "📊")
    change_arrow = "▲" if change_24h >= 0 else "▼"
    now          = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # paper trade result
    paper_opened  = state.get("paper_trade_opened", False)
    paper_section = "✅ Paper position opened" if paper_opened else "⏭️ Paper trade skipped"

    # alpaca execution result
    execution     = state.get("execution_result")
    if not execution:
        alpaca_section = "⏭️ Alpaca skipped"
    elif execution.get("status") == "submitted":
        alpaca_section = f"✅ Alpaca order submitted — {execution.get('qty')} {symbol} | ID: {execution.get('order_id', 'N/A')}"
    elif execution.get("status") == "skipped":
        alpaca_section = f"⏭️ Alpaca skipped — {execution.get('reason', '')}"
    else:
        alpaca_section = f"❌ Alpaca failed — {execution.get('error', 'unknown error')}"

    text = f"""{action_emoji} <b>{action} SIGNAL — {symbol}</b> {asset_emoji}

💰 <b>Price:</b> ${price:,.2f} ({change_arrow}{abs(change_24h):.2f}% 24h)
🎯 <b>Confidence:</b> {confidence}%

📊 <b>Technical:</b>
  • RSI: {technical.get('rsi', 'N/A')}
  • MACD: {technical.get('macd', 'N/A')}
  • Signal Strength: {technical.get('signal_strength', 'N/A')}

📰 <b>Sentiment:</b> {sentiment.get('sentiment', 'N/A')} ({sentiment.get('confidence', 'N/A')}%)
  • {sentiment.get('summary', 'N/A')}

🧠 <b>Reasoning:</b>
{reasoning}

📍 <b>Entry Zone:</b> {entry_zone}
🎯 <b>Target:</b> {target}
🛑 <b>Stop Loss:</b> {stop_loss}

🤖 <b>Execution:</b>
  • Simulator: {paper_section}
  • Alpaca: {alpaca_section}

⏰ {now}
⚠️ <i>Not financial advice. Always do your own research.</i>"""

    state["alert_message"] = {
        "text":       text,
        "symbol":     symbol,
        "action":     action,
        "confidence": confidence,
    }

    print(f"  Alert formatted for {symbol} — {action} @ {confidence}%")
    return dict(state)