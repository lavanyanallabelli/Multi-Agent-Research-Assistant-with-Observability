import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.coingecko import get_full_asset_data
from tools.technical_indicators import (
    detect_market_regime,
    calculate_indicators,
    calculate_volume_signal,
    check_timeframe_confirmation,
    score_signal,
)

data       = get_full_asset_data('BTC', 'bitcoin')
regime     = detect_market_regime(data['ohlcv'])
indicators = calculate_indicators(data['ohlcv'])
volume     = calculate_volume_signal(data['ohlcv'])
timeframe  = check_timeframe_confirmation(data['ohlcv'])
signal, strength = score_signal(
    indicators, data['price'], regime, volume, timeframe
)

print(f"Regime:    {regime}")
print(f"Trend:     {timeframe['trend']}")
print(f"Momentum:  {timeframe['momentum']}")
print(f"Confirmed: {timeframe['confirmed']}")
print(f"TF Adjust: {timeframe['score_adjust']}")
print(f"Signal:    {signal}")
print(f"Strength:  {strength}")