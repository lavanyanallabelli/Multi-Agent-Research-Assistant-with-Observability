import sys
import os
import json
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.coingecko import get_market_chart
from tools.technical_indicators import calculate_indicators, score_signal
from config import CRYPTO_ASSETS


def fetch_historical_data(coingecko_id: str, days: int = 90) -> list[dict]:
    """Fetch historical OHLCV candles for backtesting."""
    print(f"  Fetching {days} days of historical data for {coingecko_id}...")
    return get_market_chart(coingecko_id, days=days)


def simulate_signals(candles: list[dict]) -> list[dict]:
    """
    Walk through historical candles day by day.
    At each point, calculate indicators on past data only
    and generate a signal — just like the live system would.
    """
    signals  = []
    lookback = 30  # minimum candles needed

    for i in range(lookback, len(candles)):
        # only use candles up to this point — no future data
        window     = candles[:i]
        current    = candles[i]
        price      = current["c"]

        indicators = calculate_indicators(window)
        signal, strength = score_signal(indicators, price)

        signals.append({
            "index":     i,
            "price":     price,
            "signal":    signal,
            "strength":  strength,
            "rsi":       indicators.get("rsi"),
            "macd":      indicators.get("macd"),
        })

    return signals


def evaluate_signals(candles: list[dict], signals: list[dict],
                     hold_days: int = 3) -> dict:
    """
    For each BUY/SELL signal, check if the price moved
    in the predicted direction after hold_days.
    """
    results = {
        "total_signals":   0,
        "buy_signals":     0,
        "sell_signals":    0,
        "correct":         0,
        "incorrect":       0,
        "accuracy":        0.0,
        "trades":          [],
    }

    for sig in signals:
        if sig["signal"] == "HOLD":
            continue

        i          = sig["index"]
        entry_price = sig["price"]

        # check if we have enough future candles
        if i + hold_days >= len(candles):
            continue

        exit_price  = candles[i + hold_days]["c"]
        pct_change  = ((exit_price - entry_price) / entry_price) * 100

        # was the signal correct?
        if sig["signal"] == "BUY":
            correct = exit_price > entry_price
        else:  # SELL
            correct = exit_price < entry_price

        results["total_signals"] += 1
        results["buy_signals"]   += 1 if sig["signal"] == "BUY"  else 0
        results["sell_signals"]  += 1 if sig["signal"] == "SELL" else 0
        results["correct"]       += 1 if correct else 0
        results["incorrect"]     += 1 if not correct else 0

        results["trades"].append({
            "signal":       sig["signal"],
            "entry_price":  round(entry_price, 2),
            "exit_price":   round(exit_price, 2),
            "pct_change":   round(pct_change, 2),
            "correct":      correct,
            "rsi":          sig.get("rsi"),
            "strength":     sig.get("strength"),
        })

    if results["total_signals"] > 0:
        results["accuracy"] = round(
            results["correct"] / results["total_signals"] * 100, 1
        )

    return results


def print_report(symbol: str, results: dict) -> None:
    print(f"\n{'='*50}")
    print(f"Backtest Report — {symbol}")
    print(f"{'='*50}")
    print(f"Total signals:  {results['total_signals']}")
    print(f"BUY signals:    {results['buy_signals']}")
    print(f"SELL signals:   {results['sell_signals']}")
    print(f"Correct:        {results['correct']}")
    print(f"Incorrect:      {results['incorrect']}")
    print(f"Accuracy:       {results['accuracy']}%")

    print(f"\nLast 5 trades:")
    for trade in results["trades"][-5:]:
        icon = "✅" if trade["correct"] else "❌"
        print(f"  {icon} {trade['signal']:4} | "
              f"Entry: ${trade['entry_price']:,.2f} | "
              f"Exit: ${trade['exit_price']:,.2f} | "
              f"Change: {trade['pct_change']:+.2f}% | "
              f"RSI: {trade['rsi']}")
    print(f"{'='*50}\n")


def run_backtest(symbol: str, coingecko_id: str,
                 days: int = 90, hold_days: int = 3) -> dict:
    print(f"\nRunning backtest for {symbol}...")
    candles = fetch_historical_data(coingecko_id, days=days)

    if len(candles) < 35:
        print(f"  Not enough data — got {len(candles)} candles")
        return {}

    signals = simulate_signals(candles)
    results = evaluate_signals(candles, signals, hold_days=hold_days)
    print_report(symbol, results)
    return results


if __name__ == "__main__":
    print("Running backtests on all crypto assets...\n")
    all_results = {}

    for asset in CRYPTO_ASSETS:
        result = run_backtest(
            symbol=asset["symbol"],
            coingecko_id=asset["coingecko_id"],
            days=90,
            hold_days=3,
        )
        all_results[asset["symbol"]] = result

    print("\nSummary:")
    print(f"{'Symbol':<8} {'Signals':<10} {'Accuracy':<10}")
    print("-" * 30)
    for symbol, result in all_results.items():
        if result:
            print(f"{symbol:<8} {result['total_signals']:<10} "
                  f"{result['accuracy']}%")