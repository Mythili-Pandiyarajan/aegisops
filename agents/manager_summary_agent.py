"""
Manager Summary Agent

Produces an executive summary for managers by combining
the outputs of all previous agents.
"""

from graph.state import AegisOpsState

HIGH_SENSITIVITY_CATEGORIES = {"security", "database"}


def _derive_risk_level(state: AegisOpsState) -> str:

    priority = state.get("predicted_priority")

    category = state.get("predicted_category")

    priority_conf = state.get("priority_confidence") or 0.0

    category_conf = state.get("category_confidence") or 0.0

    needs_review = state.get("needs_human_review", False)

    low_confidence = (
        priority_conf < 0.60 or
        category_conf < 0.60
    )

    if priority == "P1":
        return "critical"

    if (
        priority == "P2"
        and category in HIGH_SENSITIVITY_CATEGORIES
    ):
        return "critical"

    if priority == "P2":
        return "high"

    if needs_review or low_confidence:
        return "high"

    if priority == "P3":
        return "medium"

    return "low"


###############################################################


def run_manager_summary_agent(
        state: AegisOpsState
):

    risk = _derive_risk_level(state)

    priority = state.get("predicted_priority", "Unknown")

    priority_conf = state.get(
        "priority_confidence",
        0.0,
    )

    category = state.get(
        "predicted_category",
        "Unknown",
    )

    category_conf = state.get(
        "category_confidence",
        0.0,
    )

    root = state.get(
        "suspected_root_cause",
        "Not available",
    )

    evidence = state.get(
        "log_findings",
        "No evidence available.",
    )

    command = state.get(
        "proposed_command",
        "None",
    )

    ticket = state.get(
        "ticket_payload",
        {}
    )

    approval = (
        "Pending Human Approval"
        if state.get("approval_required")
        else "Not Required"
    )

    ###########################################################

    summary = f"""
==============================
AEGISOPS INCIDENT SUMMARY
==============================

Priority
--------
{priority} (Confidence: {priority_conf:.2f})

Category
--------
{category} (Confidence: {category_conf:.2f})

Risk Level
----------
{risk.upper()}

Root Cause
----------
{root}

Supporting Log Evidence
-----------------------
{evidence}

Recommended Diagnostic Command
------------------------------
{command}

Approval Status
---------------
{approval}

Ticket
------
{ticket}

==============================
End of Summary
==============================
"""

    return {

        "manager_summary": summary.strip(),

        "risk_level": risk,

    }
