import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi import HTTPException
from pydantic import BaseModel
from memory.audit_log import (
    get_recent_runs, get_recent_alerts,
    get_portfolio, initialize_db,
)
from trading.portfolio import (
    get_open_positions, get_recent_trades
)
from memory.watchlist import (
    get_watchlist, get_all_assets,
    add_to_watchlist, remove_from_watchlist,
    add_new_asset, update_asset, deactivate_asset,
)

from trading.alpaca import get_account, get_position

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
    return get_portfolio()


@app.get("/api/positions")
def api_positions():
    return get_open_positions()


@app.get("/api/trades")
def api_trades(limit: int = 20):
    return get_recent_trades(limit)


@app.get("/api/alpaca/account")
def api_alpaca_account():
    return get_account()


@app.get("/api/alpaca/positions")
def api_alpaca_positions():
    try:
        from alpaca.trading.client import TradingClient
        from config import LIVE_TRADING
        client    = TradingClient(
            os.getenv("ALPACA_API_KEY"),
            os.getenv("ALPACA_SECRET_KEY"),
            paper=not LIVE_TRADING
        )
        positions = client.get_all_positions()
        return [
            {
                "symbol":        p.symbol,
                "qty":           float(p.qty),
                "avg_cost":      float(p.avg_entry_price),
                "market_value":  float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": round(float(p.unrealized_plpc) * 100, 2),
                "side":          p.side.value,
            }
            for p in positions
        ]
    except Exception as e:
        return {"error": str(e)}


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
    coingecko_id: str = None


class UpdateAssetRequest(BaseModel):
    symbol: str
    name: str
    asset_type: str
    coingecko_id: str = None


class DeleteAssetRequest(BaseModel):
    symbol: str


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


if __name__ == "__main__":
    import uvicorn
    

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))