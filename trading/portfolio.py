import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from memory.audit_log import (
    engine, Portfolio, Position, Trade
)
from config import PAPER_TRADING_BALANCE


def get_portfolio() -> dict:
    """Returns current portfolio snapshot."""
    from memory.audit_log import get_portfolio as _get
    return _get()


def get_open_positions() -> list[dict]:
    """Returns all currently open positions."""
    with Session(engine) as session:
        positions = session.query(Position)\
            .filter(Position.status == "OPEN").all()
        return [
            {
                "id":             p.id,
                "symbol":         p.symbol,
                "direction":      p.direction,
                "entry_price":    p.entry_price,
                "quantity":       p.quantity,
                "position_value": p.position_value,
                "stop_loss":      p.stop_loss,
                "take_profit":    p.take_profit,
                "opened_at":      str(p.opened_at),
                "signal_id":      p.signal_id,
            }
            for p in positions
        ]


def get_open_position_for(symbol: str) -> dict | None:
    """Returns open position for a specific symbol if exists."""
    with Session(engine) as session:
        p = session.query(Position).filter(
            Position.symbol == symbol,
            Position.status == "OPEN"
        ).first()
        if not p:
            return None
        return {
            "id":             p.id,
            "symbol":         p.symbol,
            "direction":      p.direction,
            "entry_price":    p.entry_price,
            "quantity":       p.quantity,
            "position_value": p.position_value,
            "stop_loss":      p.stop_loss,
            "take_profit":    p.take_profit,
            "opened_at":      str(p.opened_at),
        }


def count_open_positions() -> int:
    """Returns number of currently open positions."""
    with Session(engine) as session:
        return session.query(Position)\
            .filter(Position.status == "OPEN").count()


def open_position(
    symbol: str,
    direction: str,
    entry_price: float,
    quantity: float,
    stop_loss: float,
    take_profit: float,
    signal_id: int | None = None,
) -> int:
    """
    Opens a new position and deducts cost from cash balance.
    Returns the new position id.
    """
    position_value = entry_price * quantity
    with Session(engine) as session:
        position = Position(
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            quantity=quantity,
            position_value=position_value,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status="OPEN",
            signal_id=signal_id,
        )
        session.add(position)

        portfolio = session.query(Portfolio)\
            .order_by(Portfolio.updated_at.desc()).first()
        portfolio.cash_balance  -= position_value
        portfolio.open_positions += 1
        portfolio.updated_at     = datetime.utcnow()
        session.commit()

        print(f"  [Portfolio] Opened {direction} {symbol} "
              f"x{quantity:.6f} @ ${entry_price:,.2f} "
              f"| Value: ${position_value:,.2f}")
        return position.id


def close_position(
    position_id: int,
    exit_price: float,
    exit_reason: str,
) -> dict:
    """
    Closes an open position.
    Calculates P&L, updates portfolio, logs to trades table.
    Returns trade summary dict.
    """
    with Session(engine) as session:
        position = session.query(Position).filter(
            Position.id == position_id
        ).first()

        if not position:
            raise ValueError(f"Position {position_id} not found")

        entry_price    = position.entry_price
        quantity       = position.quantity
        position_value = position.position_value

        if position.direction == "LONG":
            pnl     = (exit_price - entry_price) * quantity
        else:
            pnl     = (entry_price - exit_price) * quantity

        pnl_pct        = (pnl / position_value) * 100
        exit_value     = position_value + pnl

        position.status     = exit_reason
        position.closed_at  = datetime.utcnow()

        trade = Trade(
            position_id  = position_id,
            symbol       = position.symbol,
            opened_at    = position.opened_at,
            direction    = position.direction,
            entry_price  = entry_price,
            exit_price   = exit_price,
            quantity     = quantity,
            pnl          = round(pnl, 2),
            pnl_pct      = round(pnl_pct, 2),
            exit_reason  = exit_reason,
            fees         = 0.0,
        )
        session.add(trade)

        portfolio = session.query(Portfolio)\
            .order_by(Portfolio.updated_at.desc()).first()
        portfolio.cash_balance   += exit_value
        portfolio.open_positions -= 1
        portfolio.total_trades   += 1
        portfolio.total_pnl      += pnl

        if pnl >= 0:
            portfolio.winning_trades += 1
        else:
            portfolio.losing_trades  += 1

        starting_balance     = PAPER_TRADING_BALANCE
        portfolio.total_pnl_pct = (
            (portfolio.total_pnl / starting_balance) * 100
        )
        portfolio.total_value = (
            portfolio.cash_balance +
            sum_open_positions_value(session)
        )
        portfolio.updated_at = datetime.utcnow()
        session.commit()

        result = {
            "symbol":      position.symbol,
            "direction":   position.direction,
            "entry_price": entry_price,
            "exit_price":  exit_price,
            "quantity":    quantity,
            "pnl":         round(pnl, 2),
            "pnl_pct":     round(pnl_pct, 2),
            "exit_reason": exit_reason,
        }

        icon = "✅" if pnl >= 0 else "❌"
        print(f"  [Portfolio] {icon} Closed {position.symbol} "
              f"@ ${exit_price:,.2f} | "
              f"P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%) | "
              f"Reason: {exit_reason}")
        return result


def sum_open_positions_value(session) -> float:
    """Helper — sum of all open position values."""
    positions = session.query(Position)\
        .filter(Position.status == "OPEN").all()
    return sum(p.position_value for p in positions)


def get_recent_trades(limit: int = 20) -> list[dict]:
    """Returns recent completed trades."""
    with Session(engine) as session:
        trades = session.query(Trade)\
            .order_by(Trade.closed_at.desc())\
            .limit(limit).all()
        return [
            {
                "id":          t.id,
                "symbol":      t.symbol,
                "direction":   t.direction,
                "entry_price": t.entry_price,
                "exit_price":  t.exit_price,
                "quantity":    t.quantity,
                "pnl":         t.pnl,
                "pnl_pct":     t.pnl_pct,
                "exit_reason": t.exit_reason,
                "opened_at":   str(t.opened_at),
                "closed_at":   str(t.closed_at),
            }
            for t in trades
        ]