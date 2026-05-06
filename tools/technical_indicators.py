import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    import pandas_ta as ta
    USE_PANDAS_TA = True
except ImportError:
    import ta as ta_lib
    USE_PANDAS_TA = False


def calculate_indicators(ohlcv: list[dict]) -> dict:
    if len(ohlcv) < 20:
        return {
            "rsi":         None,
            "macd":        None,
            "macd_signal": None,
            "bb_upper":    None,
            "bb_lower":    None,
            "bb_mid":      None,
        }

    df          = pd.DataFrame(ohlcv) # converts our list of candle dictionaries into a pandas DataFrame. Think of it as turning a list into a spreadsheet with columns.
    df["close"] = pd.to_numeric(df["c"], errors="coerce")
    #pd.to_numeric(..., errors="coerce") — converts values to numbers. 
    # If a value can't be converted it becomes NaN instead of crashing. 
    # The errors="coerce" part is the safety net.
    df["high"]  = pd.to_numeric(df["h"], errors="coerce")
    df["low"]   = pd.to_numeric(df["l"], errors="coerce")
    df["volume"]= pd.to_numeric(df["v"], errors="coerce")
    df          = df.dropna(subset=["close"])

    if USE_PANDAS_TA:
        rsi        = df.ta.rsi(length=14) #calculates RSI using 14 periods. 14 is the standard setting used by traders worldwide.
        macd_df    = df.ta.macd(fast=12, slow=26, signal=9) #the three MACD numbers are industry standard:
        bb_df      = df.ta.bbands(length=20) #Bollinger Bands using 20 periods. Also industry standard.

        rsi_val    = float(rsi.iloc[-1])        if rsi is not None and len(rsi) > 0        else None
        macd_val   = float(macd_df["MACD_12_26_9"].iloc[-1])   if macd_df is not None else None
        signal_val = float(macd_df["MACDs_12_26_9"].iloc[-1])  if macd_df is not None else None
        bb_upper   = float(bb_df["BBU_20_2.0"].iloc[-1])       if bb_df is not None   else None
        bb_lower   = float(bb_df["BBL_20_2.0"].iloc[-1])       if bb_df is not None   else None
        bb_mid     = float(bb_df["BBM_20_2.0"].iloc[-1])       if bb_df is not None   else None

    else:
        rsi_val    = float(ta_lib.momentum.RSIIndicator(df["close"], window=14).rsi().iloc[-1])
        macd_obj   = ta_lib.trend.MACD(df["close"], window_fast=12, window_slow=26, window_sign=9)
        macd_val   = float(macd_obj.macd().iloc[-1])
        signal_val = float(macd_obj.macd_signal().iloc[-1])
        bb_obj     = ta_lib.volatility.BollingerBands(df["close"], window=20, window_dev=2)
        bb_upper   = float(bb_obj.bollinger_hband().iloc[-1])
        bb_lower   = float(bb_obj.bollinger_lband().iloc[-1])
        bb_mid     = float(bb_obj.bollinger_mavg().iloc[-1])

    return {
        "rsi":         round(rsi_val, 2)    if rsi_val    is not None else None,
        "macd":        round(macd_val, 4)   if macd_val   is not None else None,
        "macd_signal": round(signal_val, 4) if signal_val is not None else None,
        "bb_upper":    round(bb_upper, 2)   if bb_upper   is not None else None,
        "bb_lower":    round(bb_lower, 2)   if bb_lower   is not None else None,
        "bb_mid":      round(bb_mid, 2)     if bb_mid     is not None else None,
    }


def score_signal(indicators: dict, price: float) -> tuple[str, float]:
    score  = 50.0
    signal = "HOLD"
    rsi    = indicators.get("rsi")
    macd   = indicators.get("macd")
    sig    = indicators.get("macd_signal")
    bb_low = indicators.get("bb_lower")
    bb_up  = indicators.get("bb_upper")

    if rsi is not None:
        if rsi < 30:
            score += 20
        elif rsi < 40:
            score += 10
        elif rsi > 70:
            score -= 20
        elif rsi > 60:
            score -= 10

    if macd is not None and sig is not None:
        if macd > sig:
            score += 15
        else:
            score -= 15

    if bb_low is not None and bb_up is not None:
        if price <= bb_low:
            score += 15
        elif price >= bb_up:
            score -= 15

    score = max(0, min(100, score))

    if score >= 65:
        signal = "BUY"
    elif score <= 35:
        signal = "SELL"
    else:
        signal = "HOLD"

    return signal, round(score, 1)