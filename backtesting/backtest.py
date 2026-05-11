import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.coingecko import get_market_chart
from tools.technical_indicators import (
    calculate_indicators, score_signal,
    detect_market_regime, calculate_volume_signal,
    check_timeframe_confirmation,
)
from config import CRYPTO_ASSETS


def fetch_historical_data(coingecko_id: str, days: int = 90) -> list[dict]:
    print(f"  Fetching {days} days of data for {coingecko_id}...")
    return get_market_chart(coingecko_id, days=days)


def simulate_signals(candles: list[dict]) -> list[dict]:
    signals  = []
    lookback = 30

    for i in range(lookback, len(candles)):
        window     = candles[:i]
        current    = candles[i]
        price      = current["c"]

        indicators = calculate_indicators(window)
        regime     = detect_market_regime(window)
        volume     = calculate_volume_signal(window)
        timeframe  = check_timeframe_confirmation(window)
        signal, strength = score_signal(
            indicators, price, regime, volume, timeframe
        )

        signals.append({
            "index":    i,
            "price":    price,
            "signal":   signal,
            "strength": strength,
            "rsi":      indicators.get("rsi"),
            "regime":   regime,
        })

    return signals


def evaluate_signals(
    candles: list[dict],
    signals: list[dict],
    hold_days: int = 3,
) -> dict:
    results = {
        "total_signals": 0,
        "buy_signals":   0,
        "sell_signals":  0,
        "correct":       0,
        "incorrect":     0,
        "accuracy":      0.0,
        "avg_gain":      0.0,
        "avg_loss":      0.0,
        "trades":        [],
    }

    gains  = []
    losses = []

    for sig in signals:
        if sig["signal"] == "HOLD":
            continue

        i           = sig["index"]
        entry_price = sig["price"]

        if i + hold_days >= len(candles):
            continue

        exit_price = candles[i + hold_days]["c"]
        pct_change = ((exit_price - entry_price) / entry_price) * 100

        if sig["signal"] == "BUY":
            correct = exit_price > entry_price
        else:
            correct = exit_price < entry_price

        results["total_signals"] += 1
        results["buy_signals"]   += 1 if sig["signal"] == "BUY"  else 0
        results["sell_signals"]  += 1 if sig["signal"] == "SELL" else 0
        results["correct"]       += 1 if correct else 0
        results["incorrect"]     += 1 if not correct else 0

        if correct:
            gains.append(abs(pct_change))
        else:
            losses.append(abs(pct_change))

        results["trades"].append({
            "signal":      sig["signal"],
            "entry_price": round(entry_price, 2),
            "exit_price":  round(exit_price, 2),
            "pct_change":  round(pct_change, 2),
            "correct":     correct,
            "rsi":         sig.get("rsi"),
            "regime":      sig.get("regime"),
            "strength":    sig.get("strength"),
        })

    if results["total_signals"] > 0:
        results["accuracy"] = round(
            results["correct"] / results["total_signals"] * 100, 1
        )
    results["avg_gain"] = round(sum(gains) / len(gains), 2) if gains else 0
    results["avg_loss"] = round(sum(losses) / len(losses), 2) if losses else 0

    return results


def walk_forward_test(
    coingecko_id: str,
    symbol: str,
    total_days: int = 180,
    window_days: int = 60,
    hold_days: int = 3,
) -> list[dict]:
    """
    Tests the strategy across multiple time windows.
    Splits total_days into overlapping windows of window_days.
    This shows if strategy works consistently or only in one period.
    """
    print(f"\n  Walk-forward test for {symbol}...")
    all_candles = fetch_historical_data(coingecko_id, days=total_days)

    if len(all_candles) < window_days:
        print(f"  Not enough data")
        return []

    window_results = []
    step           = window_days // 2

    for start in range(0, len(all_candles) - window_days, step):
        end     = start + window_days
        window  = all_candles[start:end]
        signals = simulate_signals(window)
        result  = evaluate_signals(window, signals, hold_days)

        if result["total_signals"] > 0:
            window_results.append({
                "window":   f"Days {start}-{end}",
                "signals":  result["total_signals"],
                "accuracy": result["accuracy"],
                "avg_gain": result["avg_gain"],
                "avg_loss": result["avg_loss"],
            })

    return window_results


