import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_message(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] Token or chat_id not configured")
        return False
    try:
        resp = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[Telegram] Failed to send message: {e}")
        return False

def test_connection() -> bool:
    try:
        resp = requests.get(f"{BASE_URL}/getMe", timeout=10)
        data = resp.json()
        if data.get("ok"):
            print(f"[Telegram] Connected to @{data['result']['username']}")
            return True
        print(f"[Telegram] Bad response: {data}")
        return False
    except Exception as e:
        print(f"[Telegram] Failed to connect: {e}")
        return False