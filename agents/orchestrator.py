import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from langgraph.graph import StateGraph, END
from memory.state import initial_state
from memory.audit_log import initialize_db, log_run, log_alert
from agents.market_data import market_data_agent
from agents.technical import technical_agent
from agents.sentiment import sentiment_agent
from agents.decision import decision_agent
from agents.risk import risk_agent
from agents.writer import writer_agent
from agents.notification import notification_agent
from trading.paper_trader import execute_signal, monitor_positions
from trading.circuit_breaker import run_circuit_breaker_check
from observability.tracer import start_trace, end_trace, format_trace_report
from observability.cost_tracker import format_cost_report
from agents.execution import execution_agent


def should_continue(state: dict) -> str:
    risk = state.get("risk_check")
    if risk and risk.get("passed"):
        return "continue"
    return "stop"


def wrap(agent_fn, agent_name: str):
    """Wraps an agent with start/end tracing."""
    def wrapped(state: dict) -> dict:
        run_id = state.get("run_id", "unknown")
        start_trace(run_id, agent_name)
        try:
            result = agent_fn(state)
            end_trace(run_id, agent_name, status="success")
            return result
        except Exception as e:
            end_trace(run_id, agent_name, status="failed")
            state["errors"].append(f"[{agent_name}] crashed: {e}")
            return dict(state)
    return wrapped


def paper_trader_node(state: dict) -> dict:
    """Executes paper trade after decision."""
    return execute_signal(state)


def build_graph():
    graph = StateGraph(dict)

    graph.add_node("market_data",  wrap(market_data_agent,  "market_data"))
    graph.add_node("technical",    wrap(technical_agent,    "technical"))
    graph.add_node("sentiment",    wrap(sentiment_agent,    "sentiment"))
    graph.add_node("decision",     wrap(decision_agent,     "decision"))
    graph.add_node("risk",         wrap(risk_agent,         "risk"))
    graph.add_node("paper_trader", wrap(paper_trader_node,  "paper_trader"))
    graph.add_node("execution", wrap(execution_agent, "execution"))
    graph.add_node("writer",       wrap(writer_agent,       "writer"))
    graph.add_node("notification", wrap(notification_agent, "notification"))
    

    graph.set_entry_point("market_data")
    graph.add_edge("market_data",  "technical")
    graph.add_edge("technical",    "sentiment")
    graph.add_edge("sentiment",    "decision")
    graph.add_edge("decision",     "risk")

    graph.add_conditional_edges(
        "risk",
        should_continue,
        {
            "continue": "paper_trader",
            "stop":     END,
        }
    )

    graph.add_edge("paper_trader", "writer")
    graph.add_edge("execution", "writer")
    graph.add_edge("writer", "notification")
    graph.add_edge("notification", END)

    return graph.compile()


def run_pipeline() -> dict:
    # initialize database on first run
    initialize_db()

    run_id = str(uuid.uuid4())
    print(f"\n{'='*50}")
    print(f"Pipeline Run: {run_id[:8]}")
    print(f"{'='*50}")

    # check circuit breaker before doing anything
    print("\n[CircuitBreaker] Checking...")
    if run_circuit_breaker_check():
        print("[CircuitBreaker] Trading paused — skipping pipeline")
        return {}

    app   = build_graph()
    state = initial_state(run_id)
    final = app.invoke(state)

    # monitor existing open positions
    monitor_positions(final.get("all_asset_data", []))

    # log everything to database
    log_run(final)
    if final.get("alert_sent") and final.get("alert_message"):
        alert = final["alert_message"]
        log_alert(
            alert["symbol"],
            alert["action"],
            alert["confidence"],
            alert["text"],
        )

    print(f"\n{'='*50}")
    print(format_trace_report(run_id))
    print()
    print(format_cost_report(final.get("token_usage", {})))
    print()
    print(f"Alert sent:   {final.get('alert_sent', False)}")
    print(f"Errors:       {final.get('errors', [])}")
    print(f"{'='*50}\n")

    return final