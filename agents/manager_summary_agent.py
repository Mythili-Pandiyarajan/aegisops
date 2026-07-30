"""
AegisOps - Manager Summary Agent

Produces an executive summary by combining:
- ML priority prediction
- Category classification
- RAG findings
- Log analysis
- Shell recommendations
- Ticket information
"""

from graph.state import AegisOpsState


HIGH_SENSITIVITY_CATEGORIES = {
    "security",
    "database"
}


CRITICAL_KEYWORDS = {
    "brute force",
    "credential stuffing",
    "account compromise",
    "unauthorized login",
    "failed login",
    "privileged account",
    "malware",
    "ransomware"
}



def _derive_risk_level(state: AegisOpsState) -> str:

    priority = state.get(
        "predicted_priority",
        "Unknown"
    )

    category = state.get(
        "predicted_category",
        ""
    ).lower()

    incident = state.get(
        "incident_text",
        ""
    ).lower()


    priority_conf = state.get(
        "priority_confidence",
        0.0
    )

    category_conf = state.get(
        "category_confidence",
        0.0
    )

    needs_review = state.get(
        "needs_human_review",
        False
    )


    # Security keyword escalation
    security_indicator = any(
        keyword in incident
        for keyword in CRITICAL_KEYWORDS
    )


    if priority == "P1":
        return "critical"


    if security_indicator and category == "security":
        return "critical"


    if (
        priority == "P2"
        and category in HIGH_SENSITIVITY_CATEGORIES
    ):
        return "critical"


    if priority == "P2":
        return "high"


    if needs_review:
        return "high"


    if (
        priority_conf < 0.60
        or category_conf < 0.60
    ):
        return "high"


    if priority == "P3":
        return "medium"


    return "low"



def run_manager_summary_agent(
        state: AegisOpsState
):

    risk = _derive_risk_level(state)


    priority = state.get(
        "predicted_priority",
        "Unknown"
    )

    priority_conf = state.get(
        "priority_confidence",
        0.0
    )


    category = state.get(
        "predicted_category",
        "Unknown"
    )

    category_conf = state.get(
        "category_confidence",
        0.0
    )


    root = state.get(
        "suspected_root_cause",
        "Log analysis pending."
    )


    evidence = state.get(
        "log_findings",
        "Log evidence pending."
    )


    command = state.get(
        "proposed_command",
        "No diagnostic command proposed."
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


    status = (
        "Requires Investigation"
        if risk in ["critical", "high"]
        else "Monitoring"
    )


    summary = f"""
==============================
AEGISOPS INCIDENT SUMMARY
==============================

Incident Status
---------------
{status}

Priority
--------
{priority} (Confidence: {priority_conf:.2f})


Category
--------
{category} (Confidence: {category_conf:.2f})


Risk Level
----------
{risk.upper()}


Root Cause Analysis
-------------------
{root}


Supporting Evidence
-------------------
{evidence}


Recommended Diagnostic Action
-----------------------------
{command}


Approval Status
---------------
{approval}


Ticket Information
------------------
{ticket}


==============================
End of Summary
==============================
"""


    return {

        "manager_summary": summary.strip(),

        "risk_level": risk,

        "incident_status": status

    }
