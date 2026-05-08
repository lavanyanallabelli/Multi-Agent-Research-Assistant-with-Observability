import json
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Session
from config import DATABASE_URL


class Base(DeclarativeBase):
    pass


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


engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(engine)


def log_run(state: dict) -> None:
    decision     = state.get("decision") or {}
    token_usage  = state.get("token_usage", {})
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
    print(f"  [AuditLog] Run {state['run_id'][:8]} saved to database")


def log_alert(symbol: str, action: str, confidence: int, message: str) -> None:
    with Session(engine) as session:
        alert = AlertLog(
            symbol=symbol,
            action=action,
            confidence=confidence,
            message=message,
        )
        session.add(alert)
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