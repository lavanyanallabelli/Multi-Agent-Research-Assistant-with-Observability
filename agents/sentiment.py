import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from openai import OpenAI
from tools.newsapi import get_headlines
# from memory.state import PipelineState
from config import OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS

client = OpenAI(api_key=OPENAI_API_KEY)


def sentiment_agent(state: dict) -> dict:
    print("\n[SentimentAgent] Analyzing news sentiment...")

    top        = state["top_opportunities"]
    asset_data = {a["symbol"]: a for a in state["all_asset_data"]}

    for symbol in top:
        try:
            asset      = asset_data.get(symbol, {})
            asset_type = asset.get("asset_type", "unknown")

            print(f"  Fetching headlines for {symbol}...")
            headlines  = get_headlines(symbol, asset_type, max_articles=10)

            if not headlines:
                print(f"  {symbol}: No headlines found")
                state["sentiment_results"][symbol] = {
                    "symbol":         symbol,
                    "sentiment":      "Neutral",
                    "confidence":     50.0,
                    "summary":        "No recent news found",
                }
                continue

            headlines_text = "\n".join([f"- {h}" for h in headlines])

            prompt = f"""You are a financial analyst. Analyze these headlines for {symbol} and return ONLY a JSON object.

Headlines:
{headlines_text}

Return exactly this JSON format with no extra text:
{{
    "sentiment": "Bullish" or "Bearish" or "Neutral",
    "confidence": number between 0 and 100,
    "summary": "one sentence explanation"
}}"""

            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )

            raw     = response.choices[0].message.content.strip()
            # strip markdown code fences if present
            raw     = raw.replace("```json", "").replace("```", "").strip()
            result  = json.loads(raw)

            state["sentiment_results"][symbol] = {
                "symbol":     symbol,
                "sentiment":  result.get("sentiment", "Neutral"),
                "confidence": float(result.get("confidence", 50)),
                "summary":    result.get("summary", ""),
            }

            # track token usage
            state["token_usage"]["sentiment"] = (
                state["token_usage"].get("sentiment", 0) +
                response.usage.total_tokens
            )

            print(f"  {symbol}: {result['sentiment']} | "
                  f"confidence: {result['confidence']}% | "
                  f"{result['summary']}")

        except Exception as e:
            error = f"[SentimentAgent] Failed on {symbol}: {e}"
            print(error)
            state["errors"].append(error)
            state["sentiment_results"][symbol] = {
                "symbol":     symbol,
                "sentiment":  "Neutral",
                "confidence": 50.0,
                "summary":    "Sentiment analysis failed",
            }

    return dict(state)
    # return {
        # "sentiment_results": state["sentiment_results"],
        # "token_usage":       state.get("token_usage", {}),
        # "errors":            state.get("errors", []),
    # }