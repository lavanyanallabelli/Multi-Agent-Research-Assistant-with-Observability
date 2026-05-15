import os

base_dir = r"d:\AI_folder\multi-agent"

files_to_update = {
    "trading/portfolio.py": [
        ("from config import PAPER_TRADING_BALANCE", "from memory.audit_log import get_system_settings"),
        ("starting_balance     = PAPER_TRADING_BALANCE", "starting_balance     = get_system_settings().get('portfolio_balance', 2000.0)"),
    ],
    "trading/circuit_breaker.py": [
        ("from config import CIRCUIT_BREAKER_PCT, PAPER_TRADING_BALANCE", "from config import CIRCUIT_BREAKER_PCT\nfrom memory.audit_log import get_system_settings"),
        ("PAPER_TRADING_BALANCE", "get_system_settings().get('portfolio_balance', 2000.0)"),
    ],
    "trading/algorithm.py": [
        (
            "from config import (\n    PAPER_TRADING_RISK_PCT,\n    PAPER_TRADING_MAX_POSITIONS,\n    PAPER_TRADING_STOP_LOSS_PCT,\n    PAPER_TRADING_TP_PCT,\n    PAPER_TRADING_BALANCE,\n)",
            "from config import PAPER_TRADING_RISK_PCT\nfrom memory.audit_log import get_system_settings"
        ),
        ("PAPER_TRADING_BALANCE", "get_system_settings().get('portfolio_balance', 2000.0)"),
        ("PAPER_TRADING_MAX_POSITIONS", "get_system_settings().get('max_positions', 3)"),
        ("PAPER_TRADING_STOP_LOSS_PCT", "get_system_settings().get('stop_loss_pct', 3.0)"),
        ("PAPER_TRADING_TP_PCT", "get_system_settings().get('take_profit_pct', 6.0)"),
    ],
    "agents/risk.py": [
        (
            "from config import (\n    MAX_ALERTS_PER_DAY,\n    ALERT_COOLDOWN_HOURS,\n    MIN_CONFIDENCE_SCORE,\n)",
            "from config import MAX_ALERTS_PER_DAY, ALERT_COOLDOWN_HOURS\nfrom memory.audit_log import get_system_settings"
        ),
        ("MIN_CONFIDENCE_SCORE", "get_system_settings().get('confidence_threshold', 60)"),
    ],
    "agents/execution.py": [
        ("from config import LIVE_TRADING, ALPACA_TRADE_SIZE", "from config import LIVE_TRADING\nfrom memory.audit_log import get_system_settings"),
        ("ALPACA_TRADE_SIZE", "get_system_settings().get('alpaca_trade_size', 1000.0)"),
    ]
}

for rel_path, replacements in files_to_update.items():
    file_path = os.path.join(base_dir, os.path.normpath(rel_path))
    if not os.path.exists(file_path):
        continue
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
        elif old.replace('\n', '\r\n') in content:
            content = content.replace(old.replace('\n', '\r\n'), new)
            
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

# Update main.py
main_path = os.path.join(base_dir, "main.py")
with open(main_path, "r", encoding="utf-8") as f:
    main_content = f.read()

main_insert = """
from memory.audit_log import get_trading_state, get_system_settings
"""
if "get_trading_state" not in main_content:
    main_content = main_content.replace("from scripts.daily_report", main_insert + "from scripts.daily_report")

job_old = """def job():
    log.info("Pipeline triggered")"""
job_new = """def job():
    state = get_trading_state()
    if state.get("is_paused"):
        log.info("Trading is manually paused. Skipping pipeline run.")
        return
    log.info("Pipeline triggered")"""

if job_old in main_content:
    main_content = main_content.replace(job_old, job_new)
elif job_old.replace('\n', '\r\n') in main_content:
    main_content = main_content.replace(job_old.replace('\n', '\r\n'), job_new)

scheduler_old = """def run_scheduler(interval_minutes: int = 15):
    \"\"\"Run the pipeline on a schedule forever.\"\"\"
    log.info(f"Scheduler started — running every {interval_minutes} minutes")
    log.info("Press Ctrl+C to stop\\n")

    # run immediately on start
    job()

    # schedule recurring runs
    schedule.every(interval_minutes).minutes.do(job)

    # daily report every morning at 8am UTC
    schedule.every().day.at("08:00").do(
        lambda: telegram_send(generate_daily_report())
    )

    while True:
        schedule.run_pending()
        next_run = schedule.next_run()
        if next_run:
            delta   = next_run - datetime.now()
            minutes = int(delta.total_seconds() // 60)
            seconds = int(delta.total_seconds() % 60)
            print(f"\\nNext run in {minutes}m {seconds}s — waiting...", end="\\r")
        time.sleep(30)"""

scheduler_new = """def run_scheduler(interval_minutes: int = 15):
    \"\"\"Run the pipeline on a schedule forever.\"\"\"
    log.info(f"Scheduler started")
    log.info("Press Ctrl+C to stop\\n")

    # run immediately on start
    job()

    current_interval = get_system_settings().get("scan_interval_minutes", interval_minutes)
    schedule.every(current_interval).minutes.do(job)

    # daily report every morning at 8am UTC
    schedule.every().day.at("08:00").do(
        lambda: telegram_send(generate_daily_report())
    )

    while True:
        # Check if interval changed
        new_interval = get_system_settings().get("scan_interval_minutes", current_interval)
        if new_interval != current_interval:
            log.info(f"Scan interval changed from {current_interval} to {new_interval} minutes. Rescheduling.")
            schedule.clear()
            current_interval = new_interval
            schedule.every(current_interval).minutes.do(job)
            schedule.every().day.at("08:00").do(
                lambda: telegram_send(generate_daily_report())
            )

        schedule.run_pending()
        next_run = schedule.next_run()
        if next_run:
            delta   = next_run - datetime.now()
            minutes = int(delta.total_seconds() // 60)
            seconds = int(delta.total_seconds() % 60)
            print(f"\\nNext run in {minutes}m {seconds}s — waiting...", end="\\r")
        time.sleep(5)"""

if scheduler_old in main_content:
    main_content = main_content.replace(scheduler_old, scheduler_new)
elif scheduler_old.replace('\n', '\r\n') in main_content:
    main_content = main_content.replace(scheduler_old.replace('\n', '\r\n'), scheduler_new)

with open(main_path, "w", encoding="utf-8") as f:
    f.write(main_content)

print("Pipeline files updated.")
