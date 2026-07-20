"""
Manager Summary Agent — final node. Produces a human-readable summary:
root cause, fix, time taken, priority, confidence, risk. This is what a
manager or on-call lead would actually read.
"""

from graph.state import AegisOpsState


def run_manager_summary_agent(state: AegisOpsState) -> dict:
    summary = (
        f"Priority: {state.get('predicted_priority')} "
        f"(confidence {state.get('priority_confidence')})\n"
        f"Category: {state.get('predicted_category')}\n"
        f"Root cause: {state.get('suspected_root_cause')}\n"
        f"Command output: {state.get('command_output')}\n"
        f"Ticket: {state.get('ticket_payload')}\n"
    )

    return {
        "manager_summary": summary,
        "risk_level": "low",  # TODO: derive from confidence + category
    }
