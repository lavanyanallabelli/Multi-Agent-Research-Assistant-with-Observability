import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.coingecko import get_full_asset_data as get_crypto_data
from tools.alpha_vantage import get_full_asset_data as get_stock_data
from tools.technical_indicators import (
    calculate_indicators, score_signal,
    detect_market_regime, calculate_volume_signal,
    check_timeframe_confirmation,
)
from memory.watchlist import get_watchlist
from config import TOP_N_OPPORTUNITIES


def market_data_agent(state: dict) -> dict:
    print("\n[MarketDataAgent] Starting asset scan...")

    # read from watchlist instead of hardcoded config
    watchlist      = get_watchlist()
    all_asset_data = []
    scored_assets  = []

    if not watchlist:
        print("  Watchlist is empty — nothing to scan")
        state["all_asset_data"]    = []
        state["top_opportunities"] = []
        return dict(state)

    print(f"  Scanning {len(watchlist)} assets from watchlist...")

    for asset in watchlist:
        symbol     = asset["symbol"]
        asset_type = asset["asset_type"]

        try:
            print(f"  Fetching {symbol}...")

            if asset_type == "crypto":
                data = get_crypto_data(symbol, asset["coingecko_id"])
            else:
                data = get_stock_data(symbol)

            if not data["price"] or data["price"] == 0:
                print(f"  {symbol}: No price data — skipping")
                state["errors"].append(f"No price data for {symbol}")
                continue

            all_asset_data.append(data)

            indicators = calculate_indicators(data["ohlcv"])
            regime     = detect_market_regime(data["ohlcv"])
            volume     = calculate_volume_signal(data["ohlcv"])
            timeframe  = check_timeframe_confirmation(data["ohlcv"])
            signal, strength = score_signal(
                indicators, data["price"],
                regime, volume, timeframe
            )

            scored_assets.append({
                "symbol":   symbol,
                "strength": strength,
                "signal":   signal,
                "regime":   regime,
            })

            print(f"  {symbol}: ${data['price']:,.2f} | "
                  f"{signal} | strength: {strength} | "
                  f"regime: {regime}")

        except Exception as e:
            error = f"[MarketDataAgent] Failed {symbol}: {e}"
            print(error)
            state["errors"].append(error)

    # rank by signal strength — furthest from 50 = strongest signal
    scored_assets.sort(
        key=lambda x: abs(x["strength"] - 50),
        reverse=True
    )

    # pick top assets with BUY or SELL signals first
    top = [
        a["symbol"] for a in scored_assets
        if a["signal"] in ("BUY", "SELL")
    ][:TOP_N_OPPORTUNITIES]

    # fallback — if no strong signals take highest scoring
    if not top:
        top = [a["symbol"] for a in scored_assets][:TOP_N_OPPORTUNITIES]

    print(f"\n[MarketDataAgent] Top opportunities: {top}")

    state["all_asset_data"]    = all_asset_data
    state["top_opportunities"] = top
    return dict(state)