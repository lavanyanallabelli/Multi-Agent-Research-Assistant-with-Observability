import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.technical_indicators import calculate_indicators, score_signal, detect_market_regime, calculate_volume_signal, check_timeframe_confirmation
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
            regime             = detect_market_regime(data["ohlcv"])
            volume_signal      = calculate_volume_signal(data["ohlcv"])
            timeframe          = check_timeframe_confirmation(data["ohlcv"])
            signal, strength   = score_signal(indicators, data["price"], regime, volume_signal, timeframe)

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