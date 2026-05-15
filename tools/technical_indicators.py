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

def detect_market_regime(ohlcv: list[dict]) -> str:
    """
    Detects current market regime using 200-day moving average.

    Returns:
        "bull"     — price above 200 MA, favor BUY signals
        "bear"     — price below 200 MA, favor SELL signals
        "neutral"  — not enough data
    """
    if len(ohlcv) < 50:
        return "neutral"

    df            = pd.DataFrame(ohlcv)
    df["close"]   = pd.to_numeric(df["c"], errors="coerce")
    df            = df.dropna(subset=["close"])

    ma_period     = min(200, len(df))
    ma            = df["close"].rolling(window=ma_period).mean().iloc[-1]
    current_price = df["close"].iloc[-1]

    if current_price > ma:
        return "bull"
    elif current_price < ma:
        return "bear"
    else:
        return "neutral"

def calculate_volume_signal(ohlcv: list[dict]) -> dict:
    """
    Compares current volume to average volume.
    High volume confirms signals. Low volume weakens them.

    Returns:
        volume_ratio  — current vol / average vol
        confirmation  — "high" | "normal" | "low"
        score_adjust  — points to add/subtract from signal score
    """
    if len(ohlcv) < 10:
        return {
            "volume_ratio":  1.0,
            "confirmation":  "normal",
            "score_adjust":  0,
        }

    df           = pd.DataFrame(ohlcv)
    df["volume"] = pd.to_numeric(df["v"], errors="coerce").fillna(0)

    # skip if all volumes are zero (CoinGecko OHLC limitation)
    if df["volume"].sum() == 0:
        return {
            "volume_ratio":  1.0,
            "confirmation":  "normal",
            "score_adjust":  0,
        }

    avg_volume     = df["volume"].iloc[:-1].mean()
    current_volume = df["volume"].iloc[-1]

    if avg_volume == 0:
        ratio = 1.0
    else:
        ratio = current_volume / avg_volume

    if ratio >= 1.5:
        confirmation = "high"
        score_adjust = 10
    elif ratio <= 0.5:
        confirmation = "low"
        score_adjust = -10
    else:
        confirmation = "normal"
        score_adjust = 0

    return {
        "volume_ratio":  round(ratio, 2),
        "confirmation":  confirmation,
        "score_adjust":  score_adjust,
    }

def check_timeframe_confirmation(ohlcv: list[dict]) -> dict:
    """
    Confirms signal across two timeframes.
    Daily candles = trend direction
    Last 7 candles = short term momentum

    Returns:
        trend        — "up" | "down" | "neutral"
        momentum     — "up" | "down" | "neutral"
        confirmed    — True if both agree
        score_adjust — points to add/subtract
    """
    if len(ohlcv) < 14:
        return {
            "trend":        "neutral",
            "momentum":     "neutral",
            "confirmed":    False,
            "score_adjust": 0,
        }

    df          = pd.DataFrame(ohlcv)
    df["close"] = pd.to_numeric(df["c"], errors="coerce")
    df          = df.dropna(subset=["close"])

    # long term trend — 20 day MA direction
    ma_20       = df["close"].rolling(window=20).mean()
    ma_now      = ma_20.iloc[-1]
    ma_prev     = ma_20.iloc[-5]

    if ma_now > ma_prev * 1.001:
        trend = "up"
    elif ma_now < ma_prev * 0.999:
        trend = "down"
    else:
        trend = "neutral"

    # short term momentum — last 7 candles
    recent      = df["close"].iloc[-7:]
    first_price = recent.iloc[0]
    last_price  = recent.iloc[-1]
    change_pct  = ((last_price - first_price) / first_price) * 100

    if change_pct > 1.0:
        momentum = "up"
    elif change_pct < -1.0:
        momentum = "down"
    else:
        momentum = "neutral"

    # confirmation — both timeframes agree
    confirmed = (
        (trend == "up"   and momentum == "up") or
        (trend == "down" and momentum == "down")
    )

    # score adjustment
    if confirmed and trend == "up":
        score_adjust = 10    # both bullish — boost BUY signals
    elif confirmed and trend == "down":
        score_adjust = -10   # both bearish — boost SELL signals
    elif trend == "neutral" or momentum == "neutral":
        score_adjust = 0     # unclear — no adjustment
    else:
        score_adjust = -5    # conflicting timeframes — reduce confidence

    return {
        "trend":        trend,
        "momentum":     momentum,
        "confirmed":    confirmed,
        "score_adjust": score_adjust,
    }

def score_signal(indicators: dict, price: float, regime: str = "neutral", volume_signal: dict = None, timeframe: dict = None) -> tuple[str, float]:
    score  = 50.0

    if volume_signal:
        score += volume_signal.get("score_adjust", 0)

    if timeframe:
        score += timeframe.get("score_adjust", 0)

    # adjust base score based on market regime
    if regime == "bull":
        score += 5    # slight BUY bias in bull market
    elif regime == "bear":
        score -= 5    # slight SELL bias in bear market

    # signal = "HOLD"
    rsi    = indicators.get("rsi")
    macd   = indicators.get("macd")
    sig    = indicators.get("macd_signal")
    bb_low = indicators.get("bb_lower")
    bb_up  = indicators.get("bb_upper")

     # ── RSI scoring — tighter thresholds ─────────────────
    if rsi is not None:
        if rsi < 25:       # extremely oversold
            score += 25
        elif rsi < 35:     # oversold
            score += 15
        elif rsi < 45:     # slightly oversold
            score += 5
        elif rsi > 75:     # extremely overbought
            score -= 25
        elif rsi > 65:     # overbought
            score -= 15
        elif rsi > 55:     # slightly overbought
            score -= 5
        # 45-55 = neutral zone, no score change

    # ── MACD scoring ──────────────────────────────────────
    if macd is not None and sig is not None:
        diff = macd - sig
        if diff > 0:
            score += 10
        else:
            score -= 10

    # ── Bollinger Band scoring ────────────────────────────
    if bb_low is not None and bb_up is not None:
        bb_range = bb_up - bb_low
        if bb_range > 0:
            position = (price - bb_low) / bb_range
            if position < 0.2:        # near lower band
                score += 15
            elif position < 0.35:     # below middle
                score += 5
            elif position > 0.8:      # near upper band
                score -= 15
            elif position > 0.65:     # above middle
                score -= 5
            # middle zone = neutral

    score = max(0, min(100, score))

    # ── Signal requires BOTH score threshold AND RSI confirmation ──
    if score >= 65 and rsi is not None and rsi < 55:
        signal = "BUY"
    elif score <= 35 and rsi is not None and rsi > 55:
        signal = "SELL"
    else:
        signal = "HOLD"
    # if score >= 70 and rsi is not None and rsi < 50:
        # signal = "BUY"
    # elif score <= 30 and rsi is not None and rsi > 65:
        # signal = "SELL"
    # else:
        # signal = "HOLD"

    return signal, round(score, 1)

