# Swing Trading Assistant

A multi-agent AI system that monitors crypto and stock markets, generates trading signals, executes paper trades via Alpaca, and sends real-time alerts via Telegram. Everything runs automatically — no manual intervention needed.

## How It Works
- **Market scanning** — every 15 minutes, all assets are scored and ranked
- **Signal generation** — top opportunities go through full technical + sentiment + LLM analysis
- **Risk filtering** — weak signals, spam, and overexposure are blocked automatically
- **Trade execution** — BUY/SELL orders placed on both simulator and Alpaca without any manual action
- **Alerts** — Telegram message sent with full signal details and execution results
- **Position monitoring** — open positions checked every run for stop loss and take profit hits
- **Circuit breaker** — trading pauses automatically if drawdown exceeds safe limits

## Stack
- LangGraph — agent orchestration
- OpenAI GPT-4o-mini — sentiment + decision making
- CoinGecko — crypto market data
- yfinance — stock market data (no API key required)
- NewsAPI — news sentiment (30-minute cache)
- Alpaca — paper trade execution (stocks only)
- Telegram — alert delivery
- PostgreSQL — audit logging + paper portfolio
- FastAPI — dashboard API
- Railway — 24/7 cloud deployment

## Agents
- **market_data** — fetches prices and OHLCV for all watchlist assets, scores and ranks them
- **technical** — runs RSI, MACD, Bollinger Bands, market regime, volume and timeframe analysis on top opportunities
- **sentiment** — fetches news headlines via NewsAPI and scores them with GPT-4o-mini
- **decision** — combines technical + sentiment data and makes final BUY/SELL/HOLD call with confidence score
- **risk** — gates the signal through 5 checks before allowing execution or alert
- **paper_trader** — executes trade on internal simulator, monitors all open positions for SL/TP hits
- **execution** — places real market order on Alpaca paper account for stock signals
- **writer** — formats HTML Telegram message with full signal + paper + Alpaca execution results
- **notification** — sends the alert to Telegram and logs it to the database

## Assets Monitored
Fully dynamic — manage your watchlist from the dashboard UI without touching code or redeploying.

Default assets:

Crypto: BTC, ETH, SOL, BNB, XRP
Stocks: AAPL, NVDA, TSLA, AMZN, MSFT, GOOGL, SOFI, RIVN, QQQ

Add, remove, or deactivate any asset via the dashboard:
- **Assets page** — add new assets to the universe (crypto needs CoinGecko ID, stocks just need the ticker symbol)
- **Watchlist page** — control which assets are actively scanned each run
- Changes take effect on the next pipeline run — no restart or redeploy needed


## Agent Pipeline
Every 15 minutes:
1. Scans all assets for signal strength
2. Picks top 1-2 opportunities
3. Runs technical analysis (RSI, MACD, Bollinger Bands, regime, volume, timeframe)
4. Scores news sentiment with GPT (cached 30 min)
5. Makes BUY/SELL/HOLD decision with confidence score
6. Risk checks (confidence, cooldown, daily limit, correlation filter)
7. Paper trader executes on internal simulator (crypto + stocks)
8. Execution agent places real order on Alpaca paper account (stocks only)
9. Writer formats full alert with signal + execution results
10. Sends formatted alert to Telegram if risk passes

## Risk Controls
- Minimum confidence threshold before alert
- Per-symbol cooldown period
- Daily alert cap
- Correlated asset overexposure filter
- Circuit breaker (15% drawdown, 3 consecutive losses, 10% weekly loss)

## Paper Trading
- Internal simulator: $10,000 virtual capital with stop loss + take profit monitoring
- Alpaca paper account: real market fills, stocks only
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
uvicorn dashboard.server:app --reload --port 8000

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
DATABASE_URL=postgresql://...

## Deployment
Hosted on Railway with PostgreSQL database and two services:
- worker: 24/7 scheduled pipeline
- web: FastAPI dashboard

Auto-deploys on push to main branch.
