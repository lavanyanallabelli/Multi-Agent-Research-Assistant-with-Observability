import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# GPT-4o-mini pricing (as of 2024)
# Input:  $0.150 per 1M tokens
# Output: $0.600 per 1M tokens
# We use a blended average of $0.375 per 1M tokens for simplicity

COST_PER_1K_TOKENS = 0.000375


def calculate_cost(token_usage: dict[str, int]) -> dict:
    """
    Takes token_usage dict from state and returns cost breakdown.
    Example input:  {"sentiment": 1602, "decision": 734}
    Example output: {"sentiment": 0.0006, "decision": 0.0003, "total": 0.0009}
    """
    breakdown = {}
    total     = 0.0

    for agent, tokens in token_usage.items():
        cost             = (tokens / 1000) * COST_PER_1K_TOKENS
        breakdown[agent] = round(cost, 6)
        total           += cost

    breakdown["total"] = round(total, 6)
    return breakdown


def format_cost_report(token_usage: dict[str, int]) -> str:
    """Returns a human readable cost report string."""
    if not token_usage:
        return "No token usage recorded"

    breakdown = calculate_cost(token_usage)
    lines     = ["💸 Cost Breakdown:"]

    for agent, cost in breakdown.items():
        if agent == "total":
            continue
        tokens = token_usage.get(agent, 0)
        lines.append(f"  • {agent}: {tokens} tokens = ${cost:.6f}")

    lines.append(f"  Total: ${breakdown['total']:.6f}")
    return "\n".join(lines)