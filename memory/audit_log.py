import json
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import (
    create_engine, Column, String, Float,
    Integer, Boolean, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, Session
from config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class AssetUniverse(Base):
    __tablename__ = "assets_universe"
    symbol        = Column(String, primary_key=True)
    name          = Column(String)
    asset_type    = Column(String)   # "crypto" or "stock"
    coingecko_id  = Column(String, nullable=True)
    added_at      = Column(DateTime, default=datetime.utcnow)
    is_active     = Column(Boolean, default=True)


class Watchlist(Base):
    __tablename__ = "watchlist"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    symbol     = Column(String, ForeignKey("assets_universe.symbol"))
    added_at   = Column(DateTime, default=datetime.utcnow)
    is_active  = Column(Boolean, default=True)
    notes      = Column(Text, nullable=True)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id              = Column(String,  primary_key=True)
    triggered_at    = Column(DateTime, default=datetime.utcnow)
    top_assets      = Column(String)
    decision_symbol = Column(String,  nullable=True)
    decision_action = Column(String,  nullable=True)
    confidence      = Column(Integer, nullable=True)
    alert_sent      = Column(Boolean, default=False)
    total_tokens    = Column(Integer, default=0)
    total_cost_usd  = Column(Float,   default=0.0)
    errors          = Column(Text,    default="[]")


class AlertLog(Base):
    __tablename__ = "alert_log"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    sent_at    = Column(DateTime, default=datetime.utcnow)
    symbol     = Column(String)
    action     = Column(String)
    confidence = Column(Integer)
    message    = Column(Text)


class Signal(Base):
    __tablename__ = "signals"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    symbol     = Column(String, ForeignKey("assets_universe.symbol"))
    action     = Column(String)
    confidence = Column(Integer)
    rsi        = Column(Float, nullable=True)
    macd       = Column(Float, nullable=True)
    sentiment  = Column(String, nullable=True)
    entry_zone = Column(String, nullable=True)
    target     = Column(String, nullable=True)
    stop_loss  = Column(String, nullable=True)
    reasoning  = Column(Text,   nullable=True)
    run_id     = Column(String, ForeignKey("pipeline_runs.id"), nullable=True)


class Portfolio(Base):
    __tablename__    = "portfolio"
    id               = Column(Integer, primary_key=True, autoincrement=True)
    updated_at       = Column(DateTime, default=datetime.utcnow)
    cash_balance     = Column(Float, default=10000.0)
    total_value      = Column(Float, default=10000.0)
    total_pnl        = Column(Float, default=0.0)
    total_pnl_pct    = Column(Float, default=0.0)
    open_positions   = Column(Integer, default=0)
    total_trades     = Column(Integer, default=0)
    winning_trades   = Column(Integer, default=0)
    losing_trades    = Column(Integer, default=0)


class Position(Base):
    __tablename__   = "positions"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    symbol          = Column(String, ForeignKey("assets_universe.symbol"))
    opened_at       = Column(DateTime, default=datetime.utcnow)
    closed_at       = Column(DateTime, nullable=True)
    direction       = Column(String)    # "LONG" or "SHORT"
    entry_price     = Column(Float)
    quantity        = Column(Float)
    position_value  = Column(Float)
    stop_loss       = Column(Float)
    take_profit     = Column(Float)
    status          = Column(String, default="OPEN")  # OPEN, CLOSED, STOPPED
    signal_id       = Column(Integer, ForeignKey("signals.id"), nullable=True)


class Trade(Base):
    __tablename__  = "trades"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    position_id    = Column(Integer, ForeignKey("positions.id"))
    symbol         = Column(String, ForeignKey("assets_universe.symbol"))
    opened_at      = Column(DateTime)
    closed_at      = Column(DateTime, default=datetime.utcnow)
    direction      = Column(String)
    entry_price    = Column(Float)
    exit_price     = Column(Float)
    quantity       = Column(Float)
    pnl            = Column(Float)
    pnl_pct        = Column(Float)
    exit_reason    = Column(String)   # "TAKE_PROFIT", "STOP_LOSS", "MANUAL"
    fees           = Column(Float, default=0.0)


engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(engine)


# ── Seed functions ─────────────────────────────────────────────────────────────

def seed_assets_universe():
    """Populate assets_universe with default assets on first run."""
    from config import CRYPTO_ASSETS, STOCK_ASSETS
    with Session(engine) as session:
        existing = session.query(AssetUniverse).count()
        if existing > 0:
            return
        for asset in CRYPTO_ASSETS:
            session.add(AssetUniverse(
                symbol=asset["symbol"],
                name=asset["symbol"],
                asset_type="crypto",
                coingecko_id=asset["coingecko_id"],
            ))
        for asset in STOCK_ASSETS:
            session.add(AssetUniverse(
                symbol=asset["symbol"],
                name=asset["symbol"],
                asset_type="stock",
                coingecko_id=None,
            ))
        session.commit()
        print(f"[DB] Seeded {len(CRYPTO_ASSETS) + len(STOCK_ASSETS)} assets")


def seed_watchlist():
    """Add all assets to watchlist on first run."""
    with Session(engine) as session:
        existing = session.query(Watchlist).count()
        if existing > 0:
            return
        assets = session.query(AssetUniverse).all()
        for asset in assets:
            session.add(Watchlist(symbol=asset.symbol, is_active=True))
        session.commit()
        print(f"[DB] Added {len(assets)} assets to watchlist")


def seed_portfolio():
    """Create initial portfolio on first run."""
    from config import PAPER_TRADING_BALANCE
    with Session(engine) as session:
        existing = session.query(Portfolio).count()
        if existing > 0:
            return
        session.add(Portfolio(
            cash_balance=PAPER_TRADING_BALANCE,
            total_value=PAPER_TRADING_BALANCE,
        ))
        session.commit()
        print(f"[DB] Portfolio created with ${PAPER_TRADING_BALANCE:,.2f}")


def initialize_db():
    """Call once at startup — seeds all tables if empty."""
    seed_assets_universe()
    seed_watchlist()
    seed_portfolio()


# ── Query functions ────────────────────────────────────────────────────────────

def log_run(state: dict) -> None:
    decision    = state.get("decision") or {}
    token_usage = state.get("token_usage", {})
    total_tokens = sum(token_usage.values())
    total_cost   = (total_tokens / 1000) * 0.000375
    with Session(engine) as session:
        run = PipelineRun(
            id=state["run_id"],
            triggered_at=datetime.fromisoformat(state["triggered_at"]),
            top_assets=json.dumps(state.get("top_opportunities", [])),
            decision_symbol=decision.get("symbol"),
            decision_action=decision.get("action"),
            confidence=decision.get("confidence"),
            alert_sent=state.get("alert_sent", False),
            total_tokens=total_tokens,
            total_cost_usd=round(total_cost, 6),
            errors=json.dumps(state.get("errors", [])),
        )
        session.add(run)
        session.commit()
    print(f"  [DB] Run {state['run_id'][:8]} saved")


def log_signal(state: dict, run_id: str) -> int | None:
    decision = state.get("decision")
    if not decision:
        return None
    symbol   = decision.get("symbol")
    tech     = state.get("technical_signals", {}).get(symbol, {})
    sent     = state.get("sentiment_results", {}).get(symbol, {})
    with Session(engine) as session:
        signal = Signal(
            symbol=symbol,
            action=decision.get("action"),
            confidence=decision.get("confidence"),
            rsi=tech.get("rsi"),
            macd=tech.get("macd"),
            sentiment=sent.get("sentiment"),
            entry_zone=decision.get("entry_zone"),
            target=decision.get("target"),
            stop_loss=decision.get("stop_loss"),
            reasoning=decision.get("reasoning"),
            run_id=run_id,
        )
        session.add(signal)
        session.commit()
        return signal.id


def log_alert(symbol: str, action: str, confidence: int, message: str) -> None:
    with Session(engine) as session:
        session.add(AlertLog(
            symbol=symbol, action=action,
            confidence=confidence, message=message,
        ))
        session.commit()


def get_recent_runs(limit: int = 10) -> list[dict]:
    with Session(engine) as session:
        runs = session.query(PipelineRun)\
            .order_by(PipelineRun.triggered_at.desc())\
            .limit(limit).all()
        return [
            {
                "id":             r.id[:8],
                "triggered_at":   str(r.triggered_at),
                "top_assets":     json.loads(r.top_assets),
                "action":         r.decision_action,
                "symbol":         r.decision_symbol,
                "confidence":     r.confidence,
                "alert_sent":     r.alert_sent,
                "total_tokens":   r.total_tokens,
                "total_cost_usd": r.total_cost_usd,
            }
            for r in runs
        ]


def get_recent_alerts(limit: int = 10) -> list[dict]:
    with Session(engine) as session:
        alerts = session.query(AlertLog)\
            .order_by(AlertLog.sent_at.desc())\
            .limit(limit).all()
        return [
            {
                "sent_at":    str(a.sent_at),
                "symbol":     a.symbol,
                "action":     a.action,
                "confidence": a.confidence,
            }
            for a in alerts
        ]


def get_watchlist() -> list[dict]:
    with Session(engine) as session:
        items = session.query(Watchlist)\
            .filter(Watchlist.is_active == True).all()
        return [
            {"symbol": w.symbol, "added_at": str(w.added_at)}
            for w in items
        ]


def get_portfolio() -> dict:
    with Session(engine) as session:
        p = session.query(Portfolio)\
            .order_by(Portfolio.updated_at.desc()).first()
        if not p:
            return {}
        win_rate = (
            round(p.winning_trades / p.total_trades * 100, 1)
            if p.total_trades > 0 else 0
        )
        return {
            "cash_balance":   round(p.cash_balance, 2),
            "total_value":    round(p.total_value, 2),
            "total_pnl":      round(p.total_pnl, 2),
            "total_pnl_pct":  round(p.total_pnl_pct, 2),
            "open_positions": p.open_positions,
            "total_trades":   p.total_trades,
            "winning_trades": p.winning_trades,
            "losing_trades":  p.losing_trades,
            "win_rate":       win_rate,
        }


def total_alerts_today() -> int:
    from sqlalchemy import func
    today = datetime.utcnow().date()
    with Session(engine) as session:
        return session.query(AlertLog).filter(
            func.date(AlertLog.sent_at) == today
        ).count()


def last_alert_for(symbol: str) -> datetime | None:
    with Session(engine) as session:
        row = session.query(AlertLog).filter(
            AlertLog.symbol == symbol
        ).order_by(AlertLog.sent_at.desc()).first()
        return row.sent_at if row else None