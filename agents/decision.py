import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from openai import OpenAI
# from memory.state import PipelineState
from config import OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS




def decision_agent(state: dict) -> dict:
    client = OpenAI(api_key=OPENAI_API_KEY)
    print("\n[DecisionAgent] Making trading decision...")

    top        = state["top_opportunities"]
    asset_data = {a["symbol"]: a for a in state["all_asset_data"]}

    best_decision  = None
    best_confidence = 0

    for symbol in top:
        try:
            asset      = asset_data.get(symbol, {})
            technical  = state["technical_signals"].get(symbol, {})
            sentiment  = state["sentiment_results"].get(symbol, {})

            prompt = f"""You are an expert swing trader. Analyze this data and make a trading decision.

Asset: {symbol} ({asset.get('asset_type', 'unknown')})
Current Price: ${asset.get('price', 0):,.2f}
24h Change: {asset.get('price_change_24h', 0):.2f}%

Technical Analysis:
- RSI: {technical.get('rsi', 'N/A')}
- MACD: {technical.get('macd', 'N/A')}
- MACD Signal: {technical.get('macd_signal', 'N/A')}
- Bollinger Upper: {technical.get('bb_upper', 'N/A')}
- Bollinger Lower: {technical.get('bb_lower', 'N/A')}
- Technical Signal: {technical.get('signal', 'N/A')}
- Signal Strength: {technical.get('signal_strength', 'N/A')}

News Sentiment:
- Sentiment: {sentiment.get('sentiment', 'N/A')}
- Confidence: {sentiment.get('confidence', 'N/A')}%
- Summary: {sentiment.get('summary', 'N/A')}

Return ONLY a JSON object with no extra text:
{{
    "action": "BUY" or "SELL" or "HOLD",
    "confidence": number between 0 and 100,
    "reasoning": "2-3 sentence explanation",
    "entry_zone": "price range to enter e.g. $88.00 - $90.00",
    "target": "price target e.g. $95.00",
    "stop_loss": "stop loss price e.g. $85.00"
}}"""

            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )

            raw    = response.choices[0].message.content.strip()
            raw    = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)

            confidence = int(result.get("confidence", 0))

            print(f"  {symbol}: {result['action']} | "
                  f"confidence: {confidence}% | "
                  f"{result['reasoning'][:80]}...")

            # track token usage
            state["token_usage"]["decision"] = (
                state["token_usage"].get("decision", 0) +
                response.usage.total_tokens
            )

            # keep the highest confidence decision
            if confidence > best_confidence:
                best_confidence = confidence
                best_decision   = {
                    "symbol":     symbol,
                    "asset_type": asset.get("asset_type", "unknown"),
                    "action":     result.get("action", "HOLD"),
                    "confidence": confidence,
                    "reasoning":  result.get("reasoning", ""),
                    "entry_zone": result.get("entry_zone", "N/A"),
                    "target":     result.get("target", "N/A"),
                    "stop_loss":  result.get("stop_loss", "N/A"),
                }

        except Exception as e:
            error = f"[DecisionAgent] Failed on {symbol}: {e}"
            print(error)
            state["errors"].append(error)

    # return {
        # "decision":    best_decision,
        # "token_usage": state.get("token_usage", {}),
        # "errors":      state.get("errors", []),
    # }

    state["decision"] = best_decision
    return dict(state)
    # if best_decision:
        # print(f"\n[DecisionAgent] Best opportunity: "
            #   f"{best_decision['symbol']} → {best_decision['action']} "
            #   f"@ {best_decision['confidence']}% confidence")
    # else:
        # print("\n[DecisionAgent] No strong decision found")

    # return state