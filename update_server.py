import sys

file_path = r'd:\AI_folder\multi-agent\dashboard\server.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add imports
import_insert = """
from fastapi.responses import StreamingResponse
import time

from memory.audit_log import (
    get_system_settings, update_system_settings,
    get_trading_state, update_trading_state
)
from agents.orchestrator import run_pipeline
"""
if "get_system_settings" not in content:
    content = content.replace("import threading", "import threading\n" + import_insert)

# Add API endpoints
endpoints = """
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
                    yield f"data: {line}\\n\\n"
                
                # tail the file
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.5)
                        continue
                    yield f"data: {line}\\n\\n"
        except FileNotFoundError:
            yield f"data: Log file not found.\\n\\n"
            
    return StreamingResponse(log_generator(), media_type="text/event-stream")
"""

if "/api/settings" not in content:
    # insert before if __name__ == "__main__":
    content = content.replace('if __name__ == "__main__":', endpoints + '\nif __name__ == "__main__":')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
