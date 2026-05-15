import sys
import os

file_path = r'd:\AI_folder\multi-agent\memory\audit_log.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_init = """def initialize_db():
    \"\"\"Call once at startup — seeds all tables if empty.\"\"\"
    seed_assets_universe()
    seed_watchlist()
    seed_portfolio()"""

new_init = """def seed_settings():
    \"\"\"Create default system settings on first run.\"\"\"
    from config import PAPER_TRADING_BALANCE, PAPER_TRADING_STOP_LOSS_PCT, PAPER_TRADING_TP_PCT, PAPER_TRADING_MAX_POSITIONS, MIN_CONFIDENCE_SCORE, SCAN_INTERVAL_MINUTES, ALPACA_TRADE_SIZE
    with Session(engine) as session:
        existing = session.query(SystemSettings).count()
        if existing > 0:
            return
        session.add(SystemSettings(
            id=1,
            portfolio_balance=PAPER_TRADING_BALANCE,
            stop_loss_pct=PAPER_TRADING_STOP_LOSS_PCT,
            take_profit_pct=PAPER_TRADING_TP_PCT,
            max_positions=PAPER_TRADING_MAX_POSITIONS,
            confidence_threshold=MIN_CONFIDENCE_SCORE,
            scan_interval_minutes=SCAN_INTERVAL_MINUTES,
            alpaca_trade_size=ALPACA_TRADE_SIZE
        ))
        session.commit()
        print('[DB] Default system settings created')

def seed_trading_state():
    \"\"\"Create default trading state on first run.\"\"\"
    with Session(engine) as session:
        existing = session.query(TradingState).count()
        if existing > 0:
            return
        session.add(TradingState(id=1, is_paused=False))
        session.commit()
        print('[DB] Default trading state created')

def initialize_db():
    \"\"\"Call once at startup — seeds all tables if empty.\"\"\"
    seed_assets_universe()
    seed_watchlist()
    seed_portfolio()
    seed_settings()
    seed_trading_state()"""

if old_init in content:
    content = content.replace(old_init, new_init)
elif old_init.replace('\n', '\r\n') in content:
    content = content.replace(old_init.replace('\n', '\r\n'), new_init)

getters = """

def get_system_settings() -> dict:
    with Session(engine) as session:
        settings = session.query(SystemSettings).filter_by(id=1).first()
        if not settings:
            return {}
        return {
            "portfolio_balance": settings.portfolio_balance,
            "stop_loss_pct": settings.stop_loss_pct,
            "take_profit_pct": settings.take_profit_pct,
            "max_positions": settings.max_positions,
            "confidence_threshold": settings.confidence_threshold,
            "scan_interval_minutes": settings.scan_interval_minutes,
            "alpaca_trade_size": settings.alpaca_trade_size,
        }

def update_system_settings(data: dict) -> None:
    with Session(engine) as session:
        settings = session.query(SystemSettings).filter_by(id=1).first()
        if not settings:
            settings = SystemSettings(id=1)
            session.add(settings)
        for key, value in data.items():
            if hasattr(settings, key) and key != "id":
                setattr(settings, key, value)
        session.commit()

def get_trading_state() -> dict:
    with Session(engine) as session:
        state = session.query(TradingState).filter_by(id=1).first()
        if not state:
            return {"is_paused": False}
        return {"is_paused": state.is_paused}

def update_trading_state(is_paused: bool) -> None:
    with Session(engine) as session:
        state = session.query(TradingState).filter_by(id=1).first()
        if not state:
            state = TradingState(id=1)
            session.add(state)
        state.is_paused = is_paused
        session.commit()
"""

if 'get_system_settings' not in content:
    content += getters

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