def calculate_drawdown(trades: list[dict]) -> dict:
    """
    Calculates max drawdown and longest losing streak.
    """
    if not trades:
        return {
            "max_drawdown_pct": 0,
            "longest_losing_streak": 0,
            "avg_consecutive_losses": 0,
        }

    # max drawdown
    peak        = 0
    drawdown    = 0
    max_drawdown = 0
    balance     = 100.0

    for trade in trades:
        balance  += trade["pct_change"] if trade["correct"] else -trade["pct_change"]
        peak      = max(peak, balance)
        drawdown  = (peak - balance) / peak * 100 if peak > 0 else 0
        max_drawdown = max(max_drawdown, drawdown)

    # longest losing streak
    max_streak  = 0
    curr_streak = 0
    streaks     = []

    for trade in trades:
        if not trade["correct"]:
            curr_streak += 1
            max_streak   = max(max_streak, curr_streak)
        else:
            if curr_streak > 0:
                streaks.append(curr_streak)
            curr_streak = 0

    avg_streak = round(sum(streaks) / len(streaks), 1) if streaks else 0

    return {
        "max_drawdown_pct":       round(max_drawdown, 2),
        "longest_losing_streak":  max_streak,
        "avg_consecutive_losses": avg_streak,
    }


def print_report(symbol: str, results: dict, drawdown: dict) -> None:
    print(f"\n{'='*50}")
    print(f"Backtest Report — {symbol}")
    print(f"{'='*50}")
    print(f"Total signals:    {results['total_signals']}")
    print(f"BUY signals:      {results['buy_signals']}")
    print(f"SELL signals:     {results['sell_signals']}")
    print(f"Accuracy:         {results['accuracy']}%")
    print(f"Avg gain:         {results['avg_gain']}%")
    print(f"Avg loss:         {results['avg_loss']}%")
    print(f"Max drawdown:     {drawdown['max_drawdown_pct']}%")
    print(f"Longest loss run: {drawdown['longest_losing_streak']} trades")

    print(f"\nLast 5 trades:")
    for trade in results["trades"][-5:]:
        icon   = "✅" if trade["correct"] else "❌"
        regime = trade.get("regime", "?")
        print(f"  {icon} {trade['signal']:4} | "
              f"${trade['entry_price']:,.2f} → "
              f"${trade['exit_price']:,.2f} | "
              f"{trade['pct_change']:+.2f}% | "
              f"RSI: {trade['rsi']} | "
              f"Regime: {regime}")
    print(f"{'='*50}")


def run_backtest(
    symbol: str,
    coingecko_id: str,
    days: int = 90,
    hold_days: int = 3,
) -> dict:
    print(f"\nRunning backtest for {symbol}...")
    candles = fetch_historical_data(coingecko_id, days=days)

    if len(candles) < 35:
        print(f"  Not enough data — got {len(candles)} candles")
        return {}

    signals  = simulate_signals(candles)
    results  = evaluate_signals(candles, signals, hold_days)
    drawdown = calculate_drawdown(results["trades"])
    print_report(symbol, results, drawdown)
    return {**results, **drawdown}


def run_walk_forward(symbol: str, coingecko_id: str) -> None:
    windows = walk_forward_test(coingecko_id, symbol)
    if not windows:
        return
    print(f"\nWalk-forward results for {symbol}:")
    print(f"  {'Window':<15} {'Signals':<10} {'Accuracy':<10} {'Avg Gain':<10} {'Avg Loss'}")
    print(f"  {'-'*55}")
    for w in windows:
        print(f"  {w['window']:<15} {w['signals']:<10} "
              f"{w['accuracy']}%{'':<5} "
              f"{w['avg_gain']}%{'':<5} "
              f"{w['avg_loss']}%")


if __name__ == "__main__":
    print("Running V2 backtests...\n")
    all_results = {}

    for asset in CRYPTO_ASSETS:
        result = run_backtest(
            symbol=asset["symbol"],
            coingecko_id=asset["coingecko_id"],
            days=90,
            hold_days=3,
        )
        all_results[asset["symbol"]] = result

    print("\n\nWalk-forward analysis:")
    for asset in CRYPTO_ASSETS[:2]:
        run_walk_forward(asset["symbol"], asset["coingecko_id"])

    print("\n\nSummary:")
    print(f"{'Symbol':<8} {'Signals':<10} {'Accuracy':<12} {'Max DD':<10} {'Longest Loss Run'}")
    print("-" * 55)
    for symbol, result in all_results.items():
        if result:
            print(f"{symbol:<8} {result['total_signals']:<10} "
                  f"{result['accuracy']}%{'':<7} "
                  f"{result.get('max_drawdown_pct', 0)}%{'':<5} "
                  f"{result.get('longest_losing_streak', 0)} trades")