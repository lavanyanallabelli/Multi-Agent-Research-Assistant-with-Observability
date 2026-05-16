import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi import HTTPException
from pydantic import BaseModel
from memory.audit_log import (
    get_recent_runs, get_recent_alerts,
    get_portfolio, initialize_db,
    get_recent_broker_snapshots, log_broker_snapshot,
    Session, engine, AssetUniverse,
)
from trading.portfolio import (
    close_position, get_open_positions, get_recent_trades
)
from memory.watchlist import (
    get_watchlist, get_all_assets,
    add_to_watchlist, remove_from_watchlist,
    add_new_asset, update_asset, deactivate_asset,
)

from trading.alpaca import get_account, get_all_positions

from backtesting.backtest import run_backtest as _run_backtest
from tools.alpha_vantage import get_ohlcv as get_stock_ohlcv
from backtesting.backtest import simulate_signals, evaluate_signals, calculate_drawdown
import threading

from fastapi.responses import StreamingResponse
import time

from memory.audit_log import (
    get_system_settings, update_system_settings,
    get_trading_state, update_trading_state
)
from agents.orchestrator import run_pipeline


app = FastAPI(title="Swing Trading Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_db()


@app.get("/")
def serve_dashboard():
    return FileResponse(
        os.path.join(os.path.dirname(__file__), "index.html")
    )


@app.get("/api/summary")
def get_summary():
    runs   = get_recent_runs(100)
    alerts = get_recent_alerts(100)
    portfolio = get_portfolio()
    total_cost   = sum(r["total_cost_usd"] for r in runs)
    total_tokens = sum(r["total_tokens"] for r in runs)
    avg_conf     = (
        sum(a["confidence"] for a in alerts) / len(alerts)
        if alerts else 0
    )
    return {
        "total_runs":       len(runs),
        "total_alerts":     len(alerts),
        "buy_alerts":       len([a for a in alerts if a["action"] == "BUY"]),
        "sell_alerts":      len([a for a in alerts if a["action"] == "SELL"]),
        "avg_confidence":   round(avg_conf, 1),
        "total_cost":       round(total_cost, 4),
        "total_tokens":     total_tokens,
        "avg_cost_per_run": round(total_cost / len(runs), 6) if runs else 0,
        "portfolio":        portfolio,
    }


@app.get("/api/portfolio")
def api_portfolio():
    return {"source": "simulator", **get_portfolio()}


def _mark_price_usd(symbol: str, meta: dict) -> float | None:
    """Best-effort live mark from CoinGecko (crypto) or yfinance (stock)."""
    try:
        at = (meta or {}).get("asset_type") or ""
        if at == "crypto" and (meta or {}).get("coingecko_id"):
            from tools.coingecko import get_price

            p = float(get_price(meta["coingecko_id"]).get("price_usd") or 0)
            return p if p > 0 else None
        if at == "stock":
            from tools.alpha_vantage import get_quote

            p = float(get_quote(symbol).get("price_usd") or 0)
            return p if p > 0 else None
    except Exception:
        return None
    return None


def _unrealized_for_position(position: dict, mark: float | None) -> tuple[float | None, float | None]:
    """Returns (unrealized_usd, unrealized_pct_on_entry) for LONG/SHORT."""
    if mark is None or mark <= 0:
        return None, None
    entry = float(position.get("entry_price") or 0)
    qty = float(position.get("quantity") or 0)
    if entry <= 0 or qty <= 0:
        return None, None
    direction = (position.get("direction") or "LONG").upper()
    if direction == "LONG":
        usd = (mark - entry) * qty
        pct = ((mark - entry) / entry) * 100.0
    else:
        usd = (entry - mark) * qty
        pct = ((entry - mark) / entry) * 100.0
    return round(usd, 2), round(pct, 2)


@app.get("/api/positions")
def api_positions():
    assets = get_all_assets()
    by_symbol = {a["symbol"].upper(): a for a in assets}
    rows = []
    for position in get_open_positions():
        sym = str(position.get("symbol", "")).upper()
        meta = by_symbol.get(sym, {})
        mark = _mark_price_usd(sym, meta)
        upl, upl_pct = _unrealized_for_position(position, mark)
        rows.append(
            {
                "source": "simulator",
                **position,
                "mark_price": round(mark, 4) if mark is not None else None,
                "unrealized_pl": upl,
                "unrealized_pl_pct": upl_pct,
            }
        )
    return rows


@app.get("/api/trades")
def api_trades(limit: int = 20):
    return [
        {"source": "simulator", **trade}
        for trade in get_recent_trades(limit)
    ]


@app.get("/api/alpaca/account")
def api_alpaca_account():
    account = get_account()
    return {"source": "broker", "broker": "alpaca", **account}


@app.get("/api/alpaca/positions")
def api_alpaca_positions():
    positions = get_all_positions()
    return {"source": "broker", "broker": "alpaca", **positions}


class CloseAlpacaPositionRequest(BaseModel):
    symbol: str

@app.post("/api/alpaca/positions/close")
def api_alpaca_close_position(req: CloseAlpacaPositionRequest):
    from trading.alpaca import close_position as alpaca_close_position
    result = alpaca_close_position(req.symbol)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.get("/api/alpaca/snapshots")
def api_alpaca_snapshots(limit: int = 10):
    return get_recent_broker_snapshots("alpaca", limit)


@app.post("/api/alpaca/snapshot")
def api_alpaca_snapshot():
    account = get_account()
    positions = get_all_positions()
    log_broker_snapshot("alpaca", account, positions)
    return {
        "source": "broker",
        "broker": "alpaca",
        "account": account,
        "positions": positions,
    }


@app.get("/api/runs")
def api_runs(limit: int = 20):
    return get_recent_runs(limit)


@app.get("/api/alerts")
def api_alerts(limit: int = 20):
    return get_recent_alerts(limit)


@app.get("/api/watchlist")
def api_watchlist():
    return get_watchlist()


@app.get("/api/assets")
def api_assets():
    return get_all_assets()


class WatchlistRequest(BaseModel):
    symbol: str


class NewAssetRequest(BaseModel):
    symbol: str
    name: str
    asset_type: str
    coingecko_id: Optional[str] = None


class UpdateAssetRequest(BaseModel):
    symbol: str
    name: str
    asset_type: str
    coingecko_id: str = None


class DeleteAssetRequest(BaseModel):
    symbol: str


class CloseSimulatorPositionRequest(BaseModel):
    position_id: int
    exit_price: float
    exit_reason: str = "MANUAL"


@app.post("/api/simulator/positions/close")
def api_close_simulator_position(req: CloseSimulatorPositionRequest):
    if req.exit_price <= 0:
        raise HTTPException(status_code=400, detail="Exit price must be greater than zero")
    try:
        trade = close_position(
            position_id=req.position_id,
            exit_price=req.exit_price,
            exit_reason=req.exit_reason or "MANUAL",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"source": "simulator", "trade": trade, "portfolio": get_portfolio()}


@app.post("/api/watchlist/add")
def api_add_watchlist(req: WatchlistRequest):
    result = add_to_watchlist(req.symbol)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["reason"])
    return result


