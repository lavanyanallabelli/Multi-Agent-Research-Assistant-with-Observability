import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.coingecko import get_full_asset_data as get_crypto_data
from tools.alpha_vantage import get_full_asset_data as get_stock_data
from tools.technical_indicators import calculate_indicators, score_signal
from config import CRYPTO_ASSETS, STOCK_ASSETS, TOP_N_OPPORTUNITIES
# from memory.state import PipelineState


def market_data_agent(state: dict) -> dict:
    print("\n[MarketDataAgent] Starting asset scan...")
    all_asset_data = []
    scored_assets  = []

    # ── Fetch crypto assets ───────────────────────────────
    for asset in CRYPTO_ASSETS:
        try:
            print(f"  Fetching {asset['symbol']}...")
            data = get_crypto_data(asset["symbol"], asset["coingecko_id"])
            # Skip if price is missing or zero
            if not data["price"] or data["price"] == 0:
                print(f"  {asset['symbol']}: No price data — skipping")
                state["errors"].append(f"No price data for {asset['symbol']}")
                continue
            all_asset_data.append(data)

            indicators         = calculate_indicators(data["ohlcv"])
            signal, strength   = score_signal(indicators, data["price"])
            scored_assets.append({
                "symbol":   asset["symbol"],
                "strength": strength,
                "signal":   signal,
            })
            print(f"  {asset['symbol']}: ${data['price']:,.2f} | {signal} | strength: {strength}")

        except Exception as e:
            error = f"[MarketDataAgent] Failed to fetch {asset['symbol']}: {e}"
            print(error)
            state["errors"].append(error)

    # ── Fetch stock assets ────────────────────────────────
    for asset in STOCK_ASSETS:
        try:
            print(f"  Fetching {asset['symbol']}...")
            data = get_stock_data(asset["symbol"])

            # Skip if price is missing or zero
            if not data["price"] or data["price"] == 0:
                print(f"  {asset['symbol']}: No price data — skipping")
                state["errors"].append(f"No price data for {asset['symbol']}")
                continue

            all_asset_data.append(data)
            indicators       = calculate_indicators(data["ohlcv"])
            signal, strength = score_signal(indicators, data["price"])
            scored_assets.append({
                "symbol":   asset["symbol"],
                "strength": strength,
                "signal":   signal,
            })
            print(f"  {asset['symbol']}: ${data['price']:,.2f} | {signal} | strength: {strength}")

        except Exception as e:
            error = f"[MarketDataAgent] Failed to fetch {asset['symbol']}: {e}"
            print(error)
            state["errors"].append(error)

    # ── Rank and pick top opportunities ───────────────────
    scored_assets.sort(key=lambda x: abs(x["strength"] - 50), reverse=True)
    top = [
        a["symbol"] for a in scored_assets
        if a["signal"] in ("BUY", "SELL")
    ][:TOP_N_OPPORTUNITIES]

    # fallback: if no BUY/SELL signals take strongest scores
    if not top:
        top = [a["symbol"] for a in scored_assets][:TOP_N_OPPORTUNITIES]

    print(f"\n[MarketDataAgent] Top opportunities: {top}")

    state["all_asset_data"]    = all_asset_data
    state["top_opportunities"] = top
    return dict(state)
    # return {
        # "all_asset_data":    all_asset_data,
        # "top_opportunities": top,
        # "errors":            state.get("errors", []),
    # }