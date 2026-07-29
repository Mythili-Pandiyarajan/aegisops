"""
Manager Summary Agent — final node. Produces a human-readable summary:
root cause, fix, time taken, priority, confidence, risk. This is what a
manager or on-call lead would actually read.
"""

from graph.state import AegisOpsState

# Categories where even a moderate-confidence issue deserves extra
# caution -- security incidents in particular carry asymmetric downside
# if under-escalated.
HIGH_SENSITIVITY_CATEGORIES = {"security", "database"}


def _derive_risk_level(state: AegisOpsState) -> str:
    """
    Deliberately simple, explainable rule rather than a second LLM call --
    risk classification should be auditable, not another black box on
    top of the ones already in the pipeline.
    """
    priority = state.get("predicted_priority")
    category = state.get("predicted_category")
    priority_conf = state.get("priority_confidence") or 0.0
    category_conf = state.get("category_confidence") or 0.0
    needs_review = state.get("needs_human_review", False)

    low_confidence = priority_conf < 0.6 or category_conf < 0.6

    if priority == "P2" and category in HIGH_SENSITIVITY_CATEGORIES:
        return "critical"
    if priority == "P2":
        return "high"
    if needs_review or low_confidence:
        return "high"
    if priority == "P3":
        return "medium"
    return "low"


def run_manager_summary_agent(state: AegisOpsState) -> dict:
    risk_level = _derive_risk_level(state)

    summary = (
        f"Priority: {state.get('predicted_priority')} "
        f"(confidence {state.get('priority_confidence')})\n"
        f"Category: {state.get('predicted_category')}\n"
        f"Risk level: {risk_level}\n"
        f"Root cause: {state.get('suspected_root_cause')}\n"
        f"Command output: {state.get('command_output')}\n"
        f"Ticket: {state.get('ticket_payload')}\n"
    )

    return {
        "manager_summary": summary,
        "risk_level": risk_level,
    }
