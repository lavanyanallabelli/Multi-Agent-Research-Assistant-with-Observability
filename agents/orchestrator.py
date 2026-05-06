import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from langgraph.graph import StateGraph, END
from memory.state import initial_state
from agents.market_data import market_data_agent
from agents.technical import technical_agent
from agents.sentiment import sentiment_agent
from agents.decision import decision_agent
from agents.risk import risk_agent
from agents.writer import writer_agent
from agents.notification import notification_agent
from typing import Any


def should_continue(state: dict) -> str:
    risk = state.get("risk_check")
    if risk and risk.get("passed"):
        return "continue"
    return "stop"


def build_graph():
    graph = StateGraph(dict)

    graph.add_node("market_data",  market_data_agent)
    graph.add_node("technical",    technical_agent)
    graph.add_node("sentiment",    sentiment_agent)
    graph.add_node("decision",     decision_agent)
    graph.add_node("risk",         risk_agent)
    graph.add_node("writer",       writer_agent)
    graph.add_node("notification", notification_agent)

    graph.set_entry_point("market_data")
    graph.add_edge("market_data",  "technical")
    graph.add_edge("technical",    "sentiment")
    graph.add_edge("sentiment",    "decision")
    graph.add_edge("decision",     "risk")

    graph.add_conditional_edges(
        "risk",
        should_continue,
        {
            "continue": "writer",
            "stop":     END,
        }
    )

    graph.add_edge("writer",       "notification")
    graph.add_edge("notification", END)

    return graph.compile()


def run_pipeline() -> dict:
    run_id = str(uuid.uuid4())
    print(f"\n{'='*50}")
    print(f"Pipeline Run: {run_id[:8]}")
    print(f"{'='*50}")

    app   = build_graph()
    state = initial_state(run_id)
    final = app.invoke(state)

    print(f"\n{'='*50}")
    print(f"Run complete")
    print(f"Alert sent: {final.get('alert_sent', False)}")
    print(f"Errors: {final.get('errors', [])}")
    print(f"Tokens used: {final.get('token_usage', {})}")
    print(f"{'='*50}\n")

    return final