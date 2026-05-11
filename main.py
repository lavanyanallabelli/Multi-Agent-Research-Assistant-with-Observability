import sys
import os
import time
import schedule
import logging
from datetime import datetime
from scripts.daily_report import generate_daily_report
from tools.telegram import send_message as telegram_send
sys.path.insert(0, os.path.dirname(__file__))

from agents.orchestrator import run_pipeline

# ── Logging setup ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("trading.log"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger(__name__)


def job():
    log.info("Pipeline triggered")
    try:
        final = run_pipeline()
        alert_sent = final.get("alert_sent", False)
        errors     = final.get("errors", [])
        log.info(f"Pipeline complete — alert_sent={alert_sent} errors={len(errors)}")
    except Exception as e:
        log.error(f"Pipeline crashed: {e}")


def run_once():
    """Run the pipeline exactly once and exit."""
    log.info("Running once...")
    job()
    log.info("Done.")


def run_scheduler(interval_minutes: int = 15):
    """Run the pipeline on a schedule forever."""
    log.info(f"Scheduler started — running every {interval_minutes} minutes")
    log.info("Press Ctrl+C to stop\n")

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
            print(f"\nNext run in {minutes}m {seconds}s — waiting...", end="\r")
        time.sleep(30)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Swing Trading Assistant")
    parser.add_argument(
        "--mode",
        choices=["once", "schedule"],
        default="schedule",
        help="once = run once and exit | schedule = run every 15 mins"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Interval in minutes between runs (default: 15)"
    )
    args = parser.parse_args()

    if args.mode == "once":
        run_once()
    else:
        run_scheduler(args.interval)