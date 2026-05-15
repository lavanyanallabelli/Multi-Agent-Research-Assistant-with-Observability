import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from memory.watchlist import get_watchlist
from memory.audit_log import engine, AssetUniverse
from sqlalchemy.orm import Session
from backtesting.backtest import run_backtest, run_walk_forward
from tools.technical_indicators import (
    calculate_indicators, score_signal,
    detect_market_regime, calculate_volume_signal,
    check_timeframe_confirmation,
)
import argparse


def run_stock_backtest(symbol: str, days: int = 90, hold_days: int = 3) -> dict:
    """
    Backtests a stock using yfinance data.
    Same logic as crypto backtest but uses yfinance.
    """
    from tools.alpha_vantage import get_ohlcv as get_stock_ohlcv
    print(f"\nRunning stock backtest for {symbol}...")
    print(f"  Fetching {days} days of data via yfinance...")

    candles = get_stock_ohlcv(symbol)

    if len(candles) < 35:
        print(f"  Not enough data — got {len(candles)} candles")
        return {}

    # reuse same signal simulation logic
    from backtesting.backtest import simulate_signals, evaluate_signals, calculate_drawdown, print_report
    signals  = simulate_signals(candles)
    results  = evaluate_signals(candles, signals, hold_days)
    drawdown = calculate_drawdown(results["trades"])
    print_report(symbol, results, drawdown)
    return {**results, **drawdown}


def backtest_watchlist(days: int = 90, hold_days: int = 3):
    """Backtest ALL assets in watchlist — crypto and stocks."""
    watchlist = get_watchlist()

    if not watchlist:
        print("Watchlist is empty — add assets first")
        return

    crypto = [a for a in watchlist if a["asset_type"] == "crypto"]
    stocks = [a for a in watchlist if a["asset_type"] == "stock"]

    print(f"Backtesting {len(watchlist)} assets from watchlist")
    print(f"  Crypto: {len(crypto)} | Stocks: {len(stocks)}")
    print(f"  Settings: {days} days history, {hold_days} day hold\n")

    results = {}

    # backtest crypto
    for asset in crypto:
        symbol       = asset["symbol"]
        coingecko_id = asset.get("coingecko_id")
        if not coingecko_id:
            print(f"Skipping {symbol} — no coingecko_id")
            continue
        result = run_backtest(symbol, coingecko_id, days, hold_days)
        results[symbol] = result

    # backtest stocks
    for asset in stocks:
        symbol = asset["symbol"]
        result = run_stock_backtest(symbol, days, hold_days)
        results[symbol] = result

    # print final summary
    print("\n\nFinal Summary:")
    print(f"{'Symbol':<8} {'Type':<8} {'Signals':<10} {'Accuracy':<12} "
          f"{'Avg Gain':<10} {'Max DD':<10} {'Streak'}")
    print("-" * 65)

    for asset in watchlist:
        symbol = asset["symbol"]
        r      = results.get(symbol, {})
        atype  = asset["asset_type"]

        if r and r.get("total_signals", 0) > 0:
            print(f"{symbol:<8} {atype:<8} {r['total_signals']:<10} "
                  f"{r['accuracy']}%{'':<7} "
                  f"{r.get('avg_gain', 0)}%{'':<5} "
                  f"{r.get('max_drawdown_pct', 0)}%{'':<5} "
                  f"{r.get('longest_losing_streak', 0)}")
        else:
            print(f"{symbol:<8} {atype:<8} No signals generated")


def backtest_single(symbol: str, days: int = 90, hold_days: int = 3):
    """Backtest a single asset by symbol."""
    with Session(engine) as session:
        asset = session.query(AssetUniverse)\
            .filter(AssetUniverse.symbol == symbol.upper()).first()
        if not asset:
            print(f"Asset {symbol} not found in universe")
            return

    if asset.asset_type == "crypto":
        if not asset.coingecko_id:
            print(f"{symbol} has no coingecko_id")
            return
        result = run_backtest(
            symbol.upper(),
            asset.coingecko_id,
            days, hold_days
        )
        run_walk_forward(symbol.upper(), asset.coingecko_id)

    elif asset.asset_type == "stock":
        result = run_stock_backtest(symbol.upper(), days, hold_days)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backtest assets")
    parser.add_argument("--symbol",    type=str,  help="Single symbol to backtest")
    parser.add_argument("--days",      type=int,  default=90,  help="History days")
    parser.add_argument("--hold",      type=int,  default=3,   help="Hold days")
    parser.add_argument("--watchlist", action="store_true", help="Backtest entire watchlist")
    args = parser.parse_args()

    if args.symbol:
        backtest_single(args.symbol, args.days, args.hold)
    elif args.watchlist:
        backtest_watchlist(args.days, args.hold)
    else:
        print("Usage:")
        print("  Backtest entire watchlist:")
        print("    python scripts/run_backtest.py --watchlist")
        print()
        print("  Backtest single asset:")
        print("    python scripts/run_backtest.py --symbol AAPL")
        print("    python scripts/run_backtest.py --symbol ETH")
        print()
        print("  Custom settings:")
        print("    python scripts/run_backtest.py --symbol TSLA --days 180 --hold 5")