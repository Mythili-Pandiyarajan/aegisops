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
    "database",
}


# Individual signal words rather than rigid multi-word phrases.
# Exact phrases like "failed login" miss real-world phrasing like
# "failed SSH login attempts" — requiring several distinct signal
# words to be present is more robust to natural variation while
# still avoiding a single stray word triggering a false positive.
CRITICAL_KEYWORDS = {
    "brute",
    "force",
    "credential",
    "stuffing",
    "compromise",
    "compromised",
    "unauthorized",
    "malware",
    "ransomware",
    "privileged",
    "exfiltration",
    "breach",
}


CRITICAL_KEYWORD_MIN_HITS = 2



def _security_indicator(incident: str) -> bool:

    hits = sum(
        1
        for keyword in CRITICAL_KEYWORDS
        if keyword in incident
    )

    if hits >= CRITICAL_KEYWORD_MIN_HITS:
        return True

    # Pattern fallback: repeated failed login attempts followed by
    # a success is a strong security signal even when the incident
    # text doesn't use an exact keyword like "brute force" or
    # "compromise" — e.g. "multiple failed SSH login attempts...
    # one attempt appears to have succeeded".
    failed_attempts = (
        "failed" in incident
        and "attempt" in incident
    )

    followed_by_success = any(
        word in incident
        for word in ("succeeded", "successful", "success")
    )

    return failed_attempts and followed_by_success



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


    security_indicator = _security_indicator(incident)


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
        "No log evidence available."
    )


    rag_summary = state.get(
        "rag_summary",
        "No knowledge base information available."
    )


    # Shell commands
    commands = state.get(
        "proposed_commands",
        []
    )


    command_text = (
        "\n".join(commands)
        if commands
        else "No diagnostic command proposed."
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
{priority}
Confidence: {priority_conf:.2f}


Category
--------
{category}
Confidence: {category_conf:.2f}


Risk Level
----------
{risk.upper()}


RAG Knowledge Findings
----------------------
{rag_summary}


Root Cause Analysis
-------------------
{root}


Supporting Log Evidence
-----------------------
{evidence}


Recommended Diagnostic Actions
------------------------------
{command_text}


Approval Status
---------------
{approval}


Ticket ID
---------
{ticket.get("incident_id","Unknown")}


==============================
End of Summary
==============================

"""


    return {

        "manager_summary":
            summary.strip(),

        "risk_level":
            risk,

        "incident_status":
            status,

    }