@app.post("/api/watchlist/remove")
def api_remove_watchlist(req: WatchlistRequest):
    result = remove_from_watchlist(req.symbol)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["reason"])
    return result


@app.post("/api/assets/add")
def api_add_asset(req: NewAssetRequest):
    result = add_new_asset(
        req.symbol, req.name,
        req.asset_type, req.coingecko_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["reason"])
    return result


@app.post("/api/assets/update")
def api_update_asset(req: UpdateAssetRequest):
    result = update_asset(
        req.symbol, req.name,
        req.asset_type, req.coingecko_id,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["reason"])
    return result


@app.post("/api/assets/delete")
def api_delete_asset(req: DeleteAssetRequest):
    result = deactivate_asset(req.symbol)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["reason"])
    return result


# store backtest results in memory
_backtest_results = {}
_backtest_running = {}


@app.get("/api/backtest/{symbol}")
def api_backtest_get(symbol: str, days: int = 90, hold_days: int = 3):
    """Returns running state, cached results, or not_run."""
    sym = symbol.upper()
    key = f"{sym}_{days}_{hold_days}"
    if _backtest_running.get(key):
        return {"status": "running", "symbol": sym}
    if key in _backtest_results:
        return _backtest_results[key]
    return {"status": "not_run", "symbol": sym}


