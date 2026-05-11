# Swing Trading Assistant

A multi-agent AI system that monitors crypto and stock markets,
generates trading signals, executes paper trades via Alpaca,
and sends real-time alerts via Telegram.

## Stack
- LangGraph — agent orchestration
- OpenAI GPT-4o-mini — sentiment + decision making
- CoinGecko — crypto market data
- yfinance — stock market data (no API key required)
- NewsAPI — news sentiment (30-minute cache)
- Alpaca — paper trade execution (stocks)
- Telegram — alert delivery
- SQLite — audit logging + paper portfolio
- FastAPI — dashboard API
- Railway — 24/7 cloud deployment

## Assets Monitored
Crypto: BTC, ETH, SOL, BNB
Stocks: AAPL, NVDA, TSLA

## Agent Pipeline
Every 15 minutes:
1. Scans all assets for signal strength
2. Picks top 1-2 opportunities
3. Runs technical analysis (RSI, MACD, Bollinger Bands, regime, volume, timeframe)
4. Scores news sentiment with GPT (cached 30 min)
5. Makes BUY/SELL/HOLD decision with confidence score
6. Risk checks (confidence, cooldown, daily limit, correlation filter)
7. Executes paper trade on Alpaca (stocks only)
8. Sends formatted alert to Telegram if risk passes

## Risk Controls
- Minimum confidence threshold before alert
- Per-symbol cooldown period
- Daily alert cap
- Correlated asset overexposure filter
- Circuit breaker on drawdown

## Paper Trading
- Internal paper portfolio: $10,000 virtual capital with stop loss + take profit
- Alpaca paper account: real market fills on paper account
- Both tracked separately on the dashboard

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

# Web dashboard
python dashboard/server.py

# Run backtests
python backtesting/backtest.py

# Test Alpaca connection
python scripts/test_alpaca.py

## Environment Variables
OPENAI_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
NEWSAPI_KEY=
COINGECKO_API_KEY=
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=https://paper-api.alpaca.markets
DATABASE_URL=sqlite:///trading.db

## Deployment
Hosted on Railway with persistent volume for SQLite.
Auto-deploys on push to main branch.