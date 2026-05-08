# Swing Trading Assistant

A multi-agent AI system that monitors crypto and stock markets 
and sends real-time trading signals via Telegram.

## Stack
- LangGraph — agent orchestration
- OpenAI GPT-4o-mini — sentiment + decision making
- CoinGecko — crypto market data
- Alpha Vantage — stock market data
- NewsAPI — news sentiment
- Telegram — alert delivery
- SQLite — audit logging

## Assets Monitored
Crypto: BTC, ETH, SOL, BNB  
Stocks: AAPL, NVDA, TSLA

## How It Works
Every 15 minutes the pipeline:
1. Scans all 7 assets for signal strength
2. Picks top 1-2 opportunities
3. Runs technical analysis (RSI, MACD, Bollinger Bands)
4. Scores news sentiment with GPT
5. Makes BUY/SELL/HOLD decision with confidence score
6. Sends formatted alert to Telegram if confidence > 60%

## Backtest Results (90 days)
- BTC: 60.0% accuracy
- ETH: 100.0% accuracy
- SOL: 100.0% accuracy
- BNB: 100.0% accuracy

## Usage

# Run once
python main.py --mode once

# Run on schedule every 15 minutes
python main.py --mode schedule

# Check dashboard
python dashboard/app.py

# Run backtests
python backtesting/backtest.py
