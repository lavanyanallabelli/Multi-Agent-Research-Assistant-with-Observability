import sys
import os
import time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Simple in-memory tracer
# Tracks start/end time and status of each agent per run

_traces = {}


def start_trace(run_id: str, agent: str) -> None:
    key = f"{run_id}:{agent}"
    _traces[key] = {
        "run_id":     run_id,
        "agent":      agent,
        "started_at": datetime.utcnow().isoformat(),
        "start_time": time.time(),
        "status":     "running",
        "duration_ms": None,
    }


def end_trace(run_id: str, agent: str, status: str = "success") -> float:
    """
    Ends a trace and returns duration in milliseconds.
    Status: 'success' or 'failed'
    """
    key   = f"{run_id}:{agent}"
    trace = _traces.get(key)
    if not trace:
        return 0.0

    duration_ms        = (time.time() - trace["start_time"]) * 1000
    trace["status"]    = status
    trace["duration_ms"] = round(duration_ms, 2)
    trace["ended_at"]  = datetime.utcnow().isoformat()
    return duration_ms


def get_run_summary(run_id: str) -> dict:
    """Returns all traces for a given run."""
    run_traces = {
        k.split(":")[1]: v
        for k, v in _traces.items()
        if k.startswith(run_id)
    }
    return run_traces


def format_trace_report(run_id: str) -> str:
    """Returns a human readable trace report."""
    traces = get_run_summary(run_id)
    if not traces:
        return "No traces recorded"

    lines = ["⏱️  Agent Timing:"]
    total = 0.0
    for agent, trace in traces.items():
        duration = trace.get("duration_ms", 0) or 0
        status   = trace.get("status", "unknown")
        emoji    = "✅" if status == "success" else "❌"
        lines.append(f"  {emoji} {agent}: {duration:.0f}ms")
        total += duration

    lines.append(f"  Total: {total:.0f}ms")
    return "\n".join(lines)