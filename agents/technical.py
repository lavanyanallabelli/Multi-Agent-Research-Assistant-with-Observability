import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.technical_indicators import calculate_indicators, score_signal
# from memory.state import PipelineState


def technical_agent(state: dict) -> dict:
    print("\n[TechnicalAgent] Running technical analysis...")

    top        = state["top_opportunities"]
    asset_data = {a["symbol"]: a for a in state["all_asset_data"]}

    for symbol in top:
        try:
            data       = asset_data.get(symbol)
            if not data:
                raise ValueError(f"No data found for {symbol}")

            indicators         = calculate_indicators(data["ohlcv"])
            signal, strength   = score_signal(indicators, data["price"])

            state["technical_signals"][symbol] = {
                "symbol":         symbol,
                "rsi":            indicators["rsi"],
                "macd":           indicators["macd"],
                "macd_signal":    indicators["macd_signal"],
                "bb_upper":       indicators["bb_upper"],
                "bb_lower":       indicators["bb_lower"],
                "signal":         signal,
                "signal_strength": strength,
            }

            print(f"  {symbol}: RSI={indicators['rsi']} | "
                  f"MACD={indicators['macd']} | "
                  f"Signal={signal} | "
                  f"Strength={strength}")

        except Exception as e:
            error = f"[TechnicalAgent] Failed on {symbol}: {e}"
            print(error)
            state["errors"].append(error)

    return dict(state) 
    # return {
        # "technical_signals": state["technical_signals"],
        # "errors":            state.get("errors", []),
    # }