@app.post("/api/backtest/{symbol}")
def api_run_backtest(symbol: str, days: int = 90, hold_days: int = 3):
    """Triggers a backtest run for a symbol (async thread)."""
    sym = symbol.upper()
    key = f"{sym}_{days}_{hold_days}"

    if _backtest_running.get(key):
        return {"status": "running", "symbol": sym}

    def run():
        try:
            with Session(engine) as session:
                asset = session.query(AssetUniverse).filter(
                    AssetUniverse.symbol == sym,
                    AssetUniverse.is_active == True,
                ).first()

            if not asset:
                _backtest_results[key] = {
                    "status": "error",
                    "reason": f"{sym} not in universe or inactive",
                }
                return

            if asset.asset_type == "crypto":
                cg = (asset.coingecko_id or "").strip()
                if not cg:
                    _backtest_results[key] = {
                        "status": "error",
                        "reason": f"{sym} has no CoinGecko ID (required for crypto backtest)",
                    }
                    return
                result = _run_backtest(sym, cg, days, hold_days)
                if not result:
                    _backtest_results[key] = {
                        "status": "error",
                        "reason": "Not enough historical data for this symbol",
                    }
                    return
            else:
                candles = get_stock_ohlcv(sym)
                if len(candles) < 35:
                    _backtest_results[key] = {
                        "status": "error",
                        "reason": "Not enough daily bars for stock backtest (need at least ~35)",
                    }
                    return
                signals = simulate_signals(candles)
                result = evaluate_signals(candles, signals, hold_days)
                dd = calculate_drawdown(result["trades"])
                result = {**result, **dd}

            _backtest_results[key] = {
                "status":          "done",
                "symbol":          sym,
                "days":            days,
                "hold_days":       hold_days,
                "total_signals":   result.get("total_signals", 0),
                "buy_signals":    result.get("buy_signals", 0),
                "sell_signals":   result.get("sell_signals", 0),
                "accuracy":       result.get("accuracy", 0),
                "avg_gain":       result.get("avg_gain", 0),
                "avg_loss":       result.get("avg_loss", 0),
                "max_drawdown":    result.get("max_drawdown_pct", 0),
                "max_drawdown_pct": result.get("max_drawdown_pct", 0),
                "longest_streak": result.get("longest_losing_streak", 0),
                "trades":         result.get("trades", [])[-10:],
            }
        except Exception as e:
            _backtest_results[key] = {
                "status": "error",
                "reason": str(e),
            }
        finally:
            _backtest_running[key] = False

    _backtest_running[key] = True
    _backtest_results.pop(key, None)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return {"status": "running", "symbol": sym}



@app.get("/api/settings")
def api_get_settings():
    return get_system_settings()

@app.post("/api/settings")
def api_update_settings(data: dict):
    update_system_settings(data)
    return {"status": "success"}

@app.get("/api/trading/state")
def api_get_trading_state():
    return get_trading_state()

@app.post("/api/trading/state")
def api_update_trading_state(data: dict):
    is_paused = data.get("is_paused", False)
    update_trading_state(is_paused)
    return {"status": "success", "is_paused": is_paused}

@app.post("/api/trading/trigger")
def api_trigger_pipeline():
    def run():
        try:
            run_pipeline()
        except Exception as e:
            print(f"Manual pipeline run failed: {e}")
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return {"status": "started"}

@app.get("/api/logs/stream")
def stream_logs():
    def log_generator():
        log_file = "trading.log"
        try:
            with open(log_file, "r") as f:
                # Read initial lines
                f.seek(0, 2) # go to end
                file_size = f.tell()
                # go back 10KB to send some context
                f.seek(max(0, file_size - 10000))
                # read to end
                lines = f.readlines()
                for line in lines:
                    yield f"data: {line}\n\n"
                
                # tail the file
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.5)
                        continue
                    yield f"data: {line}\n\n"
        except FileNotFoundError:
            yield f"data: Log file not found.\n\n"
            
    return StreamingResponse(log_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
