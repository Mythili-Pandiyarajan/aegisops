"""
Ticket Generator — produces a structured ticket payload (mocked, not a
live Jira/ServiceNow call). The point being demonstrated is that the
agent knows when and how to escalate, not that a live API is wired in.
See README "What this deliberately does NOT do".
"""

from graph.state import AegisOpsState


def run_ticket_generator(state: AegisOpsState) -> dict:
    ticket_payload = {
        "incident_id": state.get("incident_id"),
        "priority": state.get("predicted_priority"),
        "category": state.get("predicted_category"),
        "root_cause": state.get("suspected_root_cause"),
        "status": "open",
    }
    # TODO: log/persist ticket_payload instead of calling a real API
    return {"ticket_payload": ticket_payload}
